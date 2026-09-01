# Plan ME_30_T5 — Verificación Ed25519

## Bloque MTS (método de trabajo seguro)

### requisito:
Manual 9 §4.1: "Los artefactos se publican en la sección Releases del repositorio de GitHub. Cada release incluye: archivos de instalación para Windows, Linux, macOS y WASM. El instalador verifica la integridad del binario con Ed25519."

### texto:
Implementar verificación de integridad Ed25519:
1. Generar claves Ed25519 (par de claves)
2. Firmar binarios compilados
3. Verificar firmas en instaladores
4. Integrar con flujos de instalación

### implementacion:
1. Crear `instaladores/common/verificar_firma.py` con:
   - Generación de claves Ed25519
   - Firma de archivos
   - Verificación de firmas
   - Uso de hashlib/cryptography

### oraculo:
- Archivo verificar_firma.py existe → PASS
- Tiene función firmar_archivo → PASS
- Tiene función verificar_firma → PASS
- Usa Ed25519 → PASS

## Archivos a modificar
- `instaladores/common/verificar_firma.py`

## Citas de manuales
- Manual 9 §4.1 (GitHub Releases con verificación)
