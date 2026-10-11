#!/usr/bin/env python3
# oraculo_r183d.py — Oráculo E2E del ME r183d (dispatcher nativo: flags UX)
# cumple Manual 8 §4.2 (ME r183d R1/R2)
"""
Oráculo del ME r183d: el dispatcher nativo synapse.exe debe aceptar los
flags globales `--version`/`--help` (M8 §4.2) sin tratarlos como archivo,
validar `--target/--release/--debug/--safe/--output/-o` sin entrarlos como
archivo a la pipeline (hallazgos REAL-1 y REAL-4b del reporte R182c), y el
fallback de salida NO debe sobrescribir el compilador autoalojado
(synapse_stage2.exe debe quedar byte-idéntico tras compilar probes sin -o).

Marca de PASS: "OK: r183d PASS (N/N)" en stdout, rc=0 (convención del gate).
"""
import hashlib
import os
import subprocess
import sys
import tempfile

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
EXE = os.path.join(RAIZ, "synapse.exe")

PROBE_FUENTE = """#lang: es
funcion principal():
    escribir_linea("OK_R183D")
"""

RESULTADOS = []


def _exe():
    if not os.path.exists(EXE):
        print("FALTA: synapse.exe no existe")
        sys.exit(1)
    return EXE


def _correr(args, timeout=300):
    return subprocess.run([_exe()] + args, cwd=RAIZ, capture_output=True,
                          text=True, encoding="utf-8", errors="replace",
                          timeout=timeout)


def _chequear(nombre, cond, detalle=""):
    RESULTADOS.append((nombre, cond, detalle))
    marca = "OK" if cond else "FAIL"
    print(f"oraculo_r183d: [{marca}] {nombre} {detalle}".rstrip())
    return cond


def test_r1_version():
    r = _correr(["--version"])
    _chequear("R1 --version rc=0", r.returncode == 0, f"rc={r.returncode}")
    _chequear("R1 --version imprime versión",
              "Synapse Compiler" in (r.stdout or ""), (r.stdout or "").strip())


def test_r1_help():
    r = _correr(["--help"])
    _chequear("R1 --help rc=0", r.returncode == 0, f"rc={r.returncode}")
    _chequear("R1 --help imprime uso",
              "Uso:" in (r.stdout or "") + (r.stderr or ""))


def test_r2_prescan_target_wasm():
    # M8 §4.2: `synapse <archivo> --target wasm` debe compilar (nativo) y el
    # El target va al warning, no a la pipeline (hallazgo REAL-4b).
    with tempfile.TemporaryDirectory() as d:
        probe = os.path.join(d, "probe_r183d_t.syn")
        with open(probe, "w", encoding="utf-8") as f:
            f.write(PROBE_FUENTE)
        r = _correr([probe, "--target", "wasm"], timeout=600)
        _chequear("R2 --target wasm rc=0", r.returncode == 0,
                  f"rc={r.returncode}")
        _chequear("R2 --target wasm NO entra como archivo",
                  "Archivo no encontrado: wasm" not in (r.stdout or "") +
                  (r.stderr or ""))


def test_r2_flags_modo():
    with tempfile.TemporaryDirectory() as d:
        probe = os.path.join(d, "probe_r183d_m.syn")
        with open(probe, "w", encoding="utf-8") as f:
            f.write(PROBE_FUENTE)
        for flag in ("--release", "--debug", "--safe"):
            r = _correr([probe, flag], timeout=600)
            _chequear(f"R2 {flag} rc=0", r.returncode == 0,
                      f"rc={r.returncode}")


def test_r3_fallback_no_destruye_compilador():
    # Fallback de salida <archivo>.exe: compilar sin -o NO debe tocar
    # synapse_stage2.exe (el compilador autoalojado) — R183d R3.
    stage2 = os.path.join(RAIZ, "synapse_stage2.exe")
    if not os.path.exists(stage2):
        _chequear("R3 stage2 existe", False)
        return
    with open(stage2, "rb") as f:
        sha_antes = hashlib.sha256(f.read()).hexdigest()
    with tempfile.TemporaryDirectory() as d:
        probe = os.path.join(d, "probe_r183d_f.syn")
        with open(probe, "w", encoding="utf-8") as f:
            f.write(PROBE_FUENTE)
        r = _correr([probe], timeout=600)
        _chequear("R3 build sin -o rc=0", r.returncode == 0,
                  f"rc={r.returncode}")
        with open(stage2, "rb") as f:
            sha_despues = hashlib.sha256(f.read()).hexdigest()
        _chequear("R3 compilador intacto tras build sin -o",
                  sha_antes == sha_despues,
                  f"{sha_antes[:12]} vs {sha_despues[:12]}")


def main():
    if not os.path.exists(EXE):
        print("FALTA: synapse.exe")
        sys.exit(1)
    test_r1_version()
    test_r1_help()
    test_r2_prescan_target_wasm()
    test_r2_flags_modo()
    test_r3_fallback_no_destruye_compilador()
    total = len(RESULTADOS)
    ok_n = sum(1 for _, ok, _ in RESULTADOS if ok)
    if ok_n == total:
        print(f"OK: r183d PASS ({ok_n}/{total})")
        sys.exit(0)
    print(f"FALLO: r183d {ok_n}/{total}")
    sys.exit(1)


if __name__ == "__main__":
    main()
