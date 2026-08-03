#!/bin/bash
# build.sh - Synapse Build & Bootstrap (Unix/Linux/macOS)
# Usage: ./build.sh [clean]
#
# Etapa 1 del Manual 9 S9.1: python main.py nucleo/principal.syn -o synapse_v1.exe
# ME-R3: entrada alineada al manual (antes opensyn/principal.syn, que NO bootstrapea:
#        89 errores semanticos preexistentes); el runtime modular lo compila el
#        pipeline desde fuente (ME-R2: synapse_rt.c, runtime/core/*.c, tweetnacl.c).

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
STAGE1="$ROOT_DIR/synapse_v1.exe"

# Lanzador portable: python3 (Unix/macOS) o python (Windows/git-bash).
# Se valida por ejecucion (--version), no por presencia en PATH: en Windows el
# stub 'python3' de la Microsoft Store existe pero no ejecuta nada real.
if python3 --version >/dev/null 2>&1; then
    PY=python3
else
    PY=python
fi

echo "=== Synapse Build v2.1.0 ==="
echo ""

# Clean
if [ "${1:-}" = "clean" ]; then
    echo "[*] Cleaning artifacts..."
    rm -rf "$ROOT_DIR/build/obj"
    rm -f "$ROOT_DIR/synapse_v1.exe" "$ROOT_DIR/synapse_v2.exe" "$ROOT_DIR/synapse_v3.exe"
    rm -f "$ROOT_DIR/synapse_unity.c" "$ROOT_DIR/synapse_unity.c.o"
    rm -f "$ROOT_DIR/synapse_rt.o" "$ROOT_DIR/tweetnacl.o"
    echo "[OK] Clean"
    exit 0
fi

# Step 1: Bootstrap Etapa 1 (Manual 9 S9.1).
# El pipeline (ME-R2) compila el runtime modular desde fuente y enlaza el
# compilador nativo (synapse_v1.exe).
echo "[1/3] Bootstrap: $PY main.py nucleo/principal.syn -> synapse_v1.exe"
"$PY" "$ROOT_DIR/main.py" "$ROOT_DIR/nucleo/principal.syn" -o "$STAGE1" 2>&1
echo "[OK] synapse_v1.exe"

# Step 2: Verify executable exists
echo "[2/3] Verificando binario..."
if [ -f "$STAGE1" ]; then
    echo "[OK] $STAGE1"
else
    echo "[FAIL] No se genero $STAGE1" >&2
    exit 1
fi

# Step 3: Regenerate embedded libraries header
echo "[3/3] Regenerando librerias/embedded_libs.h..."
"$PY" "$ROOT_DIR/tests/_gen_embedded.py" 2>&1
echo "[OK] embedded_libs.h"

echo ""
echo "=== Build complete ==="
echo "Ejecuta: $STAGE1"
