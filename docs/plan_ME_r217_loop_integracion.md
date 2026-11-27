# Plan ME r217_loop_integracion - Cableado de validation_loop y pipeline al loop vivo

## Contexto

`opensyn/principal.syn` es el loop vivo del agente (TUI). Los modulos
`opensyn/validation_loop.syn` y `opensyn/pipeline_multiagente.syn` existen
con oraculos E2E propios, pero no estan cableados al loop vivo: tras
editar/escribir un `.syn`/`.syq`, el modelo no recibe validacion del
compilador real, y no hay comandos para validar o ejecutar el pipeline.

Este ME cierra el bucle editar->compilar->corregir (Manual 7 §4.2) y expone
`/validar` y `/pipeline` en la TUI.

## Requisitos (MTS)

requisito: Manual 7 §2.1
texto: "El orquestador es un proceso en C que gestiona el ciclo de vida del servidor de inferencia (`llama-server`)."
implementacion: `opensyn/principal.syn` importa `validation_loop` y `pipeline_multiagente` y reutiliza sus funciones (`validar_con_check`, `ejecutar_pipeline`) en lugar de reimplementarlas.
oraculo: tests/opensyn/test_validation_loop_comportamiento.py

requisito: Manual 7 §2.3
texto: "El pipeline RAG (Retrieval-Augmented Generation) es el cerebro de OpenSyn."
implementacion: el comando `/pipeline` invoca `ejecutar_pipeline` para orquestar las fases Explorer/Architect/Coder/Verifier deterministas.
oraculo: tests/opensyn/test_pipeline_multiagente_comportamiento.py

requisito: Manual 7 §4.2
texto: "Validación (paso crítico): El LSP toma el código generado y ejecuta el compilador de Synapse/Syquex en modo `--check` (solo validación, sin generar binario)."
implementacion: `validar_fuente_si_aplica` se ejecuta tras `TOOL editar/escribir/aplicar_patch` sobre `.syn/.syq`, invocando `validar_con_check`; el resultado se anexa a la salida para que el modelo auto-corrija (maximo 3 intentos segun §4.2).
oraculo: tests/opensyn/test_validation_loop_comportamiento.py

requisito: Manual 7 §7.3
texto: "Cero telemetría: Verificado con monitoreo de red (sin conexiones salientes)."
implementacion: la validacion usa el compilador local (sin red); no se agregan conexiones salientes.
oraculo: tests/opensyn/test_validation_loop_comportamiento.py

## Archivos

- `opensyn/principal.syn` - imports, helper `validar_fuente_si_aplica`, wiring en bucle de herramientas, comandos `/validar` y `/pipeline`.

## Desviaciones declaradas

- Las declaraciones `externo` de `_syn_ollama_consultar`/`_syn_ollama_modelos` se retiran de `principal.syn` porque `validation_loop` ya las provee; evita "Redefinicion".
- El pipeline se invoca con archivo vacio en `/pipeline` (modo determinista); el cableado a un archivo concreto se deja al agente.
- No se modifican tests existentes.

## Oraculos de cierre

1. `.venv\Scripts\python.exe main.py opensyn/principal.syn --check --no-emit` -> rc 0.
2. `.venv\Scripts\python.exe -m pytest tests/opensyn/test_validation_loop.py tests/opensyn/test_validation_loop_comportamiento.py tests/opensyn/test_pipeline_multiagente.py tests/opensyn/test_pipeline_multiagente_comportamiento.py -v` -> verde.
3. `.venv\Scripts\python.exe auditoria/verificar_alineacion.py` -> 0 brechas.
4. `.venv\Scripts\python.exe auditoria/alineacion.py --verificar --me r217_loop_integracion` -> sin brechas.
5. `.venv\Scripts\python.exe auditoria/contrastar.py --plan docs/plan_ME_r217_loop_integracion.md` -> sin brechas.
