#!/bin/bash
# build.sh - Synapse Build & Bootstrap (Unix/Linux/macOS)
# Usage: ./build.sh [clean]
#
# Pipeline (Manual 9 S9.1/S9.7):
#   Etapa 1: python compila nucleo/principal.syn -> synapse_stage1.exe
#   Etapa 2: synapse_stage1.exe compila nucleo/principal.syn -> synapse_stage2.exe
#   Etapa 3: synapse_stage2.exe compila nucleo/principal.syn -> synapse_stage3.exe
#   Verificacion: diff 0 bytes entre Etapa 2 y Etapa 3 (dos auto-compilaciones
#   nativas consecutivas; Manual 9 S9.7 y roadmap Fase 5).
# ME-R3: entrada alineada al manual (nucleo/principal.syn); el runtime modular lo
# compila el pipeline desde fuente (ME-R2: synapse_rt.c, runtime/core/*.c, axon/tweetnacl.c).
# NOTA: archivo en ASCII puro (sin acentos) para compatibilidad de codepage en Windows/git-bash.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
STAGE1="$ROOT_DIR/synapse_stage1.exe"
STAGE2="$ROOT_DIR/synapse_stage2.exe"
STAGE3="$ROOT_DIR/synapse_stage3.exe"

# Lanzador portable: python3 (Unix/macOS) o python (Windows/git-bash).
# Se valida por ejecucion (--version), no por presencia en PATH: en Windows el
# stub 'python3' de la Microsoft Store existe pero no ejecuta nada real.
if python3 --version >/dev/null 2>&1; then
    PY=python3
else
    PY=python
fi

echo "=== Synapse Build v8.1.0 ==="
echo ""

# Clean
if [ "${1:-}" = "clean" ]; then
    echo "[*] Cleaning artifacts..."
    rm -rf "$ROOT_DIR/build/obj"
    rm -f "$STAGE1" "$STAGE2" "$STAGE3"
    rm -f "$ROOT_DIR/synapse_unity.c" "$ROOT_DIR/synapse_unity.c.o"
    rm -f "$ROOT_DIR/synapse_rt.o" "$ROOT_DIR/tweetnacl.o"
    echo "[OK] Clean"
    exit 0
fi

# Etapa 1: Bootstrap (Manual 9 S9.1).
# El pipeline (ME-R2) compila el runtime modular desde fuente y enlaza el
# compilador nativo (synapse_stage1.exe).
echo "[1/3] Bootstrap: $PY main.py nucleo/principal.syn -> synapse_stage1.exe"
"$PY" "$ROOT_DIR/main.py" "$ROOT_DIR/nucleo/principal.syn" -o "$STAGE1" 2>&1
if [ ! -f "$STAGE1" ]; then
    echo "[FAIL] No se genero $STAGE1" >&2
    exit 1
fi
echo "[OK] Etapa 1 complete: $STAGE1"

# Etapa 2: Self-hosting 1 -- el compilador nativo se compila a si mismo
echo "[2/3] Etapa 2: synapse_stage1.exe -> synapse_stage2.exe"
"$STAGE1" "$ROOT_DIR/nucleo/principal.syn" "$STAGE2" >/dev/null 2>&1 || true
if [ ! -f "$STAGE2" ]; then
    echo "[FAIL] Etapa 2 (auto-compilacion 1) no genero $STAGE2" >&2
    exit 1
fi
echo "[OK] Etapa 2 complete: $STAGE2"

# Etapa 3: Self-hosting 2 -- el compilador auto-compilado se compila a si mismo
echo "[3/3] Etapa 3: synapse_stage2.exe -> synapse_stage3.exe"
"$STAGE2" "$ROOT_DIR/nucleo/principal.syn" "$STAGE3" >/dev/null 2>&1 || true
if [ ! -f "$STAGE3" ]; then
    echo "[FAIL] Etapa 3 (auto-compilacion 2) no genero $STAGE3" >&2
    exit 1
fi
echo "[OK] Etapa 3 complete: $STAGE3"

# Verificacion: diff 0 bytes entre Etapa 2 y Etapa 3 (Manual 9 S9.7)
echo "=============================================="
STAGE2_HASH=$(sha256sum "$STAGE2" | cut -d' ' -f1)
STAGE3_HASH=$(sha256sum "$STAGE3" | cut -d' ' -f1)
STAGE2_SIZE=$(stat -c%s "$STAGE2")
STAGE3_SIZE=$(stat -c%s "$STAGE3")
echo "  synapse_stage2.exe: ${STAGE2_SIZE} bytes  SHA256: ${STAGE2_HASH}"
echo "  synapse_stage3.exe: ${STAGE3_SIZE} bytes  SHA256: ${STAGE3_HASH}"
if [ "$STAGE2_HASH" = "$STAGE3_HASH" ]; then
    echo ""
    echo "  BOOTSTRAP VERIFIED: diff = 0 bytes"
    echo "  Etapa 2 == Etapa 3 (byte-identical)"
    echo "=============================================="
else
    echo ""
    echo "  Bootstrap INCOMPLETE: binary mismatch"
    echo "=============================================="
    exit 1
fi

echo ""
echo "=== Build complete ==="
echo "Ejecuta: $STAGE1"
