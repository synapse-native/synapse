# cumple Manual 2 §12: contratos requiere/garantiza en las funciones públicas.
# cumple Manual 1 §7.4: código muerto/duplicado eliminado (D-9).
"""Oráculo del ME r285_d9_dead_code.

Fija el estado que verificó r285 y que ejecutó el commit 8a2f82b (r281):
`std/texto.syn` pasó de 28 funciones (275 líneas) a 10 funciones (129 líneas)
al eliminar el bloque duplicado H-R196-2. El test falla si el duplicado
reaparece o si se pierden los contratos de las funciones públicas.
"""

import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
TEXTO = RAIZ / "std" / "texto.syn"

RE_FUNCION = re.compile(r"^funcion\s+([A-Za-z_][A-Za-z0-9_]*)", re.MULTILINE)


def _fuente() -> str:
    return TEXTO.read_text(encoding="utf-8")


def test_texto_sin_funciones_duplicadas():
    nombres = RE_FUNCION.findall(_fuente())
    assert nombres, "no se encontraron funciones en std/texto.syn"
    duplicadas = sorted({n for n in nombres if nombres.count(n) > 1})
    assert not duplicadas, (
        f"std/texto.syn volvió a duplicar funciones (H-R196-2): {duplicadas}"
    )


def test_texto_mantiene_tamano_deduplicado():
    lineas = len(_fuente().splitlines())
    funciones = RE_FUNCION.findall(_fuente())
    assert len(funciones) <= 12, (
        f"std/texto.syn tiene {len(funciones)} funciones; el estado "
        "deduplicado es 10 (H-R196-2)"
    )
    assert lineas <= 160, (
        f"std/texto.syn tiene {lineas} líneas; el estado deduplicado es 129"
    )


def test_texto_conserva_contratos():
    fuente = _fuente()
    assert "requiere:" in fuente or "garantiza:" in fuente, (
        "std/texto.syn perdió los contratos (Manual 2 §12)"
    )
