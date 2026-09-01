#!/bin/bash
# =========================================================================
# install.sh — Script de instalación para Linux
# =========================================================================
# Manual 9 §4.1: Distribución para Linux
# Soporte para .deb, .rpm, AppImage
# =========================================================================

set -e

SYNAPSE_VERSION="8.1.0"
INSTALL_DIR="/opt/synapse"
BIN_DIR="/usr/local/bin"

echo "=== Instalador Synapse Ecosystem v${SYNAPSE_VERSION} ==="
echo ""

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
    echo "Gestor de paquetes detectado: ${PKG_MANAGER}"
}

# Instalar dependencias
instalar_dependencias() {
    echo "Verificando dependencias..."
    if [ "${PKG_MANAGER}" = "apt" ]; then
        sudo apt-get update -qq
        $PKG_INSTALL build-essential curl wget
    elif [ "${PKG_MANAGER}" = "dnf" ] || [ "${PKG_MANAGER}" = "yum" ]; then
        $PKG_INSTALL gcc make curl wget
    fi
}

# Seleccionar componentes
seleccionar_componentes() {
    echo ""
    echo "Seleccione componentes a instalar:"
    echo "  1) Solo Synapse (compilador y runtime)"
    echo "  2) Ecosistema completo (Synapse + Syquex + OpenSyn)"
    echo ""
    read -p "Opción [1/2]: " opcion
    
    case $opcion in
        2)
            INSTALAR_SYQUEX=true
            INSTALAR_OPENSYN=true
            INSTALAR_LIB=true
            echo "Instalando ecosistema completo..."
            ;;
        *)
            INSTALAR_SYQUEX=false
            INSTALAR_OPENSYN=false
            INSTALAR_LIB=false
            echo "Instalando solo Synapse..."
            ;;
    esac
}

# Crear directorio de instalacion
crear_directorios() {
    echo "Creando directorios..."
    sudo mkdir -p "${INSTALL_DIR}"
    sudo mkdir -p "${BIN_DIR}"
}

# Copiar archivos
copiar_archivos() {
    echo "Copiando archivos de Synapse..."
    sudo cp -r ../../build/bin/synapse "${INSTALL_DIR}/"
    sudo cp -r ../../nucleo "${INSTALL_DIR}/"
    sudo cp -r ../../std "${INSTALL_DIR}/"
    sudo cp -r ../../runtime "${INSTALL_DIR}/"
    
    if [ "${INSTALAR_SYQUEX}" = true ]; then
        echo "Copiando Syquex..."
        sudo cp -r ../../syquex "${INSTALL_DIR}/" 2>/dev/null || true
    fi
    
    if [ "${INSTALAR_OPENSYN}" = true ]; then
        echo "Copiando OpenSyn..."
        sudo cp -r ../../opensyn "${INSTALL_DIR}/" 2>/dev/null || true
    fi
    
    if [ "${INSTALAR_LIB}" = true ]; then
        echo "Copiando biblioteca estándar..."
        sudo cp -r ../../lib "${INSTALL_DIR}/" 2>/dev/null || true
    fi
}

# Crear enlaces simbolicos
crear_enlaces() {
    echo "Creando enlaces simbólicos..."
    sudo ln -sf "${INSTALL_DIR}/synapse" "${BIN_DIR}/synapse"
}

# Verificar instalacion
verificar_instalacion() {
    echo ""
    echo "Verificando instalación..."
    if command -v synapse &> /dev/null; then
        echo "✅ Synapse instalado correctamente"
        synapse --version
    else
        echo "⚠️  Synapse instalado en ${INSTALL_DIR}/synapse"
        echo "   Agrega ${BIN_DIR} a tu PATH"
    fi
}

# Ejecutar
detectar_distribucion
instalar_dependencias
seleccionar_componentes
crear_directorios
copiar_archivos
crear_enlaces
verificar_instalacion

echo ""
echo "=== Instalación completada ==="
echo "Documentación: https://github.com/synapse-lang/synapse"
