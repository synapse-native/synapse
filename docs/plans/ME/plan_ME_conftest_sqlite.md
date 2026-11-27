# Plan ME — Enlazado de sqlite3 en el harness de tests (conftest)

## Requisito 1: rt_objs() debe proveer sqlite3.o

requisito: Manual 3 §12.1 (Estructura de Módulos: "DB | lib/db.syq | Conexión a
  SQLite (FFI a libsqlite3)") + Manual 9 §2.3 (Pipeline de Compilación CI/CD:
  "Compilar el runtime y enlazar estáticamente").
texto: El módulo DB del runtime (`runtime/core/db.c` → `db.o`) invoca símbolos
  `sqlite3_*`; por tanto cualquier binario que enlace `db.o` debe proveer sqlite3.
  El manual exige que el runtime (con el módulo DB) sea enlazable. El build de
  producción cumple (`pipeline.py` compila `vendor/sqlite3/sqlite3.c`); el harness
  de tests (`conftest.rt_objs()` / `_RT_BINARIOS_EXTRA`) no lo incluía, rompiendo
  toda la suite de integración que toca `db.o`.
implementacion: En `tests/conftest.py` se agregó
  `("vendor/sqlite3/sqlite3.o", "vendor/sqlite3/sqlite3.c", [])` a `_RT_OBJ_DEFS`,
  de modo que `rt_objs()` (único punto de verdad) incluya `sqlite3.o` y todos los
  binarios de integration que enlazan `db.o` resuelvan las referencias a
  `sqlite3_*`. De paso, `tests/fuzz/test_distributed_fuzz.py` ya agregó
  explícitamente `vendor/sqlite3/sqlite3.o` a sus dos comandos gcc (redundante pero
  inofensivo tras este cambio).
oraculo: tests/stress/test_cluster_stress.py

## Requisito 2: binarios de integration que usan db.o compilan y corren

requisito: Manual 3 §12.1 + Manual 9 §2.3 (runtime enlazable con DB/SQLite).
texto: Los binarios de integration que enlazan el runtime completo (incl. `db.o`)
  deben compilar y ejecutarse; el hueco de sqlite3 los dejaba en estado de falla de
  enlazado, impidiendo validar el módulo DB del manual.
implementacion: Al incluir `sqlite3.o` en `rt_objs()`, el fixture autouse
  `_auto_compilar_objetos_runtime` re-enlaza los `_RT_BINARIOS_EXTRA` (p.ej.
  test_work_stealing, test_cluster_raft, test_path_traversal_new,
  test_ed25519_axon_new) ya no fallan por sqlite3, y el binario de
  test_fibras_estres (vía `rt_objs()`) enlaza correctamente.
oraculo: tests/fuzz/test_distributed_fuzz.py
