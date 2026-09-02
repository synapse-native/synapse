#!/usr/bin/env bash
# ============================================================================
# Instala los git hooks de auditoría (gate de alineación con los manuales).
#
# Uso:  bash scripts/githooks/instalar_hooks.sh
#
# Configura core.hooksPath=scripts/githooks para que git ejecute scripts/githooks/pre-commit
# en cada commit. La config es LOCAL del repo (no se comparte ni se sobreescribe
# por clones). El CI (.github/workflows/ci-tests.yml job 'auditoria') aplica el
# mismo gate de forma infalible en cada push/PR, así que saltar el hook local
# con --no-verify no evita el cumplimiento.
# ============================================================================

set -euo pipefail
RAIZ=$(git rev-parse --show-toplevel)

if [ ! -f "$RAIZ/scripts/githooks/pre-commit" ]; then
    echo "❌ scripts/githooks/pre-commit no existe" >&2
    exit 1
fi

git config core.hooksPath scripts/githooks

# Ejecutar el hook una vez para verificar que funciona
if bash "$RAIZ/scripts/githooks/pre-commit"; then
    echo ""
    echo "✅ Hooks instalados (core.hooksPath=scripts/githooks)."
    echo "   Cada commit ejecutará auditoria/verificar_alineacion.py (gate de alineación)."
else
    echo "⚠️  Hook instalado pero la verificación de prueba detectó brechas."
    echo "   Resuélvelas antes del siguiente commit."
fi
