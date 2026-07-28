#!/bin/bash
# build.sh — OpenSyn Build Script (Unix/Linux/macOS)
# Usage: ./build.sh [clean]

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
OPENEXE="$ROOT_DIR/opensyn/principal.exe"

echo "=== OpenSyn Build v1.0.0 ==="
echo ""

# Clean
if [ "${1:-}" = "clean" ]; then
    echo "[*] Cleaning artifacts..."
    rm -f "$ROOT_DIR/opensyn/principal.c" "$ROOT_DIR/opensyn/principal.exe"
    rm -f "$ROOT_DIR/opensyn/principal.syn.json"
    rm -f "$ROOT_DIR/synapse_rt.o"
    echo "[OK] Clean"
    exit 0
fi

# Step 1: Build runtime object
echo "[1/4] Compilando runtime (synapse_rt.c)..."
gcc -c "$ROOT_DIR/synapse_rt.c" -o "$ROOT_DIR/synapse_rt.o" \
    -std=c99 -Wall -Wextra \
    -Wno-unused-parameter -Wno-unused-function \
    -lpthread -lm -lws2_32 2>&1
echo "[OK] synapse_rt.o"

# Step 2: Compile the orchestrator from Synapse source (via Python compiler)
echo "[2/4] Compilando opensyn/principal.syn..."
python3 "$ROOT_DIR/main.py" "$ROOT_DIR/opensyn/principal.syn" 2>&1
echo "[OK] principal.c + principal.exe"

# Step 3: Verify executable exists
echo "[3/4] Verificando binario..."
if [ -f "$OPENEXE" ]; then
    echo "[OK] $OPENEXE"
else
    # Fallback: direct GCC link
    echo "[*] Fallback: enlazando con GCC directamente..."
    gcc -o "$OPENEXE" "$ROOT_DIR/opensyn/principal.c" \
        "$ROOT_DIR/synapse_rt.c" \
        -std=c99 -Wall -Wextra -fno-ident \
        -Wno-unused-parameter -Wno-unused-function \
        -Wl,--no-insert-timestamp \
        -I"$ROOT_DIR" -lws2_32 2>&1
    echo "[OK] $OPENEXE (fallback)"
fi

# Step 4: Regenerate embedded libraries header
echo "[4/4] Regenerando librerias/embedded_libs.h..."
python3 "$ROOT_DIR/tests/_gen_embedded.py" 2>&1
echo "[OK] embedded_libs.h"

echo ""
echo "=== Build complete ==="
echo "Ejecuta: ./opensyn/principal.exe"
