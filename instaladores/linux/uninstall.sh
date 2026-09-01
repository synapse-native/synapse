#!/bin/bash
# =========================================================================
# uninstall.sh — Script de desinstalación para Linux
# =========================================================================
# Manual 9 §4.1: Distribución para Linux
# Desinstalación de Synapse Ecosystem
# =========================================================================

set -e

INSTALL_DIR="/opt/synapse"
BIN_DIR="/usr/local/bin"
LOG_FILE="/var/log/synapse-install.log"

# Función de logging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "=== Desinstalador Synapse Ecosystem ==="
log ""

# Confirmar desinstalación
confirmar_desinstalacion() {
    log "¿Está seguro de que desea desinstalar Synapse?"
    read -p "Escriba 'SÍ' para confirmar: " confirmacion
    if [ "$confirmacion" != "SÍ" ]; then
        log "Desinstalación cancelada."
        exit 0
    fi
}

# Eliminar archivos
eliminar_archivos() {
    log "Eliminando archivos de Synapse..."
    sudo rm -rf "${INSTALL_DIR}"
    sudo rm -f "${BIN_DIR}/synapse"
    log "✅ Archivos eliminados"
}

# Verificar desinstalacion
verificar_desinstalacion() {
    log ""
    log "Verificando desinstalación..."
    if ! command -v synapse &> /dev/null; then
        log "✅ Synapse desinstalado correctamente"
    else
        log "⚠️  Synapse aún está en el sistema"
    fi
}

# Ejecutar
confirmar_desinstalacion
eliminar_archivos
verificar_desinstalacion

log ""
log "=== Desinstalación completada ==="
log "Log de desinstalación: ${LOG_FILE}"
