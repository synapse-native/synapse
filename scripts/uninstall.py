#!/usr/bin/env python3
# scripts/uninstall.py — Desinstalador Synapse Ecosystem
# Reversa de lo instalado por instaladores/linux/install.sh y opensyn/installer.syn
# cumple Manual 9 4.1 (distribución Linux) y 9 5.4 (datos de OpenSyn)

import os
import shutil
import sys

# Paths de instalación que los instaladores del paquete crean.
HOME = os.path.expanduser("~")
OPENSYN_DIR = os.path.join(HOME, ".opensyn")            # opensyn/installer.syn (M9 §5.4)
SYS_DIR = "/opt/synapse"                                 # instaladores/linux/install.sh (M9 §4.1)
SYS_SYMLINK = "/usr/local/bin/synapse"                   # install.sh crear_enlaces()
SYS_LOG = "/var/log/synapse-install.log"                 # install.sh log()
SYS_PLATFORM = sys.platform.startswith("linux") or sys.platform == "darwin"


def _quitar_dir_sistema(ruta):
    """Intenta eliminar un directorio de sistema; False si falta permiso."""
    # En Linux/macOS el install.sh requiere root (sudo).
    if not sys.platform.startswith("linux") and not sys.platform == "darwin":
        return None  # no aplica en esta plataforma
    try:
        if os.path.isdir(ruta) and not os.path.islink(ruta):
            # Permitir escribir aunque los archivos venían de un sudo cp
            for root, dirs, files in os.walk(ruta):
                for f in files + dirs:
                    p = os.path.join(root, f)
                    try:
                        os.chmod(p, 0o755)
                    except OSError:
                        return False
            shutil.rmtree(ruta)
            return True
    except PermissionError:
        return None
    except OSError:
        return False
    return None


def listar():
    """Devuelve dict {nombre: [rutas a eliminar]} de lo instalado detectado."""
    plan = {"usuario": [], "sistema": []}
    if os.path.isdir(OPENSYN_DIR):
        plan["usuario"].append(OPENSYN_DIR)
    if SYS_PLATFORM:
        if os.path.isdir(SYS_DIR):
            plan["sistema"].append(SYS_DIR)
        if os.path.islink(SYS_SYMLINK):
            plan["sistema"].append(SYS_SYMLINK)
        if os.path.isfile(SYS_LOG):
            plan["sistema"].append(SYS_LOG)
    return plan


def imprimir(plan):
    total = len(plan["usuario"]) + len(plan["sistema"])
    if total == 0:
        print("Nada instalado por los instaladores Synapse/OpenSyn en este sistema.")
        return
    print("Artefactos instalados detectados:")
    for r in plan["usuario"] + plan["sistema"]:
        print("  - " + r)


def desinstalar(plan):
    """Elimina las rutas del plan. Devuelve (ok, errores)."""
    errores = []
    for r in plan["usuario"]:
        try:
            shutil.rmtree(r)
            print("[OK] eliminado " + r)
        except OSError as e:
            errores.append(f"{r}: {e}")
    for r in plan["sistema"]:
        if r == SYS_SYMLINK:
            try:
                os.unlink(r)
                print("[OK] enlace eliminado " + r)
            except OSError as e:
                errores.append(f"{r}: {e}")
            continue
        resultado = _quitar_dir_sistema(r) if os.path.isdir(r) else None
        if r == SYS_LOG and os.path.isfile(r):
            try:
                os.remove(r)
                print("[OK] log eliminado " + r)
                continue
            except OSError as e:
                errores.append(f"{r}: {e}")
                continue
        if resultado is False:
            errores.append(r + ": no se pudo eliminar")
        elif resultado is None and (r == SYS_DIR):
            # Falto permiso de root para un artefacto de sistema (install.sh usa sudo)
            print("[AVISO] requiere root: " + r)
            errores.append(r + ": requiere permisos de root (ejecutar con sudo)")
        elif resultado is True:
            print("[OK] directorio de sistema eliminado " + r)
    return (not errores), errores


def main():
    listado = listar()
    imprimir(listado)

    if "--list" in sys.argv or "--dry-run" in sys.argv:
        return 0

    if not (listado["usuario"] or listado["sistema"]):
        return 0

    if "--yes" not in sys.argv and sys.stdin.isatty():
        resp = input("¿Desinstalar lo listado? [s/N]: ").strip().lower()
        if resp not in ("s", "si", "y", "yes"):
            print("Cancelado por el usuario.")
            return 0

    ok, errores = desinstalar(listado)
    if errores:
        print("\nErrores:")
        for e in errores:
            print("  - " + e)
        return 1
    print("Desinstalación completada.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
