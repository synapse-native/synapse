# Plan ME — OpenSyn agente con herramientas + presentación estilo OpenCode/Freebuff

FASE: 30-b / R140 (hardening F30 + visión Manual 7 §1.1; F31 por verificar en ROADMAP)
ID: ME_agente_opensyn
ESTADO: en ejecución

## Resumen del micro-entregable

El chat de OpenSyn pasa de "relay de prompt" a **agente local con lectura del
repositorio** (estilo OpenCode/Freebuff): al iniciar muestra un banner ASCII
retro "OpenSyn", ofrece prompt interactivo con colores ANSI (solo consola real)
y, ante una pregunta, puede **inspeccionar el repo** (listar directorios, leer
archivos, estado git) iterando con el modelo hasta responder con contexto real
— todo local, sin telemetría (Manual 7 §1.1).

## Requisitos del manual (MTS — bloque estricto)

### Requisito R1 — Asistente local equivalente a Copilot/OpenCode con inyección de contexto

requisito: Manual 7 §1.1 — visión de OpenSyn
texto: "OpenSyn es el asistente de inteligencia artificial local del ecosistema Synapse. Es el equivalente a un «Copilot» o «OpenCode»... Aprendizaje de Synapse: OpenSyn conoce Synapse y Syquex de forma nativa mediante inyección de contexto estático... Validación automática y bucle de corrección: El código generado se valida con el compilador real"
implementacion: 
  - `opensyn/principal.syn`: al entrar en `modo_oraculo`, OpenSyn construye un
    System Prompt con (a) rol de asistente de código local, (b) reglas de
    sintaxis Synapse/Syquex reales del repo, (c) contexto del repositorio
    (carpetas/archivos raíz, estado git, AGENTS.md si existe). Presentación:
    banner ASCII "OpenSyn" + prompt `❯` con colores ANSI únicamente cuando
    `_syn_es_consola()` es verdadero (los pipes quedan limpios).
oraculo: tests/e2e_oracle_opensyn_banner.py

### Requisito R2 — Extraer contexto del código (herramientas de lectura local)

requisito: Manual 7 §2.3 — Pipeline RAG
texto: "El pipeline RAG (Retrieval-Augmented Generation) es el cerebro de OpenSyn. Extrae el contexto más relevante del código fuente para construir un prompt eficiente y preciso... El RAG lee el n_ctx del modelo... temperature: 0.3"
implementacion:
  - `runtime/core/sistema.c`: `_syn_listar_directorio(ruta)` (entradas
    "nombre/" dirs / "nombre" archivos) y `_syn_capturar_comando(cmd)`
    (salida de comandos de SOLO lectura: git status/log). El cliente fija el
    comando; el modelo NUNCA ejecuta comandos arbitrarios.
  - `opensyn/principal.syn`: bucle de agente (máx. 6 iteraciones) con protocolo
    textual: el modelo pide contexto con una línea `[TOOL] nombre|argumento`;
    el cliente ejecuta (listar / leer_archivo / git_estado), devuelve el
    resultado con `[TOOL_RESULT]` y repite hasta que el modelo responde sin
    línea de herramienta. Regla R113: copias `strcpy_f` en los call sites;
    helpers single-pass, retornos solo en depth 0.
  - `runtime/core/io.c`: `_syn_es_consola()` y `_syn_ansi(sgr)` + activación
    de ANSI VT en consola real (banner/prompt con color sin ensuciar pipes).
oraculo: tests/e2e_oracle_opensyn_agente.py

### Requisito R3 — Cliente del oráculo local robusto (sin cuelgues silenciosos)

requisito: Manual 7 §8 — flujo de IA del chat local
texto: La consulta al oraculo local Ollama (POST /api/chat, stream:false) debe
  retornar el contenido del asistente o un mensaje de error claro, y la lectura
  de la respuesta HTTP debe estar acotada en el tiempo para que un servidor
  colgado no bloquee el chat en silencio (calidad industrial).
implementacion:
  - `runtime/core/ollama.c`: `_ollama_leer_respuesta` con `SO_RCVTIMEO` (2 s) y
    plazo absoluto (300 s: carga del modelo en frío + generación); corte
    temprano cuando `Content-Length` queda satisfecho; código de resultado que
    distingue error de red (-1), plazo agotado (-2) y conexión cortada a mitad
    de cuerpo (-3); `_syn_ollama_consultar` traduce cada caso a un mensaje
    claro para el chat (el usuario nunca ve un prompt congelado).
  - `opensyn/principal.syn`: línea de estado "[*] Consultando a <modelo>…"
    antes de cada llamada bloqueante (skills y prompt normal) para que la
    carga del modelo en frío sea visible.
oraculo: tests/e2e_oracle_opensyn_agente.py

## Archivos que modifica

- runtime/core/sistema.c, runtime/core/sistema.h (helpers de herramientas)
- runtime/core/io.c (consola/ANSI)
- runtime/core/ollama.c (hardening Manual 7 §8: plazo absoluto + SO_RCVTIMEO en
  _ollama_leer_respuesta — nunca cuelga en silencio; errores distinguidos
  timeout/corte/red para el chat)
- opensyn/principal.syn (banner, prompt, contexto, tool loop, estado
  "[*] Consultando a <modelo>…" antes de cada llamada bloqueante)
- opensyn/principal.syn.json (AST canónico regenerado)
- tests/e2e_oracle_opensyn_banner.py, tests/e2e_oracle_opensyn_agente.py
  (oráculos del MTS)
- docs/verificacion_ME_agente_opensyn.md (cierre del gate)

## Verificación

- `.venv\Scripts\python.exe main.py opensyn/principal.syn` rc=0 → exe nuevo.
- Prueba E2E con Ollama real (localhost:11434): banner, prompt, pregunta de
  contexto con herramientas; `salir` rc=0.
- `python auditoria/verificar_alineacion.py` → 0 brechas.
- `python auditoria/contrastar.py --plan docs/plan_ME_agente_opensyn.md` → sin brechas.
