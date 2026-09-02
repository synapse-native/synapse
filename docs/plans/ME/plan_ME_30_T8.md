# Plan ME_30_T8 — Docs/Packaging

## Bloque MTS (método de trabajo seguro)

### requisito:
Manual 9 §4.1: "Los artefactos se publican en la sección Releases del repositorio de GitHub. Cada release incluye: archivos de instalación para Windows, Linux, macOS y WASM."

### texto:
Documentar el proceso de packaging:
1. README de instaladores con instrucciones
2. Scripts de build para cada plataforma
3. Configuración de CI/CD para releases
4. Guía de contribución para nuevos instaladores

### implementacion:
1. Crear `instaladores/README.md` con:
   - Instrucciones por plataforma
   - Requisitos previos
   - Troubleshooting
   - Ejemplos de uso

### oraculo:
- Archivo README.md existe → PASS
- Contiene instrucciones por plataforma → PASS
- Contiene requisitos previos → PASS
- Contiene troubleshooting → PASS

## Archivos a modificar
- `instaladores/README.md`

## Citas de manuales
- Manual 9 §4.1 (GitHub Releases)
