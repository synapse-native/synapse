# Plan ME_30_T3 — Instalador Linux (Bash)

## Bloque MTS (método de trabajo seguro)

### requisito:
Manual 9 §4.1: "Los artefactos se publican en la sección Releases del repositorio de GitHub. Cada release incluye: archivos de instalación para Windows, Linux, macOS y WASM."

### texto:
Implementar script de instalación Bash para Linux que:
1. Detecte distribución (Debian/Ubuntu, Fedora/RHEL, etc.)
2. Instale Synapse y componentes seleccionados
3. Opciones: "Solo Synapse" vs "Ecosistema completo"
4. Cree enlaces simbólicos en /usr/local/bin
5. Soporte para .deb, .rpm

### implementacion:
1. Completar `instaladores/linux/install.sh` con:
   - Detección de distribución
   - Instalación de dependencias
   - Copia de archivos
   - Creación de enlaces simbólicos
   - Opciones de componentes

### oraculo:
- Archivo install.sh existe y es ejecutable → PASS
- Detecta distribución Linux → PASS
- Instala componentes → PASS
- Crea enlaces simbólicos → PASS

## Archivos a modificar
- `instaladores/linux/install.sh`

## Citas de manuales
- Manual 9 §4.1 (GitHub Releases)
