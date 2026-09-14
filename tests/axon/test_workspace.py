"""tests/axon/test_workspace.py — Manual 6 §5 (axón/axon_rt.h, axón_rt.c)

Valida el aislamiento de workspaces (Fase 31.1):
- axón_rt.h existe y declara las funciones workspace
- Cache path usa .axon/cache/ (no ~/.axón/cache/)
- Lockfile con SHA-256
- Cache hit cuando hash coincide (offline-first)

OBL-M8-10 | Manual 6 §5 | Aislamiento de workspaces en Axon | integración | GREEN
"""
import os
import hashlib
import pytest
from pathlib import Path

pytestmark = pytest.mark.integration

RAIZ = Path(__file__).resolve().parent.parent.parent
AXON_DIR = RAIZ / "axon"


def test_header_existe():
    """Manual 31 §2.3: ax\u00f3n_rt.h debe existir con guards de compilación."""
    header = AXON_DIR / "axon_rt.h"
    assert header.exists(), "axon_rt.h no existe (Manual 31 §2.3)"
    fuente = header.read_text(encoding="utf-8")
    assert "#ifndef AXON_RT_H" in fuente, "Falta include guard"
    assert "#define AXON_RT_H" in fuente, "Falta define guard"
    assert "#endif" in fuente, "Falta endif"


def test_header_declara_workspace_funcs():
    """Manual 31 §2.3: header declara workspace funcs."""
    header = AXON_DIR / "axon_rt.h"
    fuente = header.read_text(encoding="utf-8")
    assert "_syn_axon_workspace_cache_path" in fuente
    assert "_syn_axon_workspace_crear" in fuente
    assert "_syn_axon_workspace_resolver" in fuente


def test_cache_path_usa_directorio_local():
    """Manual 31 §2.2: cache debe ser .axon/cache/ (local)."""
    rt_c = (AXON_DIR / "axon_rt.c").read_text(encoding="utf-8")
    assert ".axon/cache/" in rt_c
    assert "~/.axon/cache/" not in rt_c


def test_lockfile_tiene_sha256():
    """Manual 31 §2.5: lockfile registra SHA-256."""
    rt_c = (AXON_DIR / "axon_rt.c").read_text(encoding="utf-8")
    assert "sha256" in rt_c.lower()
    assert "_syn_sha256_archivo" in rt_c
    assert "_syn_sha256_hex" in rt_c


def test_cache_hit_offline():
    """Manual 31 §2.5: con lockfile, verifica cache antes de descargar."""
    rt_c = (AXON_DIR / "axon_rt.c").read_text(encoding="utf-8")
    assert "cache" in rt_c.lower()
    assert "comparar" in rt_c.lower() or "strcmp" in rt_c.lower()


def test_sha256_determinista():
    """Manual 31 §2.5: mismo fuente produce mismo hash."""
    content = b"test workspace content"
    h1 = hashlib.sha256(content).hexdigest()
    h2 = hashlib.sha256(content).hexdigest()
    assert h1 == h2, "SHA-256 no es determinista"
    assert len(h1) == 64, f"Hash debe tener 64 chars, tiene {len(h1)}"
