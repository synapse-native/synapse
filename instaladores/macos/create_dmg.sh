#!/bin/bash
# =========================================================================
# create_dmg.sh — Script para crear .dmg en macOS
# =========================================================================
# Manual 9 §4.1: Distribución para macOS
# =========================================================================

set -e

SYNAPSE_VERSION="8.1.0"
APP_NAME="Synapse"
DMG_NAME="synapse-${SYNAPSE_VERSION}-macos.dmg"

echo "=== Creando instalador macOS para Synapse v${SYNAPSE_VERSION} ==="

# Crear estructura .app
echo "Creando estructura .app..."
mkdir -p "${APP_NAME}.app/Contents/MacOS"
mkdir -p "${APP_NAME}.app/Contents/Resources"

# Copiar binario
cp ../../build/bin/synapse "${APP_NAME}.app/Contents/MacOS/"

# Crear Info.plist
cat > "${APP_NAME}.app/Contents/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>synapse</string>
    <key>CFBundleIdentifier</key>
    <string>com.synapse.lang</string>
    <key>CFBundleName</key>
    <string>${APP_NAME}</string>
    <key>CFBundleVersion</key>
    <string>${SYNAPSE_VERSION}</string>
</dict>
</plist>
EOF

# Crear .dmg
echo "Creando .hdiutil create..."
hdiutil create -volname "${APP_NAME}" -srcfolder "${APP_NAME}.app" -ov -format UDZO "${DMG_NAME}"

echo ""
echo "✅ Instalador creado: ${DMG_NAME}"
echo "   Abrir el .dmg y arrastrar ${APP_NAME} a Applications"
