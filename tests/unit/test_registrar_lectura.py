"""
test_registrar_lectura.py — gate de lectura previa (regla 1).

Prueba las funciones puras del registrador contra fixtures temporales:
carga del mapa, parseo/validación de citas (anti-fabricación de §N) y
cobertura de requisitos. No muta el repo real.
"""

import importlib.util
import json
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
SCRIPT = RAIZ / "auditoria" / "registrar_lectura.py"

spec = importlib.util.spec_from_file_location("registrar_lectura", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def _raiz_tmp(tmp_path, secciones="## 1. COSAS\n### 1.1. Sub\n## 13. PRUEBAS\n"):
    """Crea un árbol raíz falso con mapa + manual 6 y retorna el módulo
    reconfigurado a esa raíz."""
    manuales = tmp_path / "docs" / "manuales"
    manuales.mkdir(parents=True)
    (manuales / "MANUAL 6.md").write_text("# MANUAL 6\n" + secciones,
                                          encoding="utf-8")
    (tmp_path / "docs" / "mapa_manuales.md").write_text(
        "```json\n"
        '{"syquex/traductor.syn": ["Manual 6 \\u00a71.3"],'
        ' "nucleo/*": ["Manual 6"]}\n'
        "```\n",
        encoding="utf-8")
    mod.MAPA_MD = tmp_path / "docs" / "mapa_manuales.md"
    mod.MANUALES_DIR = manuales
    return tmp_path


def test_mapa_carga(tmp_path):
    _raiz_tmp(tmp_path)
    mapa = mod.cargar_mapa()
    assert "syquex/traductor.syn" in mapa
    assert any("\u00a7" in c for c in mapa["syquex/traductor.syn"])


def test_cita_valida_con_seccion_existente(tmp_path):
    _raiz_tmp(tmp_path)
    assert mod.validar_cita("Manual 6 §1") == []
    assert mod.validar_cita("Manual 6 §13; Manual 6 §1.1") == []


def test_cita_fabricada_rechazada(tmp_path):
    _raiz_tmp(tmp_path)
    errores = mod.validar_cita("Manual 6 §99")
    assert any("fabricada" in e or "no existe" in e for e in errores)
    errores2 = mod.validar_cita("Manual 42 §1")
    assert any("inexistente" in e for e in errores2)


def test_cita_sin_manual_rechazada():
    with pytest.raises(ValueError):
        mod.parsear_cita("sección 3 sin manual")


def test_resolver_requisitos_primer_match_gana(tmp_path):
    _raiz_tmp(tmp_path)
    mapa = mod.cargar_mapa()
    reqs, sin_mapa = mod.resolver_requisitos(
        ["syquex/traductor.syn", "nucleo/foo.syn", "tests/x.py",
         "nuevo/foo.syn"],
        mapa)
    assert reqs["syquex/traductor.syn"] == ["Manual 6 §1.3"]
    assert reqs["nucleo/foo.syn"] == ["Manual 6"]
    assert "tests/x.py" not in reqs      # excluido: no producción
    assert "nuevo.xyz" not in reqs       # extensión ajena: no producción
    assert sin_mapa == ["nuevo/foo.syn"]  # productivo sin mapear


def test_cobertura_parcial_detecta_faltante(tmp_path):
    _raiz_tmp(tmp_path)
    reqs = {"syquex/traductor.syn": ["Manual 6 §1.3"]}
    # lectura del manual entero NO cubre la sección puntual exigida
    ok, ruta, cita = mod.cobertura(reqs, [{"fecha": "x", "cita": "Manual 6"}])
    assert ok is False
    assert ruta == "syquex/traductor.syn"
    ok2, _, _ = mod.cobertura(reqs, [{"fecha": "x", "cita": "Manual 6 §1.3"}])
    assert ok2 is True


def test_cobertura_manual_entero_cubierto_por_seccion(tmp_path):
    _raiz_tmp(tmp_path)
    reqs = {"nucleo/foo.syn": ["Manual 6"]}
    ok, _, _ = mod.cobertura(reqs, [{"fecha": "x", "cita": "Manual 6 §1.3"}])
    assert ok is True


def test_cobertura_jerarquica_subseccion_cubre_padre(tmp_path):
    _raiz_tmp(tmp_path)
    reqs = {"syquex/traductor.syn": ["Manual 3 §11"]}
    # §11.2 (subsección leída) cubre el requisito §11 (sección contenedora)
    ok, _, _ = mod.cobertura(reqs, [{"fecha": "x", "cita": "Manual 3 §11.2"}])
    assert ok is True
    # una subsección de OTRA sección no cubre
    ok2, _, _ = mod.cobertura(reqs, [{"fecha": "x", "cita": "Manual 3 §10.1"}])
    assert ok2 is False
