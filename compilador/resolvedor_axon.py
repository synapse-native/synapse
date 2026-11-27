import os
from typing import Dict, Optional

AXON_MODULES = "axon_modules"

# cumple Manual 1 §3.1: resolución de imports con fallback a la RAÍZ del
# workspace (raiz_repo). H-CFG-4: cuando el fuente vive en un subdirectorio
# (p.ej. un probe en $TEMP o tests/), `importar opensyn` debe resolver contra
# la raíz del repo — igual que cuando el fuente está en la raíz (abre/
# nucleo/, std/). Sin el fallback, el mismo import funciona o falla según
# la carpeta del fuente (test_ia_adv_10 test_opensyn_importar_compila, 15
# errores de link preexistentes en rojo).
_RAIZ_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


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

    # Convención de PAQUETE (H-CFG-4): `importar opensyn` -> <base>/opensyn/
    # principal.syn (el punto de entrada del paquete local).
    ruta_pkg = os.path.normpath(
        os.path.join(dir_base, ruta_import.replace('.', os.sep), 'principal.syn'))
    if os.path.exists(ruta_pkg):
        return ruta_pkg

    # Fallback a la RAÍZ del workspace (H-CFG-4): el módulo puede ser local
    # del repo (opensyn/, nucleo/, std/ en la raíz) aunque el fuente que
    # importa viva en un subdirectorio o un directorio temporal.
    if os.path.normpath(os.path.abspath(dir_base)) != os.path.normpath(_RAIZ_REPO):
        ruta_raiz = _buscar_en(_RAIZ_REPO, ruta_import)
        if ruta_raiz:
            return ruta_raiz
        ruta_raiz_directa = os.path.normpath(os.path.join(_RAIZ_REPO, ruta_import + '.syn'))
        if os.path.exists(ruta_raiz_directa):
            return ruta_raiz_directa
        ruta_raiz_subdir = os.path.normpath(
            os.path.join(_RAIZ_REPO, ruta_import.replace('.', '/') + '.syn'))
        if os.path.exists(ruta_raiz_subdir):
            return ruta_raiz_subdir
        ruta_raiz_pkg = os.path.normpath(
            os.path.join(_RAIZ_REPO, ruta_import.replace('.', os.sep), 'principal.syn'))
        if os.path.exists(ruta_raiz_pkg):
            return ruta_raiz_pkg

    raise DepNoDeclaradaError(f"No se pudo resolver la importacion: {ruta_import}")
