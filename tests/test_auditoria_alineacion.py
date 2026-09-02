# Verificacion del verificador de alineacion (auditoria/verificar_alineacion.py).
# Manual 1 §1 (fundamentos del lenguaje).
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "auditoria"))
import verificar_alineacion as va


def test_encabezados_md():
    assert va.encabezados_md("# 5 titulo") == {5}
    assert va.encabezados_md("## 4.2 subtitulo") == {4}


def test_limpiar_ref():
    assert va.limpiar_ref("nucleo/foo.py:123") == "nucleo/foo.py"
    assert va.limpiar_ref("nucleo/foo.py:12-18") == "nucleo/foo.py"
    assert va.limpiar_ref("a/b.py::metodo") == "a/b.py"


def test_seccion_es_de_manual():
    detalle = "cumple Manual 2 3 en el codigo"
    pos = detalle.index("§")
    assert va.seccion_es_de_manual(detalle, pos) is True
    detalle2 = "la seccion §3 del informe"
    pos2 = detalle2.index("§")
    assert va.seccion_es_de_manual(detalle2, pos2) is False


def test_cargar_canon_deudas():
    canon = va.cargar_canon_deudas()
    assert "D-9" in canon
    assert canon["D-9"]["estado"] == "CERRADA"


def test_extraer_filas_bitacora():
    texto = "| 2026-08-31 | tarea X | ✅ | detalle con reporte R_A.md y hash abc1234 |\n"
    filas = va.extraer_filas_bitacora(texto)
    assert len(filas) == 1
    assert filas[0]["estado"].startswith("✅")
