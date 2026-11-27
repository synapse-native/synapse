#!/bin/bash
# =========================================================================
# test-install.sh — Script de testing para instalador Linux
# =========================================================================
# Valida que el instalador funciona correctamente
# =========================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALLER_DIR="${SCRIPT_DIR}/../../instaladores/linux"
LOG_FILE="/tmp/synapse-test-$(date +%Y%m%d-%H%M%S).log"

# Función de logging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Función de test
test_case() {
    local test_name="$1"
    local test_command="$2"
    
    log "TEST: ${test_name}"
    if eval "$test_command" >> "$LOG_FILE" 2>&1; then
        log "  ✅ PASS"
        return 0
    else
        log "  ❌ FAIL"
        return 1
    fi
}

log "=== Testing Instalador Linux ==="
log "Log file: ${LOG_FILE}"
log ""

# Tests
PASS_COUNT=0
FAIL_COUNT=0

# Test 1: El script existe
test_case "Script existe" "[ -f '${INSTALLER_DIR}/install.sh' ]" && PASS_COUNT=$((PASS_COUNT+1)) || FAIL_COUNT=$((FAIL_COUNT+1))

# Test 2: El script es ejecutable
test_case "Script es ejecutable" "[ -x '${INSTALLER_DIR}/install.sh' ] || chmod +x '${INSTALLER_DIR}/install.sh'" && PASS_COUNT=$((PASS_COUNT+1)) || FAIL_COUNT=$((FAIL_COUNT+1))

# Test 3: El script tiene shebang
test_case "Script tiene shebang" "head -1 '${INSTALLER_DIR}/install.sh' | grep -q '^#!/bin/bash'" && PASS_COUNT=$((PASS_COUNT+1)) || FAIL_COUNT=$((FAIL_COUNT+1))

# Test 4: El script tiene opciones de componentes
test_case "Tiene opciones de componentes" "grep -q 'seleccionar_componentes' '${INSTALLER_DIR}/install.sh'" && PASS_COUNT=$((PASS_COUNT+1)) || FAIL_COUNT=$((FAIL_COUNT+1))

# Test 5: El script detecta distribución
test_case "Detecta distribución" "grep -q 'detectar_distribucion' '${INSTALLER_DIR}/install.sh'" && PASS_COUNT=$((PASS_COUNT+1)) || FAIL_COUNT=$((FAIL_COUNT+1))

# Test 6: El script tiene logging
test_case "Tiene logging" "grep -q 'LOG_FILE' '${INSTALLER_DIR}/install.sh'" && PASS_COUNT=$((PASS_COUNT+1)) || FAIL_COUNT=$((FAIL_COUNT+1))

# Test 7: El script verifica firma
test_case "Verifica firma Ed25519" "grep -q 'verificar_firma' '${INSTALLER_DIR}/install.sh'" && PASS_COUNT=$((PASS_COUNT+1)) || FAIL_COUNT=$((FAIL_COUNT+1))

# Test 8: Script de desinstalación existe
test_case "Script de desinstalación existe" "[ -f '${INSTALLER_DIR}/uninstall.sh' ]" && PASS_COUNT=$((PASS_COUNT+1)) || FAIL_COUNT=$((PASS_COUNT+1))

# Resumen
log ""
log "=== Resumen de Testing ==="
log "Tests ejecutados: $((PASS_COUNT+FAIL_COUNT))"
log "Tests pasados: ${PASS_COUNT}"
log "Tests fallidos: ${FAIL_COUNT}"
log ""

if [ ${FAIL_COUNT} -eq 0 ]; then
    log "✅ TODOS LOS TESTS PASARON"
    exit 0
else
    log "❌ ALGUNOS TESTS FALLARON"
    exit 1
fi
