# Verificación ME — Enlazado de sqlite3 en el harness de tests (conftest)

## Requisito 1: rt_objs() debe proveer sqlite3.o

- CUMPLE: `tests/conftest.py` `_RT_OBJ_DEFS` contiene
  `("vendor/sqlite3/sqlite3.o", "vendor/sqlite3/sqlite3.c", [])` con comentario
  grep-chequeable `cumple Manual 3 §12.1`.
- Oración de oracle: `tests/fuzz/test_distributed_fuzz.py` → 15 passed;
  `tests/stress/test_cluster_stress.py` → PASSED (69.73s). Al ejecutar, ya no
  aparece el WARNING `[ME-R7] ... test_work_stealing.exe ... undefined reference to
  sqlite3_open`.

## Requisito 2: binarios de integration que usan db.o compilan y corren

- CUMPLE: `test_cluster_stress.py` delega en `tests/integration/test_fibras_estres.py`,
  cuyo binario compila y ejecuta 10,000 fibras con rc=0 (antes fallaba por
  `undefined reference to sqlite3_*`). `test_distributed_fuzz.py` (15 passed) confirma
  que el enlazado del runtime con DB/SQLite funciona en el harness.
- Nota: los binarios `_RT_BINARIOS_EXTRA` (test_work_stealing, test_cluster_raft,
  test_path_traversal_new, test_ed25519_axon_new) ahora se re-enlazan con sqlite3.o
  vía el fixture autouse y dejan de emitir el WARNING de sqlite3.

## Conclusión
CUMPLE los dos requisitos derivados de Manual 3 §12.1 + Manual 9 §2.3. El hueco de
enlazado de sqlite3 (desviación del manual) quedó corregido en la raíz (conftest),
no solo en un test aislado, eliminando la deuda técnica sistémica.
