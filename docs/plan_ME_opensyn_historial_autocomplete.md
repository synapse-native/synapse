# Plan ME — OpenSyn Historial Persistente + Autocompletado Tab

FASE: 30-b / R142 (hardening F30 + UX parity OpenCode/Freebuff)
ID: ME_opensyn_historial_autocomplete
ESTADO: completado (oráculo tests/e2e_oracle_opensyn_historial.py GREEN +
tests/e2e_oracle_opensyn_autocomplete.py GREEN; verificación en
docs/verificacion_ME_opensyn_historial_autocomplete.md; cierre en docs/reportes/R141.md)

## Resumen del micro-entregable

Añadir dos features críticas para paridad UX con OpenCode/Freebuff:
1. **Historial persistente** — guarda cada sesión en `~/.opensyn/history.jsonl`; flechas ↑↓ en la caja de entrada navegan el historial (como readline).
2. **Autocompletado Tab** — en la caja de entrada: Tab completa rutas relativas (archivos/directorios) y comandos `/`; doble Tab muestra menú de opciones.

## Requisitos del manual (MTS — bloque estricto)

### Requisito R1 — Historial persistente entre sesiones

requisito: Manual 7 §1.1 — visión de OpenSyn (equivalente local a OpenCode)
texto: OpenSyn es el asistente local del ecosistema Synapse, equivalente a un Copilot u OpenCode, que conoce Synapse y Syquex de forma nativa.
implementacion:
  - `runtime/core/tui.c`: nuevas funciones `_syn_tui_historial_cargar()`, `_syn_tui_historial_guardar()`, `_syn_tui_historial_anterior()`, `_syn_tui_historial_siguiente()`.
  - Archivo `~/.opensyn/history.jsonl` (una línea JSON por entrada: `{"ts":123,"role":"user","text":"..."}`).
  - En `_syn_tui_evento()`: teclas ↑ (VK_UP / 'A') y ↓ (VK_DOWN / 'B') navegan historial si la caja está vacía o el cursor está al final.
  - Al enviar entrada (Enter), se añade al historial en memoria y se persiste (append).
  - Límite: 1000 entradas (FIFO).
oraculo: tests/e2e_oracle_opensyn_historial.py (simula ↑↓ en modo pipe, verifica persistencia entre ejecuciones)

### Requisito R2 — Autocompletado Tab en caja de entrada

requisito: Manual 7 §8 — chat local con flujo robusto y UX de asistente
texto: OpenSyn consulta al oraculo local Ollama con POST /api/chat; la respuesta debe ser acotada en el tiempo y mostrarse conforme se genera.
implementacion:
  - `runtime/core/tui.c`: nueva función `_syn_tui_completar()` invocada en `_syn_tui_evento()` al recibir Tab (VK_TAB / '\t').
  - Contexto: si la entrada empieza con `/` → completa comandos (`/model`, `/modelos`, `/tdd`, `/revisar`, `/plan`, `/skills`, `/ayuda`, `/salir`).
  - Si no empieza con `/` y contiene `/` o `\` → completa rutas relativas desde cwd (usa `_syn_listar_directorio` + filtrado por prefijo).
  - Lógica: primer Tab = completa hasta prefijo común único; segundo Tab consecutivo (sin otros keystrokes) = abre menú modal con opciones (reutiliza `_syn_tui_menu`).
  - En modo pipe (`OPENSN_TUI_TEST=1`): Tab se simula enviando `\t` en stdin.
oraculo: tests/e2e_oracle_opensyn_autocomplete.py (simula Tab en modo pipe, verifica completado de ruta y comando)

## Archivos que modifica

- runtime/core/tui.c, runtime/core/tui.h (nuevas APIs: _syn_tui_historial_*, _syn_tui_completar)
- opensyn/principal.syn (integración: llama a historial cargar/guardar en chat_tui)
- tests/e2e_oracle_opensyn_historial.py (nuevo oráculo)
- tests/e2e_oracle_opensyn_autocomplete.py (nuevo oráculo)
- docs/plan_ME_opensyn_historial_autocomplete.md, docs/verificacion_ME_opensyn_historial_autocomplete.md

## Verificación

- `python main.py opensyn/principal.syn` rc=0 → exe nuevo (timestamp).
- Modo pipe forzado (OPENSN_TUI_TEST=1): historial carga/guarda, ↑↓ navega, Tab completa ruta y comando.
- `python auditoria/verificar_alineacion.py` → 0 brechas.
- `python auditoria/contrastar.py --plan docs/plan_ME_opensyn_historial_autocomplete.md` → sin brechas.