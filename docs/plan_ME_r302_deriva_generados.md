# Plan de Micro-Entregable r302_deriva_generados

## Objetivo

Buscar el patrón de H-R300-1 (artefacto generado que deriva de su generador) en
el resto del repositorio. Resultado del barrido:

| artefacto | generador | estado |
|---|---|---|
| `runtime/core/ast_nodos.h` | `scripts/gen_ast_nodos_h.py --check` | **en sync** |
| `lib/runtime_bindings.syq` | `opensyn/generate_runtime_bindings.py` | **en sync** (tras arreglar el generador) |
| `librerias/embedded_libs.h` | `tests/_gen_embedded.py` | **DERIVA**: sin regenerar desde 2026-08-17; embebía CRLF de fuentes ya normalizadas a LF |
| `nucleo/generator.syn` | `nucleo/_rebuild_generator.py` | en sync (ME r301) |
| `nucleo/*.c` (6 generados) | compilador S1 | **DERIVA CONGELADA** (sept-2026 vs .syn de nov-2026); no se enlazan → H-R302-1 |

Además, tres generadores Python estaban **rotos** por el barrido de BOM de r288,
que les inyectó comentarios `// cumple Manual ...` (sintaxis inválida):
`opensyn/generate_runtime_bindings.py`, `opensyn/bindings_generator.py` y
`opensyn/full_pipeline.py`. El hook regeneraba bindings como paso **no
bloqueante**, así que el fallo quedó oculto.

## Requisito 1 — generador de bindings operativo

requisito: Manual 6 §3.1
texto: "Tanto Synapse como Syquex permiten declarar funciones de C con la palabra clave `externo`."
implementacion: se corrigen las citas inválidas (`//` → `#`) en `opensyn/generate_runtime_bindings.py`, `opensyn/bindings_generator.py` y `opensyn/full_pipeline.py`; el generador vuelve a ejecutarse y produce exactamente `lib/runtime_bindings.syq` (97 funciones).
oraculo: tests/auditoria/test_r302_generados_sin_deriva.py

## Requisito 2 — pipeline de OpenSyn ejecutable

requisito: Manual 7 §2.1
texto: "El orquestador es un proceso en C que gestiona el ciclo de vida del servidor de inferencia (`llama-server`)."
implementacion: `opensyn/full_pipeline.py` y `opensyn/bindings_generator.py` vuelven a importarse (AST válido); sus líneas de anclaje `# cumple Manual 7 §2.1` sustituyen a las inválidas `//`.
oraculo: tests/auditoria/test_r302_generados_sin_deriva.py

## Requisito 3 — librerías embebidas sincronizadas

requisito: Manual 1 §3.1
texto: "El compilador unificado procesa código fuente de Synapse (.syn), Syquex (.syq) e incluso prompts en lenguaje natural (via OpenSyn) a través de un pipeline compar"
implementacion: `librerias/embedded_libs.h` se regenera con `tests/_gen_embedded.py`; el artefacto lleva la cita `// cumple Manual 1 §3.1` que lo vincula a su requisito y el generador gana `--check` para detectar deriva sin escribir.
oraculo: tests/auditoria/test_r302_generados_sin_deriva.py

## Requisito 4 — ningún generador puede quedar roto

requisito: Manual 1 §7.4
texto: "Aprobación del 100% de los tests unitarios, de integración y fuzzing sin regresiones."
implementacion: el oráculo parsea **todos** los `.py` versionados y falla con el archivo:línea del primero inválido, más los `--check` de `ast_nodos.h`, bindings y embedded libs.
oraculo: tests/auditoria/test_r302_generados_sin_deriva.py

## Evidencia

| check | resultado |
|---|---|
| `pytest tests/auditoria/test_r302_generados_sin_deriva.py` | 4 passed |
| `scripts/gen_ast_nodos_h.py --check` | sincronizado (134 constantes) |
| `opensyn/generate_runtime_bindings.py -o <tmp>` + diff | 0 bytes (97 funciones) |
| `tests/_gen_embedded.py --check` | sincronizado (11 librerías) |
| `build.py --skip-test` | rc=0, S2==S3 `ad65693a51c2` |
| `pytest` harness gcc + r301 | 13 passed |
| `verificar_alineacion.py` / `verificar_encoding.py --estricto` | 0 brechas / OK (2391 archivos) |

## Hallazgos

- **H-R302-2** (resuelto): el agregado `librerias/embedded_libs.h` embebe las
  citas `cumple Manual ...` de sus fuentes dentro de literales C, y los gates
  las leían como citas propias sin sección válida. Se excluye del escaneo de
  citas en `verificar_alineacion.py` y `alineacion.py` (sus `.syn` fuente sí se
  escanean); el archivo conserva su cita de cabecera para `contrastar.py`.

- **H-R302-1** (nuevo, requiere decisión): 6 `.c` generados por S1 y
  versionados (`analizador_semantico`, `ast_nodes`, `diagnostics`, `errores`,
  `estado_global`, `generator_constants`) están congelados en sept-2026
  mientras sus `.syn` cambiaron hasta nov-2026. No se enlazan en el build, pero
  figuran en `auditoria/contratos_baseline.txt` y en `synapse.spdx.json`.
  Resolución asignada: ME `r303_artefactos_c_generados` (regenerar o retirar,
  actualizando baseline y SPDX con decisión del Arquitecto).
