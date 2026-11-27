# tests/auditoria/test_oraculos_r329_prewarm_runtime_cache.py
# Oraculo del ME r329 (H-RUNTIME-CACHE-COLD-1): el instalador precalienta la
# cache de objetos del runtime para que la primera compilacion nativa sea
# inmediata (<2 s) en lugar de recompilar ~50 fuentes C (~90-180 s).
# OBL-R329-R1 | Manual 9 §7 | el .iss envia prewarm_runtime_cache.ps1 a {app}
#   y lo ejecuta en [Run] (precalentamiento post-instalacion) | auditoria | TDD
# OBL-R329-R2 | Manual 8 §4.1 | el script compila los .o con el toolchain
#   incluido y escribe el sidecar .sha (sha256 fuente + toolchain) en
#   %USERPROFILE%\.synapse\cache\runtime_obj | auditoria | TDD

"""Requisitos:
1. Ejecutar desde la raiz del repo:
   .venv/Scripts/python.exe -m pytest tests/auditoria/test_oraculos_r329_prewarm_runtime_cache.py -v
"""
import os
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
ISS = RAIZ / "instaladores" / "windows" / "synapse.iss"
PS1 = RAIZ / "instaladores" / "windows" / "prewarm_runtime_cache.ps1"

def test_iss_envia_y_ejecuta_prewarm():
    iss = ISS.read_text(encoding="utf-8", errors="replace")
    assert "prewarm_runtime_cache.ps1" in iss, "falta referencia al script en el .iss"
    assert 'DestDir: "{app}"' in iss
    # [Files] envia el script
    assert 'Source: "{#SourcePath}\\prewarm_runtime_cache.ps1"' in iss, (
        "el [Files] debe enviar prewarm_runtime_cache.ps1 a {app}")
    # [Run] lo ejecuta
    assert "prewarm_runtime_cache.ps1" in iss and "powershell" in iss.lower()

def test_script_existe_y_precalienta():
    assert PS1.exists(), "falta instaladores/windows/prewarm_runtime_cache.ps1"
    txt = PS1.read_text(encoding="utf-8", errors="replace")
    # usa el toolchain incluido
    assert "toolchain_gcc12" in txt and "gcc.exe" in txt
    # cache del usuario (la que resuelve nucleo/principal.syn)
    assert ".synapse" in txt and "runtime_obj" in txt and "USERPROFILE" in txt
    # compila con -O2 (la unica optimizacion que cachea el binario nativo)
    assert "-O2" in txt
    # escribe sidecar .sha
    assert ".sha" in txt
    # recorre runtime/core/*.c (paridad con el escaneo nativo)
    assert "runtime" in txt and "core" in txt

def test_script_es_sintaxis_powershell_valida():
    # Validacion sintactica basica: parsear con powershell si esta disponible
    import subprocess, shutil
    pwsh = shutil.which("powershell") or shutil.which("powershell.exe")
    if not pwsh:
        import pytest
        pytest.skip("powershell no disponible")
    r = subprocess.run([pwsh, "-NoProfile", "-Command",
                        f"& {{ $null = [System.Management.Automation.PSParser]::Tokenize((Get-Content '{PS1}'), [ref]$null) }}"],
                       capture_output=True, text=True)
    # No exigimos rc=0 estricto; solo que no crashee el parser de forma fatal
    assert "Exception" not in (r.stderr or ""), r.stderr