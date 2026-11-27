# Plan ME r207 - Pipeline multiagente compilable y cableado

## Contexto

`opensyn/pipeline_multiagente.syn` no compila: la indentación de
`crear_modo_debug` no es múltiplo de 4, importa `opensyn.grafo_conocimiento`
(inexistente; el módulo real es `nucleo/grafo_conocimiento.syn`) y usa
`GrafoProyecto`/`MetricasGrafo` con campos que no existen. Además el Coder
llama a un stub que no consulta el LLM, `validation_loop_corregir` devuelve un
`Resultado` cuyos campos (`es_error`, `error`, `codigo`) no existen, y la
validación final es una comprobación textual en vez de compilar con el
compilador real.

El ME deja el pipeline en un estado compilable y verificable E2E: fases
deterministas Explorer/Architect sobre el grafo canónico, Coder/Reviewer/Fixer
con LLM real (o servidor falso en el oráculo), 2-3 inferencias y código final
validado con `synapse check --no-emit`.

## Requisitos (MTS)

requisito: Manual 6 §1.1
texto: "El ecosistema Synapse se basa en un árbol de Sintaxis Abstracta (AST) canónico y unificado denominado `SemNodo[]`."
implementacion: `opensyn/pipeline_multiagente.syn` importa `nucleo.grafo_conocimiento` y usa las estructuras reales `GrafoProyecto`, `NodoGrafo`, `AristaGrafo` y `MetricasGrafo`; el pipeline consume el grafo de conocimiento construido desde el AST canónico.
oraculo: tests/opensyn/test_pipeline_multiagente_comportamiento.py

requisito: Manual 6 §1.1
texto: "Tanto Synapse como Syquex traducen su código fuente a esta representación intermedia. El backend (análisis semántico, generación de código, optimizaciones) es compartido y solo opera sobre `SemNodo[]`."
implementacion: las fases Explorer y Architect recorren `GrafoProyecto.nodos`/`GrafoProyecto.aristas` de forma determinista (sin LLM); el resultado se usa como contexto del Coder y se mide el tiempo de ambas fases.
oraculo: tests/opensyn/test_pipeline_multiagente_comportamiento.py

requisito: Manual 2 §5.1
texto: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
implementacion: toda función pública nueva o modificada del pipeline (`ejecutar_pipeline`, `ejecutar_con_modo`, `crear_modo_*`, `tiene_fase`, `construir_prompt_*`, `explorar_contexto`, `analizar_impacto_completo`, `validar_codigo`, `llama_client_completar`, `validation_loop_corregir`, auxiliares) declara `requiere`/`garantiza`; las garantías no prometen más de lo verificable.
oraculo: tests/opensyn/test_pipeline_multiagente_comportamiento.py

requisito: Manual 6 §1.1
texto: "Compatibilidad binaria absoluta: Código Synapse y Syquex se enlazan a nivel de instrucciones de máquina sin overhead FFI."
implementacion: el pipeline usa `std.texto`, `std.tiempo`, `std.sistema` y `opensyn.validation_loop` sin inventar APIs; el Coder/Reviewer/Fixer consultan `_syn_ollama_consultar` y la validación final usa `validar_con_check` (`synapse check --no-emit`), no una heurística textual.
oraculo: tests/opensyn/test_pipeline_multiagente_comportamiento.py

## Archivos

- `opensyn/pipeline_multiagente.syn` - reparación de compilación, structs reales, fases deterministas locales y cableado LLM/validación.
- `tests/opensyn/test_pipeline_multiagente_comportamiento.py` - oráculo E2E nuevo con LLM falso HTTP y compilador real.
- `tests/fixtures/compilacion_baseline.txt` - retirar `opensyn/pipeline_multiagente.syn` al compilar.
- `docs/alineacion/r207_pipeline_multiagente.md` - expediente de alineación (generado después).
- `docs/verificacion_ME_r207_pipeline_multiagente.md` - verificación de oráculos (generado después).
- `docs/reportes/R207.md` - reporte del ME (generado después).

## Desviaciones declaradas

- El plan maestro cita Manual 32 §5.3-§5.5, pero `docs/manuales/MANUAL 32.md`
  no existe con ese nombre (el archivo real es
  `MANUAL  FASE 32 AGENTE DE CODIFICACIÓN.md`, con dos espacios) y el índice de
  manuales no lo reconoce. El gate de alineación se ancla en Manual 6 §1.1
  (sección mapeada para este archivo); Manual 32 §5.3-§5.5 se conserva como
  referencia funcional en este plan y en la verificación.
- `opensyn/explorer_det.syn` y `opensyn/architect_det.syn` siguen en el baseline
  de compilación y pertenecen a r210/r211. Para que r207 compile sin adelantar
  esos MEs, el pipeline implementa localmente las fases deterministas mínimas
  (`explorar_contexto`, `analizar_impacto_completo`) sobre el grafo real; cuando
  r210/r211 compilen, el pipeline podrá delegar en esos módulos sin cambiar su
  contrato externo. Queda registrado como deuda de integración para r217.
- El codegen actual no soporta campos de struct anidados: un campo
  `analisis_impacto: AnalisisImpacto` (que a su vez contiene `MetricasImpacto`)
  se emite como puntero y el constructor falla en C. Por eso
  `ContextoPipeline` aplana las métricas (`total_afectados`,
  `profundidad_maxima`, `contratos_criticos`, `ciclos_potenciales`) y
  `analizar_impacto_completo` retorna `MetricasImpacto` (struct solo de
  escalares); las listas `NodoAfectado`/`ContratoCritico`/`Ciclo` se usan
  localmente para calcular los conteos. Se registra como limitación de codegen
  para r217.
- `validation_loop_corregir` usa `validar_con_check` del módulo r206 y una sola
  corrección LLM, no el bucle completo de 3 intentos, para respetar el límite de
  3 inferencias del pipeline. El bucle completo permanece en
  `opensyn/validation_loop.syn`.
- `synapse.exe` instalado puede estar stale; el oráculo usa un wrapper de test
  que invoca el compilador actual (`python main.py <archivo> --check --no-emit`).
- No se toca `docs/gobernancia/GUIA_DE_GOBERNANZA.md` (modificado por otro
  agente) ni los artefactos no rastreados `nucleo/embedded_libs.h`,
  `nucleo/lsp_v3.c.bak`, `nucleo/lsp_v3.c.new`.
- Los tests existentes no se modifican; se ejecutan como oráculos de regresión.

## Oráculos de cierre

1. `.venv\Scripts\python.exe main.py opensyn/pipeline_multiagente.syn --check --no-emit` -> rc 0.
2. `.venv\Scripts\python.exe -m pytest tests/opensyn/test_pipeline_multiagente_comportamiento.py -v` -> verde.
3. `.venv\Scripts\python.exe -m pytest tests/opensyn/test_pipeline_multiagente.py -v` -> verde sin modificar el test existente.
4. `.venv\Scripts\python.exe -m pytest tests/integration/test_compilacion_fase32.py -v` -> verde sin `pipeline_multiagente` en baseline.
5. `.venv\Scripts\python.exe auditoria/verificar_alineacion.py` -> 0 brechas.
6. `python auditoria/alineacion.py --verificar --me r207_pipeline_multiagente` -> sin brechas.
7. `python auditoria/contrastar.py --plan docs/plan_ME_r207_pipeline_multiagente.md` -> sin brechas.
