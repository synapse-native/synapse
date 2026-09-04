# Regresion: el MTO OBL-M2-02 debe citar Manual 2 §5 (CONTRATOS), no §12
# (Manual 2 §12 = "Pruebas obligatorias"). El gate contrastar.seccion_existe
# solo comprueba que el numero de encabezado existe, NO que el tema coincida;
# este test aniade la verificacion semantica (Manual 2 §5 = contratos reales).
# Manual 2 §5, §12 — fuentes de verdad (gobernanza FUENTES DE VERDAD #1).
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "auditoria"))
import contrastar as ct

RAIZ = os.path.join(os.path.dirname(__file__), "..")
MTO = os.path.normpath(os.path.join(RAIZ, "docs", "manuales", "MANUAL_TESTS_OBLIGATORIOS.md"))
M2 = os.path.normpath(os.path.join(RAIZ, "docs", "manuales", "MANUAL 2.md"))


def _encabezado_seccion(num):
    txt = open(M2, encoding="utf-8", errors="replace").read().splitlines()
    for ln in txt:
        m = re.match(r"^##\s+" + re.escape(num) + r"\.\s+(.*)", ln)
        if m:
            return m.group(1)
    return None


def test_obt_m2_02_cita_seccion_contratos():
    linea = None
    for ln in open(MTO, encoding="utf-8", errors="replace").read().splitlines():
        if ln.startswith("- OBL-M2-02"):
            linea = ln
            break
    assert linea is not None, "No se encontro OBL-M2-02 en el MTO"
    assert "Manual 2 §5" in linea, f"OBL-M2-02 debe citar Manual 2 §5 (contratos), cita: {linea!r}"
    assert "Manual 2 §12" not in linea, f"OBL-M2-02 no debe citar §12 (pruebas), cita: {linea!r}"


def test_seccion_semantica_contratos_vs_pruebas():
    assert _encabezado_seccion("5") is not None and "CONTRATO" in _encabezado_seccion("5").upper()
    assert _encabezado_seccion("12") is not None and "PRUEBA" in _encabezado_seccion("12").upper()
    assert ct.seccion_existe("2", "5") is True
    assert ct.seccion_existe("2", "12") is True
