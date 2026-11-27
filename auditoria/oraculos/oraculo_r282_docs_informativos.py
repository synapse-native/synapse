#!/usr/bin/env python3
# cumple Manual 9 §6.1: documentacion versionada y enlazada.
# cumple Manual 1 §7.4: Definition of Done incluye documentacion actualizada.
"""Oraculo r282: cabeceras, mapas canonicos y enlaces de docs/book2-desarrollo."""

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "auditoria"))

import verificar_manuales as vm  # noqa: E402


def main() -> int:
    """Ejecuta el gate documental de book2 y devuelve su codigo de salida."""
    return vm.main(["--docs"])


if __name__ == "__main__":
    sys.exit(main())
