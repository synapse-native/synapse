# -*- coding: utf-8 -*-
"""
tests/auditoria/test_oraculos_r182a_wasm_valido.py — Manual 1 §5 + Manual 8 §4.2

Criterio (ME r182a, Fase 25):
- Manual 1 §5: "Traduce el AST validado a código intermedio: C (C99/C11),
  LLVM IR o WAT (WASM)." → el WAT emitido por `synapse build --target wasm`
  debe ser VÁLIDO (wat2wasm rc=0, magic \0asm).
- Manual 8 §4.2: "| --target | native, wasm, llvm (por defecto native). |" →
  el pipeline resuelve wat2wasm local (emsdk/wabt) y emite el .wasm.
"""
import os
import subprocess
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


def _buscar_wat2wasm():
    import shutil
    import glob
    for c in ("wat2wasm", "wat2wasm.exe"):
        p = shutil.which(c)
        if p:
            return p
    for patron in ('C:/emsdk/node/*/wat2wasm.CMD',
                   'C:/emsdk/node/*/wat2wasm.cmd',
                   'C:/emsdk/node/*/wat2wasm.exe'):
        hallados = sorted(glob.glob(patron))
        if hallados:
            return hallados[0]
    return None


def _compilar_wasm(nombre, fuente, tmp_path):
    """Compila fuente .syn con --target wasm; retorna (rc, ruta_wat, ruta_wasm)."""
    syn = tmp_path / nombre
    syn.write_text(fuente, encoding='utf-8')
    base = str(tmp_path / nombre[:-4])
    r = subprocess.run(
        [sys.executable, '-X', 'utf8', os.path.join(RAIZ, 'cli.py'),
         'build', str(syn), '--target', 'wasm'],
        capture_output=True, text=True, encoding='utf-8', errors='replace',
        cwd=RAIZ, timeout=120)
    return r, base + '.wat', base + '.wasm'


FUENTE = """#lang: es
funcion suma(a: entero, b: entero) -> entero:
    retornar a + b

funcion clasificar(n: decimal) -> texto:
    si n > 0.0:
        retornar "positivo"
    sino:
        retornar "no positivo"

funcion cuenta(n: entero) -> entero:
    let total = 0
    let i = 0
    mientras i < n:
        total = total + i
        i = i + 1
    retornar total

funcion principal() -> nulo:
    escribir_linea(entero_a_texto(suma(2, 3)))
    escribir_linea(clasificar(3.5))
    escribir_linea(entero_a_texto(cuenta(5)))
"""


class TestOraculoR182aWasmValido:
    """Manual 1 §5: WAT emitido válido; Manual 8 §4.2: --target wasm operativa."""

    def test_wat_valido_por_wat2wasm(self, tmp_path):
        wat2wasm = _buscar_wat2wasm()
        if not wat2wasm:
            pytest.skip("wat2wasm no disponible en esta estación")
        r, wat_path, wasm_path = _compilar_wasm('oraculo_r182a.syn', FUENTE, tmp_path)
        assert r.returncode == 0, f"compilación falló: {r.stdout[-400:]} {r.stderr[-400:]}"
        assert os.path.exists(wat_path), "no se generó .wat"

        v = subprocess.run([wat2wasm, wat_path, '-o', str(tmp_path / 'v.wasm')],
                           capture_output=True, text=True, timeout=60)
        assert v.returncode == 0, f"WAT inválido: {v.stderr}"

    def test_wasm_magic_y_export_entrada(self, tmp_path):
        r, wat_path, wasm_path = _compilar_wasm('oraculo_r182a.syn', FUENTE, tmp_path)
        assert r.returncode == 0
        assert "[OK] WASM generado" in r.stdout, "el pipeline no resolvió wat2wasm"
        assert os.path.exists(wasm_path), "no se generó .wasm"
        with open(wasm_path, 'rb') as f:
            magic = f.read(4)
        assert magic == b'\x00asm', f"magic WASM inválido: {magic!r}"
        wat = open(wat_path, encoding='utf-8').read()
        assert '(export "principal"' in wat, "falta export del punto de entrada"
        assert '(import "env" "escribir_linea"' in wat, \
            "llamada externa no declarada como import"

    def test_determinismo_wat(self, tmp_path):
        r1, wat1, _ = _compilar_wasm('det1.syn', FUENTE, tmp_path)
        r2, wat2, _ = _compilar_wasm('det2.syn', FUENTE, tmp_path)
        assert r1.returncode == 0 and r2.returncode == 0
        h1 = open(wat1, 'rb').read()
        h2 = open(wat2, 'rb').read()
        # Manual 1 §5: "Emite funciones en orden alfabético (determinismo)" —
        # el WAT de dos compilaciones del mismo fuente es idéntico byte a byte.
        assert h1 == h2, "WAT no determinista entre compilaciones"

    def test_imports_antes_de_definiciones(self, tmp_path):
        r, wat_path, _ = _compilar_wasm('orden.syn', FUENTE, tmp_path)
        assert r.returncode == 0
        wat = open(wat_path, encoding='utf-8').read()
        idx_import = wat.index('(import ')
        idx_func = wat.index('(func ')
        assert idx_import < idx_func, \
            "import después de definición (wat2wasm lo rechaza)"
