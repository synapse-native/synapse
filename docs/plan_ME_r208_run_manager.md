# Plan ME r208 - Run manager reanudable y limites de ejecucion

## Contexto

`opensyn/run_manager.syn` no compilaba (`si json[fin] == 34:` usaba indexacion
no soportada) y su logica de checkpoint tenia fallos de ownership: liberaba
`run_id`/`checkpoint_path` compartidos, interpretaba `0` de
`_syn_escribir_archivo` como error y no reconstruia `checkpoint_path` ni
`timestamp_inicio` al deserializar. El ME deja el modulo compilable, con
checkpoints persistentes y reanudacion verificable por un oraculo E2E.

## Requisitos (MTS)

requisito: Manual 7 §4.3
texto: "Si el servidor de inferencia no responde en 30 segundos, el LSP devuelve un error al usuario."
implementacion: `opensyn/run_manager.syn` mantiene `TIMEOUT_RUN_ABSOLUTO_MS = 300000`, `tiempo_transcurrido(run)` y `run_timeout(run)`; el oraculo crea un run con `timestamp_inicio = ahora_ms() - 300001` y verifica `run_timeout == verdadero`.
oraculo: tests/opensyn/test_run_manager_comportamiento.py

requisito: Manual 7 §4.3
texto: "Si el código generado es inválido y se agotan los intentos, el LSP muestra un mensaje y ofrece regenerar (o pedir ayuda al usuario)."
implementacion: `marcar_subtarea_fallida(run, error, intentos)` marca `RUN_FALLIDO` cuando `intentos >= MAX_INTENTOS_SUBTAREA` (3), persiste el checkpoint y `run_terminado(run)` devuelve verdadero; el oraculo verifica el estado persistido.
oraculo: tests/opensyn/test_run_manager_comportamiento.py

requisito: Manual 2 §5.1
texto: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
implementacion: toda funcion publica nueva o modificada de `run_manager.syn` (`crear_run`, `guardar_checkpoint`, `cargar_checkpoint`, `marcar_subtarea_completada`, `marcar_subtarea_fallida`, `run_terminado`, `resumir_run`, `tiempo_transcurrido`, `run_timeout`, `serializar_run`, `deserializar_run`, `construir_ruta_checkpoint`, helpers de archivo) conserva `requiere`/`garantiza` booleanos y verificables.
oraculo: tests/opensyn/test_run_manager_comportamiento.py

requisito: Manual 2 §5.1
texto: "**`garantiza`:** Se evalúa inmediatamente antes de cada `retornar`. La variable `_resultado_` contiene el valor que se va a retornar."
implementacion: las garantias de `run_manager.syn` se limitan a rangos y relaciones observables (`estado` entre `RUN_PENDIENTE` y `RUN_FALLIDO`, resultados `0/-1`, `_resultado_ >= 0`); el oraculo compila el modulo con el compilador real.
oraculo: tests/opensyn/test_run_manager_comportamiento.py

## Archivos

- `opensyn/run_manager.syn` - compilacion, ownership con `_syn_strcpy`, propagacion de errores de checkpoint, override `OPENSYN_RUNS_DIR`, deserializacion completa.
- `tests/opensyn/test_run_manager_comportamiento.py` - oraculo E2E nuevo con compilador real y directorio de runs aislado.
- `tests/fixtures/compilacion_baseline.txt` - retirar `opensyn/run_manager.syn` tras verificar.
- `docs/alineacion/r208_run_manager.md` - expediente de alineacion (generado despues).
- `docs/verificacion_ME_r208_run_manager.md` - verificacion de oraculos (generado despues).
- `docs/reportes/R208.md` - reporte del ME (generado despues).

## Desviaciones declaradas

- El plan maestro cita `Manual 32 §3.2/§3.4`, pero `docs/manuales/MANUAL 32.md`
  no existe con ese nombre (el archivo real es
  `MANUAL  FASE 32 AGENTE DE CODIFICACIÓN.md`, con dos espacios) y el indice de
  manuales no lo reconoce. El gate de alineacion se ancla en `Manual 7 §4.3`
  (seccion mapeada para este archivo) y `Manual 2 §5.1`; `Manual 32 §3.2/§3.4`
  se conserva como referencia funcional de sesiones/reanudacion.
- `cargar_checkpoint`, `resumir_run`, `construir_ruta_checkpoint`,
  `escribir_checkpoint_local` y `leer_checkpoint_local` consumen sus parametros
  `texto` (convencion RAII del compilador). El llamador que necesite conservar
  una cadena pasa `_syn_strcpy`; el oraculo lo hace y el modulo lo documenta en
  los comentarios de las funciones afectadas.
- No se toca `docs/gobernancia/GUIA_DE_GOBERNANZA.md` (modificado por otro
  agente) ni los artefactos no rastreados `nucleo/embedded_libs.h`,
  `nucleo/lsp_v3.c.bak`, `nucleo/lsp_v3.c.new`.
- Los tests existentes no se modifican; se ejecutan como regresion.

## Oraculos de cierre

1. `.venv\Scripts\python.exe main.py opensyn/run_manager.syn --check --no-emit` -> rc 0.
2. `.venv\Scripts\python.exe -m pytest tests/opensyn/test_run_manager_comportamiento.py -v` -> verde.
3. `.venv\Scripts\python.exe -m pytest tests/integration/test_compilacion_fase32.py -v` -> verde sin `run_manager.syn` en baseline.
4. `.venv\Scripts\python.exe auditoria/verificar_alineacion.py` -> 0 brechas.
5. `python auditoria/alineacion.py --verificar --me r208_run_manager` -> sin brechas.
6. `python auditoria/contrastar.py --plan docs/plan_ME_r208_run_manager.md` -> sin brechas.
