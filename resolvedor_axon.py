import os
from typing import Dict, Optional

AXON_MODULES = "axon_modules"


class DepNoDeclaradaError(ValueError):
    pass


def _buscar_en(dir_base: str, ruta_import: str) -> Optional[str]:
    ruta_axon = os.path.normpath(
        os.path.join(dir_base, AXON_MODULES, ruta_import, "principal.syn")
    )
    if os.path.exists(ruta_axon):
        return ruta_axon

    ruta_axon_plano = os.path.normpath(
        os.path.join(dir_base, AXON_MODULES, ruta_import.replace('.', '/') + '.syn')
    )
    if os.path.exists(ruta_axon_plano):
        return ruta_axon_plano

    return None


def resolver(ruta_import: str, dir_base: str,
             dependencias: Optional[Dict[str, str]] = None) -> str:
    if dependencias is not None and ruta_import not in dependencias:
        raise DepNoDeclaradaError(
            f"Dependencia '{ruta_import}' importada en el código "
            f"pero no declarada en el manifiesto axon.toml"
        )

    resultado = _buscar_en(dir_base, ruta_import)
    if resultado:
        return resultado

    cwd = os.getcwd()
    if cwd != dir_base:
        resultado = _buscar_en(cwd, ruta_import)
        if resultado:
            return resultado

    raise FileNotFoundError(
        f"Módulo '{ruta_import}' no encontrado en '{AXON_MODULES}/'"
    )
