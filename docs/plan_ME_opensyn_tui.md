# Plan ME — OpenSyn TUI estilo OpenCode/Freebuff (pantalla completa, streaming, menús /)

FASE: 30-b / R141 (hardening F30 + visión Manual 7 §1.1; F31 por verificar en ROADMAP)
ID: ME_opensyn_tui
ESTADO: completado (oráculos banner/agente/autocomplete; verificación en
docs/verificacion_ME_opensyn_tui.md; cierre en docs/reportes/R141.md)

## Resumen del micro-entregable

Reemplazar el chat de línea de OpenSyn por una **TUI de pantalla completa** en
consola real, con la misma experiencia que OpenCode/Freebuff:
1. **Banner retro legible "OpenSyn"** (fuente de píxeles nítida, ya no se lee
   "Opfsyn") pintado como primera escena del panel.
2. **Dos zonas**: arriba el panel de actividad/mensajes (lo que hace el agente:
   consultas, herramientas, respuestas); abajo una **caja de entrada fija**
   con borde, cursor y marcador `❯`.
3. **Streaming**: la respuesta del modelo aparece token a token
   (`stream:true` de Ollama) con repintado en vivo.
4. **Menús interactivos para TODOS los comandos `/`**: al escribir `/` se abre
   el menú de comandos (filtra mientras se escribe); `/model` abre el selector
   de modelos instalados (flechas + Enter) igual que OpenCode.
5. En pipes/tests sin consola real se conserva el modo línea actual (fallback).

## Requisitos del manual (MTS — bloque estricto)

### Requisito R1 — Asistente local con identidad y presentación de TUI

requisito: Manual 7 §1.1 — visión de OpenSyn (equivalente local a OpenCode)
texto: OpenSyn es el asistente local del ecosistema Synapse, equivalente a un
  Copilot u OpenCode, que conoce Synapse y Syquex de forma nativa.
implementacion:
  - `runtime/core/tui.c` (nuevo): motor TUI — pantalla alternativa, entrada en
    modo crudo (flechas/Enter/Esc/UTF-8), cursor, colores, ajuste de línea por
    ancho visual, caja de entrada inferior y panel de mensajes superior.
  - `opensyn/principal.syn`: banner de píxeles "OpenSyn" legible + encabezado
    con el modelo activo; el resto de funciones del chat actual se conservan.
oraculo: tests/e2e_oracle_opensyn_banner.py

### Requisito R2 — Extraer contexto del código (herramientas de lectura local)

requisito: Manual 7 §2.3 — Pipeline RAG / inyección de contexto
texto: El pipeline RAG extrae el contexto del código para construir el prompt;
  el asistente puede pedir contexto con herramientas y luego responder.
implementacion:
  - Se conserva el bucle de agente con `[TOOL] listar/leer/git` ya existente;
    en la TUI el pedido de herramienta se muestra como evento en el panel de
    actividad (rol sistema) y su resultado también, antes de la respuesta final.
oraculo: tests/e2e_oracle_opensyn_agente.py

### Requisito R3 — Chat local contra Ollama con streaming y menús

requisito: Manual 7 §8 — chat local (oraculo) con flujo robusto
texto: OpenSyn consulta al oraculo local Ollama con POST /api/chat; la
  respuesta debe ser acotada en el tiempo y mostrarse conforme se genera.
implementacion:
  - `runtime/core/ollama.c`: API de sesión streaming — `_syn_ollama_stream_*`
    (iniciar/leer/estado/cerrar) con `"stream":true`, parsing NDJSON línea a
    línea, plazo absoluto y timeout de inactividad heredados de R140.
  - `runtime/core/tui.c`: menú modal genérico (flechas/Enter/Esc/filtro) usado
    por `/` y `/model`; repintado completo por evento.
  - `opensyn/principal.syn`: bucle TUI — lee eventos, dibuja, ejecuta comandos
    y skills, hace stream del modelo en el panel y repinta por chunk.
oraculo: tests/e2e_oracle_opensyn_agente.py

## Archivos que modifica

- runtime/core/tui.c, runtime/core/tui.h (nuevos — Motor TUI)
- runtime/core/ollama.c (sesión streaming NDJSON)
- opensyn/principal.syn (banner nuevo, chat TUI, menús, streaming; fallback línea intacto)
- opensyn/principal.syn.json (AST canónico regenerado)
- docs/plan_ME_opensyn_tui.md, docs/verificacion_ME_opensyn_tui.md
- tests/e2e_oracle_opensyn_tui.py (oráculo nuevo: banner + panel + entrada + menú en modo pipe forzado)

## Verificación

- `python main.py opensyn/principal.syn` rc=0 → exe nuevo (timestamp).
- Modo pipe forzado (OPENSN_TUI_TEST=1): banner legible, panel y caja de
  entrada presentes en el repintado, /model abre menú, streaming llega al
  panel, `salir` rc=0.
- `python auditoria/verificar_alineacion.py` → 0 brechas.
- `python auditoria/contrastar.py --plan docs/plan_ME_opensyn_tui.md` → sin brechas.
