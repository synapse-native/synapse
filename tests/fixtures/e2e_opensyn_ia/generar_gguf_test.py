# -*- coding: utf-8 -*-
"""
Construye un GGUF sintético mínimo (determinista) para el oráculo
tests/e2e_oracle_opensyn_ia_gguf.py — Manual 7 §3.1/§3.3.

Formato escrito según el parser de runtime/core/modelo.c (_syn_gguf_abrir):
  header:   "GGUF" | version u32 | tensor_count u64 | kv_count u64
  KV:       key_len u64 | key bytes | value_type u32 | value
            (value_type 4=u32 5=i32 6=f32 7=bool 8=u64; 8=str; array=str: u32 elem_type + u64 n + n*(u64 len + bytes))
  tensores: name_len u64 | name | n_dims u32 | ne[0..n-1] u64 | type u32 | offset u64
  datos:    alineados a 32 bytes desde el fin de los tensor infos (MEM_ALIGN=32);
            dentro de cada tensor, offset relativo alineado a 16.
  Q8_0:     bloques de 32: [fp16 d][32 x int8]; des-cuantizado = int8 * d
  F32:      float crudo little-endian.

Uso: python generar_gguf_test.py [ruta_salida]
"""
import struct
import sys
import os

GGUF_MAGIC = b"GGUF"
VERSION = 3
MEM_ALIGN = 32
ALGN = 16

# Tipos GGML (valores del enum ggml, mismos que usa modelo.c)
GGML_TYPE_F32 = 0
GGML_TYPE_Q8_0 = 8


def _align(n, a):
    return (n + a - 1) // a * a


def _u32(v):
    return struct.pack("<I", v)


def _u64(v):
    return struct.pack("<Q", v)


def _f32(v):
    return struct.pack("<f", v)


def _fp16(v):
    return struct.pack("<e", v)


def _str_b(s):
    b = s.encode("utf-8")
    return _u64(len(b)) + b


def _escalar(tipo, valor):
    if tipo == 4:
        return _u32(valor)
    if tipo == 5:
        return struct.pack("<i", valor)
    if tipo == 6:
        return _f32(valor)
    if tipo == 7:
        return struct.pack("<B", 1 if valor else 0)
    if tipo == 8:
        return _u64(valor)
    raise ValueError("tipo escalar no soportado: %d" % tipo)


def _kv_par(clave, tipo, valor):
    if tipo == 8:  # STRING
        return _str_b(clave) + _u32(tipo) + _str_b(valor)
    return _str_b(clave) + _u32(tipo) + _escalar(tipo, valor)


def _kv_array_strings(clave, lista):
    # value_type 9 = ARRAY; elem_type 8 = STRING; luego u64 count y n strings
    out = _str_b(clave) + _u32(9) + _u32(8) + _u64(len(lista))
    for s in lista:
        out += _str_b(s)
    return out


class Tensory:
    def __init__(self, nombre, ne, tipo, datos):
        self.nombre = nombre
        self.ne = ne          # dims GGUF: ne[0] = dimension contigua (columnas)
        self.tipo = tipo
        self.datos = datos
        self.offset = 0


def construir_gguf(ruta):
    # Vocabulario: id 0 = BOS, id 1 = EOS (igual que eos/bos por defecto del BPE),
    # piezas de 1 char para mapeo byte->token del fallback GPT-2.
    # IMPORTANTE: la pieza resultado de cada merge debe existir en el vocab
    # (resolucion por texto exacto en modelo.c: _tokidx_buscar(first+second)).
    vocab = ["<s>", "</s>", "a", "b", "c", "d", "e", "f", "ab", "cd", "ef"]
    merges = ["a b", "c d", "e f"]

    metadatos = [
        _kv_par("general.architecture", 8, "llama"),
        _kv_par("llama.block_count", 4, 1),
        _kv_par("llama.attention.head_count", 4, 2),
        _kv_par("llama.attention.head_count_kv", 4, 1),
        _kv_par("llama.embedding_length", 4, 32),
        _kv_par("llama.feed_forward_length", 4, 64),
        _kv_par("llama.context_length", 4, 32),
        _kv_par("llama.rope.freq_base", 6, 10000.0),
        _kv_par("tokenizer.ggml.bos_id", 4, 0),
        _kv_par("tokenizer.ggml.eos_id", 4, 1),
        _kv_array_strings("tokenizer.ggml.tokens", vocab),
        _kv_array_strings("tokenizer.ggml.merges", merges),
    ]
    kv_blob = b"".join(metadatos)

    # Dimensiones coherentes: n_embd=32, n_heads=2 (head_dim=16), n_kv=1
    # (kv_dim=16), ffn=64. Solo los tensores cara-vocab (token_embd/output)
    # tienen n_vocab=11 filas; token_embd Q8_0 exige multiplo de 32 elementos
    # (11*32=352 = 11 bloques exactos).
    # Modelo determinista por construccion: embeddings Q8_0 todos >= 0, normas
    # identicas (1.0) y pesos de capa en cero (la ruta KV/FFN se ejercita igual),
    # de modo que hidden > 0 y output.weight (fila 8 = +1.0, resto -1.0) hace
    # que el argmax con temperatura 0 sea SIEMPRE el id 8 ("ab"): generacion
    # "abababab" sin fuga de EOS/BOS.
    n_embd = 32
    n_vocab = 11
    ffn = 64

    def _q8_val(r, k):
        return k % 16  # 0..15, nunca negativo => suma de hidden > 0

    def _tensor_q8_0_vocab(filas, columnas):
        nb = filas
        out = bytearray()
        for b in range(nb):
            out += _fp16(1.0)
            for i in range(32):
                out += struct.pack("<b", _q8_val(b, i))
        return bytes(out)

    def _f32_ceros(n):
        return b"".join(_f32(0.0) for _ in range(n))

    def _f32_const(n, v):
        return b"".join(_f32(v) for _ in range(n))

    def _salida_logit(i):
        r = i // n_embd
        return 1.0 if r == 8 else -1.0

    tensores = [
        Tensory("token_embd.weight", [n_embd, n_vocab], GGML_TYPE_Q8_0, _tensor_q8_0_vocab(n_vocab, n_embd)),
        Tensory("output_norm.weight", [n_embd], GGML_TYPE_F32, _f32_const(n_embd, 1.0)),
        Tensory("output.weight", [n_embd, n_vocab], GGML_TYPE_F32, b"".join(_f32(_salida_logit(i)) for i in range(n_vocab * n_embd))),
        Tensory("blk.0.attn_norm.weight", [n_embd], GGML_TYPE_F32, _f32_const(n_embd, 1.0)),
        Tensory("blk.0.attn_q.weight", [n_embd, n_embd], GGML_TYPE_F32, _f32_ceros(n_embd * n_embd)),
        Tensory("blk.0.attn_k.weight", [n_embd, 16], GGML_TYPE_F32, _f32_ceros(16 * n_embd)),
        Tensory("blk.0.attn_v.weight", [n_embd, 16], GGML_TYPE_F32, _f32_ceros(16 * n_embd)),
        Tensory("blk.0.attn_output.weight", [n_embd, n_embd], GGML_TYPE_F32, _f32_ceros(n_embd * n_embd)),
        Tensory("blk.0.ffn_norm.weight", [n_embd], GGML_TYPE_F32, _f32_const(n_embd, 1.0)),
        Tensory("blk.0.ffn_gate.weight", [ffn, n_embd], GGML_TYPE_F32, _f32_ceros(n_embd * ffn)),
        Tensory("blk.0.ffn_down.weight", [n_embd, ffn], GGML_TYPE_F32, _f32_ceros(ffn * n_embd)),
        Tensory("blk.0.ffn_up.weight", [ffn, n_embd], GGML_TYPE_F32, _f32_ceros(n_embd * ffn)),
    ]

    # Offsets de datos: base alineada a 32 tras tensor infos; cada tensor alineado a 16
    # Tamano exacto de la seccion de tensor infos (offsets no afectan su longitud):
    # por tensor: u64 len(nombre) + nombre + u32 n_dims + 8*n_dims + u32 tipo + u64 offset
    tam_infos = sum(8 + len(t.nombre.encode()) + 4 + 8 * len(t.ne) + 4 + 8 for t in tensores)
    base_datos = _align(len(GGUF_MAGIC) + 4 + 8 + 8 + len(kv_blob) + tam_infos, MEM_ALIGN)
    cur = base_datos
    for t in tensores:
        cur = _align(cur, ALGN)
        t.offset = cur - base_datos
        cur += len(t.datos)

    infos_blob = b""
    for t in tensores:
        infos_blob += _str_b(t.nombre) + _u32(len(t.ne))
        for d in t.ne:
            infos_blob += _u64(d)
        infos_blob += _u32(t.tipo)
        infos_blob += _u64(t.offset)

    out = bytearray()
    out += GGUF_MAGIC
    out += _u32(VERSION)
    out += _u64(len(tensores))
    out += _u64(len(metadatos))
    out += kv_blob
    out += infos_blob
    out += b"\x00" * (base_datos - len(out))
    for t in tensores:
        out += b"\x00" * (_align(len(out), ALGN) - len(out))
        out += t.datos

    with open(ruta, "wb") as f:
        f.write(bytes(out))
    return ruta, len(out)


if __name__ == "__main__":
    destino = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "modelo_test.gguf")
    _, tam = construir_gguf(destino)
    print("GGUF sintetico: %s (%d bytes)" % (destino, tam))
