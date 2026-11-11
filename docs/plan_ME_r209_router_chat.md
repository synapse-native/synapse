# Plan ME r209 - Router y chat compilables con extraccion verificable

## Contexto

`opensyn/router.syn` no compila: usa helpers de texto no declarados
(`cmp_texto`, `strstr_f`, `atoi_f`), asigna variables sin `let` y declara
`ejecutar_lint`/`ejecutar_fmt` como `texto` aunque `ejecutar_comando` retorna
`entero`; ademas referencia `orchestrator_verificar_estado`, simbolo sin
implementacion local. `opensyn/chat.syn` usa sintaxis no soportada (`[]`,
`intentar`, `para cada`, argumentos con nombre, `listar_directorio`) y llama a
`oraculo_consultar`, que no existe.

El ME deja ambos modulos compilables, agrega extraccion de bloques de codigo en
router y chat, y valida el comportamiento con un oraculo E2E real.

## Requisitos (MTS)

requisito: Manual 7 §2.4
texto: "**Formateo de respuesta:** Extrae el código de la respuesta del modelo (usando expresiones regulares o parseo de bloques), lo valida con el compilador, y lo muestra."
implementacion: `opensyn/router.syn` agrega `extraer_codigo_router(respuesta)` y `procesar_consulta` lo aplica cuando la consulta es de generacion; `opensyn/chat.syn` agrega `extraer_codigo_chat(respuesta)` y valida el bloque con `compilar_codigo` de `std.oraculo`.
oraculo: tests/opensyn/test_router_chat_comportamiento.py

requisito: Manual 7 §2.4
texto: "El router está escrito en Synapse y actúa como el cerebro de alto nivel de OpenSyn. Decide qué modelo usar y cómo procesar la respuesta."
implementacion: `router.syn` conserva `clasificar_tarea`, `modo_para_tarea`, `orquestar`, `planificar_antes_de_actuar` y `file_finder`; el oraculo verifica la clasificacion de una tarea de error, una de generacion y el modo asignado.
oraculo: tests/opensyn/test_router_chat_comportamiento.py

requisito: Manual 7 §4.2
texto: "**Validación (paso crítico):** El LSP toma el código generado y ejecuta el compilador de Synapse/Syquex en modo `--check` (solo validación, sin generar binario)."
implementacion: `revisar_codigo_inline` conserva archivo/linea/mensaje/sugerencia y parsea `linea:columna:mensaje`; el oraculo compila el modulo y verifica `linea == 5` para `5:3:error de sintaxis`.
oraculo: tests/opensyn/test_router_chat_comportamiento.py

requisito: Manual 7 §6.2
texto: "**Nota de restauración (2026-10-01):** Sección restaurada textualmente por decisión del Arquitecto (Opción A, ME barrido_citas_v820) tras su eliminación involuntaria en la revisión de manuales v8.2.0 (commit 154a544); con ella, la selección de modelo (`[modelo]` nombre/ruta) vuelve a tener hogar normativo."
implementacion: `opensyn/chat.syn` agrega `leer_modelo_config()` y `seleccionar_modelo(args)`; prioriza el argumento CLI, luego `~/.opensyn/config.toml` (`[modelo] ruta = "..."`) y por ultimo el modelo por defecto.
oraculo: tests/opensyn/test_router_chat_comportamiento.py

requisito: Manual 7 §8
texto: "El LSP valida con `synapse check --no-emit` (compila correctamente)."
implementacion: `opensyn/chat.syn` agrega `validar_codigo_extraido(codigo)` que delega en `compilar_codigo` de `std.oraculo`; el oraculo verifica que un bloque extraido con `funcion` sea reconocido como codigo.
oraculo: tests/opensyn/test_router_chat_comportamiento.py

## Archivos

- `opensyn/router.syn` - helpers de texto, `let` en variables, tipos de lint/fmt, lifecycle local determinista y extraccion de codigo.
- `opensyn/chat.syn` - reescritura a sintaxis Synapse valida, contexto de workspace, seleccion de modelo, extraccion y validacion.
- `tests/opensyn/test_router_chat_comportamiento.py` - oraculo E2E nuevo (compila driver real y verifica enrutado/extraccion).
- `tests/fixtures/compilacion_baseline.txt` - retirar ambos modulos tras verificar.
- `docs/alineacion/r209_router_chat.md` - expediente de alineacion (generado despues).
- `docs/verificacion_ME_r209_router_chat.md` - verificacion de oraculos (generado despues).
- `docs/reportes/R209.md` - reporte del ME (generado despues).

## Desviaciones declaradas

- `orchestrator_iniciar_lifecycle`/`orchestrator_detener_lifecycle` no pueden
  enlazar contra `orquestrador_iniciar`/`orchestrator_apagar` porque
  `opensyn/orchestrator.h` declara esas funciones pero no existe implementacion
  C en el repo. Se reemplazan por stubs locales deterministas que retornan 0;
  la integracion real del ciclo de vida queda para el ME de orchestrator.
- `ejecutar_lint` y `ejecutar_fmt` retornan `entero` (codigo de salida de
  `ejecutar_comando`), no `texto`; no hay consumidores que esperen texto.
- No se toca `docs/gobernancia/GUIA_DE_GOBERNANZA.md` (modificado por otro
  agente) ni los artefactos no rastreados `nucleo/embedded_libs.h`,
  `nucleo/lsp_v3.c.bak`, `nucleo/lsp_v3.c.new`.
- Los tests existentes no se modifican; se ejecutan como regresion.

## Oraculos de cierre

1. `.venv\Scripts\python.exe main.py opensyn/router.syn --check --no-emit` -> rc 0.
2. `.venv\Scripts\python.exe main.py opensyn/chat.syn --check --no-emit` -> rc 0.
3. `.venv\Scripts\python.exe -m pytest tests/opensyn/test_router_chat_comportamiento.py -v` -> verde.
4. `.venv\Scripts\python.exe -m pytest tests/integration/test_compilacion_fase32.py -v` -> verde sin ambos modulos en baseline.
5. `.venv\Scripts\python.exe auditoria/verificar_alineacion.py` -> 0 brechas.
6. `python auditoria/alineacion.py --verificar --me r209_router_chat` -> sin brechas.
7. `python auditoria/contrastar.py --plan docs/plan_ME_r209_router_chat.md` -> sin brechas.
