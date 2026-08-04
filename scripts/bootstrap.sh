#!/bin/bash
# bootstrap.sh — Synapse Bootstrap Pipeline (Manual 9 S9.1/S9.7)
# Usage: ./bootstrap.sh [--clean]
#
# Pipeline:
#   Stage 1: Python compiler (nucleo/principal.syn) -> synapse_stage1.exe
#   Stage 2: synapse_stage1.exe -> synapse_stage2.exe (self-hosting 1)
#   Stage 3: synapse_stage2.exe -> synapse_stage3.exe (self-hosting 2)
#   Verificacion: diff 0 bytes entre Stage 2 y Stage 3 (dos auto-compilaciones
#   nativas consecutivas; Manual 9 S9.7 y roadmap Fase 5).
# ME-R3: entrada alineada al manual (nucleo/principal.syn); el runtime modular lo
# compila el pipeline desde fuente (ME-R2, build/obj/).
# NOTA: el binario de Etapa 1 generado por el pipeline ya es autonocontenido;
# no se compilan objetos de runtime a mano (ME-R2 compila desde fuente).
#
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
STAGE1="$ROOT_DIR/synapse_stage1.exe"
STAGE2="$ROOT_DIR/synapse_stage2.exe"
STAGE3="$ROOT_DIR/synapse_stage3.exe"
ENTRY_POINT="$ROOT_DIR/src/main.syn"
COMPILER_SRC="$ROOT_DIR/nucleo/principal.syn"

# Lanzador portable: python3 (Unix/macOS) o python (Windows/git-bash).
# Se valida por ejecucion (--version), no por presencia en PATH: en Windows el
# stub 'python3' de la Microsoft Store existe pero no ejecuta nada real.
if python3 --version >/dev/null 2>&1; then
    PY=python3
else
    PY=python
fi

echo "=============================================="
echo "  Synapse Bootstrap Pipeline"
echo "  Stage 1 → Stage 2 → Stage 3 (diff 0 bytes)"
echo "=============================================="
echo ""

# Clean
if [ "${1:-}" = "--clean" ]; then
    echo "[*] Cleaning artifacts..."
    rm -f "$STAGE1" "$STAGE2" "$STAGE3"
    rm -rf "$ROOT_DIR/build/obj"
    echo "[OK] Clean"
    exit 0
fi

# Stage 1: Python compiler -> synapse_stage1.exe
echo "[1/3] Stage 1: $PY main.py nucleo/principal.syn -> synapse_stage1.exe"
"$PY" "$ROOT_DIR/main.py" "$COMPILER_SRC" -o "$STAGE1"
if [ ! -f "$STAGE1" ]; then
    echo "[FAIL] Stage 1 no genero $STAGE1"
    exit 1
fi
echo "[OK] Stage 1 complete: $STAGE1"
echo ""

# Stage 2: Self-hosting 1 — el compilador nativo se compila a si mismo
echo "[2/3] Stage 2: synapse_stage1.exe -> synapse_stage2.exe"
"$STAGE1" "$COMPILER_SRC" "$STAGE2" >/dev/null 2>&1 || true
if [ ! -f "$STAGE2" ]; then
    echo "[FAIL] Stage 2 (auto-compilacion 1) no genero $STAGE2"
    exit 1
fi
echo "[OK] Stage 2 complete: $STAGE2"
echo ""

# Stage 3: Self-hosting 2 — el compilador auto-compilado se compila a si mismo
echo "[3/3] Stage 3: synapse_stage2.exe -> synapse_stage3.exe"
"$STAGE2" "$COMPILER_SRC" "$STAGE3" >/dev/null 2>&1 || true
if [ ! -f "$STAGE3" ]; then
    echo "[FAIL] Stage 3 (auto-compilacion 2) no genero $STAGE3"
    exit 1
fi
echo "[OK] Stage 3 complete: $STAGE3"
echo ""

# Verificacion: diff 0 bytes entre Stage 2 y Stage 3 (Manual 9 S9.7)
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
    echo "  Stage 2 == Stage 3 (byte-identical)"
    echo "=============================================="
else
    echo ""
    echo "  Bootstrap INCOMPLETE: binary mismatch"
    echo "  Stage 2 != Stage 3"
    echo "=============================================="
    exit 1
fi

echo ""
echo "Pipeline complete."
