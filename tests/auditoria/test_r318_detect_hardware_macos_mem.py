# tests/auditoria/test_r318_detect_hardware_macos_mem.py
# cumple Manual 9 §6.2: el bootstrap compila en cada target del pipeline.
"""`_SC_AVPHYS_PAGES` es exclusivo de Linux: macOS no lo declara.

Tras r317, `release_matrix (macos-latest)` seguía fallando (run 45185835609):

```
runtime/core/detect_hardware.c:61:26: error: '_SC_AVPHYS_PAGES' undeclared (first use in this function)
```

La memoria disponible en macOS se obtiene del VM del kernel por
`host_statistics64` (`mach/mach.h`), no por `sysconf`.
"""

from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
RUNTIME = RAIZ / "runtime" / "core" / "detect_hardware.c"


def test_sin_sc_avphys_pages():
    texto = RUNTIME.read_text(encoding="utf-8")
    assert "_SC_AVPHYS_PAGES" not in texto, "macOS no declara _SC_AVPHYS_PAGES"


def test_rama_apple_usa_mach_host_statistics64():
    lineas = RUNTIME.read_text(encoding="utf-8").splitlines()
    texto = "\n".join(lineas)
    assert "#elif defined(__APPLE__)" in texto
    assert "#include <mach/mach.h>" in texto
    include = next(n for n, l in enumerate(lineas, 1) if "#include <mach/mach.h>" in l)
    contexto = "\n".join(lineas[max(0, include - 4):include])
    assert "__APPLE__" in contexto, "mach/mach.h debe incluirse solo en macOS"


def test_rama_apple_no_esta_en_el_camino_windows():
    lineas = RUNTIME.read_text(encoding="utf-8").splitlines()
    # La rama _WIN32 precede a __APPLE__: Windows no ve mach.
    win = next(n for n, l in enumerate(lineas) if l.startswith("#ifdef _WIN32"))
    apple = next(n for n, l in enumerate(lineas, 1) if "#elif defined(__APPLE__)" in l)
    assert win < apple
