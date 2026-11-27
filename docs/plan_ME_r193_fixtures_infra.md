# ME r193_fixtures_infra — grupos A del barrido r191 (fixtures/entsorno de pruebas)

**Fecha:** 2026-10-21 · **Fase:** POST-FASE 33 — deuda cero · **Base:** 40fc1cc
**Ámbito:** SOLO archivos de `tests/**` (exentos del gate de lectura según
`docs/gobernancia/mapa_manuales.md` §Exclusiones; modificación gobernada por la
regla 5 con la autorización del Arquitecto registrada en
`docs/plan_maestro_deudas.md`: "los tests SOLO se modifican para ALINEARLOS al
manual" + "estás autorizado a tomar las decisiones siempre que sigas las reglas").
0 archivos de producción: no toca compilador ni std.

## Diagnóstico (reproducido en vivo 2026-10-21)

1. `test_cache_audit.py::test_axon_lock_existente` (1): el lanzador
   `_find_python()` resuelve un `python` del SISTEMA (venv ajeno SIN pytest)
   y el subproceso `python -m pytest tests/integration/test_axon_e2e.py`
   muere con rc=1. Con el intérprete del proyecto `sys.executable`
   (`.venv/Scripts/python.exe`) la misma suite da RC=0 (verificado 5/5).
2. `test_opensyn_cli.py` (3 del barrido): rutas RELATIVAS
   (`'opensyn/opensyn.bat'`, `'opensyn/principal.syn'`) dependen del cwd del
   runner; con cwd≠raíz fallan. Aisladas ahora pasan (12/12 con cache_adv).
3. `test_axon_e2e.py` (3 del barrido: test_axon_lock, test_gen_helper,
   test_path_traversal_binary): residuo del worktree del triaje (los .exe no
   versionados faltaban ahí); en este árbol pasan 5/5 y el conftest ya los
   reconstruye por mtime (`_RT_BINARIOS_EXTRA`, Causa E). Sin reparación
   necesaria en este ME — se re-verifica con el oráculo.
4. `test_cache_adv_10.py::test_segunda_compilacion_mas_rapida` (1): aserción
   de TIMING (">=50% más rápida") sobre un pipeline que NO involve caché
   (`_compilar` instancia Lexer→Parser→Analizador→Generador directamente) —
   flacky y NO alineada al manual. La propiedad del manual es el
   DETERMINISMO de la clave/código (ver nota citada abajo), no la velocidad
   medida. La aserción condicional de ratio (`if duracion2 < duracion1`) es
   una lotería en runs cargados (fue el caso del barrido: 2da pasada más
   lenta ⇒ sin ratio; 1ra lenta ⇒ ratio>0.5 ⇒ rojo).

## Hallazgo NUEVO de producción (H-R193-1, reproducido 2026-10-21): paridad
## del enlace cacheado `_link_object`

En la corrida del grupo A completo, `test_cache_stale` expuso un fallo REAL del
compilador (deuda preexistente que el contador global compartido ocultaba):
la segunda compilación con `main.py --incremental` usó la ruta de enlace
cacheado `_link_object` (pipeline.py:~1155, imprime `[CACHE LINK]`) que arma
`rt_objs` SIN los módulos quantum/federated/IA que el enlace normal (~:892) sí
incluye ⇒ `undefined reference to 'qc_aplicar_pauli_z'` (quantum_err_corr.o
usa símbolos de quantum_runtime.o). Fix de producción: añadir los mismos tres
bloques de módulos opcionales en `_link_object` (paridad de ambos caminos).
`# cumple Manual 1 §4` en `pipeline.py`.

Validación E2E del HIT (2026-10-21): pasada 1 fría ~101 s con los 46 .o
compilados; pasada 2 **0,9 s** con `[CACHE HIT]` y **0 recompilas** de runtime
— la semántica de `cache.syn` (M1 §4) quedó operativa de punta a punta.

Hallazgo complementario del mismo fix de producción (H-R193-2): la key de
caché de los .o del runtime incluía `base_flags` como cadena CRUDA y los dos
caminos la conformaban distinta (el enlace normal intercala `no_std_flags`/
`env_gcc_flags` vacíos ⇒ DOBLE espacio, y añade `-static` win32 que faltaba en
`_link_object`) ⇒ los 46 .o se recompilaban en CADA pasada (~90 s). Fix:
normalizar la key (`' '.join(base_flags.split())`) y dar a `_link_object` la
`base_flags` de paridad con el camino normal.

Además: el módulo auditor `test_cache_audit.py` compartía contadores globales
sin que cada test cobrara su propia cuenta — checks fallidos de T1-T3 (que
terminaban en `return bool`, que pytest ignora marcándolos passed) los
 cobraba `test_axon_lock_existente`. Reparación de fixture: fixture autouse
 que resetea contadores por test + cada test aserta `FAIL == 0` al final; el
 check de timing puramente probabilístico ("segunda más rápida", margen de
 jitter ~5%) se complementa con la semántica DETERMINISTA del HIT real:
 `[RUNTIME] gcc -c` no puede aparecer en la salida de la segunda pasada.

## Bloque MTS

requisito: Manual 1 §7.2
texto: "`Todo cambio debe pasar la suite completa de pruebas:` — `pytest tests/integration/`"
implementacion:
- (a) `tests/integration/test_cache_audit.py`: `PYTHON = _find_python()` →
  `PYTHON = sys.executable` (el suite metastest EJECUTA pytest, así que el
  intérprete debe ser el del proyecto que sí tiene pytest; la detección de
  `python3/python` del SISTEMA es la deuda). Sin cambios de semántica de los
  checks: mismos checks, mismo orden.
- (b) `tests/integration/test_opensyn_cli.py`: anclar las rutas del wrapper y
  de `principal.syn` a la RAÍZ del repo derivada de `__file__`
  (cwd-independiente); el resto de los checks no cambia. El fixture
  `synapse_installed` mantiene su `pytest.skip` si synapse.exe no está
  instalado (ya alineado).
- (c) `tests/integration/test_cache_adv_10.py`: docstring re-anclado de la
  cita histórica "Manual 1 §6" (M1 §6 = hoja de ruta; la caché vive en la
  ESTRUCTURA del repo, M1 §4: `cache.syn — Sistema de caché incremental SHA-256`,
  con la nota `Manual 9 §2.5`: la clave de caché incluye hash SHA-256 de la
  fuente/compilador/flags ⇒ `.o` byte-idéntico) a **Manual 1 §4 / Manual 9 §2.5**
  y la aserción de ratio aleatoria sustituida por la misma propiedad que el
  manual declara: DETERMINISMO de dos compilaciones del mismo contenido
  (`cod1 == cod2` en ambas pasadas, ya presente) + coste acotado por arriba
  con margen fijo (ambas pasadas bajo FACTOR de la 1ra), que sí es verificable
  sin apostar a que la 2da sea el doble de rápida en un runner cargado.
- (d) `tests/integration/test_axon_e2e.py`: SIN cambios (pasa; fallo del
  barrido era el worktree del triaje + el subprocess roto del punto (a)).
- (e) `tests/integration/test_cache_audit.py` (cirugía de fixture): fixture
  autouse `_contadores_limpios_por_test` (contadores global reseteados por
  test), cada test aserta SU `FAIL == 0` al final; `return bool` de T1-T3
  eliminados (pytest ignores return values — warnings
  PytestReturnNotNoneWarning incluidos); returns tempranos de T2 →
  `pytest.fail`/`pytest.skip`; checks de timing sustituidos por el HIT
  DETERMINISTA (`[RUNTIME] gcc -c` ausente en la segunda salida).
- (f) `pipeline.py` `_link_object` (H-R193-1, producción): paridad de la lista
  de objetos del enlace cacheado con el enlace normal — quantum
  (`_compilar_quantum_objetos`), federated (`_RT_FEDERATED_FUENTES`) e IA
  (`_RT_IA_FUENTES`) añadidos a `rt_objs` en el camino `[CACHE LINK]`.
  # cumple Manual 1 §4.
oraculo: tests/auditoria/test_oraculos_r193_fixtures_infra.py
  (ejecuta `sys.executable -m pytest` sobre los 4 archivos del grupo A con
  cwd=raíz y exige rc==0 — la suite completa de `pytest tests/integration/`
  de estos archivos pasa bajo el intérprete del proyecto).

## Verificación

- Oráculo r193 ejecutado (4 archivos, rc=0).
- `unit 514✓` (regresión) + `pytest tests/integration/` grupales B/C sin cambios
  (los archivos tocados son solo estos 4 de grupo A).
- No hay archivos de producción ⇒ `contrastar`/`verificar_alineacion` sin
  brechas; expediente `--nuevo/--verificar` con los tests como archivos del
  cambio (exentos de gate, documento el motivo aquí).
