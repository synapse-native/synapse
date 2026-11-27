# -*- coding: utf-8 -*-
"""
tests/integration/test_installer_modelo_grande.py — oráculo del ME r273.

Manual 9 §5.3: "El modelo se descarga desde Hugging Face o Axon Hub, y se
verifica su integridad mediante SHA‑256."

Contrato medido por este oráculo (no modifica `tests/opensyn/test_installer.py`,
que es preexistente e inmutable):

 1. El hashing de archivo sigue siendo streaming y da el MISMO digest que
    `hashlib` (incluye tamaños que cruzan bordes de bloque de 64 B y del buffer
    de lectura).
 2. `_syn_hash_archivo` cachea el digest por ruta + tamaño + mtime y lo
    reutiliza solo cuando la entrada coincide con el archivo en disco.
 3. La caché se invalida por mtime y por tamaño, se puede desactivar con
    `SYNAPSE_HASH_CACHE=0` y no cachea archivos recién escritos (mtime < 5 s).
 4. Con el GGUF real local, el instalador reporta el tiempo de verificación
    ("Verificacion SHA-256: N ms") y termina dentro del timeout de 10 s del test
    preexistente. Sin modelo local el caso se omite: el gate nunca descarga.

No descarga nada ni requiere red.
"""
import hashlib
import os
import subprocess
import sys

import pytest

from conftest import rt_objs

pytestmark = pytest.mark.integration

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
GGUF = os.path.join(os.path.expanduser('~'), '.opensyn', 'models',
                    'deepseek-coder-1.3b-Q4_K_M.gguf')

# Sonda C: usa el runtime real (no una copia de la implementación) para que el
# oráculo mida lo que el instalador ejecuta en producción.
PROBE_C = r'''
#include "synapse_rt_types.h"
#include <stdio.h>
#include <string.h>

extern void pool_init(uint32_t total_blocks, uint32_t block_size);
extern void pool_destroy(void);
extern long long _syn_tamano_archivo_c(const char* ruta);
CadenaSegura _syn_hash_archivo(CadenaSegura ruta);
CadenaSegura _syn_sha256_archivo(const char* ruta);

int main(int argc, char** argv) {
    if (argc < 3) { fprintf(stderr, "uso: probe <hash|stream> <ruta>\n"); return 2; }
    pool_init(POOL_BLOQUES, TAMANO_BLOQUE);
    CadenaSegura salida;
    if (strcmp(argv[1], "stream") == 0) {
        salida = _syn_sha256_archivo(argv[2]);
    } else {
        CadenaSegura ruta;
        ruta.longitud = (int)strlen(argv[2]);
        ruta.datos = (const char*)argv[2];
        salida = _syn_hash_archivo(ruta);
    }
    printf("HASH %.*s\n", (int)salida.longitud, salida.datos);
    printf("TAM %lld\n", _syn_tamano_archivo_c(argv[2]));
    pool_destroy();
    return 0;
}
'''


@pytest.fixture(scope='module')
def probe(tmp_path_factory):
    """Compila una vez la sonda contra los objetos del runtime."""
    from conftest import _rt_resolver_gcc
    gcc = _rt_resolver_gcc()
    tmp = tmp_path_factory.mktemp('r273_probe')
    fuente = tmp / 'probe_r273.c'
    fuente.write_text(PROBE_C, encoding='utf-8')
    exe = tmp / 'probe_r273.exe'
    cmd = [gcc, '-O2', '-I.', '-I' + RAIZ, str(fuente)] + rt_objs() + \
          ['-lm', '-lpthread', '-lws2_32']
    if sys.platform == 'win32':
        cmd += ['-lole32', '-ldxgi', '-luuid']
    cmd += ['-o', str(exe)]
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=300, cwd=RAIZ)
    assert res.returncode == 0, f'la sonda no compiló: {res.stderr[-800:]}'
    return str(exe)


def _entorno_cache(cache_dir):
    env = dict(os.environ)
    env['SYNAPSE_HASH_CACHE_DIR'] = str(cache_dir)
    env.pop('SYNAPSE_HASH_CACHE', None)
    return env


def _probe_hash(probe, ruta, cache_dir=None, env_extra=None):
    env = _entorno_cache(cache_dir) if cache_dir is not None else dict(os.environ)
    env.pop('SYNAPSE_HASH_CACHE', None)
    if env_extra:
        env.update(env_extra)
    res = subprocess.run([probe, 'hash', str(ruta)], capture_output=True,
                         text=True, timeout=120, env=env)
    assert res.returncode == 0, res.stderr[-400:]
    lineas = dict(l.split(' ', 1) for l in res.stdout.splitlines() if ' ' in l)
    return lineas['HASH'], int(lineas['TAM'])


def _probe_stream(probe, ruta):
    env = dict(os.environ)
    env['SYNAPSE_HASH_CACHE'] = '0'  # streaming puro, sin caché de digest
    res = subprocess.run([probe, 'stream', str(ruta)], capture_output=True,
                         text=True, timeout=120, env=env)
    assert res.returncode == 0, res.stderr[-400:]
    for linea in res.stdout.splitlines():
        if linea.startswith('HASH '):
            return linea.split(' ', 1)[1].strip()
    raise AssertionError(f'sin digest en la salida: {res.stdout!r}')


def _archivo_antiguo(path, datos):
    """Escribe `datos` y envejece el mtime (la caché ignora archivos frescos)."""
    with open(path, 'wb') as f:
        f.write(datos)
    viejo = 1_600_000_000  # 2020-09-13, muy anterior a cualquier corrida
    os.utime(path, (viejo, viejo))
    return path


# ── 1. Streaming correcto: mismo digest que hashlib ────────────────────────

@pytest.mark.parametrize('tamano', [0, 1, 55, 56, 63, 64, 65, 127, 128,
                                    1024 * 1024 + 7, 4 * 1024 * 1024 + 3])
def test_sha256_streaming_coincide_con_hashlib(probe, tmp_path, tamano):
    ruta = tmp_path / f'blob_{tamano}.bin'
    patron = bytes((i * 37 + tamano) & 0xFF for i in range(4096))
    datos = (patron * (tamano // 4096 + 1))[:tamano]
    ruta.write_bytes(datos)
    assert _probe_stream(probe, ruta) == hashlib.sha256(datos).hexdigest(), \
        f'digest distinto para {tamano} bytes'


# ── 2. Caché: golpe, invalidación y opt-out ────────────────────────────────

def test_cache_guarda_y_reutiliza_digest(probe, tmp_path):
    cache = tmp_path / 'cache'
    objetivo = _archivo_antiguo(tmp_path / 'modelo.gguf', b'A' * (256 * 1024))

    primero, tam = _probe_hash(probe, objetivo, cache)
    assert primero == hashlib.sha256(b'A' * (256 * 1024)).hexdigest()
    assert tam == 256 * 1024
    entradas = list(cache.glob('*.entry'))
    assert len(entradas) == 1, f'la caché no escribió entrada: {list(cache.iterdir())}'
    contenido = entradas[0].read_text(encoding='utf-8').splitlines()
    assert contenido[0] == 'v1'
    assert int(contenido[1]) == tam
    assert int(contenido[2]) == int(os.path.getmtime(objetivo))
    assert contenido[3] == primero

    # Mismo tamaño y mismo mtime: la entrada se reutiliza (no se rehashea). Si
    # se rehasheara, el digest cambiaría porque el contenido es otro.
    with open(objetivo, 'wb') as f:
        f.write(b'B' * (256 * 1024))
    os.utime(objetivo, (1_600_000_000, 1_600_000_000))
    segundo, _ = _probe_hash(probe, objetivo, cache)
    assert segundo == primero, 'el digest cacheado no se reutilizó'


def test_cache_se_invalida_por_mtime(probe, tmp_path):
    cache = tmp_path / 'cache'
    objetivo = _archivo_antiguo(tmp_path / 'modelo.gguf', b'A' * 8192)
    primero, _ = _probe_hash(probe, objetivo, cache)

    with open(objetivo, 'wb') as f:
        f.write(b'C' * 8192)
    os.utime(objetivo, (1_600_000_100, 1_600_000_100))  # mismo tamaño, otro mtime
    segundo, _ = _probe_hash(probe, objetivo, cache)
    assert segundo == hashlib.sha256(b'C' * 8192).hexdigest()
    assert segundo != primero


def test_cache_se_invalida_por_tamano(probe, tmp_path):
    cache = tmp_path / 'cache'
    objetivo = _archivo_antiguo(tmp_path / 'modelo.gguf', b'A' * 8192)
    primero, _ = _probe_hash(probe, objetivo, cache)

    with open(objetivo, 'ab') as f:
        f.write(b'Z')
    os.utime(objetivo, (1_600_000_000, 1_600_000_000))  # mismo mtime, otro tamaño
    segundo, tam = _probe_hash(probe, objetivo, cache)
    assert tam == 8193
    assert segundo == hashlib.sha256(b'A' * 8192 + b'Z').hexdigest()
    assert segundo != primero


def test_cache_desactivable_por_entorno(probe, tmp_path):
    cache = tmp_path / 'cache'
    objetivo = _archivo_antiguo(tmp_path / 'modelo.gguf', b'A' * 4096)
    digest, _ = _probe_hash(probe, objetivo, cache,
                            env_extra={'SYNAPSE_HASH_CACHE': '0'})
    assert digest == hashlib.sha256(b'A' * 4096).hexdigest()
    assert not list(cache.glob('*.entry')), 'SYNAPSE_HASH_CACHE=0 no desactivó la caché'


def test_cache_no_guarda_archivos_recien_escritos(probe, tmp_path):
    cache = tmp_path / 'cache'
    fresco = tmp_path / 'fresco.gguf'
    fresco.write_bytes(b'A' * 4096)  # mtime = ahora (< 5 s)
    digest, _ = _probe_hash(probe, fresco, cache)
    assert digest == hashlib.sha256(b'A' * 4096).hexdigest()
    assert not list(cache.glob('*.entry')), 'se cacheó un archivo recién escrito'


# ── 3. Instalador real con el GGUF local (opt-in, sin red) ─────────────────

@pytest.mark.opensyn
def test_instalador_gguf_real_reporta_tiempo_y_cabe_en_timeout():
    """Manual 9 §6.1 / Manual 7 §6.1: el instalador no parece colgado y el test
    preexistente (timeout=10) pasa con el modelo real."""
    if not os.path.exists(GGUF):
        pytest.skip('GGUF real ausente: el gate no descarga modelos (r273)')

    exe = os.path.join(RAIZ, 'tests', 'fixtures', 'installer.exe')
    if not os.path.exists(exe):
        comp = subprocess.run([sys.executable, 'main.py', 'opensyn/installer.syn',
                               '--output', exe], capture_output=True, text=True,
                              timeout=300, cwd=RAIZ,
                              encoding='utf-8', errors='replace')
        assert comp.returncode == 0, f'installer.syn no compiló: {comp.stdout[-500:]}'

    proc = subprocess.run([exe], capture_output=True, text=True, timeout=10,
                          encoding='utf-8', errors='replace')
    assert proc.returncode == 0, f'ejecución falló: {proc.stderr[-300:]}'
    salida = proc.stdout + proc.stderr
    assert 'Verificando integridad (SHA-256)' in salida, \
        f'sin aviso previo de verificación: {salida}'
    assert 'Verificacion SHA-256:' in salida, \
        f'sin tiempo medido de verificación: {salida}'
    assert 'Modelo ya descargado y verificado' in salida
