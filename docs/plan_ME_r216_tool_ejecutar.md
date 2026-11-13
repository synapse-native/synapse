# Plan ME r216_tool_ejecutar

Origen: `docs/gobernancia/PLAN_MAESTRO_INDUSTRIAL.md` (ola posterior a r215_tool_patch).

## Requisito 1 — allowlist y sandbox

requisito: `Manual 7 §7.3` — sandboxing y permisos mínimos.

texto: "**Sandboxing:** El servidor de inferencia se ejecuta con permisos mínimos."

implementacion: `opensyn/herramientas.syn` valida el comando antes de ejecutarlo: solo `synapse check`, `synapse build`, `pytest`, `git status`, `git diff`; rechaza metacaracteres de shell, `..`, rutas absolutas y flags peligrosos de git. Windows usa `CreateProcessA` y POSIX usa `execvp` con argv dividido por espacios; no usa `system()` ni `sh -c` en el nuevo camino.

oraculo: tests/integration/test_tool_ejecutar.py

## Requisito 2 — contrato público

requisito: `Manual 2 §5.1` — contratos `requiere`/`garantiza` en toda función pública.

texto: "`requiere`:** Se evalúa antes de la primera instrucción del cuerpo."; "`garantiza`:** Se evalúa inmediatamente antes de cada `retornar`."

implementacion: `herramienta_ejecutar` y los helpers públicos declaran contratos booleanos; `opensyn/principal.syn` despacha `TOOL ejecutar <comando>` en modos Code/Debug y actualiza prompt/ayuda.

oraculo: tests/integration/test_tool_ejecutar.py

## Referencia funcional — timeout

El timeout de 5 s se especifica en `docs/manuales/MANUAL  FASE 32 AGENTE DE CODIFICACIÓN.md` §6.4 (`runtime/core/proceso.c`), documento no indexado por `MANUAL 32.md`; se cita como referencia funcional y se prueba con el oráculo `test_e2e_timeout_mata_bucle_infinito`.
