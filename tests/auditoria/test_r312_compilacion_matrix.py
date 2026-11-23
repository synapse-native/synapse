# tests/auditoria/test_r312_compilacion_matrix.py
# cumple Manual 9 §6.1: las cuatro filas de la matriz compilan.
"""Segunda vuelta del CI: errores que solo aparecen fuera de Windows.

- `web.c`: `PATH_MAX` sin `<limits.h>` → falla en linux_x64 y linux_arm64.
- `concurrency.c`: con `_XOPEN_SOURCE` (exigido por ucontext.h en el SDK de
  macOS) Darwin no declara `_SC_NPROCESSORS_ONLN`.
- El instalador exige `dist\\bin\\opensyn.exe`, que el workflow no construía.
"""

import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]


def test_web_c_incluye_limits():
    texto = (RAIZ / "runtime" / "core" / "web.c").read_text(encoding="utf-8")
    assert "#include <limits.h>" in texto, "web.c usa PATH_MAX"
    assert texto.index("#include <limits.h>") < texto.index("char req_ruta[PATH_MAX]")


def test_darwin_cuenta_cpus_con_sysctl():
    texto = (RAIZ / "runtime" / "core" / "concurrency.c").read_text(encoding="utf-8")
    assert "defined(__APPLE__)" in texto
    assert "sysctlbyname(\"hw.ncpu\"" in texto, (
        "con _XOPEN_SOURCE, _SC_NPROCESSORS_ONLN no existe en Darwin")
    assert "#include <sys/sysctl.h>" in texto
    assert '#pragma GCC diagnostic ignored "-Wdeprecated-declarations"' in texto


def test_workflow_construye_opensyn():
    texto = (RAIZ / ".github" / "workflows" / "cross-compile.yml").read_text(encoding="utf-8")
    assert re.search(r"python main\.py opensyn/principal\.syn -o dist\\bin\\opensyn\.exe", texto), (
        "el .iss requiere dist\\bin\\opensyn.exe sin skipifsourcedoesntexist")
