# Verificacion ME r230_opensyn_contratos_mocks

## Causa raiz

`bucle_validacion_detallado` llamaba a `validar_con_check` con la respuesta del
LLM sin comprobar que no estuviera vacia. Ese contrato exige
`longitud(codigo) > 0`, asi que una respuesta vacia abortaba el proceso con
`Assertion failed: Fallo en contrato: requiere` en vez de devolver un error
honesto. El pipeline multiagente tenia el mismo hueco: `validar_codigo("")`
devolvia falso y `validation_loop_corregir("")` violaba su propio
`requiere: longitud(codigo) > 0`.

## Marcas por requisito

- Manual 7 §6.3 CUMPLE. Este bucle asegura que el codigo generado cumpla con
  las reglas del compilador. `es_codigo_vacio` intercepta la respuesta vacia
  antes del compilador en el intento inicial y en los reintentos; evidencia
  `opensyn/validation_loop.syn:60`, guardas en `:321` y `:343`.
- Manual 2 §5.1 CUMPLE. `requiere` se evalua antes de la primera instruccion
  del cuerpo y todas las expresiones deben ser booleanas. La guarda evita
  invocar `validar_con_check` cuando su precondicion no se cumple; evidencia
  `opensyn/validation_loop.syn:61`.
- Manual 6 §1.1 CUMPLE. El backend (analisis semantico, generacion de codigo,
  optimizaciones) es compartido y solo opera sobre `SemNodo[]`.
  `validation_loop_corregir` acepta cualquier texto y rechaza la respuesta vacia
  antes de invocar el backend compartido; evidencia
  `opensyn/pipeline_multiagente.syn:426`.

## Oraculos

- `tests/opensyn/test_validation_loop_comportamiento.py`:
  - `test_respuesta_vacia_inicial_se_intercepta_sin_abortar`: primer turno
    vacio -> `EXITO=0`, `INTENTOS=1`, `ERROR=ERR_RESPUESTA_VACIA`, sin prompt de
    correccion.
  - `test_respuesta_vacia_en_correccion_se_intercepta_sin_abortar`: codigo
    invalido y luego vacio -> `EXITO=0`, `INTENTOS=2`,
    `ERROR=ERR_RESPUESTA_VACIA`, con prompt de correccion.
- `tests/opensyn/test_pipeline_multiagente_comportamiento.py`:
  - `test_pipeline_respuesta_vacia_no_aborta_por_contrato`: Coder devuelve vacio
    -> `EXITO=0`, `INFERENCIAS=1`, `RAZONAMIENTO=ERR_RESPUESTA_VACIA`; el
    proceso termina con rc=0.

## Evidencia ejecutada

- Oraculos R230: **8 passed** (6 de validation_loop + 2 de pipeline).
- Regresion `tests/opensyn`: **136 passed, 1 skipped, 1 failed**.
  El unico fallo es `test_installer_opensyn`, preexistente y ambiental:
  `subprocess.TimeoutExpired` a 10 s porque `installer.exe` tarda ~16 s
  verificando el GGUF local de 873 MB. No toca los archivos de R230.
- `contrastar.py --plan docs/plan_ME_r230_opensyn_contratos_mocks.md`: PASS con
  indice temporal aislado (no se mezclo el trabajo staged de R256).
- `alineacion.py --verificar --me r230_opensyn_contratos_mocks`: OK,
  evidencia `6950a8a8421573ce`.
- `verificar_alineacion.py`: **SIN BRECHAS**.

## Limites

- El cliente Ollama reintenta internamente una respuesta vacia; la guarda
  intercepta el resultado final y los tests verifican los intentos logicos del
  bucle, no el numero de peticiones HTTP.
- El timeout de `test_installer` requiere decision aparte (subir el timeout o
  cachear el hash del modelo); no se modifico en R230 para no tocar un test sin
  aprobacion.
