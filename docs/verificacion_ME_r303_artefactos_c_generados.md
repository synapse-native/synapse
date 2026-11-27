# Verificación — ME r303_artefactos_c_generados

CUMPLE. Cierra H-R302-1; abre H-R303-1 (SBOM con entradas fantasma preexistentes).

## Requisitos del plan y su verificación

| requisito | verificación | resultado |
|---|---|---|
| Manual 9 §6.1 — CUMPLE — SBOM sin referencias a archivos inexistentes | `pytest tests/auditoria/test_r303_dumps_c_retirados.py::test_sbom_sin_entradas_de_los_retirados_y_checksum_coherente` | passed (0 entradas de los 6; sha256 del documento coincide) |
| Manual 1 §7.4 — CUMPLE — ninguna regresión por el retiro | oráculo completo + `build.py --skip-test` | 4 passed; build rc=0; S2==S3 `ad65693a51c2` |

## Qué se retiró y por qué

Los seis `.c` son dumps del compilador S1 (`// salida_metal.c - Generado por
Synapse Compilador`), no fuentes ni insumos del build: el build compila
`nucleo/<módulo>.syn` y produce sus propios objetos `_<módulo>.c`. Regenerarlos
habría recreado el mismo problema en la siguiente edición del `.syn`; se
retiran del control de versiones y la fuente de verdad queda en los `.syn`.

| archivo retirado (eliminado del repo) | fuente de verdad |
|---|---|
| `nucleo/analizador_semantico.c` | `nucleo/analizador_semantico.syn` |
| `nucleo/ast_nodes.c` | `nucleo/ast_nodes.syn` |
| `nucleo/diagnostics.c` | `nucleo/diagnostics.syn` |
| `nucleo/errores.c` | `nucleo/errores.syn` |
| `nucleo/estado_global.c` | `nucleo/estado_global.syn` |
| `nucleo/generator_constants.c` | `nucleo/generator_constants.syn` |

## Baseline de contratos

`auditoria/contratos_baseline.txt` **no tenía** entradas de esos `.c` (su
formato es `ruta::función` y solo audita `.syn`); la nota de H-R302-1 que los
citaba era imprecisa. Se verificó antes y después: 516 entradas de deuda, 0
nuevas. Sin cambios en el archivo.

## SBOM

- Se podaron las 4 entradas existentes (`files`, `packages`, `relationships`)
  de los retirados: el documento pasa de 2024 a 2020 archivos y de 2025 a 2021
  paquetes. Dos de los seis (`estado_global.c`, `generator_constants.c`) no
  figuraban en el SBOM.
- El checksum raíz (`sha256(nombre + versión + año)` en
  `nucleo/sbom.py::_generar_packages`) no depende del inventario: sigue válido.
- `synapse.spdx.json.sha256` estaba **desactualizado** (declaraba `18c25118…`
  frente al `94c6c3a2…` real); se recalcula y ahora coincide
  (`4eeae401…`).

## Otros checks

| check | resultado |
|---|---|
| `pytest tests/auditoria/test_r303_dumps_c_retirados.py` | 4 passed |
| `git ls-files nucleo` | sin los 6 dumps |
| `build.py --skip-test` | rc=0, S2==S3 `ad65693a51c2` |
| `verificar_contratos.py` | 516 deuda, 0 nuevas |
| `verificar_alineacion.py` | 0 brechas |
| `verificar_encoding.py --estricto` | OK (2388 archivos) |
| `contrastar.py --plan docs/plan_ME_r303_artefactos_c_generados.md` | PASS (2/2) |
| `alineacion.py --verificar --me r303_artefactos_c_generados` | OK: sin archivos de producción (solo retiros) |

## Deuda registrada

- **H-R303-1** (nueva): el SBOM versionado lista **1068 entradas de archivos
  que ya no existen** (objetos `.o`, `build/obj/*`, `synapse_unity.c`,
  `verificar_e2e.py`, instaladores movidos), resto de un escaneo del árbol de
  trabajo sucio en 2026-08-21. Requiere regeneración determinista (solo
  archivos versionados) en el pipeline. Resolución asignada: ME
  `r304_sbom_regeneracion`.
- **H25** (histórica, sin cambios de alcance): los otros ocho `.c` con `.syn`
  homónimo (`generator.c`, `generator_pgo.c`, `lexer.c`, `memoria.c`,
  `parser.c`, `principal.c`, `resolvedor_axon.c`, `tabla_simbolos.c`) quedan en
  la lista `DEUDA_H25` del oráculo: puede menguar, no crecer.
