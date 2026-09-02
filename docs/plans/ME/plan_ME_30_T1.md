# Plan ME_30_T1 — Estructura base del instalador

## Bloque MTS (método de trabajo seguro)

### requisito:
Manual 9 §4.1: "Los artefactos se publican en la sección Releases del repositorio de GitHub. Cada release incluye: archivos de instalación para Windows, Linux, macOS y WASM."
Manual 9 §4.2: "Los paquetes se publican en el Axon Hub (descentralizado en IPFS)."

### texto:
Crear la estructura de directorios y archivos base para los instaladores multiplataforma. El instalador debe soportar:
- Windows (Inno Setup)
- Linux (Bash + .deb/.rpm/AppImage)
- macOS (.dmg/.pkg)
- Opciones: "Solo Synapse" vs "Ecosistema completo"

### implementacion:
1. Crear directorio `instaladores/` con subdirectorios para cada plataforma
2. Crear scripts básicos para cada plataforma
3. Crear tests TDD que verifiquen la estructura

### oraculo:
- Directorios creados → PASS
- Scripts básicos existen → PASS
- Tests verifican estructura → PASS

## Archivos a crear
- `instaladores/windows/`
- `instaladores/linux/`
- `instaladores/macos/`
- `instaladores/common/`
- `tests/installers/test_estructura.py`

## Citas de manuales
- Manual 9 §4.1 (GitHub Releases)
- Manual 9 §4.2 (Axon Hub)
