# tests/auditoria/test_r319_detect_hardware_mach_consts.py
# cumple Manual 9 §6.2: el bootstrap compila en cada target del pipeline.
"""Las constantes de `host_statistics64` viven en `mach/host_info.h`.

r318 usó `HOST_VMSTATS64`/`HOST_VMSTATS64_COUNT`, que no existen; clang en
macOS lo dijo claro (run 45210212682):

```
runtime/core/detect_hardware.c:68:36: error: 'HOST_VMSTATS64_COUNT' undeclared; did you mean 'HOST_VM_INFO64_COUNT'?
```

La pareja correcta es `HOST_VM_INFO64` + `HOST_VM_INFO64_COUNT`.
"""

from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
RUNTIME = RAIZ / "runtime" / "core" / "detect_hardware.c"


def test_constantes_mach_correctas():
    texto = RUNTIME.read_text(encoding="utf-8")
    assert "HOST_VM_INFO64_COUNT" in texto
    assert "host_statistics64(host, HOST_VM_INFO64," in texto
    assert "HOST_VMSTATS64" not in texto, "HOST_VMSTATS64 no existe en mach"


def test_incluye_mach_bajo_apple():
    lineas = RUNTIME.read_text(encoding="utf-8").splitlines()
    include = next(n for n, l in enumerate(lineas, 1) if "#include <mach/mach.h>" in l)
    assert "__APPLE__" in "\n".join(lineas[max(0, include - 4):include])


def test_page_size_se_consulta_al_kernel():
    texto = RUNTIME.read_text(encoding="utf-8")
    assert "host_page_size(host, &page_size)" in texto
