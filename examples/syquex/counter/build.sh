#!/bin/bash
# examples/syquex/counter/build.sh
# FASE 25 — Build script para Counter App WASM
#
# Compila counter.wat → counter.wasm usando wat2wasm (wabt)
#
# Requisitos:
#   - wabt instalado (npm install -g wabt)
#   - wat2wasm en PATH
#
# Uso:
#   bash build.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

WAT_FILE="counter.wat"
WASM_FILE="counter.wasm"

echo "=== Syquex Counter App — Build WASM ==="
echo ""

# Verificar wat2wasm
if ! command -v wat2wasm &> /dev/null; then
    echo "❌ wat2wasm no encontrado. Instalar wabt:"
    echo "   npm install -g wabt"
    exit 1
fi

echo "📦 Compiling $WAT_FILE → $WASM_FILE..."
wat2wasm "$WAT_FILE" -o "$WASM_FILE"

if [ $? -eq 0 ]; then
    SIZE=$(wc -c < "$WASM_FILE")
    echo "✅ $WASM_FILE generado ($SIZE bytes)"
    echo ""
    echo "Para ejecutar:"
    echo "  1. Abrir index.html en un navegador"
    echo "  2. O usar un servidor local:"
    echo "     python -m http.server 8080"
    echo "     http://localhost:8080"
else
    echo "❌ Error al compilar $WAT_FILE"
    exit 1
fi
