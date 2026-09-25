# AUDITORÍA DE OPERATIVIDAD — OpenSyn (opensyn/)

**Fecha:** 2026-09-25
**Alcance:** Funcionalidades declaradas de OpenSyn y su operatividad REAL verificada
(estática + dinámica + E2E sobre el binario), incluyendo el estado de los artefactos
distribuidos.
**Entorno de la auditoría:** Windows, sin backend IA activo (`:11434` sin `/api/tags`
ni `/health`; `llama-server` no localizado en las rutas conocidas de esta máquina).
**Método:** lectura dirigida de fuentes, `synapse --check`, compilación modular S1 del
fuente actual con smoke del binario fresco, ejecución de las suites pytest y de los
oráculos E2E, smokes manuales del binario instalado y del LSP. Auditoría de SOLO
LECTURA: ningún archivo de producción fue modificado.

---

## 1. Inventario verificado

| Módulo (opensyn/) | Líneas | Función | Operatividad verificada |
|---|---|---|---|
| `principal.syn` | 1766 | Chat TUI agente + modos + oráculo + CLI | SÍ — build+smoke GREEN |
| `router.syn` | 844 | Enrutado de consultas IA | SÍ (test_transpile lo ejercita) |
| `run_manager.syn` | 411 | Gestión de ejecuciones | Compila; SIN test directo |
| `validation_loop.syn` | 295 | Bucle de validación 3 intentos | SÍ (test_bucle_validacion) |
| `pipeline_multiagente.syn` | 499 | Pipeline 5 fases/5 modos | SÍ (15 tests F32.4) |
| `memoria_persistente_cifrada.syn` | 276 | Memoria cifrada XSalsa20-Poly1305 | SÍ (14 tests F32.3) |
| `verificacion_aot.syn` | 272 | Auto-refutación AOT | SÍ (13 tests F32.5) |
| `architect_det.syn` / `explorer_det.syn` | 273/203 | Análisis de impacto determinista | SÍ (17 tests F32.2) |
| `permisos.syn` | 216 | Matriz de permisos + sandbox workspace (M7 §1.1) | SÍ |
| `installer.syn` | 248 | Gestión de modelos/hardware | SÍ (tests installer) |
| `planificador.syn` | 175 | Planificación de tareas | Compila; SIN test directo |
| `chat.syn` | ~60 | Soporte de chat | Compila |
| `transpiler.py` / `bindings_generator.py` / `full_pipeline.py` | 433/557/— | Transpilación Python→Syquex, bindings C | SÍ (tests transpile/bindings) |
| `modelos.toml` | — | Catálogo de modelos GGUF | SÍ — 0 placeholders (ver §5) |

Artefactos distribuidos: `dist/bin/opensyn.exe` (17-sep 21:11), `dist/bin/synapse_lsp.exe`
(10-sep 08:41).

## 2. Verificaciones ejecutadas (evidencia)

| Verificación | Resultado |
|---|---|
| `pytest tests/opensyn` (16 archivos, 123 tests) | **122 passed, 1 skipped** (67 s; skip = depende de backend IA) |
| Oráculo `e2e_oracle_opensyn_historial.py` | **GREEN** — persistencia + navegación ↑↓ |
| Oráculo `e2e_oracle_opensyn_autocomplete.py` | **GREEN** — Tab comandos/rutas/doble Tab |
| Oráculo `e2e_oracle_opensyn_banner.py` | **GREEN** — banner + sistema de modos |
| Oráculo `e2e_oracle_opensyn_ia_gguf.py` | **GREEN** — GGUF sintético: carga+vocab real+generación determinista+cierre limpio |
| Oráculo `e2e_oracle_opensyn_agente.py` | RED **por entorno** — requiere Ollama vivo (patrón conocido, memoria: máquina sin backend hoy) |
| `main.py --check opensyn/principal.syn` | rc=0 — sintaxis OK, semántica OK |
| Build modular S1 del fuente actual (`main.py opensyn/principal.syn`) | rc=0, exe fresco 2026-09-25 20:29 |
| Smoke binario FRESCO (`echo "salir" \| opensyn`) | rc=0 — banner, degradación elegante sin IA ("Ollama apagado?"), modo ASK, salida limpia |
| Smoke binario INSTALADO (`dist/bin/opensyn.exe`) | rc=0 — mismo comportamiento |
| Smoke LSP (`initialize` JSON-RPC por pipe) | rc=0 — respuesta `capabilities` válida (hover/completion/definition) |
| Comandos TUI presentes en `principal.syn` | salir/exit//salir, /ask /plan /code /debug /orchestrator, /ayuda, /skills, /modelos, /model <n>, /tdd, /revisar, /next, /plan <prompt> |
| Sandbox de permisos (`permisos.syn`) | Presente y con feedback de denegación (M7 §1.1: workspace-only, sin nube) |

## 3. Veredicto de operatividad

**OPERATIVO en degradación elegante.** Sin backend IA, OpenSyn arranca, presenta el
banner, informa con claridad que Ollama no está disponible, ofrece los comandos, y
termina limpio (rc=0). Con backend IA: la funcionalidad E2E fue validada históricamente
con llama-server real (R145b: chat 87 s→~5 s, R146: respuestas deterministas) y los
oráculos que no dependen de IA pasan HOY. Todas las capacidades de Fase 32 (grafo,
memoria cifrada, pipeline multiagente, verificación AOT) mantienen sus suites GREEN.

## 4. Hallazgos

- **H-AUD-OP-1 (NUEVO, ALTO — resolución asignada):** el chat en modo oráculo NO termina
  ante EOF de stdin: si el pipe se cierra sin enviar "salir", `chat_tui` re-imprime el
  prompt en bucle infinito. Evidencia: `echo "status" | timeout 12 dist/bin/opensyn.exe`
  → rc=124 (timeout) y log de 21 MB con ~210.000 repeticiones de "Tu>". Los oráculos no
  lo detectan porque SIEMPRE envían "salir" como última línea. Afecta a automatización
  (pipes sin terminador explícito). Clase: manejo de fin-de-entrada en la lectura de
  `chat_tui`. Resolución: ME futuro — `leer_micro` debe distinguir EOF de línea vacía y
  el bucle debe romper en EOF (como ya hace el modo oráculo en su prompt "salir").
- **H-AUD-OP-2 (NUEVO, MEDIO):** exe stale distribuido — `dist/bin/opensyn.exe`
  (17-sep 21:11) es ANTERIOR a la última edición de `principal.syn` (17-sep 22:19, fix
  H-R149-WIP). El binario instalado puede carecer de la eliminación del estado global
  `ultimo_tipo_tarea`. Mitigado: la compilación fresca del fuente actual es verde y el
  smoke es idéntico. Resolución: regenerar `dist/bin/` en el próximo ME y añadir
  verificación de frescura fuente→exe al release (lección R144/R146 ya documentada).
- **H-AUD-OP-3 (NUEVO, MENOR):** el marker `@pytest.mark.tdd` no está registrado en
  `pytest.ini` → 8 PytestUnknownMarkWarning en la suite. Es un cambio de CONFIGURACIÓN
  de tests (no de tests, regla 5 intacta). Resolución: añadir `tdd:` a la sección
  `markers`.
- **CONFIRMACIÓN de efectos conocidos:** los oráculos E2E escriben
  `~/.opensyn/config_ollama.txt` (efecto R145) — durante la auditoría quedó en
  `model=qwen-coder` tras pasar el oráculo agente; sin daño, pero restaurar antes de
  cualquier prueba de usuario (lección R145 ya registrada).
- **H-R145-5 sigue abierto** (timeout fijo del oráculo historial con backend real;
  resolución asignada — ME futuro del Arquitecto).

## 5. Cruce con la deuda registrada en memoria

| Deuda | Estado tras esta auditoría |
|---|---|
| H-R144-3 (modelos.toml con placeholders) | **PROPUESTA DE CIERRE:** el catálogo actual tiene URLs reales de HuggingFace LFS + SHA-256 reales, 0 placeholders (grep). Cerrar con ratificación del Arquitecto. |
| H-R144-2 (detección -1 en contexto elevado) | Persiste (no verificable aquí; resolución asignada). |
| H-R144-5 (upgrade silencioso sin GGUF) | Persiste (resolución asignada). |
| ME-agente-herramientas (few-shot [TOOL] opcional) | Persiste como mejora opcional de prompts. |
| H-R113 / clase RAII de retorno | Mitigada estructuralmente por r153 R6 (expresión de retorno evaluada antes de destructores). |

## 6. Recomendaciones priorizadas

1. **ME fix EOF (H-AUD-OP-1):** romper el bucle de `chat_tui` en EOF de stdin + oráculo
   que pipee stdin cerrado sin "salir" y exija rc=0. Es el único defecto REAL nuevo.
2. **Regenerar `dist/bin/opensyn.exe`** desde el fuente actual (H-AUD-OP-2) e incorporar
   la comprobación de frescura al pipeline de release.
3. **Registrar el marker `tdd`** en `pytest.ini` (un cambio, elimina 8 warnings).
4. **Ratificar el cierre de H-R144-3** en la próxima sesión de Arquitecto.
5. **Revisitar H-R145-5** (timeout del oráculo historial) cuando haya backend en esta
   máquina para re-verificar el bucle agente completo E2E.

## 7. Conclusión

OpenSyn v1.1.0 (Modo Oráculo) está **operativo y sano**: 122/123 tests GREEN, 4 de 5
oráculos E2E ejecutables en verde (el quinto requiere backend IA ausente en esta
máquina, no es defecto del producto), compilación y `--check` limpios con el compilador
r153, sandbox de permisos activo y degradación elegante sin IA. Se registra UN defecto
nuevo de automatización (H-AUD-OP-1, bucle en EOF), un riesgo de distribución
(H-AUD-OP-2, exe stale) y una mejora de higiene de tests (H-AUD-OP-3). Los tres quedan
registrados en `MEMORIA_PROYECTO.md` con resolución asignada.

---
*Auditoría realizada por Buffy (Codebuff) el 2026-09-25 a solicitud del Arquitecto.
Metodología: solo verificación ejecutada y citada; sin fabricación (regla 3).*
