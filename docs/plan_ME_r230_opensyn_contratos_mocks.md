# Plan ME r230 - Contratos y mocks de OpenSyn sin respuestas vacías

FASE: R230 (normalización de contratos y mocks)
ID: r230_opensyn_contratos_mocks

## Contexto

La suite `tests/opensyn/` ya no usa `""` como turno fallido en los mocks de
`test_validation_loop_comportamiento.py` y `test_pipeline_multiagente_comportamiento.py`:
devuelve código sintácticamente inválido no vacío. Queda el caso real que el
plan original quería cubrir: si el LLM devuelve una cadena vacía,
`bucle_validacion_detallado` llama a `validar_con_check`, cuyo contrato
`requiere: longitud(codigo) > 0` aborta el proceso con
`Assertion failed: Fallo en contrato: requiere`. El pipeline multiagente tiene
el mismo riesgo cuando el Coder devuelve vacío: `validar_codigo("")` es falso y
`validation_loop_corregir("")` también viola su precondición.

El objetivo es que una respuesta vacía se intercepte como
`ERR_RESPUESTA_VACIA` antes de invocar al compilador, sin depender de que la
validación por contrato mate el proceso.

## Requisitos (MTS)

requisito: Manual 7 §6.3
texto: "Este bucle asegura que el código generado cumpla con las reglas del compilador."
implementacion: `opensyn/validation_loop.syn` agrega `ERR_RESPUESTA_VACIA` y una
guarda `es_codigo_vacio()` en `bucle_validacion_detallado` (intento inicial y
reintentos); `opensyn/pipeline_multiagente.syn` usa la misma guarda en
`validation_loop_corregir`. Una respuesta vacía del LLM retorna
`ResultadoBucle`/`ResultadoCorreccion` con `errores = ERR_RESPUESTA_VACIA` sin
llamar a `validar_con_check`.
oraculo: tests/opensyn/test_validation_loop_comportamiento.py

requisito: Manual 2 §5.1
texto: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
implementacion: la guarda respeta la precondición `longitud(codigo) > 0` de
`validar_con_check`: la cadena vacía se clasifica antes de la llamada y el
contrato nunca se viola en runtime. Los tests E2E ejercitan la ruta completa con
el compilador real y verifican que el proceso termina con rc=0.
oraculo: tests/opensyn/test_validation_loop_comportamiento.py

requisito: Manual 6 §1.1
texto: "El backend (análisis semántico, generación de código, optimizaciones) es **compartido** y solo opera sobre `SemNodo[]`."
implementacion: `validation_loop_corregir` de `opensyn/pipeline_multiagente.syn`
deja de exigir `longitud(codigo) > 0` en su `requiere`; rechaza la respuesta
vacía antes de invocar el backend compartido de validación y devuelve
`ERR_RESPUESTA_VACIA` con `intentos = 0|1`.
oraculo: tests/opensyn/test_pipeline_multiagente_comportamiento.py

## Archivos

- `opensyn/validation_loop.syn` - guarda de respuesta vacía en el bucle.
- `opensyn/pipeline_multiagente.syn` - guarda de respuesta vacía en
  `validation_loop_corregir` para la ruta del pipeline.
- `tests/opensyn/test_validation_loop_comportamiento.py` - dos oráculos nuevos:
  respuesta vacía inicial y respuesta vacía durante la corrección.
- `tests/opensyn/test_pipeline_multiagente_comportamiento.py` - oráculo nuevo:
  Coder devuelve vacío y el pipeline retorna `ERR_RESPUESTA_VACIA` sin abortar.
- `docs/alineacion/r230_opensyn_contratos_mocks.md` - expediente de alineación.
- `docs/verificacion_ME_r230_opensyn_contratos_mocks.md` - verificación del ME.

## Verificación

- `.venv\Scripts\python.exe -m pytest tests/opensyn/test_validation_loop_comportamiento.py tests/opensyn/test_pipeline_multiagente_comportamiento.py -v`
- `.venv\Scripts\python.exe -m pytest tests/opensyn -q` (regresión completa; el
  timeout de `test_installer` por hash del GGUF local se registra como límite
  ambiental si persiste)
- `.venv\Scripts\python.exe auditoria\verificar_alineacion.py`
- `.venv\Scripts\python.exe auditoria\contrastar.py --plan docs/plan_ME_r230_opensyn_contratos_mocks.md`
- `.venv\Scripts\python.exe auditoria\alineacion.py --verificar --me r230_opensyn_contratos_mocks`
