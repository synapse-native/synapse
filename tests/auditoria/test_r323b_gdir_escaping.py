"""Oraculo r323b: la extraccion de _gdir usa el escape C correcto.

cumple Manual 9 §6.2: el bootstrap nativo debe ajustar el PATH del GCC en
Windows y POSIX; un literal C multicaracter no encuentra el separador.
"""
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
PRINCIPAL = RAIZ / "nucleo" / "principal.syn"


def test_gdir_usa_cuatro_barras_en_la_fuente():
    texto = PRINCIPAL.read_text(encoding="utf-8")
    linea = next(l for l in texto.splitlines() if "strrchr(_gdir" in l)
    assert "strrchr(_gdir, '/')" in linea
    assert r"strrchr(_gdir, '\\\\')" in linea
    assert r"strrchr(_gdir, '\\\\\\\\')" not in linea
