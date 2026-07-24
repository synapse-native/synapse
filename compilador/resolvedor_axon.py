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
            f"Dependencia no declarada: {ruta_import}. "
            f"Agregar la dependencia en el bloque 'dependencias' del archivo axon.toml"
        )

    if dependencias and ruta_import in dependencias:
        return dependencias[ruta_import]

    ruta = _buscar_en(dir_base, ruta_import)
    if ruta:
        return ruta

    ruta_directa = os.path.normpath(os.path.join(dir_base, ruta_import + '.syn'))
    if os.path.exists(ruta_directa):
        return ruta_directa

    # Try with dots converted to slashes (for subdirectory imports like generador.contexto)
    ruta_subdir = os.path.normpath(os.path.join(dir_base, ruta_import.replace('.', '/') + '.syn'))
    if os.path.exists(ruta_subdir):
        return ruta_subdir

    raise DepNoDeclaradaError(f"No se pudo resolver la importacion: {ruta_import}")
