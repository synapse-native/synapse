# Verificación — ME r304_sbom_regeneracion

CUMPLE. Cierra H-R303-1.

## Requisito del plan y su verificación

| requisito | verificación | resultado |
|---|---|---|
| Manual 9 §6.1 — CUMPLE — inventario SPDX determinista y verificable | `pytest tests/auditoria/test_r304_sbom_determinista.py` | 5 passed |

## Qué cambió

`nucleo/sbom.py`:

- `solo_versionados` / `--versionados`: inventaría `git ls-files` (determinista
  entre máquinas) en lugar del árbol de trabajo. Si la ruta no es un repo git,
  cae al escaneo del árbol (modo que sigue usando `pipeline.py --sbom`).
- El SBOM no se inventaría a sí mismo (`.spdx.json`, `.sha256`, `.sig`): era
  imposible que su propio hash coincidiera.
- `packageVerificationCode` conforme a SPDX 2.3: SHA-1 de la concatenación de
  los SHA-1 de archivo ordenados. Antes repetía `sha256(nombre + versión + año)`,
  que no verifica contenido.
- Checksum raíz = digest reproducible del inventario
  (`sha256` de `ruta<TAB>sha256` ordenado por ruta).
- `--check`: compara contra el SBOM versionado e informa faltantes, sobrantes y
  hashes desactualizados; ignora `creationInfo.created` (cambia en cada
  generación y no es deriva).

`synapse.spdx.json` regenerado: **2290 archivos, 0 inexistentes, 0 artefactos
de build** (antes 2024 archivos con 1068 rutas fantasma). `.sha256`
recalculado.

## Otros checks

| check | resultado |
|---|---|
| `pytest tests/auditoria/test_r304_sbom_determinista.py` | 5 passed |
| `pytest tests/integration/test_slsa_sbom_security.py` | 37 passed |
| `nucleo/sbom.py --versionados` dos veces | documentos idénticos (salvo `created`) |
| `nucleo/sbom.py --versionados --check` | rc=0 |
| `build.py --skip-test` | rc=0, S2==S3 `ad65693a51c2` |
| `verificar_alineacion.py` | 0 brechas |
| `contrastar.py --plan docs/plan_ME_r304_sbom_regeneracion.md` | PASS (1/1) |
| `alineacion.py --verificar --me r304_sbom_regeneracion` | OK, evidencia `43531cfef7b85054` |

## Nota operativa

El SBOM inventaría lo versionado: cualquier alta/baja de archivos lo deja
desactualizado y `--check` lo reporta. La regeneración es
`python nucleo/sbom.py --versionados -o synapse.spdx.json` seguida del
recalculo de `synapse.spdx.json.sha256` (y de la firma en el pipeline de
release). En este ME se regeneró como último paso antes del commit, después de
que `alineacion.py --verificar` escribiera `cambio_hash` en el expediente.

## Deuda registrada

- Ninguna nueva. Queda **H25** (los ocho dumps `.c` históricos) con su ME
  asignado, fuera del alcance de r304.
