"""Oráculo r328: contratos sin comparaciones inválidas con `nulo`.

Manual 2 §5.1: `requiere`/`garantiza` solo admiten expresiones booleanas
válidas. `nulo` es un valor de tipo `nulo`; compararlo con un struct pasado
por valor genera C inválido (`invalid operands to binary !=`). El barrido
r307/r308 insertó además tautologías `_resultado_ == _resultado_` que, en
funciones que retornan structs, tampoco son C válido.

Este oráculo es estático: protege el build de stage1/stage2 sin compilar.
"""
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]

CITAS = {
    "std/json.syn": [r"\bn\s*!=\s*nulo", r"\bnodo\s*!=\s*nulo"],
    "std/cluster.syn": [r"\bch\s*!=\s*nulo"],
    "std/io.syn": [r"\bc\s*!=\s*nulo"],
    "std/net.syn": [r"\bsocket\s*!=\s*nulo"],
    "std/debug.syn": [r"\bevento\s*!=\s*nulo"],
    "std/atp_engine.syn": [
        r"\bpre\s*!=\s*nulo",
        r"\bpost\s*!=\s*nulo",
        r"\bprecondiciones\s*!=\s*nulo",
        r"\bpostcondiciones\s*!=\s*nulo",
    ],
    "nucleo/diagnostics.syn": [r"\bdiag\s*!=\s*nulo"],
    "nucleo/parser_base.syn": [r"\best\s*!=\s*nulo"],
    "nucleo/analizador_semantico.syn": [r"\best\s*!=\s*nulo"],
    "nucleo/generador/escaneo.syn": [r"\best\s*!=\s*nulo", r"\bprograma\s*!=\s*nulo"],
    "nucleo/wasm_backend.syn": [r"\best\s*!=\s*nulo"],
}


def _texto(rel):
    return (RAIZ / rel).read_text(encoding="utf-8", errors="replace")


def test_sin_comparaciones_struct_nulo_en_contratos():
    fallos = []
    for rel, patrones in CITAS.items():
        texto = _texto(rel)
        for patron in patrones:
            if re.search(patron, texto):
                fallos.append(f"{rel}: {patron}")
    assert not fallos, "comparaciones struct/nulo reintroducidas: " + ", ".join(fallos)


def test_sin_tautologia_resultado_resultado():
    fallos = []
    for rel in (
        "nucleo/lexer.syn",
        "nucleo/parser_base.syn",
        "nucleo/analizador_semantico.syn",
        "std/ai.syn",
        "std/atp_engine.syn",
        "std/federated.syn",
        "std/dist_orchestrator.syn",
        "std/quantum.syn",
        "std/net.syn",
        "std/modelo.syn",
        "std/symbolic_exec.syn",
        "std/surface_code.syn",
        "std/tensor.syn",
        "std/proof_bridge.syn",
        "std/simd.syn",
    ):
        if re.search(r"(?m)^\s*_resultado_\s*==\s*_resultado_\s*$", _texto(rel)):
            fallos.append(rel)
    assert not fallos, "tautologías _resultado_ == _resultado_: " + ", ".join(fallos)
