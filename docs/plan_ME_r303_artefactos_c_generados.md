# Plan de Micro-Entregable r303_artefactos_c_generados

## Objetivo

Cerrar **H-R302-1**. Decisión de ingeniería: los seis `.c` señalados
(`nucleo/analizador_semantico.c`, `ast_nodes.c`, `diagnostics.c`, `errores.c`,
`estado_global.c`, `generator_constants.c`) son **dumps del compilador S1**
(primera línea: `// salida_metal.c - Generado por Synapse Compilador`), no
insumos de build. El build compila desde las fuentes `.syn` y escribe sus
propios objetos `nucleo/_<módulo>.c` (prefijo `_`, ver `_es_produccion` y las
reglas 12 del repo: los artefactos/instrumentación con `_` no son producción).

Por lo tanto **no se regeneran**: regenerarlos fabricaría de nuevo un
artefacto versionado que deriva a la primera edición de su `.syn`. La fuente de
verdad es `nucleo/<módulo>.syn`; el `.c` versionado solo aporta deriva y ruido
en el SBOM. Se **retiran del control de versiones**.

Los otros ocho `.c` de la misma clase (`generator.c`, `generator_pgo.c`,
`lexer.c`, `memoria.c`, `parser.c`, `principal.c`, `resolvedor_axon.c`,
`tabla_simbolos.c`) ya están registrados como deuda histórica **H25** ("higiene
en ME-R8"); este ME los deja en una lista explícita del oráculo para que no
aparezcan nuevos, sin ampliar el alcance aprobado de H-R302-1.

Además:
- `auditoria/contratos_baseline.txt` **no contiene** entradas de esos `.c` (su
  formato es `ruta::función` sobre `.syn`): se verifica y queda sin cambios. La
  nota de H-R302-1 que los citaba era imprecisa.
- `synapse.spdx.json` se poda de las entradas de archivo/paquete/relación de
  los seis retirados. El checksum raíz del SBOM
  (`sha256(nombre + versión + año)`) no depende del inventario —verificado
  contra `nucleo/sbom.py::_generar_packages`—, así que el documento queda
  autoconsistente; se actualiza su `.sha256`.

## Requisito 1 — SBOM sin referencias a archivos inexistentes

requisito: Manual 9 §6.1
texto: "□ **SBOM y SLSA**: generados y firmados correctamente."
implementacion: se retiran de `synapse.spdx.json` las entradas `files`, `packages` y `relationships` de los seis `.c` eliminados, y se recalcula `synapse.spdx.json.sha256`; el inventario deja de listar rutas que ya no existen en el árbol.
oraculo: tests/auditoria/test_r303_dumps_c_retirados.py

## Requisito 2 — ninguna regresión por el retiro

requisito: Manual 1 §7.4
texto: "Aprobación del 100% de los tests unitarios, de integración y fuzzing sin regresiones."
implementacion: el oráculo comprueba que los seis `.c` ya no están versionados ni presentes, que el build sigue produciendo sus `nucleo/_*.c` desde los `.syn`, y que ningún `.c` versionado con `.syn` homónimo aparece fuera de la lista H25.
oraculo: tests/auditoria/test_r303_dumps_c_retirados.py

## Evidencia

| check | resultado |
|---|---|
| `pytest tests/auditoria/test_r303_dumps_c_retirados.py` | 4 passed |
| `auditoria/verificar_contratos.py` | OK: 516 deuda en baseline, 0 nuevas |
| `python build.py --skip-test` | rc=0, S2==S3 `ad65693a51c2` (los dumps no eran insumos del build) |
| `python auditoria/verificar_alineacion.py` | 0 brechas |
| `python auditoria/verificar_encoding.py --estricto` | OK (2388 archivos) |
| `python auditoria/contrastar.py --plan docs/plan_ME_r303_artefactos_c_generados.md` | PASS (2/2) |
| `python auditoria/alineacion.py --verificar --me r303_artefactos_c_generados` | OK: sin archivos de producción (solo retiros) |
