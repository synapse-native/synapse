#!/bin/bash
set -euo pipefail

INSTALL_DIR="${INSTALL_DIR:-/usr/local/lib/synapse}"
BIN_PATH="/usr/local/bin/synapse"
VERSION="v2.0.0-rc1"
REPO="synapse-native/synapse"
DOWNLOAD_URL="https://github.com/$REPO/releases/download/$VERSION/synapse-windows-amd64.exe"

echo "============================================"
echo " Synapse v2.0 - Unix Installer (Placeholder)"
echo "============================================"
echo ""
echo "NOTICE: Synapse does not yet ship a native Linux binary."
echo "On Windows / WSL, run:  powershell -File instalar.ps1"
echo ""
echo "When a Linux binary is available, run this script again."
echo ""
echo "Download page: $DOWNLOAD_URL"
echo ""
