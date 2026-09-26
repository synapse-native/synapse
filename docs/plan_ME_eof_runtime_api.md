# Plan ME eof_runtime_api — H-EOF-1 (deuda de ME eof_cierre_chat, R155; 2026-09-26)

**Deuda:** `_syn_leer_linea()` (runtime/core/io.c:195) colapsa EOF y línea vacía
en `{longitud=0}`: 3 puntos de retorno vacío (consola fgets NULL, pipe ReadFile
0 bytes, POSIX fgets NULL) son indistinguibles de que el usuario presionó Enter.
La corrección del ME eof_cierre_chat (contadores de 3 lecturas vacías) es un
paliativo en capa aplicación; el cierre real por EOF requiere que el runtime
DISTINGA ambos casos. **Nota de alcance:** chat_tui() (ruta TUI) ya maneja EOF
vía `_syn_tui_evento()` (tui.c:642, retorna 10) — este ME solo cubre el modo
línea (chat de modo_oraculo y menú de bienvenida).

## R1 — API del runtime: flag de EOF + `_syn_stdin_eof()`
requisito: Manual 5 §2.6
texto: "### 2.6. Implementación en el Runtime (C)" — la sección canónica de la
implementación C del runtime: el estado de E/S estándar y su consulta son parte
del runtime (mutex `_leer_linea_mutex` ya protege `_buf` estático bajo este
mismo encuadre).
implementacion: `runtime/core/io.c` (NUEVO estado + API):
1. `static int _syn_stdin_eof_flag = 0;` protegido por el mutex existente
   `_leer_linea_mutex` (sin mutex nuevo).
2. En los 3 puntos EOF de `_syn_leer_linea`: consola `fgets()==NULL` (parte
   Windows), pipe `ReadFile` con `_pos==0` y `!ok || _leidos==0` (parte
   Windows), POSIX `fgets()==NULL` → `_syn_stdin_eof_flag = 1` justo antes de
   cada `return {0,""}` de EOF. Las lecturas exitosas (línea completa o línea
   parcial con datos) NO tocan el flag. NOTA límite 4095 bytes: una línea
   truncada por el límite puede dejar el flag en 0 con más datos pendientes —
   comportamiento aceptado (documentado).
3. NUEVA función pública `int _syn_stdin_eof(void)`: lock → leer flag →
   unlock → retornar (thread-safe igual que el resto del módulo).
// cumple Manual 5 §2.6
oraculo: tests/auditoria/test_oraculos_eof_runtime.py

## R2 — Binding Synapse: `stdin_eof()` en std.io con contratos
requisito: Manual 2 §5.1
texto: "- **`requiere`:** Se evalúa antes de la primera instrucción del cuerpo.
Todas las expresiones deben ser booleanas.\n- **`garantiza`:** Se evalúa
inmediatamente antes de cada `retornar`. La variable `_resultado_` contiene el
valor que se va a retornar."
implementacion: `std/io.syn` (NUEVO externo + wrapper público junto a
leer_linea): `externo funcion _syn_stdin_eof() -> entero` y
```
funcion stdin_eof() -> entero:
    garantiza:
        resultado == 0 o resultado == 1
    retornar _syn_stdin_eof()
```
Convención documentada en std/io.syn: 0 = hay (posiblemente más) entrada, 1 =
stdin agotado (EOF). `// cumple Manual 2 §5.1` en el wrapper.
// cumple Manual 2 §5.1
oraculo: tests/auditoria/test_oraculos_eof_runtime.py

## R3 — Consumo en OpenSyn: EOF real en chat modo línea y menú
requisito: Manual 7 §2.1
texto: "El orquestador es un proceso en C que gestiona el ciclo de vida del
servidor de inferencia (`llama-server`)." — robustez del ciclo de vida del
asistente local (misma ancla del ME eof_cierre_chat; R155 ya cerró el bucle con
contadores: este requisito REFINA la detección para que sea por EOF real y no
por heurística).
implementacion: `opensyn/principal.syn` (2 sitios, sin tocar los tests
inmutables de R155):
1. Bucle de chat de modo_oraculo (después de `prompt = leer_linea()`), si
   `prompt == ""` Y `stdin_eof() == 1` → aviso "[EOF] Entrada cerrada. Saliendo."
   + `retornar 0` INMEDIATO. Las líneas vacías del usuario (stdin_eof()==0) NO
   incrementan `eof_consecutivos` (debe resetear a 0 en vacío real — hoy no lo
   hace) y el límite >=3 queda como RESPALDO ante runtimes viejos.
2. mostrar_menu_bienvenida: misma lógica — `entrada == ""` y `stdin_eof() == 1`
   → retornar "2" con aviso "[EOF]"; `intentos_menu >= 3` queda de respaldo.
   El flag de EOF NO se purga (no hay API de reset; semántica de flujo: EOF es
   terminal). Encadenado deseado en pipes: menú EOF → "2" → modo_oraculo →
   chat lee EOF → rc=0 inmediato (una sola pasada limpia). La escritura de
   config por la selección por defecto es idéntica a la de un usuario que
   presiona "2" (paridad con r155, no es regresión).
// cumple Manual 7 §2.1
oraculo: tests/auditoria/test_oraculos_eof_runtime.py

## R4 — Oráculo: EOF real ≠ líneas vacías (E2E)
requisito: Manual 9 §6.2
texto: "El pipeline de CI/CD ejecuta automáticamente: La suite de tests completa
en cada target."
implementacion: `tests/auditoria/test_oraculos_eof_runtime.py` (NUEVO, sin
skips): (a) estructural — io.c contiene `_syn_stdin_eof` + los 3 puntos EOF
marcan el flag; std/io.syn declara stdin_eof con garantiza; principal.syn
consulta stdin_eof en ambos sitios (anti-sniff); (b) E2E — compila
`opensyn/principal.syn` on-demand con `python main.py` (pipeline real; la ruta
nativa stage1 hornea el main del compilador núcleo, NO OpenSyn) y ejecuta un
probe que DISTINGUE: stdin con solo líneas vacías → el proceso SIGUE vivo
(prompt repetido, NO cierra por EOF) y EOF → rc==0 rápido; (c) regresión del
comportamiento r155 (oráculo existente GREEN intacto). Aislamiento
USERPROFILE/HOME virtual + cwd tmp (H-EOF-2).
// cumple Manual 9 §6.2
oraculo: tests/auditoria/test_oraculos_eof_runtime.py (auto-referencial)

## R5 — Mapa de alineación: entradas explícitas para los archivos tocados
requisito: Manual 5 §2.6 (runtime) y Manual 2 §5.1 (std) — el mapa es fuente
máquina del gate; hoy io.c/std-io.syn caen al legacy difuso (`runtime/*`→M5,
`std/*`→M2) que obscurece la ancla exigida.
implementacion: `docs/gobernancia/mapa_alineacion.md` (NUEVAS entradas JSON):
`"runtime/core/io.c": ["Manual 5 §2.6"]` y `"std/io.syn": ["Manual 2 §5.1"]`.
(Nota: el mapa legacy exige Manual 5 para std/io.syn — entrada inválida con el
manual real, por eso la entrada explícita gana por especificidad; corrección de
higiene del mapa, no cambio de reglas.)
oraculo: auditoria/verificar_alineacion.py (gate del pre-commit)
// cumple Manual 5 §2.6

## Archivos a modificar
Producción:
- runtime/core/io.c (R1 — NUEVO ancla M5 §2.6)
- std/io.syn (R2 — NUEVO ancla M2 §5.1)
- opensyn/principal.syn (R3 — ancla M7 §2.1 vigente)
Docs de gobernanza:
- docs/gobernancia/mapa_alineacion.md (R5)
Tests (NUEVOS, TDD):
- tests/auditoria/test_oraculos_eof_runtime.py (R4)

## Notas de riesgo
- Cache runtime: los .o de runtime se invalidan solos (clave = SHA-256 fuente +
  flags, pipeline.py:170) — editar io.c recompila io.o en el próximo build.
  Lección R145 verificada: NO hace falta purgar cache a mano.
- Guard de frescura OBL-EXE-R2 (ME-B): tras COMITEAR este ME, el exe queda
  "stale" respecto al nuevo commit de principal.syn → REGENERAR
  dist/bin/opensyn.exe inmediatamente después del commit (comportamiento
  diseñado del guard: fuerza rebuild).
- lsp.c/lsp_v3.c definen wrappers `leer_linea` propios que delegan en
  `_syn_leer_linea` — NO se tocan (LSP sensible, fuera de alcance).
