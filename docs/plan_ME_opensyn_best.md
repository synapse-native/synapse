# Plan ME — OpenSyn con lo mejor de opencode + Kilo + freebuff + Claude Code/Codex/Cursor (en Synapse/Syquex, bajo Manual 7)

FASE: 30-c / propuesta (Fase 30-b completada R141-R146; proximo: FASE 31 del roadmap)
ID: ME_opensyn_best
ESTADO: planificacion (SOLO PLAN — sin codigo en este ME)
ORIGEN: comparativa opencode vs Kilo Code vs freebuff como agentes (sin modelos),
  mas el podio actual sept-2026: Claude Code (#1 sistema agente), Codex (#2 runs
  largos/review), Cursor (mejor IDE/flujo base), opencode (#1 open-source, nucleo
  que Kilo forkea).

## 1. Resumen del micro-entregable (que SÍ y que NO)

Tomar las mejores caracteristicas AGENTE de los tres y reimplementarlas en
nuestros lenguajes (.syn el orquestador/router/TUI, .syq la transpilacion/bindings
de alto nivel), bajo nuestras normas (manuales ley, tests inmutables, contratos
requiere/garantiza, `// cumple Manual 7 §Y` grep-chequeable, 0 brechas).

QUE TOMAMOS:
- De opencode: separacion Plan/Build, permisos allow/ask/deny por herramienta,
  pregunta al usuario (question), lista de tareas (todowrite), undo/redo,
  agentes definibles en markdown, compartir sesion.
- De Kilo: modos Ask/Architect/Code/Debug/Orchestrator, orquestador que delega,
  auto-recuperacion ante fallos (detectar error + correr tests + reintentar),
  indice semantico + consulta de docs (anti-alucinacion de APIs), sandbox
  (solo-workspace), forks de sesion, Agent Manager/worktrees paralelos,
  revision inline.
- De freebuff: file-finder que mapea contexto ANTES de editar, duo
  implementador+revisor, proponer 3 siguientes pasos, browser-use integrado,
  filosofia cero-config.
- De Claude Code (#1): planificar multi-paso ANTES de actuar (ahorra ~80%
  tokens), esfuerzo/modelo distinto por subtarea (en local: temperatura y
  max_tokens por modo), subagentes con contexto propio, hooks pre/post
  herramienta, background agents. Todo reescrito determinista y local.
- De Codex (#2): runs largos con reanudacion + code-review de alta senal
  (detectar integracion antes del merge) + generacion de tests.
- De Cursor (base de flujo): autocomplete rapido en editor + chat en el editor
  + review en panel lateral (via extension VS Code existente + aiExplain).

QUE NO TOMAMOS (decision explicita):
- Nada cloud con telemetria, nada de ads, nada de suscripciones/gateway con
  markup. OpenSyn sigue 100% local, cero telemetria (Manual 7 §1.1 / §7.3).
- No se porta codigo Go/TS de ellos. Solo la IDEA, reescrita en .syn/.syq/C del
  runtime y citada al manual. Los manuales mandan, no su codigo.

Lenguaje por pieza (eficiencia):
- `.syn` (bajo nivel, sistemas): modos, bucle agente, router/orquestador,
  permisos/sandbox, TUI, sesion/forks, validacion con compilador.
- `.syq` (alto nivel, productividad): skills de plan/review, transpilacion,
  bindings, formateo de respuestas.
- C runtime (solo puentes): lo que hoy ya existe (ollama.c, tui.c, sistema.c) +
  extensiones minimas (sandbox, indice). Sin logica de negocio nueva en C.

## 2. Requisitos del manual (MTS — bloque estricto, solo secciones REALES del Manual 7)

### Requisito R1 — Vision: modos Plan/Build + Ask/Architect/Code/Debug/Orchestrator

requisito: Manual 7 §1.1
texto: "OpenSyn es el asistente de inteligencia artificial local del ecosistema Synapse. Es el equivalente a un «Copilot» o «OpenCode»... Aprendizaje de Synapse: OpenSyn conoce Synapse y Syquex de forma nativa mediante inyección de contexto estático... Validación automática y bucle de corrección: El código generado se valida con el compilador real"
implementacion:
  - Origen: opencode (Build/Plan con Tab) + Kilo (Ask/Architect/Code/Debug/Orchestrator).
  - En `opensyn/principal.syn`: tabla de MODOS (ask=solo lectura, plan=solo escribe plan, code=edita validando, debug=diagnostica, orchestrator=descompone y delega a los anteriores). Cada modo fija que herramientas [TOOL] estan permitidas. `plan` nunca edita; `ask` nunca escribe.
  - En `.syq` (skills): prompts de arquitecto/revisor ya existentes (/plan /revisar) se reutilizan como personalidades de cada modo. Sin codigo nuevo en C.
  - Regla: `orchestrator` no ejecuta herramientas directas, solo crea subtareas que resuelven `code/debug/ask` (como Kilo, pero determinista y local).
oraculo: tests/e2e_oracle_opensyn_banner.py

### Requisito R2 — File-finder + indice semantico antes de editar (anti-alucinacion)

requisito: Manual 7 §2.3
texto: "El pipeline RAG (Retrieval-Augmented Generation) es el cerebro de OpenSyn. Extrae el contexto más relevante del código fuente para construir un prompt eficiente y preciso."
implementacion:
  - Origen: freebuff (file-picker mapea ANTES de editar) + Kilo (indice semantico + Context7 docs).
  - En `opensyn/router.syn` + pipeline RAG: fase 0 OBLIGATORIA de localizacion (que archivos tocan la tarea) antes de generar codigo. Fuentes por prioridad: nodo AST actual > lineas cercanas al cursor > diagnosticos > std/lib reglas > feedback.jsonl.
  - Catalogo local de APIs reales de `std/*.syn` y `lib/*.syq` (generado del repo, no del modelo) para que el modelo no invente funciones .syn/.syq. Es el equivalente local al Context7 de Kilo.
  - Negociacion n_ctx 30/70 existente se conserva; el file-finder recorta por cercania al cursor (ya prescrito en §2.3 punto 4).
oraculo: tests/opensyn/test_rag.py

### Requisito R3 — Router-orquestador que delega + 3 siguientes pasos

requisito: Manual 7 §2.4
texto: "El router está escrito en Synapse y actúa como el cerebro de alto nivel de OpenSyn. Decide qué modelo usar y cómo procesar la respuesta."
implementacion:
  - Origen: Kilo Orchestrator (descompone y delega) + freebuff (tras cada respuesta propone 3 siguientes pasos clicables).
  - En `opensyn/router.syn`: `procesar_respuesta` crece a `orquestar(tarea)`: clasifica (explicar/diagnosticar/refactor/generar), parte en subtareas 1-N verticales, asigna cada una a un modo de R1, y fusiona. Extraccion de bloques ```synapse/```syquex``` existente se conserva.
  - En TUI: tras cada respuesta, linea `siguientes: 1) ... 2) ... 3) ...` (texto seleccionable, sin telemetria). Equivale a los next-steps de freebuff.
  - Lo que NO se copia: comparacion de modelos lado a lado (somos locales, un modelo activo basta).
oraculo: tests/e2e_oracle_opensyn_agente.py

### Requisito R4 — Auto-recuperacion: detectar error + correr tests + reintentar

requisito: Manual 7 §6.3
texto: "se implementa un bucle de validación y corrección automática orquestado por el LSP (ver sección 4.2). Este bucle asegura que el código generado cumpla con las reglas del compilador."
implementacion:
  - Origen: Kilo automatic failure recovery (lee el error, corre la suite, se recupera solo).
  - En `opensyn/validation_loop.syn` (MAX_INTENTOS=3 existente): cada intento fallido anexa `linea/columna/mensaje` exacto del compilador al prompt ("El código anterior tiene el siguiente error: {mensaje_error}. Por favor, corrígelo."). Si el error viene de tests, se anexa la salida del test que fallo. Al 3er fallo se devuelve ultimo codigo + errores (mensaje ya prescrito en §6.3).
  - En `.syq`: skill de debug sistematico (analizar > acotar > corregir) reutilizando SKILL_REVIEW existente.
oraculo: tests/integration/test_ai_correction.py

### Requisito R5 — Validacion LSP orquestada + revision inline

requisito: Manual 7 §4.2
texto: "El LSP es el responsable de orquestar el bucle de validación (descrito en la sección 6.3). No se limita a ser un proxy pasivo."
implementacion:
  - Origen: Kilo inline code review (comentar por linea, devolver diff con contexto).
  - Flujo 10 pasos existente (peticion -> RAG -> inferencia -> router -> `synapse check --no-emit` -> reintento) se conserva intacto. Se anade: la respuesta del LSP incluye archivo+linea+diff para que la revision cite codigo exacto, y el comando `aiExplain` existente se reutiliza para explicar cada bloque antes de aplicarlo.
  - Timeouts/errores de §4.3 se conservan (30 s, modelo no cargado, regenerar).
oraculo: tests/integration/test_ai_correction_opensyn.py

### Requisito R6 — Permisos ask/deny + sandbox minimo (cuando exista escritura)

requisito: Manual 7 §7.3
texto: "Sandboxing: El servidor de inferencia se ejecuta con permisos mínimos."
implementacion:
  - Origen: opencode (permission allow/ask/deny por herramienta y por patron bash) + Kilo Sandbox (workspace-only writes, red denegada).
  - Diseno (SOLO diseno en este plan; la escritura llega en ME posterior): matriz `lectura=allow, edicion=ask, bash=ask-por-patron, red=deny, fuera-workspace=deny`. Hoy el agente es solo-lectura (listar/leer/git), asi que R6 hoy = documentar la matriz + hacer cumplir `deny` fuera del repo. Cuando se anada edit/write, cada escritura pide confirmacion y queda confinada al workspace.
  - Privacidad: "Cero telemetría: Verificado con monitoreo de red (sin conexiones salientes)." (§7.3) — por eso NO se copian gateway cloud, Slack bot, ni browser con exfiltracion.
oraculo: tests/e2e_oracle_opensyn_agente.py

### Requisito R7 — Comandos CLI + sesiones (fork, review, next)

requisito: Manual 7 §6.4
texto: "Muestra el estado de OpenSyn (modelo cargado, uso de VRAM)."
implementacion:
  - Origen: Kilo (Session Forks, Agent Manager, /review) + freebuff (cero-config) + opencode (/undo, /share local).
  - Nuevos comandos disenados (nombres propuestos, implementacion en ME posterior): `/plan /ask /code /debug` (cambio de modo R1), `/review` (revision 5 ejes existente), `/fork` (ramificar sesion como rama git del chat), `/next` (mostrar los 3 pasos de R3), `/undo` (deshacer ultima edicion cuando exista escritura). `status/download/finetune/bindings/transpile` existentes intactos.
  - Sesiones: historial JSONL existente se extiende con `sesion_id + padre` para forks; sin cloud, todo en `~/.opensyn/`.
oraculo: tests/e2e_oracle_opensyn_historial.py

### Requisito R8 — Runs largos con reanudacion + errores/timeouts (receta Codex)

requisito: Manual 7 §4.3
texto: "- Si el servidor de inferencia no responde en 30 segundos, el LSP devuelve un error al usuario."
implementacion:
  - Origen: Codex (runs autonomos largos, Terminal-Bench) + Claude Code (background agents).
  - Diseno: el plazo absoluto 300 s de R140 se conserva para inferencia; para TAREAS largas (transpilar/generar proyecto) el orquestador parte en subtareas reanudables con estado en `~/.opensyn/sesiones/<id>.jsonl` (el fork de R7 da la rama). Si el backend cae, la tarea se retoma desde la ultima subtarea OK en vez de empezar de cero. Sin cloud: todo en disco local.
  - Hooks pre/post herramienta (receta Claude): pre = chequeo permiso/matriz R6; post = validacion `synapse check --no-emit` + append a feedback.jsonl.
oraculo: tests/e2e_oracle_opensyn_ia_gguf.py

### Requisito R9 — Eficiencia de tokens: planificar antes de actuar (receta Claude #1)

requisito: Manual 7 §7.2
texto: "- **Latencia de inferencia:** < 1s para prompts cortos (modelo 7B en GPU)."
implementacion:
  - Origen: Claude Code (5.5x token-eficiente vs Cursor: planifica multi-paso antes de ejecutar, no recarga contexto).
  - Diseno: regla de oro del orquestador — 1 llamada de PLAN (barata, temp 0.1-0.3, pocos tokens) decide archivos+pasos; solo luego N llamadas de ejecucion con contexto acotado del file-finder R2. Esfuerzo por modo: ask/debug = contexto minimo; code = contexto funcion/archivo; orchestrator = solo lista de subtareas. Asi un 1.3B local rinde como uno grande: menos contexto = menos alucinacion + menos latencia (clave para la meta <1 s en prompts cortos).
  - Lo ya logrado (truncado system 3500B R145, listado 2400 chars R146) se declara como implementacion parcial de este requisito.
oraculo: tests/integration/test_rag_pipeline.py

### Requisito R10 — Review de alta senal + tests generados (receta Codex/Cursor)

requisito: Manual 7 §8
texto: "El LSP valida con `synapse check --no-emit` (compila correctamente)."
implementacion:
  - Origen: Codex (review que caza integracion + genera tests) + Cursor (review en panel) + skill /revisar existente (5 ejes).
  - Diseno: tras generar codigo, el revisor (modo review de R1) verifica: compila (`--check`), integra (imports/símbolos existen en el catalogo R2), y propone el test que lo prueba. El `aiExplain` del LSP explica cada bloque antes de aplicar (flujo Cursor en panel lateral, sin app nueva).
oraculo: tests/integration/test_rag_adv_10.py

## 3. Fases de ejecucion (MEs pequenos, en orden)

- ME-1 (lectura+modos): R1. Solo `principal.syn` + skills. Sin escritura nueva.
- ME-2 (contexto): R2. `router.syn` + catalogo APIs std. Oraculo test_rag.
- ME-3 (orquesta+UX): R3+R7. Router delega + next-steps + /fork. Oraculo agente+historial.
- ME-4 (recuperacion): R4+R5+R10. validation_loop con tests + LSP inline + review. Oraculo correction x2 + rag_adv.
- ME-5 (permisos+sandbox): R6. Matriz + confinamiento. Recien aqui se propone edit/write con `ask`.
- ME-6 (el mejor: eficiencia+fondos): R8+R9. Runs reanudables + plan-antes-de-actuar. Oraculo gguf + rag_pipeline.
- Cada ME: `registrar_lectura` el mismo dia, `// cumple Manual 7 §Y` por archivo, `verificar_alineacion.py` 0 brechas, `contrastar.py --plan` verde, reporte R<N> + fila auditoria + MEMORIA.

## 6. Terminal vs app propia (decision)

PREGUNTA: ¿seguir en terminal o hacer app propia, todo en nuestros lenguajes?

RESPUESTA: terminal primero (ME-1..ME-6), app despues como cascara fina.
Motivos:
1. Eficiencia: la TUI ya existe y compila (banner, streaming, historial, Tab,
   `principal.syn` ~1511 lineas). Una app GUI/escritorio desde cero en .syn
   costaria 3-5 MEs solo de runtime grafico, sin mejorar el agente. El podio
   (Claude Code, Codex, opencode) gano desde la terminal; Cursor gano como
   extension del editor, no como OS nuevo.
2. Arquitectura: lo que importa es el NUCLEO (modos, router, RAG, validacion,
   permisos). Kilo lo demuestra: un solo nucleo portable (el suyo sobre
   OpenCode) sirve a VS Code + JetBrains + CLI + Cloud + Slack. Nuestro nucleo
   es `principal.syn + router.syn + validation_loop.syn`: si es el mejor en
   terminal, la app lo hereda gratis.
3. Cobertura sin app: terminal (chat largo, runs, todos los comandos) +
   extension VS Code existente (aiExplain, aiComplete, review en panel =
   el flujo Cursor) cubren el 90% del uso con el 20% del coste.
4. Cuando SI hacer la app (FASE 32+, tras ME-6): cascara fina sobre el mismo
   nucleo — gestor de sesiones paralelas (Agent Manager), diff inline,
   worktrees. Requiere antes runtime grafico en .syn + decision D-* del
   Arquitecto (modulo >1200 lineas, regla 13). NO entra en este plan.

REGLA: ningun ME de este plan crea app nueva. Todo vive en TUI + CLI + LSP.

## 4. Archivos que TOCARA (futuro, NO en este plan)

- opensyn/principal.syn (modos, permisos, sesion/fork, next-steps)
- opensyn/router.syn (orquestacion, clasificacion, fusion)
- opensyn/validation_loop.syn (reintentos con salida de tests)
- opensyn/chat.syn (comandos /plan /review /fork /next /undo)
- std/agent_skills.syn (personalidades ask/architect/code/debug en .syq)
- runtime/core/sistema.c/.h, io.c, tui.c (puentes minimos sandbox/sesion)
- tests/e2e_oracle_opensyn_*.py + tests/opensyn/test_rag.py + tests/integration/test_ai_correction*.py (oraculos, inmutables sin Arquitecto)
- docs/verificacion_ME_opensyn_best.md (cierre del gate por ME)

## 5. Verificacion de ESTE plan (sin codigo)

- `python auditoria/contrastar.py --plan docs/plan_ME_opensyn_best.md` debe pasar cuando existan los oraculos citados (todos existen hoy salvo futuros test_sandbox, por eso R6 reusa e2e_agente).
- No hay archivos de produccion modificados en este commit del plan: solo este `docs/plan_ME_opensyn_best.md`.
- Proximo paso tras aprobar el plan: ME-1 con `registrar_lectura --archivos "opensyn/principal.syn" --cita "Manual 7 §1.1"`.
