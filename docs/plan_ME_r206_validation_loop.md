# Plan ME r206 - Bucle de validación y corrección automática

## Contexto

`opensyn/validation_loop.syn` no compila: usa `_syn_capturar_comando`, símbolo
que no está declarado en el módulo ni en `std.sistema`, y por eso arrastra dos
errores de variable no declarada. Además, el bucle actual no distingue warnings
de errores (marca inválido cualquier texto de salida), no parsea línea/columna,
no devuelve el último código junto con los errores y escribe feedback aunque no
haya corrección humana.

El ME repara el módulo y lo lleva a comportamiento E2E verificable con el
compilador real: 3 intentos máximo, error exacto en el prompt, fallo definitivo
honesto y éxito cuando el código corregido compila.

## Requisitos (MTS)

requisito: Manual 7 §4.2
texto: "El LSP es el responsable de orquestar el bucle de validación (descrito en la sección 6.3)."
implementacion: `bucle_validacion` y `bucle_validacion_detallado` viven en `opensyn/validation_loop.syn`; el LSP delega en ellos y recibe un resultado estructurado con código, errores, intentos y ubicación del último error.
oraculo: tests/opensyn/test_validation_loop_comportamiento.py

requisito: Manual 7 §4.2
texto: "El LSP toma el código generado y ejecuta el compilador de Synapse/Syquex en modo `--check` (solo validación, sin generar binario)."
implementacion: `validar_con_check` escribe el código en un temporal único con extensión `.syn` o `.syq` según el idioma, ejecuta `synapse check --no-emit "<archivo>"` con `std.sistema.ejecutar_comando` y decide validez por el código de salida, no por la mera presencia de texto.
oraculo: tests/opensyn/test_validation_loop_comportamiento.py

requisito: Manual 7 §4.2
texto: "Si falla: El LSP captura el error (stderr del compilador) y repite el proceso (hasta 3 intentos), añadiendo el error al prompt para que OpenSyn lo corrija."
implementacion: `validar_con_check` redirige stdout+stderr a un archivo temporal y lo lee; `bucle_validacion_detallado` repite generación y validación hasta `MAX_INTENTOS`, reconstruyendo el prompt con `parsear_error_compilacion` y `reconstruir_prompt_con_error`.
oraculo: tests/opensyn/test_validation_loop_comportamiento.py

requisito: Manual 7 §4.2
texto: "Si después de 3 intentos el código no compila, el LSP devuelve el último código generado y los errores al editor, mostrando un mensaje de \"No se pudo generar código válido automáticamente. Intenta ajustar la instrucción.\""
implementacion: `ResultadoBucle` conserva `codigo`, `errores`, `intentos` y la ubicación del último error; `bucle_validacion` devuelve el código si hubo éxito o el mensaje prescrito con los errores si se agotaron los intentos.
oraculo: tests/opensyn/test_validation_loop_comportamiento.py

requisito: Manual 7 §6.3
texto: "Generación inicial (intento 1): OpenSyn genera código basado en la instrucción y el contexto."
implementacion: `bucle_validacion_detallado` genera una vez con `generar_codigo_ia(prompt_inicial)`, valida y sólo corrige si la primera validación falla; el contador arranca en 1.
oraculo: tests/opensyn/test_validation_loop_comportamiento.py

requisito: Manual 7 §6.3
texto: "El compilador devuelve el error exacto (línea, columna, mensaje) a través de su salida de error estándar."
implementacion: `parsear_error_compilacion` extrae `archivo:línea:columna - mensaje` del primer diagnóstico `[Synapse]` y rellena `ErrorCompilacion`; el resultado estructurado expone esos campos sin structs anidados.
oraculo: tests/opensyn/test_validation_loop_comportamiento.py

requisito: Manual 7 §6.3
texto: "Construye un nuevo prompt añadiendo: \"El código anterior tiene el siguiente error: {mensaje_error}. Por favor, corrígelo.\""
implementacion: `reconstruir_prompt_con_error` conserva el prompt original y añade mensaje, línea, columna e instrucción exacta; el test verifica que el segundo prompt enviado al LLM contiene el diagnóstico del compilador.
oraculo: tests/opensyn/test_validation_loop_comportamiento.py

requisito: Manual 7 §6.3
texto: "Se repiten los pasos 2 y 3 para el intento 2. Si vuelve a fallar, se hace un intento 3."
implementacion: el bucle `mientras intentos < MAX_INTENTOS` ejecuta exactamente dos correcciones tras el intento inicial; el test cuenta las peticiones al LLM y exige 1, 2 o 3 según el caso.
oraculo: tests/opensyn/test_validation_loop_comportamiento.py

requisito: Manual 7 §6.3
texto: "Si el tercer intento falla, el LSP muestra el último código generado y los errores al usuario, con un mensaje: \"No se pudo generar código válido automáticamente. Intenta ajustar la instrucción o corrige manualmente.\""
implementacion: tras el tercer fallo, `bucle_validacion_detallado` devuelve `exito = falso`, el último código y la última salida del compilador; `bucle_validacion` compone el mensaje prescrito y no oculta los errores.
oraculo: tests/opensyn/test_validation_loop_comportamiento.py

requisito: Manual 7 §6.3
texto: "Cuando el usuario corrige el código manualmente (después de un fallo), OpenSyn guarda el par (instrucción, código_corregido) en `~/.opensyn/feedback.jsonl`."
implementacion: `guardar_feedback` resuelve `~` con `USERPROFILE`/`HOME` (o `OPENSYN_FEEDBACK_PATH` para pruebas), escribe JSONL con `instruction`/`output` y devuelve `0`/`-1`; `registrar_correccion_manual` es el punto de entrada para la corrección humana, no el fallo automático.
oraculo: tests/opensyn/test_validation_loop_comportamiento.py

requisito: Manual 2 §5.1
texto: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
implementacion: toda función pública nueva o modificada (`validar_con_check`, `parsear_error_compilacion`, `bucle_validacion_detallado`, `bucle_validacion`, `guardar_feedback`, `registrar_correccion_manual`, auxiliares de archivo) declara `requiere`/`garantiza`; las garantías usan `_resultado_` y no prometen más de lo verificable.
oraculo: tests/opensyn/test_validation_loop_comportamiento.py

## Archivos

- `opensyn/validation_loop.syn` - reparación de compilación, validación por rc, parseo de diagnóstico, bucle estructurado y feedback.
- `tests/opensyn/test_validation_loop_comportamiento.py` - oráculo E2E nuevo con LLM falso y compilador real.
- `tests/fixtures/compilacion_baseline.txt` - retirar `opensyn/validation_loop.syn` al compilar.
- `docs/alineacion/r206_validation_loop.md` - expediente de alineación (generado después).
- `docs/verificacion_ME_r206_validation_loop.md` - verificación de oráculos (generado después).
- `docs/reportes/R206.md` - reporte del ME (generado después).

## Desviaciones declaradas

- El plan maestro cita Manual 32 §6.3/§6.4 para r206, pero en el manual real
  `MANUAL  FASE 32 AGENTE DE CODIFICACIÓN.md` esas secciones son "Pipeline AOT
  Asíncrono" y "Ejecución Asíncrona con Timeout", no el bucle de validación. El
  requisito funcional se toma de Manual 7 §4.2/§6.3, que es la sección mapeada
  para `opensyn/validation_loop.syn`.
- No se usa `_syn_capturar_comando`: no está declarado en el módulo y no expone
  código de salida. Se usa `std.sistema.ejecutar_comando` con redirección a un
  temporal para obtener rc + stdout/stderr, sin inventar APIs.
- El `synapse.exe` instalado (8.1.0) reporta el módulo como válido aunque
  `main.py` detecta los 3 errores reales; el oráculo usa un wrapper de test que
  invoca el compilador actual (`python main.py ... --check --no-emit`) y no
  depende del binario stale.
- `guardar_feedback` ya no se llama automáticamente al agotar intentos: el
  manual lo define para la corrección manual del usuario. Se expone
  `registrar_correccion_manual` y se prueba `guardar_feedback` directamente con
  `OPENSYN_FEEDBACK_PATH` para no escribir en el HOME real.
- No se toca `docs/gobernancia/GUIA_DE_GOBERNANZA.md` (modificado por otro
  agente) ni los artefactos no rastreados `nucleo/embedded_libs.h`,
  `nucleo/lsp_v3.c.bak`, `nucleo/lsp_v3.c.new`.
- Los tests existentes no se modifican; se ejecutan como oráculos de regresión.

## Oráculos de cierre

1. `.venv\Scripts\python.exe main.py opensyn/validation_loop.syn --check --no-emit` -> rc 0.
2. `.venv\Scripts\python.exe -m pytest tests/opensyn/test_validation_loop_comportamiento.py -v` -> verde.
3. `.venv\Scripts\python.exe -m pytest tests/test_bucle_validacion.py tests/integration/test_ai_correction_opensyn.py tests/integration/test_ai_correction.py tests/integration/test_opensyn_integration.py -v` -> verde sin modificar tests.
4. `.venv\Scripts\python.exe -m pytest tests/integration/test_compilacion_fase32.py -v` -> verde sin `validation_loop` en baseline.
5. `.venv\Scripts\python.exe auditoria/verificar_alineacion.py` -> 0 brechas.
6. `python auditoria/alineacion.py --verificar --me r206_validation_loop` -> sin brechas.
7. `python auditoria/contrastar.py --plan docs/plan_ME_r206_validation_loop.md` -> sin brechas.
