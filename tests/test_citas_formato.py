# Verificacion del gate MTS: parser de citas `// cumple Manual X [§] Y.Z`.
# Manual 1 §3.1: comentario de cita grep-chequeable anclado a la construccion real.
# Regla 5: los tests son inmutables y derivados del comportamiento especificado.
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "auditoria"))
import contrastar as ct


def _write_tmp(src):
    p = os.path.join(tempfile.gettempdir(), "t_citas_fmt.syn")
    with open(p, "w", encoding="utf-8") as f:
        f.write(src)
    return p


def test_formato_espacio_sin_sect_signo():
    p = _write_tmp("// cumple Manual 8 1.2\nfuncion x() {}\n")
    citas = ct.citas_archivo(p)
    assert ("8", "1.2") in citas
    os.remove(p)


def test_formato_canonical_con_sect_signo():
    p = _write_tmp("# cumple Manual 2 §8.2\n")
    citas = ct.citas_archivo(p)
    assert ("2", "8.2") in citas
    os.remove(p)


def test_subseccion_y_multiples_citas():
    p = _write_tmp(
        "// cumple Manual 9 5.7: VRAM\n"
        "// cumple Manual 2 §4.1: tipos\n"
        "x = 1\n"
    )
    citas = ct.citas_archivo(p)
    assert ("9", "5.7") in citas
    assert ("2", "4.1") in citas
    os.remove(p)


def test_seccion_existe_real_y_fabricada():
    assert ct.seccion_existe("2", "5") is True
    assert ct.seccion_existe("2", "12") is True
    assert ct.seccion_existe("2", "999") is False


def test_citas_archivo_productivo_real():
    p = os.path.join(os.path.dirname(__file__), "..", "nucleo", "ast_nodes.c")
    citas = ct.citas_archivo(p)
    assert ("2", "4.1") in citas
