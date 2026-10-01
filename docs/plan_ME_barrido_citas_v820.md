# Plan MTS — ME barrido_citas_v820

> Cierre del barrido de las 39 citas `cumple Manual X §Y` que quedaron sin
> sección tras la revisión v8.2.0 (154a544): quinta oleada de reparación de la
> misma cadena de causa (precedentes: §5.1/R119, §6.3/b1ac1c2, §7.3/72d77f3).
> Estrategia (decisión del Arquitecto, Opción A): restaurar TEXTUALMENTE las
> secciones citadas que existían pre-154a544 (§4.3, §6.1, §6.2, §6.4, §7.2, §8)
> y re-anclar las 3 citas al capítulo §6 a subsecciones reales.
> Regla de oro: el contenido normativo es byte-exacto pre-154a544; la nota de
> restauración es metadato de procedencia, no norma.

requisito: Manual 7 §4.3 (Manejo de Errores y Timeouts — restauración textual del estado pre-154a544)
texto: "Si el servidor de inferencia no responde en 30 segundos, el LSP devuelve un error al usuario."
implementacion: docs/manuales/MANUAL 7.md — §4.3 restaurada byte-exacta del
  estado pre-154a544 (3 bullets: timeout 30s, modelo no cargado, regenerar
  tras agotar intentos) insertada en su posición canónica tras §4.2, con Nota
  de restauración 2026-10-01. Con ella las 13 citas §4.3 de run_manager.syn y
  router.syn vuelven a resolver.
oraculo: tests/integration/test_permisos_opensyn.py

requisito: Manual 7 §6.1 + §6.2 (Instalación de un solo clic + config.toml — restauración textual)
texto: "El instalador de OpenSyn es parte del instalador unificado del ecosistema (Manual 9). Pasos:"
implementacion: docs/manuales/MANUAL 7.md — §6.1 (5 pasos + prueba de humo) y
  §6.2 (config.toml: [general]/[modelo]/[server]/[rag]/[generacion]) restauradas
  byte-exactas pre-154a544 como apéndice, con Nota de restauración. Con ellas
  el capítulo 6 vuelve a existir y las citas al capítulo resuelven.
oraculo: tests/integration/test_permisos_opensyn.py

requisito: Manual 7 §6.4 (Comandos CLI de OpenSyn — restauración textual)
texto: "| `opensyn transpile --from python script.py` | Transpila Python a Syquex. |"
implementacion: docs/manuales/MANUAL 7.md — tabla de comandos CLI restaurada
  byte-exacta pre-154a544 (status/download/finetune/bindings/transpile), con
  Nota de restauración. La cita §6.4 de router.syn:716 vuelve a resolver.
oraculo: tests/integration/test_permisos_opensyn.py

requisito: Manual 7 §7.2 (Pruebas de Rendimiento — restauración textual)
texto: "Latencia de inferencia: < 1s para prompts cortos (modelo 7B en GPU)."
implementacion: docs/manuales/MANUAL 7.md — 4 bullets de rendimiento
  restaurados byte-exactos pre-154a544, con Nota de restauración. Las 12
  citas §7.2 de planificador.syn y router.syn vuelven a resolver.
oraculo: tests/integration/test_permisos_opensyn.py

requisito: Manual 7 §8 (EJEMPLO COMPLETO DE FLUJO DE IA — restauración textual)
texto: "El LSP valida con `synapse check --no-emit` (compila correctamente)."
implementacion: docs/manuales/MANUAL 7.md — §8 completa restaurada
  byte-exacta pre-154a544 (2 escenarios: suma con aiComplete y dividir con
  bucle de corrección), con Nota de restauración. Las 10 citas §8 de
  validation_loop.syn, chat.syn y runtime (modelo.c, ollama.c, tui.c)
  vuelven a resolver.
oraculo: tests/integration/test_permisos_opensyn.py

requisito: Manual 7 §6.2 (config.toml [modelo] — re-anclaje de las citas al capítulo)
texto: "System Prompt: las reglas de Synapse/Syquex (sección 2.3)."
implementacion: opensyn/chat.syn L3 y L54: `cumple Manual 7 §6` →
  `cumple Manual 7 §6.2` (selección/detección de modelo = [modelo] de
  config.toml; el capítulo §6 restaurado ya resolvería, pero la ancla
  subsección es más precisa). Solo comentarios, sin cambios ejecutables.
oraculo: tests/integration/test_opensyn_integration.py

requisito: Manual 7 §2.1 (Orquestador — re-anclaje de la cita al capítulo)
texto: "El orquestador es un proceso en C que gestiona el ciclo de vida del servidor de inferencia (`llama-server`)."
implementacion: nucleo/ai_orchestrator.h L146: `cumple Manual 7 §6` →
  `cumple Manual 7 §2.1` (integración de agent-skills con el orquestador del
  modelo local = §2.1 Orquestador, sección vigente). Solo comentario, sin
  cambios ejecutables. mapa_alineacion.md: entrada nueva
  nucleo/ai_orchestrator.h → [Manual 7 §2.1]; chat.syn → [§6.2, §8]
  (§6.4 de la entrada era stale: chat.syn nunca citó §6.4).
oraculo: tests/integration/test_opensyn_integration.py

## Notas de alcance
- Tests: NINGUNO modificado — todas las citas existían y apuntaban a secciones
  reales pre-154a544; la verdad vive en el manual (dirección manual→código).
- Sin cambios ejecutables: los 3 re-anclajes son líneas de comentario.
- El oráculo tests/integration/test_permisos_opensyn.py (43/43) es el suite
  vigente de la zona con TestCitasCumpleManual; test_opensyn_integration
  (18/18) cubre la compilación de la zona opensyn/.
- Resultado esperado: citas_muertas_repo == 0 (verificado: 39 → 0).
