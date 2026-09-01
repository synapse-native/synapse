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
if command -v apt-get &> /dev/null; then
    PKG_MANAGER="apt"
elif command -v dnf &> /dev/null; then
    PKG_MANAGER="dnf"
elif command -v yum &> /dev/null; then
    PKG_MANAGER="yum"
else
    PKG_MANAGER="unknown"
fi

echo "Gestor de paquetes detectado: ${PKG_MANAGER}"

# Crear directorio de instalación
echo "Creando directorio de instalación..."
sudo mkdir -p "${INSTALL_DIR}"
sudo mkdir -p "${BIN_DIR}"

# Copiar archivos
echo "Copiando archivos de Synapse..."
sudo cp -r ../../build/bin/synapse "${INSTALL_DIR}/"
sudo cp -r ../../nucleo "${INSTALL_DIR}/"
sudo cp -r ../../std "${INSTALL_DIR}/"
sudo cp -r ../../runtime "${INSTALL_DIR}/"

# Opcional: Ecosistema completo
read -p "¿Instalar ecosistema completo (Syquex + OpenSyn)? [s/N]: " install_full
if [[ "${install_full}" =~ ^[Ss]$ ]]; then
    echo "Instalando ecosistema completo..."
    sudo cp -r ../../syquex "${INSTALL_DIR}/" 2>/dev/null || true
    sudo cp -r ../../opensyn "${INSTALL_DIR}/" 2>/dev/null || true
    sudo cp -r ../../lib "${INSTALL_DIR}/" 2>/dev/null || true
fi

# Crear enlaces simbólicos
echo "Creando enlaces simbólicos..."
sudo ln -sf "${INSTALL_DIR}/synapse" "${BIN_DIR}/synapse"

# Verificar instalación
echo ""
echo "Verificando instalación..."
if command -v synapse &> /dev/null; then
    echo "✅ Synapse instalado correctamente"
    synapse --version
else
    echo "⚠️  Synapse instalado en ${INSTALL_DIR}/synapse"
    echo "   Agrega ${BIN_DIR} a tu PATH"
fi

echo ""
echo "=== Instalación completada ==="
echo "Documentación: https://github.com/synapse-lang/synapse"
