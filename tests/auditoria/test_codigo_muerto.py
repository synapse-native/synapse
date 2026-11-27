#!/usr/bin/env python3
# cumple Manual 1 §7.4: Definition of Done sin código muerto.
"""Oráculo del barrido de código muerto (ME r299_codigo_muerto).

Verifica que:
1. el auditor de código muerto existe y es ejecutable;
2. el alcance son los módulos alcanzables desde el build (principal.syn),
   no el filesystem;
3. no quedan funciones sin referencias en el código que se enlaza.
"""

import json
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
AUDITOR = RAIZ / "auditoria" / "verificar_codigo_muerto.py"


def _ejecutar(*args):
    return subprocess.run(
        [sys.executable, str(AUDITOR), *args],
        cwd=RAIZ, capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )


def test_auditor_existe_y_corre():
    assert AUDITOR.is_file(), "falta auditoria/verificar_codigo_muerto.py"
    r = _ejecutar("--json")
    assert r.returncode == 0, r.stdout + r.stderr


def test_alcance_son_modulos_del_build():
    datos = json.loads(_ejecutar("--json").stdout)
    modulos = set(datos["modulos_alcance"])
    assert "nucleo/principal.syn" in modulos
    assert "nucleo/cache.syn" in modulos
    assert "nucleo/formatter.syn" in modulos
    # Los backends standalone no se importan ni figuran en `_files[]`:
    # son corpus de tests, no código enlazado en el binario.
    assert "nucleo/llvm_backend.syn" not in modulos
    assert "nucleo/wasm_backend.syn" not in modulos
    assert "nucleo/llvm_backend.syn" in datos["modulos_fuera"]


def test_sin_funciones_muertas():
    r = _ejecutar("--estricto")
    assert r.returncode == 0, r.stdout + r.stderr
    datos = json.loads(_ejecutar("--json").stdout)
    assert datos["muertas"] == []


def test_funciones_podadas_no_reaparecen():
    muertas_por_poda = {
        "nucleo/cache.syn": [
            "_calcular_hash_archivo",
            "_obtener_hashes_dependencias",
            "_leer_flags_compilacion",
            "_resolver_ruta_import",
        ],
        "nucleo/formatter.syn": ["formatear_archivo", "fmt_directorio"],
    }
    for archivo, nombres in muertas_por_poda.items():
        texto = (RAIZ / archivo).read_text(encoding="utf-8")
        for nombre in nombres:
            assert f"funcion {nombre}(" not in texto, f"{archivo}: {nombre} volvió"
