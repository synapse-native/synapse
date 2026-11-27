# Plan ME_30_T6 — Tests de Smoke (Instaladores)

## Bloque MTS (método de trabajo seguro)

### requisito:
Manual 9 §4.1: "Los artefactos se publican en la sección Releases del repositorio de GitHub. Cada release incluye: archivos de instalación para Windows, Linux, macOS y WASM."

### texto:
Implementar tests de smoke que verifiquen que los instaladores:
1. Pueden ejecutarse sin errores críticos
2. Validan la integridad de binarios
3. Producen artefactos válidos

### implementacion:
1. Crear `tests/installers/test_smoke.py` con:
   - Test de smoke para install.sh (Bash)
   - Test de smoke para create_dmg.sh (macOS)
   - Test de smoke para verificar_firma.py (Ed25519)
   - Verificar que scripts no tienen errores de sintaxis

### oraculo:
- Archivo test_smoke.py existe → PASS
- Tests verifican ejecución básica → PASS
- Tests verifican integridad → PASS
- Tests verifican artefactos → PASS

## Archivos a modificar
- `tests/installers/test_smoke.py`

## Citas de manuales
- Manual 9 §4.1 (GitHub Releases)
