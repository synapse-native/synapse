# Plan ME_30_T4 — Instalador macOS (.dmg/.pkg)

## Bloque MTS (método de trabajo seguro)

### requisito:
Manual 9 §4.1: "Los artefactos se publican en la sección Releases del repositorio de GitHub. Cada release incluye: archivos de instalación para Windows, Linux, macOS y WASM."

### texto:
Implementar scripts para macOS que:
1. Crear aplicación .app (Synapse.app)
2. Generar archivo .dmg para distribución
3. Opciones: "Solo Synapse" vs "Ecosistema completo"
4. Incluir Info.plist con metadata

### implementacion:
1. Completar `instaladores/macos/create_dmg.sh` con:
   - Creación de estructura .app
   - Info.plist con metadata
   - Generación de .dmg con hdiutil
   - Opciones de componentes

### oraculo:
- Archivo create_dmg.sh existe y es ejecutable → PASS
- Crea estructura .app → PASS
- Genera .dmg → PASS
- Info.plist válido → PASS

## Archivos a modificar
- `instaladores/macos/create_dmg.sh`

## Citas de manuales
- Manual 9 §4.1 (GitHub Releases)
