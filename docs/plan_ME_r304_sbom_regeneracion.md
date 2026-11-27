# Plan de Micro-Entregable r304_sbom_regeneracion

## Objetivo

Cerrar **H-R303-1**. El SBOM versionado (`synapse.spdx.json`) inventariaba el
árbol de trabajo sucio del 2026-08-21: de sus 2024 entradas, **1068 apuntaban a
rutas inexistentes** (`.o`, `build/obj/*`, `synapse_unity.c`, instaladores
movidos). Además su `packageVerificationCode` no era un código SPDX (repetía
`sha256(nombre+versión+año)`, que no verifica contenido) y su `.sha256` estaba
desactualizado.

Decisión: el inventario del SBOM se genera **solo desde archivos versionados**
(`git ls-files`), lo que lo hace reproducible en cualquier máquina; el PVC se
calcula según SPDX 2.3 y el checksum raíz pasa a ser un digest del inventario.
Se añade `--check` para detectar deriva, que es el gate que faltaba.

El escaneo del árbol de trabajo se conserva como modo por defecto para el uso
en compilación (`--sbom` de `pipeline.py`, proyectos de usuario sin git), que no
debe cambiar de semántica.

## Requisito 1 — inventario SPDX determinista y verificable

requisito: Manual 9 §6.1
texto: "□ **SBOM y SLSA**: generados y firmados correctamente."
implementacion: `nucleo/sbom.py` gana `solo_versionados` (`--versionados`), inventaría `git ls-files`, excluye su propio archivo (`.spdx.json`), calcula `packageVerificationCode` como SHA-1 de los SHA-1 de archivo ordenados y el checksum raíz como SHA-256 del inventario (`ruta<TAB>hash`, ordenado); `--check` compara contra el SBOM versionado ignorando `creationInfo.created`, y `synapse.spdx.json` + `.sha256` se regeneran.
oraculo: tests/auditoria/test_r304_sbom_determinista.py

## Evidencia

| check | resultado |
|---|---|
| `pytest tests/auditoria/test_r304_sbom_determinista.py` | 5 passed |
| `pytest tests/integration/test_slsa_sbom_security.py` | 37 passed |
| `python nucleo/sbom.py --versionados --check` | rc=0, sincronizado |
| inventario regenerado | 2290 archivos, 0 inexistentes, 0 artefactos de build |
| `python build.py --skip-test` | rc=0, S2==S3 `ad65693a51c2` |
| `python auditoria/verificar_alineacion.py` | 0 brechas |
| `python auditoria/contrastar.py --plan docs/plan_ME_r304_sbom_regeneracion.md` | PASS (1/1) |
| `python auditoria/alineacion.py --verificar --me r304_sbom_regeneracion` | OK, evidencia `43531cfef7b85054` |
