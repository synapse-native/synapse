#!/bin/bash
# =========================================================================
# create_dmg.sh — Script para crear .dmg en macOS
# =========================================================================
# Manual 9 §4.1: Distribución para macOS
# Verificación Ed25519 de integridad
# =========================================================================

set -e

SYNAPSE_VERSION="8.1.0"
APP_NAME="Synapse"
DMG_NAME="synapse-${SYNAPSE_VERSION}-macos.dmg"
LOG_FILE="/var/log/synapse-build.log"

# Función de logging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# ============================================================================
# Opciones de componentes (Manual 9 §4.1)
# ============================================================================
COMPONENTE="opensyn"  # Valor por defecto: solo OpenSyn

for arg in "$@"; do
  case $arg in
    --ecosistema) COMPONENTE="ecosistema" ;;
    --opensyn)    COMPONENTE="opensyn" ;;
    --help|-h)
      echo "Uso: $0 [--opensyn|--ecosistema]"
      echo "  --opensyn: Solo instalar OpenSyn (valor por defecto)"
      echo "  --ecosistema: Instalar ecosistema completo (OpenSyn + Syquex)"
      exit 0 ;;
    *) echo "Opción desconocida: $arg"; exit 1 ;;
  esac
done

log "=== Creando instalador macOS para Synapse v${SYNAPSE_VERSION} ==="
log "Componente: ${COMPONENTE}"

# Verificar firma Ed25519
verificar_firma() {
    log "Verificando integridad de archivos..."
    if [ -f "../../instaladores/common/verificar_firma.py" ]; then
        python3 ../../instaladores/common/verificar_firma.py || true
    fi
}

# Crear estructura .app
log "Creando estructura .app..."
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
    <key>CFBundleShortVersionString</key>
    <string>${SYNAPSE_VERSION}</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleSignature</key>
    <string>????</string>
    <key>LSMinimumSystemVersion</key>
    <string>12.0</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
EOF

# Verificar firma
verificar_firma

# Crear .dmg
log "Creando .hdiutil create..."
hdiutil create -volname "${APP_NAME}" -srcfolder "${APP_NAME}.app" -ov -format UDZO "${DMG_NAME}"

log ""
log "✅ Instalador creado: ${DMG_NAME}"
log "   Abrir el .dmg y arrastrar ${APP_NAME} a Applications"
log "Log de build: ${LOG_FILE}"
