# tests/auditoria/test_r306_hook_generados.py
# cumple Manual 1 §7.4: oráculo del ME r306 (hook no oculta generadores rotos).
"""El pre-commit no puede volver a fallar en silencio con artefactos generados.

Lecciones de r302 aplicadas al hook:
  * un generador que falla bloquea el commit (antes: "no bloqueante");
  * los borrados staged no se pasan a `sed` (ruido inofensivo pero confuso);
  * el SBOM determinista de r304 tiene gate: si deriva, se regenera y stagea.
"""

import subprocess
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
HOOK = RAIZ / "scripts" / "githooks" / "pre-commit"


def _texto():
    return HOOK.read_text(encoding="utf-8", errors="replace")


def test_hook_es_bash_valido():
    r = subprocess.run(["bash", "-n", str(HOOK)], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    assert r.returncode == 0, r.stderr


def test_ningun_generador_es_no_bloqueante():
    lineas = [l for l in _texto().splitlines()
              if "no bloqueante" in l and not l.lstrip().startswith("#")]
    assert not lineas, (
        "el hook vuelve a declarar un paso no bloqueante (lección r302): "
        f"{lineas}")


def test_check_pattern_ignora_borrados_staged():
    texto = _texto()
    inicio = texto.index("check_pattern()")
    funcion = texto[inicio:texto.index("}", inicio)]
    assert '[ -f "$f" ] || continue' in funcion, (
        "check_pattern debe saltar archivos borrados (git rm) antes de usar sed")


def test_hook_regenera_y_verifica_el_sbom():
    texto = _texto()
    assert "nucleo/sbom.py" in texto, "el hook debe invocar el generador de SBOM"
    assert "--versionados --check" in texto, "el hook debe verificar deriva del SBOM"
    assert "--versionados -o synapse.spdx.json" in texto, (
        "el hook debe regenerar el SBOM cuando deriva")
    assert "synapse.spdx.json.sha256" in texto, (
        "el hook debe recalcular el checksum del SBOM regenerado")
