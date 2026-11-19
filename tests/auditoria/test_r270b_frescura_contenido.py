# -*- coding: utf-8 -*-
"""Oráculo r270b: frescura del bootstrap por contenido, no por mtime (H-R252-5).

El guard de `synapse_stage2.exe` comparaba `mtime` contra
`nucleo/principal.syn`, así que un `git checkout` o un guardado del editor
—mismo contenido— ponía el sello en rojo y obligaba a reconstruir la cadena.
Estos tests fijan el comportamiento nuevo: con `synapse_stage2.stamp` manda el
SHA-256 de la fuente; sin sello se conserva el criterio anterior con aviso.
"""
import importlib.util
import json
import os

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RUTA_ORACULO = os.path.join(
    RAIZ, "auditoria", "oraculos", "oraculo_r252_paridad_bootstrap.py"
)


def _cargar():
    especificacion = importlib.util.spec_from_file_location(
        "oraculo_r270b", RUTA_ORACULO
    )
    modulo = importlib.util.module_from_spec(especificacion)
    especificacion.loader.exec_module(modulo)
    return modulo


def _escribir(ruta, contenido, mtime=None):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_bytes(contenido)
    if mtime is not None:
        os.utime(ruta, (mtime, mtime))


def _escenario(tmp_path, contenido_fuente=b"fuente", contenido_binario=b"igual"):
    """Deja etapa 2 == etapa 3 y la fuente en disco; devuelve la ruta de la fuente."""
    fuente = tmp_path / "nucleo" / "principal.syn"
    _escribir(fuente, contenido_fuente)
    _escribir(tmp_path / "synapse_stage2.exe", contenido_binario)
    _escribir(tmp_path / "synapse_stage3.exe", contenido_binario)
    return fuente


def _sellar(oraculo, tmp_path, fuente):
    oraculo._escribir_sello(
        str(tmp_path),
        oraculo.sha256(str(fuente)),
        oraculo.sha256(str(tmp_path / "synapse_stage2.exe")),
        3,
    )


def test_tocar_solo_el_mtime_de_la_fuente_no_invalida_el_bootstrap(tmp_path):
    """El falso rojo de H-R252-5: mismo contenido, mtime más nuevo."""
    oraculo = _cargar()
    fuente = _escenario(tmp_path)
    ahora = os.path.getmtime(str(fuente))
    _sellar(oraculo, tmp_path, fuente)

    # Sólo se toca la hora: el contenido no cambia.
    os.utime(str(fuente), (ahora + 3600, ahora + 3600))

    ok, lineas = oraculo.comparar_artefactos(str(tmp_path))
    assert ok is True, lineas
    assert any("sello de frescura" in linea for linea in lineas), lineas
    assert not any("[FAIL]" in linea for linea in lineas), lineas


def test_fuente_modificada_despues_del_build_falla(tmp_path):
    """Si el contenido cambia, la etapa 2 no corresponde al código actual."""
    oraculo = _cargar()
    fuente = _escenario(tmp_path)
    _sellar(oraculo, tmp_path, fuente)

    _escribir(fuente, b"fuente con un cambio real")

    ok, lineas = oraculo.comparar_artefactos(str(tmp_path))
    assert ok is False, lineas
    assert any("cambio desde el build" in linea for linea in lineas), lineas


def test_sin_sello_avisa_y_conserva_el_criterio_de_mtime(tmp_path):
    """Un checkout limpio no tiene `.stamp`: el criterio anterior sigue vigente."""
    oraculo = _cargar()
    fuente = _escenario(tmp_path)
    ahora = os.path.getmtime(str(fuente))
    # Etapa 2 anterior a la fuente y sin sello: se rechaza como antes.
    os.utime(str(fuente), (ahora + 3600, ahora + 3600))

    ok, lineas = oraculo.comparar_artefactos(str(tmp_path))
    assert ok is False, lineas
    assert any("[WARN] sin synapse_stage2.stamp" in linea for linea in lineas), lineas
    assert any("es anterior a" in linea for linea in lineas), lineas


def test_sellar_escribe_el_hash_del_contenido(tmp_path, monkeypatch, capsys):
    oraculo = _cargar()
    fuente = _escenario(tmp_path)
    monkeypatch.setattr(oraculo, "RAIZ", str(tmp_path))

    assert oraculo.main(["--artefactos", "--sellar"]) == 0
    assert "sello de frescura escrito" in capsys.readouterr().out

    sello = json.loads((tmp_path / "synapse_stage2.stamp").read_text(encoding="utf-8"))
    assert sello["sha256_fuente"] == oraculo.sha256(str(fuente))
    assert sello["sha256_etapa2"] == oraculo.sha256(
        str(tmp_path / "synapse_stage2.exe")
    )


def test_sellar_no_certifica_un_bootstrap_que_no_pasa(tmp_path, monkeypatch):
    """El sello se escribe sólo después de verificar: nunca tapa un fallo."""
    oraculo = _cargar()
    fuente = _escenario(tmp_path, contenido_binario=b"etapa")
    _escribir(tmp_path / "synapse_stage3.exe", b"otra etapa")
    ahora = os.path.getmtime(str(fuente))
    os.utime(str(fuente), (ahora + 3600, ahora + 3600))
    monkeypatch.setattr(oraculo, "RAIZ", str(tmp_path))

    assert oraculo.main(["--artefactos", "--sellar"]) == 1
    assert not (tmp_path / "synapse_stage2.stamp").exists()
