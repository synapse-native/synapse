# Plan ME eof_cierre_chat — H-AUD-OP-1 (auditoría de operatividad OpenSyn, 2026-09-25)

**Hallazgo:** el chat de OpenSyn NO termina ante EOF de stdin. Evidencia ejecutada:
`echo "status" | timeout 12 dist/bin/opensyn.exe` → rc=124 con ~210.000 repeticiones
de "Tu>" (log de 21 MB); verificado también contra binario fresco (r153).

**Causa raíz (verificada por lectura + probe):** `_syn_leer_linea()`
(runtime/core/io.c:195) colapsa EOF y línea vacía en `{longitud=0}` → `leer_linea()`
retorna "" en EOF → los bucles lectores hacen `siguiente` infinito:

1. `modo_oraculo()` bucle de chat modo línea (principal.syn:1461) — **confirmado colgado**:
   `_syn_tui_iniciar()` falla en pipes sin `OPENSN_TUI_TEST=1` (TUI exige consola real),
   cae a modo línea, `prompt == ""` → `siguiente`.
2. `mostrar_menu_bienvenida()` (principal.syn:270) — bucle de validación 1/2 también
   giraría en EOF.

No defecto: `chat_tui()` (bucle TUI, principal.syn:1348) YA maneja EOF —
`_syn_tui_evento()` en modo pipe retorna 10 (Ctrl+C) ante EOF sin buffer (tui.c:642) y
el bucle termina (`retornar 0` en evento 10). Verificado: oráculos TUI con
`OPENSN_TUI_TEST=1` GREEN y stdin cerrado no cuelga esa ruta.

## R1 — Cierre determinista en EOF del chat modo línea
requisito: Manual 7 §2.1
texto: "El orquestador es un proceso en C que gestiona el ciclo de vida del servidor
de inferencia (`llama-server`)." — el ciclo de vida (Inicio/Monitoreo/Apagado/
Recuperación) exige terminación determinista; el chat modo línea sin cierre ante EOF
viola la robustez del ciclo de vida del asistente local (se acumula a la degradación
elegante ya lograda en R140/R152 para el backend apagado).
implementacion: `opensyn/principal.syn` (bucle chat de `modo_oraculo`, L1461): contador
`let eof_consecutivos: entero = 0` local al bucle. Tras `prompt = leer_linea()`:
si `prompt == ""` → `eof_consecutivos = eof_consecutivos + 1`; si llega a 3 →
"  [EOF] Entrada cerrada. Saliendo." + `retornar 0`; en línea NO vacía →
`eof_consecutivos = 0`. Tres lecturas vacías = EOF confirmado (una línea en blanco del
usuario solo reinicia el prompt 2 veces más; indistinguible de EOF por diseño del
runtime, se asume interrupción del flujo y se cierra limpio rc=0).
// cumple Manual 7 §2.1
oraculo: tests/auditoria/test_oraculos_eof_cierre.py

## R2 — Cierre determinista en EOF del menú de bienvenida
requisito: Manual 7 §2.1
texto: (mismo imperativo de robustez; el menú de primera ejecución es parte del mismo
flujo de arranque del asistente).
implementacion: `mostrar_menu_bienvenida()` (L265-270): contador local
`let intentos_menu: entero = 0`; en el bucle de entrada inválida, si `entrada == ""` →
`intentos_menu = intentos_menu + 1`; si llega a 3 → retornar "2" (Modo Oráculo, el modo
por defecto del producto según config del instalador) tras avisar
"  [EOF] Entrada cerrada. Seleccionando Modo Oráculo por defecto.".
// cumple Manual 7 §2.1
oraculo: tests/auditoria/test_oraculos_eof_cierre.py

## R3 — Oráculo E2E anti-regresión (stdin cerrado sin "salir")
requisito: Manual 9 §6.2
texto: "**Nuevo (Fase 31):** `synapse test --junit --coverage` para generar reportes de
tests y cobertura." (convención de verificación E2E del ecosistema; el oráculo compila
el fuente con el S1 real, patrón test_r3_param_adt_s1 del ME r151).
implementacion: `tests/auditoria/test_oraculos_eof_cierre.py` (NUEVO): (a) test
estructural — el bucle de chat cita `eof_consecutivos` y el límite 3, y
`mostrar_menu_bienvenida` cita `intentos_menu` (anti-sniff: verifican el mecanismo);
(b) test E2E — compila `opensyn/principal.syn` on-demand con el comando del CI
(`main.py nucleo/principal.syn -o <stage1>` + stage1 compila principal.syn, patrón
test_r3_param_adt_s1), ejecuta el binario NATIVO resultante con stdin cerrado tras una
línea y EXIGE rc==0 en <= 60 s; (c) guard — si `principal.syn` pierde el contador, el
test falla. Aislamiento: se copia el cwd a un tmp (el binario muta `.synapse_config`).
// cumple Manual 9 §6.2
oraculo: tests/auditoria/test_oraculos_eof_cierre.py (auto-referencial)

## Archivos a modificar
Producción (mapa_alineacion.md: principal.syn → Manual 7 §2.1 + Manual 7 §4.2):
- opensyn/principal.syn (R1, R2)
Tests (NUEVOS, TDD):
- tests/auditoria/test_oraculos_eof_cierre.py (R3)

## Hallazgos previstos
- H-EOF-1: `_syn_leer_linea` no distingue EOF de línea vacía — fix en runtime/core/io.c
  (API nueva) queda FUERA de alcance (io.c sin mapeo, LSP sensible); el contador de 3
  lecturas vacías es la corrección mínima segura en capa aplicación. Registrar como
  deuda con resolución asignada.
- H-EOF-2: el binario del oráculo E2E mutará `.synapse_config` del cwd del tmp —
  mitigado copiando el cwd a un directorio temporal.
- H-EOF-3 (nuevo, descubierto en ME-A): la lectura de config RELATIVA al cwd no
  funciona — `_validar_ruta_segura` (std/sistema.syn:16) rechaza rutas relativas;
  el modo oráculo en esta máquina viene del fallback HOME/Program Files
  (`leer_modo_config` paso 2/3). Mitigación en el oráculo E2E: HOME virtual + config
  en home_tmp (sin newline final, comparación de contenido EXACTA). Deuda:
  normalizar ruta de config relativa→absoluta.
