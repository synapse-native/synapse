#!/usr/bin/env python3
"""Oráculo r275 — E2E real y privacidad de red de OpenSyn.

cumple Manual 7 §7.2, §7.3, §8; Manual 9 §5.5.

Oráculo único del plan `docs/plan_ME_r275_opensyn_e2e_bench.md`:

  tests/integration/test_opensyn_sin_red.py    (siempre; sin red ni modelo)
  tests/integration/test_opensyn_e2e_local.py  (E2E real con modelo local)

El E2E es opt-in en el test (`OPENSYN_E2E=1`) para que un CI sin modelo no
finga verde. Este runner resuelve la capacidad real del entorno (binario
`llama-server` + GGUF) y exporta el opt-in él mismo: si hay modelo, la
evidencia se ejecuta; si no lo hay, termina rc=1 con la causa concreta
(`contrastar.py` trata el SKIP como ausencia de evidencia, así que devolver 0
sin haber medido nada sería un falso verde).

Flags:
  --sin-red : sólo el gate estático de privacidad.
  --e2e     : sólo el E2E local (exige modelo; falla si no lo hay).
  (sin flags): ambos, con detección automática de capacidad.
"""
import glob
import os
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
ESTATICO = "tests/integration/test_opensyn_sin_red.py"
E2E = "tests/integration/test_opensyn_e2e_local.py"

# Mismos candidatos que el test E2E (evita dos fuentes de verdad divergentes).
SERVIDORES = (
    RAIZ / "dist" / "opensyn" / "ia" / "llama-server.exe",
    RAIZ / "dist" / "ia" / "llama-server.exe",
    Path.home() / ".opensyn" / "ia" / "llama-server.exe",
    RAIZ / "dist" / "opensyn" / "ia" / "llama-server",
    RAIZ / "dist" / "ia" / "llama-server",
    Path.home() / ".opensyn" / "ia" / "llama-server",
)
DIRECTORIOS_MODELO = (
    Path.home() / ".opensyn" / "models",
    RAIZ / "dist" / "opensyn" / "models",
    RAIZ / "dist" / "ia",
    RAIZ / "models",
)


def _opt_in():
    return os.environ.get("OPENSYN_E2E", "").strip().lower() in (
        "1", "true", "yes", "si",
    )


def _servidor():
    if os.environ.get("OPENSYN_LLAMA_SERVER"):
        ruta = Path(os.environ["OPENSYN_LLAMA_SERVER"])
        if ruta.is_file():
            return ruta
    for ruta in SERVIDORES:
        if ruta.is_file():
            return ruta
    return None


def _modelo():
    if os.environ.get("OPENSYN_GGUF"):
        ruta = Path(os.environ["OPENSYN_GGUF"])
        if ruta.is_file():
            return ruta
    for directorio in DIRECTORIOS_MODELO:
        if directorio.is_dir():
            encontrados = sorted(glob.glob(str(directorio / "*.gguf")))
            if encontrados:
                return Path(encontrados[0])
    return None


def _capacidad_e2e():
    """Devuelve (hay_capacidad, motivo)."""
    if _opt_in():
        return True, "OPENSYN_E2E ya exportado"
    servidor = _servidor()
    if servidor is None:
        return False, ("no hay llama-server (OPENSYN_LLAMA_SERVER / "
                       "dist/opensyn/ia)")
    modelo = _modelo()
    if modelo is None:
        return False, "no hay GGUF (OPENSYN_GGUF / ~/.opensyn/models/*.gguf)"
    return True, f"llama-server={servidor.name} modelo={modelo.name}"


def ejecutar(ruta, env_extra=None):
    """Ejecuta un test del plan y devuelve (rc, salida)."""
    cmd = [sys.executable, "-m", "pytest", ruta, "-q", "--no-header",
           "-p", "no:cacheprovider"]
    env = dict(os.environ)
    if env_extra:
        env.update(env_extra)
    res = subprocess.run(cmd, cwd=str(RAIZ), capture_output=True, text=True,
                         encoding="utf-8", errors="replace", timeout=900,
                         env=env)
    salida = (res.stdout or "") + (res.stderr or "")
    return res.returncode, salida


def _fallo(etiqueta, rc, salida):
    print(f"[FAIL] {etiqueta} (rc={rc})")
    print("\n".join(salida.strip().splitlines()[-12:]))


def main():
    flags = set(sys.argv[1:])
    correr_estatico = "--e2e" not in flags or "--sin-red" in flags
    correr_e2e = "--sin-red" not in flags

    if correr_estatico:
        rc, salida = ejecutar(ESTATICO)
        if rc != 0:
            _fallo("r275 gate estático", rc, salida)
            return 1
        print("[OK] r275 sin-red: endpoints locales y cero telemetría verificados")

    if correr_e2e:
        capacidad, motivo = _capacidad_e2e()
        if not capacidad:
            print(f"[FAIL] r275 E2E local: sin capacidad de ejecución — {motivo}")
            print("       instala el modelo con el instalador (Manual 9 §5.3) o "
                  "define OPENSYN_GGUF; un SKIP no es evidencia.")
            return 1
        print(f"[INFO] r275 E2E local: {motivo}")
        rc, salida = ejecutar(E2E, {"OPENSYN_E2E": "1"})
        if rc != 0:
            _fallo("r275 E2E local", rc, salida)
            return 1
        print("[OK] r275 E2E local: chat, validación, sandbox y red verificados")

    print("[OK] r275 gates ejecutados")
    return 0


if __name__ == "__main__":
    sys.exit(main())
