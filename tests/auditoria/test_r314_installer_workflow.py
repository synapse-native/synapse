# tests/auditoria/test_r314_installer_workflow.py
# cumple Manual 9 §6.1: el job del instalador arranca y usa el build canónico.
"""`Build Synapse Installer (Fase 4.1)` fallaba en 0 s, sin jobs.

GitHub descarta el workflow entero cuando el YAML repite una clave en el mismo
mapa (`shell: powershell` dos veces), y reporta "workflow file issue" sin
ejecutar nada. Además el paso 4b usaba `main.py --output`, que no enlaza el
runtime modular, y el `.iss` exigía `dl_helper.exe`, ausente del repositorio.
"""

import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
WORKFLOW = RAIZ / ".github" / "workflows" / "build-installer.yml"
ISS = RAIZ / "instaladores" / "windows" / "synapse.iss"


def _lineas(ruta):
    return ruta.read_text(encoding="utf-8").splitlines()


def test_sin_claves_duplicadas_en_el_mismo_mapa():
    duplicadas = []
    anterior = ""
    for n, linea in enumerate(_lineas(WORKFLOW), 1):
        clave = re.match(r"^(\s*)([A-Za-z0-9_.-]+):", linea)
        if not clave or not anterior:
            anterior = linea
            continue
        duplicada = re.match(r"^(\s*)([A-Za-z0-9_.-]+):", anterior)
        if duplicada and duplicada.group(1) == clave.group(1) \
                and duplicada.group(2) == clave.group(2):
            duplicadas.append(f"{n}: {linea.strip()}")
        anterior = linea
    assert not duplicadas, (
        "GitHub descarta el workflow cuando una clave se repite en el mismo "
        "mapa:\n" + "\n".join(duplicadas))


def test_workflow_usa_build_canonico():
    texto = WORKFLOW.read_text(encoding="utf-8")
    assert re.search(r"^\s*python build\.py\s*$", texto, re.MULTILINE)
    assert "--output dist/bin/synapse.exe" not in texto, (
        "main.py --output no enlaza el runtime modular")
    assert "opensyn/principal.syn -o dist\\bin\\opensyn.exe" in texto


def test_iss_no_exige_artefactos_ausentes():
    lineas = [l for l in _lineas(ISS) if l.startswith("Source:")]
    for linea in lineas:
        ruta = re.search(r'Source: "([^"]+)"', linea)
        if not ruta:
            continue
        destino = ruta.group(1).replace("{#SourcePath}", "").replace("\\", "/")
        if ".." in destino:
            continue
        archivo = RAIZ / "instaladores" / "windows" / destino.lstrip("/")
        if not archivo.exists():
            assert "skipifsourcedoesntexist" in linea, (
                f"el .iss exige un archivo que no está en el repo: {destino}")
