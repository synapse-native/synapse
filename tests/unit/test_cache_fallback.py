# -*- coding: utf-8 -*-
"""Oraculo R229: cache persistente solo en home; degradacion efimera.

# cumple Manual 9 §1: si ~/.synapse/cache no es escribible, no se crea una
# cache persistente en workspace/temp; se compila con artefactos efimeros.
# cumple Manual 1 §3.1: el pipeline compartido sigue compilando y enlazando.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pipeline


pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def _limpiar_estado_cache():
    pipeline._CACHE_ESTADO.clear()
    pipeline._CACHE_ADVERTIDOS.clear()
    pipeline._CACHE_EPHEMERAL_MEMO.clear()
    yield
    pipeline._CACHE_ESTADO.clear()
    pipeline._CACHE_ADVERTIDOS.clear()
    pipeline._CACHE_EPHEMERAL_MEMO.clear()


def _gcc_disponible():
    try:
        return pipeline._resolver_toolchain_gcc()
    except Exception as exc:
        pytest.skip(f"toolchain C no disponible: {exc}")


def _preparar_fuente(tmp_path, monkeypatch):
    monkeypatch.setattr(pipeline, 'SYNAPSE_BIN', str(tmp_path))
    (tmp_path / 'mini.c').write_text(
        'int mini(void) { return 7; }\n', encoding='utf-8'
    )
    return _gcc_disponible()


def test_cache_no_escribible_compila_en_efimero(tmp_path, monkeypatch, capsys):
    gcc = _preparar_fuente(tmp_path, monkeypatch)
    bloqueada = tmp_path / 'cache_no_escribible'
    bloqueada.write_text('esto no es un directorio', encoding='utf-8')
    monkeypatch.setattr(pipeline, '_cache_dir', lambda: str(bloqueada))

    obj1 = pipeline._compilar_objeto_cacheado(
        gcc, '-O2', '', 'mini.c', 'mini'
    )
    assert obj1 and os.path.exists(obj1)
    assert os.path.normpath(obj1).startswith(
        os.path.normpath(str(tmp_path / 'build' / 'obj' / 'runtime_ephemeral'))
    )
    assert not (tmp_path / '.synapse_cache').exists()
    assert not (tmp_path / 'cache_no_escribible' / 'runtime_obj').exists()

    salida = capsys.readouterr()
    assert 'sin caché persistente' in salida.err

    obj2 = pipeline._compilar_objeto_cacheado(
        gcc, '-O2', '', 'mini.c', 'mini'
    )
    assert obj2 == obj1
    salida2 = capsys.readouterr()
    assert '[RUNTIME] gcc -c' not in salida2.out


def test_cache_escribible_guarda_en_home(tmp_path, monkeypatch):
    gcc = _preparar_fuente(tmp_path, monkeypatch)
    home_cache = tmp_path / 'home_cache'
    monkeypatch.setattr(pipeline, '_cache_dir', lambda: str(home_cache))

    obj1 = pipeline._compilar_objeto_cacheado(
        gcc, '-O2', '', 'mini.c', 'mini'
    )
    esperado = home_cache / 'runtime_obj' / 'mini.o'
    assert obj1 == str(esperado)
    assert os.path.exists(obj1)
    assert os.path.exists(str(esperado) + '.sha')
    assert not (tmp_path / 'build' / 'obj' / 'runtime_ephemeral').exists()

    obj2 = pipeline._compilar_objeto_cacheado(
        gcc, '-O2', '', 'mini.c', 'mini'
    )
    assert obj2 == obj1


def test_cache_ensure_dirs_no_rompe_con_home_no_escribible(
    tmp_path, monkeypatch
):
    bloqueada = tmp_path / 'cache_no_escribible'
    bloqueada.write_text('esto no es un directorio', encoding='utf-8')
    monkeypatch.setattr(pipeline, '_cache_dir', lambda: str(bloqueada))

    pipeline._cache_ensure_dirs()
    assert pipeline._cache_disponible() is False
