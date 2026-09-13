# -*- coding: utf-8 -*-
"""Tests del control de alineación (auditoria/alineacion.py + indice_manual.py).

Cubren las reglas que el rediseño agrega al control:
  - la cita textual debe existir LITERALMENTE en la sección del manual vigente
  - el ancla CUMPLE exige el comentario `cumple Manual X §Y` en el código
  - la DESVIACION no puede quedar abierta (correccion: / decision:)
  - el expediente debe cubrir exactamente los archivos del cambio
  - los oráculos se ejecutan (SKIP / sin-test / rc!=0 no es evidencia)
"""
import importlib.util
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "auditoria"))


def _cargar(nombre, archivo):
    spec = importlib.util.spec_from_file_location(nombre, RAIZ / "auditoria" / archivo)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


im = _cargar("indice_manual_test", "indice_manual.py")
al = _cargar("alineacion_test", "alineacion.py")

INDICE = im.construir_indice()


# ---------------------------------------------------------------------------
# indice_manual: normalización, ids y citas literales
# ---------------------------------------------------------------------------
def test_norm_ignora_crlf_acentos_y_markdown():
    a = im.norm("**Síntesis** de voz: `requiere` acentos\r\n")
    b = im.norm("sintesis de voz: requiere acentos")
    assert a == b


def test_id_oracion_estable_y_sensible_al_contenido():
    t = "El router decide cuál usar según la instrucción."
    assert im.id_oracion(t) == im.id_oracion(t.replace("  ", " "))
    assert im.id_oracion(t) != im.id_oracion(t + " No.")


def test_indice_indexa_secciones_y_subsecciones_reales():
    assert im.buscar_seccion(INDICE, "7", "2.4") is not None
    assert im.buscar_seccion(INDICE, "2", "1.3") is not None
    assert im.buscar_seccion(INDICE, "7", "9999") is None


def test_validar_cita_textual_acepta_oracion_real():
    oracion = im.oraciones_citables(INDICE, "7", "2.4")[0]["texto"]
    ok, msg = im.validar_cita_textual(INDICE, "7", "2.4", oracion)
    assert ok is True, msg


def test_validar_cita_textual_rechaza_parafrasis():
    ok, msg = im.validar_cita_textual(
        INDICE, "7", "2.4", "el router elige el modelo mas adecuado segun la tarea")
    assert ok is False
    assert "no aparece literalmente" in msg


def test_validar_cita_textual_rechaza_seccion_inexistente():
    ok, msg = im.validar_cita_textual(INDICE, "7", "9999", "texto cualquiera largo")
    assert ok is False
    assert "no existe" in msg


# ---------------------------------------------------------------------------
# cobertura de requisitos y parseo del expediente
# ---------------------------------------------------------------------------
def test_cubre_es_jerarquico_y_no_acepta_seccion_mas_gruesa():
    assert al.cubre(("7", "2.4"), "7", "2.4") is True
    assert al.cubre(("7", "2"), "7", "2.4") is True      # leer subsección cubre
    assert al.cubre(("7", "2.4"), "7", "2") is False     # no al revés
    assert al.cubre(("7", "2.4"), "8", "2.4") is False
    assert al.cubre(("7", ""), "7", "2.4") is True       # manual entero


def test_requisitos_archivo_prioriza_mapa_puntual():
    mapa = {"opensyn/*": ["Manual 7"], "opensyn/router.syn": ["Manual 7 §2.4"]}
    assert al.requisitos_archivo("opensyn/router.syn", mapa, {}) == [("7", "2.4")]
    assert al.requisitos_archivo("opensyn/otro.syn", mapa, {}) == [("7", "")]


def test_parsear_expediente_lee_anclas_por_archivo():
    texto = (
        "# Exp\ncambio_hash: abc123\n\n## opensyn/router.syn\n"
        "- manual: 7\n  seccion: 2.4\n  cita: \"una cita\"\n"
        "  tipo: comportamiento\n  estado: CUMPLE\n"
        "  evidencia: opensyn/router.syn:120\n"
        "  oraculo: tests/e2e_oracle_opensyn_router.py\n"
        "## opensyn/permisos.syn\n- manual: 7\n  seccion: 7.3\n"
        "  estado: DESVIACION\n  correccion: opensyn/permisos.syn:10-12\n"
    )
    exp = al.parsear_expediente(texto)
    assert exp["cambio_hash"] == "abc123"
    assert set(exp["archivos"]) == {"opensyn/router.syn", "opensyn/permisos.syn"}
    ancla = exp["archivos"]["opensyn/router.syn"][0]
    assert ancla["manual"] == "7" and ancla["seccion"] == "2.4"
    assert ancla["estado"] == "CUMPLE" and ancla["cita"] == "una cita"
    assert exp["archivos"]["opensyn/permisos.syn"][0]["correccion"].endswith("10-12")


def test_indice_desactualizado_detecta_manual_cambiado(monkeypatch, tmp_path):
    manual = tmp_path / "docs" / "manuales" / "MANUAL 7.md"
    manual.parent.mkdir(parents=True)
    manual.write_text("### 2.4. Enrutador\nEl router decide.\n", encoding="utf-8")
    monkeypatch.setattr(im, "MANUALES_DIR", manual.parent)
    indice = im.construir_indice()
    monkeypatch.setattr(al, "RAIZ", tmp_path)
    assert al.indice_desactualizado(indice) is False
    manual.write_text("### 2.4. Enrutador\nEl router decide otra cosa.\n",
                      encoding="utf-8")
    assert al.indice_desactualizado(indice) is True


def test_verificar_bloquea_indice_desactualizado(monkeypatch, tmp_path):
    exp = ("cambio_hash:\n## foo.syn\n- manual: 7\n  seccion: 2.4\n"
           "  cita: \"x\"\n  estado: PENDIENTE\n")
    _preparar(monkeypatch, tmp_path, exp, indice_ok=False)
    manual = tmp_path / "docs" / "manuales" / "MANUAL 7.md"
    manual.parent.mkdir(parents=True, exist_ok=True)
    manual.write_text("### 2.4. Enrutador\nEl router decide.\n", encoding="utf-8")
    monkeypatch.setattr(im, "MANUALES_DIR", manual.parent)
    monkeypatch.setattr(im, "INDICE", tmp_path / "docs" / "manuales" / ".indice.json")
    im.guardar_indice(im.construir_indice())
    manual.write_text("### 2.4. Enrutador\nCambió el texto.\n", encoding="utf-8")
    errores, _av, _det = al.verificar(["foo.syn"], me="ME-T", con_oraculos=False)
    assert any("índice de manuales está desactualizado" in e for e in errores)


def test_parsear_expediente_ignora_hash_comentado():
    exp = al.parsear_expediente("# Exp\ncambio_hash:   # lo completa --verificar\n")
    assert exp["cambio_hash"] == ""


def test_scaffold_incluye_requisito_y_cita_candidata():
    contenido = al.scaffold_expediente(
        "ME-T", ["opensyn/router.syn"], {"opensyn/router.syn": [("7", "2.4")]},
        INDICE)
    assert "## opensyn/router.syn" in contenido
    assert "seccion: 2.4" in contenido
    assert "estado: PENDIENTE" in contenido
    # la cita candidata sale del manual real, no de una plantilla
    assert im.validar_cita_textual(
        INDICE, "7", "2.4",
        [l for l in contenido.splitlines() if l.strip().startswith("cita:")][0]
        .split('"')[1])[0] is True


# ---------------------------------------------------------------------------
# oráculos: se ejecutan, y un SKIP no es evidencia
# ---------------------------------------------------------------------------
def test_oraculo_inexistente_falla():
    res = al.ejecutar_oraculo("tests/no_existe_jamas.py")
    assert res["ok"] is False
    assert "no existe" in res["motivo"]


def test_oraculo_pytest_verde_es_evidencia(tmp_path):
    t = tmp_path / "test_ok_gate_alineacion.py"
    t.write_text("def test_ok():\n    assert True\n", encoding="utf-8")
    res = al.ejecutar_oraculo(str(t))
    assert res["ok"] is True, res
    assert res["rc"] == 0


def test_oraculo_que_solo_tiene_skip_no_es_evidencia(tmp_path):
    t = tmp_path / "test_skip_gate_alineacion.py"
    t.write_text("import pytest\n\n"
                 "def test_x():\n    pytest.skip('sin binario')\n",
                 encoding="utf-8")
    res = al.ejecutar_oraculo(str(t))
    assert res["ok"] is False      # así se mata el falso verde de los E2E


# ---------------------------------------------------------------------------
# pipeline de verificación (hermético: RAIZ y expedientes en tmp)
# ---------------------------------------------------------------------------
def _preparar(monkeypatch, tmp_path, expediente, archivo="foo.syn",
              contenido="// sin citas\n", indice_ok=True):
    (tmp_path / "docs" / "gobernancia").mkdir(parents=True, exist_ok=True)
    (tmp_path / "docs" / "alineacion").mkdir(parents=True, exist_ok=True)
    mapa = {"foo.syn": ["Manual 7 §2.4"]}
    (tmp_path / "docs" / "gobernancia" / "mapa_alineacion.md").write_text(
        "```json\n" + json.dumps(mapa) + "\n```\n", encoding="utf-8")
    (tmp_path / archivo).write_text(contenido, encoding="utf-8")
    if expediente is not None:
        (tmp_path / "docs" / "alineacion" / "ME-T.md").write_text(
            expediente, encoding="utf-8")
    monkeypatch.setattr(al, "RAIZ", tmp_path)
    monkeypatch.setattr(al, "EXPEDIENTES_DIR", tmp_path / "docs" / "alineacion")
    monkeypatch.setattr(al, "MAPA_ALINEACION",
                        tmp_path / "docs" / "gobernancia" / "mapa_alineacion.md")
    monkeypatch.setattr(al, "MAPA_LEGACY",
                        tmp_path / "docs" / "gobernancia" / "no_existe.md")
    monkeypatch.setattr(al, "SELLO_DIR", tmp_path / ".git" / "alineacion")
    if indice_ok:
        # El índice real no vive en el tmp: sin esto el check de frescura
        # dispararía en todos los tests herméticos.
        monkeypatch.setattr(al, "indice_desactualizado", lambda _ind: False)


def test_sin_archivos_de_produccion_no_aplica(monkeypatch, tmp_path):
    _preparar(monkeypatch, tmp_path, None)
    errores, _av, detalle = al.verificar(["docs/notas.md"])
    assert errores == []
    assert detalle["archivos_produccion"] == []


def test_falta_expediente_bloquea(monkeypatch, tmp_path):
    _preparar(monkeypatch, tmp_path, None)
    errores, _av, _det = al.verificar(["foo.syn"], me="ME-T")
    assert any("falta el expediente" in e for e in errores)


def test_ancla_pendiente_bloquea(monkeypatch, tmp_path):
    exp = ("cambio_hash:\n## foo.syn\n- manual: 7\n  seccion: 2.4\n"
           "  cita: \"x\"\n  estado: PENDIENTE\n")
    _preparar(monkeypatch, tmp_path, exp)
    errores, _av, _det = al.verificar(["foo.syn"], me="ME-T")
    assert any("sin completar" in e for e in errores)


def test_desviacion_sin_correccion_ni_decision_bloquea(monkeypatch, tmp_path):
    exp = ("cambio_hash:\n## foo.syn\n- manual: 7\n  seccion: 2.4\n"
           "  cita: \"x\"\n  estado: DESVIACION\n")
    _preparar(monkeypatch, tmp_path, exp)
    errores, _av, _det = al.verificar(["foo.syn"], me="ME-T", con_oraculos=False)
    assert any("DESVIACION sin" in e for e in errores)


def test_cita_parafraseada_bloquea(monkeypatch, tmp_path):
    exp = ("cambio_hash:\n## foo.syn\n- manual: 7\n  seccion: 2.4\n"
           "  cita: \"el router elige el modelo mas adecuado\"\n"
           "  tipo: contrato\n  estado: CUMPLE\n  evidencia: foo.syn:1\n")
    _preparar(monkeypatch, tmp_path, exp)
    errores, _av, _det = al.verificar(["foo.syn"], me="ME-T", con_oraculos=False)
    assert any("no aparece literalmente" in e for e in errores)


def test_cumple_sin_cita_en_el_codigo_bloquea(monkeypatch, tmp_path):
    oracion = im.oraciones_citables(INDICE, "7", "2.4")[0]["texto"]
    exp = ("cambio_hash:\n## foo.syn\n- manual: 7\n  seccion: 2.4\n"
           f"  cita: \"{oracion}\"\n  tipo: contrato\n  estado: CUMPLE\n"
           "  evidencia: foo.syn:2\n")
    _preparar(monkeypatch, tmp_path, exp, contenido="linea1\nlinea2\nlinea3\n")
    errores, _av, _det = al.verificar(["foo.syn"], me="ME-T", con_oraculos=False)
    assert any("CUMPLE declarado sin ancla" in e for e in errores)


def test_cumple_con_ancla_real_pasa(monkeypatch, tmp_path):
    oracion = im.oraciones_citables(INDICE, "7", "2.4")[0]["texto"]
    exp = ("cambio_hash:\n## foo.syn\n- manual: 7\n  seccion: 2.4\n"
           f"  cita: \"{oracion}\"\n  tipo: contrato\n  estado: CUMPLE\n"
           "  evidencia: foo.syn:3\n")
    contenido = "linea1\nlinea2\n// cumple Manual 7 §2.4: delega al modo adecuado\n"
    _preparar(monkeypatch, tmp_path, exp, contenido=contenido)
    errores, _av, detalle = al.verificar(["foo.syn"], me="ME-T", con_oraculos=False)
    assert not errores, errores
    assert detalle["expediente"] == "docs/alineacion/ME-T.md"


def test_archivo_del_cambio_sin_ancla_bloquea(monkeypatch, tmp_path):
    exp = ("cambio_hash:\n## otro.syn\n- manual: 7\n  seccion: 2.4\n"
           "  cita: \"x\"\n  estado: PENDIENTE\n")
    _preparar(monkeypatch, tmp_path, exp)
    errores, _av, _det = al.verificar(["foo.syn"], me="ME-T", con_oraculos=False)
    assert any("no tiene bloque para: foo.syn" in e for e in errores)
