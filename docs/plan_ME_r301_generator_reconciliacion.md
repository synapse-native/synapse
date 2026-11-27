# Plan de Micro-Entregable r301_generator_reconciliacion

## Objetivo

Cerrar **H-R300-1**: `nucleo/generator.syn` se declara auto-generado por
`nucleo/_rebuild_generator.py`, pero el archivo versionado contenía correcciones
manuales que el rebuild descartaba. Regenerarlo antes de este ME perdía:

- los contratos `requiere`/`garantiza` de cinco funciones públicas de
  `emision_c.syn` (Manual 2 §12/§5.1);
- cuatro bloques de **H-R275-1** (indexado de `texto` produce `CadenaSegura`)
  en `expr_eval.syn`, `nodos_flujo.syn`, `funciones.syn` y `orquestador.syn`
  (Manual 2 §8.2);
- la cita de norma del encabezado y arrastraba comentarios inválidos
  (`// cumplé Manual ...`).

Reconciliación: las correcciones se portan a los submódulos, se regenera el
combinado y se verifica que la regeneración es **idempotente**.

## Requisito 1 — contratos de las funciones públicas de emisión

requisito: Manual 2 §5.1
texto: "**`garantiza`:** Se evalúa inmediatamente antes de cada `retornar`. La variable `_resultado_` contiene el valor que se va a retornar."
implementacion: `nucleo/generador/emision_c.syn` recibe los bloques `requiere`/`garantiza` de `traducir_tipo_c_campo`, `traducir_tipo_retorno`, `gen_emitir_linea`, `gen_emitir_str` y `gen_emitir_nueva_linea`; `traducir_tipo_c` conserva el contrato más estricto del submódulo (`tipo_synapse != nulo`) en lugar del `verdadero` manual.
oraculo: tests/auditoria/test_r301_generator_reconciliacion.py

## Requisito 2 — paridad de inferencia del indexado de texto

requisito: Manual 2 §8.2
texto: "Synapse utiliza un algoritmo de inferencia de tipos basado en **Hindley‑Milner** (algoritmo W)."
implementacion: los cuatro bloques H-R275-1 se mueven desde `generator.syn` a sus submódulos de origen (`expr_eval.syn`, `nodos_flujo.syn`, `funciones.syn`, `orquestador.syn`), de modo que la regeneración los conserve; `nucleo/generador/contexto.syn` lleva la cita §8.2 que sobrevive al rebuild.
oraculo: tests/auditoria/test_r301_generator_reconciliacion.py

## Requisito 3 — handles FFI del indexado

requisito: Manual 6 §3.1
texto: "Tanto Synapse como Syquex permiten declarar funciones de C con la palabra clave `externo`."
implementacion: en `expr_eval.syn` el bloque de indexado mantiene el cast `(void*)(intptr_t)` y la llamada a `_syn_nativo_expr_tipo_c` documentados con `// cumple Manual 6 §3.1`; no cambia la ABI.
oraculo: tests/auditoria/test_r301_generator_reconciliacion.py

## Evidencia

| check | resultado |
|---|---|
| `pytest tests/auditoria/test_r301_generator_reconciliacion.py` | 4 passed |
| `python nucleo/_rebuild_generator.py` + `diff` | idempotente (0 bytes) |
| `synapse fmt --check` en `generator.syn` y `generador/*.syn` | rc=0 |
| `build.py --skip-test` | rc=0, S2==S3 `ad65693a51c2` |
| `pytest` (formatter, fmt, r300, módulos, backend) | 50 passed |
| `verificar_alineacion.py` / `verificar_encoding.py --estricto` | 0 brechas / OK (2385 archivos) |

## Hallazgos

- **H-R300-1**: **RESUELTO** — `generator.syn` == salida de los submódulos, con
  las correcciones H-R275-1 y los contratos viviendo en su origen.
- Se eliminan las citas inválidas `// cumplé Manual ...` (5 ocurrencias en
  `emision_c.syn`/combinado) que no podían ser chequeadas por el gate.
