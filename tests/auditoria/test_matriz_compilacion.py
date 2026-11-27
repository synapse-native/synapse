# tests/auditoria/test_matriz_compilacion.py
# Oráculo matriz de compilación std.* — causa raíz R149 §4 (la frontera
# std↔runtime que ningún gate miraba). Plan ME r150_funcional, bloque final.
# OBL-R150-MATRIZ | Manual 1 §3 | TODO std/*.syn compila y enlaza con el
# runtime real (enlace completo via pipeline, no check_only) | integracion | TDD
#
# Requisitos:
# 1. Ejecutar desde la raíz: .venv/Scripts/python.exe -m pytest tests/auditoria/test_matriz_compilacion.py -v
# 2. Los probes usan TEMP (convención regla 12). Suite LENTA: timeout 300 por
#    módulo; el CI (ci-tests.yml) la invoca como job aparte.
import os
import subprocess
import sys
import tempfile

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PY = sys.executable


def _compilar_completo(ruta_syn: str, tmp: str, nombre: str) -> subprocess.CompletedProcess:
    """Compila y ENLAZA un .syn con el pipeline S1 real (no check_only).
    output_path debe terminar en .exe: el pipeline verifica la existencia de
    ESE nombre exacto (ME-R2)."""
    salida = os.path.join(tmp, nombre + ".exe")
    script = (
        "import sys;"
        "sys.path.insert(0, r'%s');"
        "from pipeline import ejecutar_compilador;"
        "sys.exit(ejecutar_compilador(r'%s', output_path=r'%s'))"
        % (RAIZ, ruta_syn, salida)
    )
    return subprocess.run([PY, "-c", script], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", cwd=tmp, timeout=600)


MODULOS_STD = [
    "agent_skills", "ai", "atp_engine", "cluster", "concurrencia", "cripto",
    "debug", "dist_orchestrator", "err", "federated", "http", "io", "json",
    "llvm", "math", "mem", "modelo", "net", "oraculo", "os",
    "proof_bridge", "quantum", "quantum_err_corr", "quantum_memory",
    "simd", "sistema", "surface_code", "symbolic_exec", "sync", "tensor",
    "testing", "texto", "tiempo", "toml", "wasm",
]


@pytest.mark.slow
@pytest.mark.parametrize("modulo", MODULOS_STD)
def test_matriz_std_importa_y_enlaza(modulo):
    """Programa mínimo por std.*: importar + llamada inocua + escribir_linea.
    Enlace COMPLETO via pipeline (no check_only) y ejecución rc=0.
    Cubre la frontera std↔runtime donde sobrevivieron R149-B3/B4."""
    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(tmp, f"matriz_{modulo}.syn")
        cuerpo = {
            "llvm": "    ctx = LLVMContextCreate()\n"
                    "    escribir_linea(entero_a_texto(LLVMContextGetErrorCount(ctx)))\n",
            "wasm": "    mod = WasmModuleCreate(\"m\")\n"
                    "    escribir_linea(entero_a_texto(WasmModuleGetWATLength(mod)))\n",
            "testing": "    escribir_linea(entero_a_texto(verificar(1 == 1, \"m\")))\n",
            "tiempo": "    escribir_linea(entero_a_texto(ahora_ms()))\n",
            "cluster": "    escribir_linea(entero_a_texto(worker_cola_vacia(0)))\n",
        }.get(modulo, "")
        programa = (
            f"#lang: es\nimportar std.{modulo}\n\n"
            f"funcion principal() -> entero:\n"
            f"{cuerpo}"
            f"    escribir_linea(\"matriz {modulo} ok\")\n"
            f"    retornar 0\n"
        )
        with open(src, "w", encoding="utf-8", newline="\n") as f:
            f.write(programa)
        r = _compilar_completo(src, tmp, f"matriz_{modulo}")
        assert r.returncode == 0, (
            f"std.{modulo}: no compila/enlaza:\n{r.stdout}\n{r.stderr[:1500]}")
        candidato = os.path.join(tmp, f"matriz_{modulo}.exe")
        run = subprocess.run([candidato], capture_output=True, text=True,
                             encoding="utf-8", errors="replace", timeout=120)
        assert run.returncode == 0, (
            f"std.{modulo}: el binario fallo rc={run.returncode}: "
            f"{run.stdout} {run.stderr[:400]}")
        assert f"matriz {modulo} ok" in run.stdout
