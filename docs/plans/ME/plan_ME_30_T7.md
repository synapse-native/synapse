# Plan ME_30_T7 — Auto-actualización

## Bloque MTS (método de trabajo seguro)

### requisito:
Manual 9 §4.1: "Los artefactos se publican en la sección Releases del repositorio de GitHub. Cada release incluye: archivos de instalación para Windows, Linux, macOS y WASM."

### texto:
Implementar sistema de auto-actualización:
1. Verificar nueva versión en GitHub
2. Descargar y verificar integridad (Ed25519)
3. Instalar actualización
4. Rollback en caso de error

### implementacion:
1. Crear `instaladores/common/auto_actualizar.py` con:
   - Verificación de versiones
   - Descarga desde GitHub Releases
   - Verificación Ed25519
   - Instalación y rollback

### oraculo:
- Archivo auto_actualizar.py existe → PASS
- Tiene función verificar_version → PASS
- Tiene función descargar_actualizacion → PASS
- Tiene función instalar_actualizacion → PASS

## Archivos a modificar
- `instaladores/common/auto_actualizar.py`

## Citas de manuales
- Manual 9 §4.1 (GitHub Releases)
