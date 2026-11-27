# Plan de Mejoras a Instaladores (Post-FASE 30)

## Objetivo
Mejorar los instaladores con funcionalidades adicionales para preparar el lanzamiento público.

## Mejoras por plataforma

### Windows (Inno Setup)
1. **Verificación Ed25519**: Agregar verificación de integridad antes de instalar
2. **Actualización automática**: Opción para buscar actualizaciones
3. **Logging detallado**: Registrar instalación en archivo de log

### Linux (Bash)
1. **Verificación Ed25519**: Verificar firma antes de instalar
2. **Desinstalación**: Script de desinstalación
3. **Logging**: Registrar instalación en archivo de log
4. **Verificación de dependencias**: Mejorar detección

### macOS (.dmg)
1. **Verificación Ed25519**: Verificar firma antes de instalar
2. **Codesigning**: Firmar aplicación con certificado
3. **Notarización**: Enviar a Apple para notarización

## Archivos a crear/modificar
- `instaladores/windows/synapse.iss` (modificar)
- `instaladores/linux/install.sh` (modificar)
- `instaladores/linux/uninstall.sh` (nuevo)
- `instaladores/macos/create_dmg.sh` (modificar)
- `instaladores/common/verificar_firma.py` (ya existe)

## Orden de ejecución
1. Windows: Verificación Ed25519
2. Linux: Verificación Ed25519 + Desinstalación
3. macOS: Verificación Ed25519
