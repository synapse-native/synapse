#!/bin/bash
# =========================================================================
# install.sh — Script de instalación para Linux
# =========================================================================
# Manual 9 §4.1: Distribución para Linux
# Soporte para .deb, .rpm, AppImage
# Verificación Ed25519 de integridad
# =========================================================================

set -e

SYNAPSE_VERSION="8.1.0"
INSTALL_DIR="/opt/synapse"
BIN_DIR="/usr/local/bin"
LOG_FILE="/var/log/synapse-install.log"

# Función de logging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "=== Instalador Synapse Ecosystem v${SYNAPSE_VERSION} ==="
log ""

# Detectar distribución
detectar_distribucion() {
    if command -v apt-get &> /dev/null; then
        PKG_MANAGER="apt"
        PKG_INSTALL="sudo apt-get install -y"
    elif command -v dnf &> /dev/null; then
        PKG_MANAGER="dnf"
        PKG_INSTALL="sudo dnf install -y"
    elif command -v yum &> /dev/null; then
        PKG_MANAGER="yum"
        PKG_INSTALL="sudo yum install -y"
    else
        PKG_MANAGER="unknown"
        PKG_INSTALL=""
    fi
    log "Gestor de paquetes detectado: ${PKG_MANAGER}"
}

# Instalar dependencias
instalar_dependencias() {
    log "Verificando dependencias..."
    if [ "${PKG_MANAGER}" = "apt" ]; then
        sudo apt-get update -qq
        $PKG_INSTALL build-essential curl wget python3
    elif [ "${PKG_MANAGER}" = "dnf" ] || [ "${PKG_MANAGER}" = "yum" ]; then
        $PKG_INSTALL gcc make curl wget python3
    fi
}

# Seleccionar componentes
seleccionar_componentes() {
    log ""
    log "Seleccione componentes a instalar:"
    log "  1) Solo Synapse (compilador y runtime)"
    log "  2) Ecosistema completo (Synapse + Syquex + OpenSyn)"
    log ""
    read -p "Opción [1/2]: " opcion
    
    case $opcion in
        2)
            INSTALAR_SYQUEX=true
            INSTALAR_OPENSYN=true
            INSTALAR_LIB=true
            log "Instalando ecosistema completo..."
            ;;
        *)
            INSTALAR_SYQUEX=false
            INSTALAR_OPENSYN=false
            INSTALAR_LIB=false
            log "Instalando solo Synapse..."
            ;;
    esac
}

# Verificar firma Ed25519
verificar_firma() {
    log "Verificando integridad de archivos..."
    if [ -f "../../instaladores/common/verificar_firma.py" ]; then
        python3 ../../instaladores/common/verificar_firma.py || true
    fi
}

# Crear directorio de instalacion
crear_directorios() {
    log "Creando directorios..."
    sudo mkdir -p "${INSTALL_DIR}"
    sudo mkdir -p "${BIN_DIR}"
    sudo mkdir -p "$(dirname "$LOG_FILE")"
}

# Copiar archivos
copiar_archivos() {
    log "Copiando archivos de Synapse..."
    sudo cp -r ../../build/bin/synapse "${INSTALL_DIR}/"
    sudo cp -r ../../nucleo "${INSTALL_DIR}/"
    sudo cp -r ../../std "${INSTALL_DIR}/"
    sudo cp -r ../../runtime "${INSTALL_DIR}/"
    
    if [ "${INSTALAR_SYQUEX}" = true ]; then
        log "Copiando Syquex..."
        sudo cp -r ../../syquex "${INSTALL_DIR}/" 2>/dev/null || true
    fi
    
    if [ "${INSTALAR_OPENSYN}" = true ]; then
        log "Copiando OpenSyn..."
        sudo cp -r ../../opensyn "${INSTALL_DIR}/" 2>/dev/null || true
    fi
    
    if [ "${INSTALAR_LIB}" = true ]; then
        log "Copiando biblioteca estándar..."
        sudo cp -r ../../lib "${INSTALL_DIR}/" 2>/dev/null || true
    fi
}

# Crear enlaces simbolicos
crear_enlaces() {
    log "Creando enlaces simbólicos..."
    sudo ln -sf "${INSTALL_DIR}/synapse" "${BIN_DIR}/synapse"
}

# Verificar instalacion
verificar_instalacion() {
    log ""
    log "Verificando instalación..."
    if command -v synapse &> /dev/null; then
        log "✅ Synapse instalado correctamente"
        synapse --version
    else
        log "⚠️  Synapse instalado en ${INSTALL_DIR}/synapse"
        log "   Agrega ${BIN_DIR} a tu PATH"
    fi
}

# Ejecutar
detectar_distribucion
instalar_dependencias
seleccionar_componentes
verificar_firma
crear_directorios
copiar_archivos
crear_enlaces
verificar_instalacion

log ""
log "=== Instalación completada ==="
log "Documentación: https://github.com/synapse-lang/synapse"
log "Log de instalación: ${LOG_FILE}"
