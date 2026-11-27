# Plan de Micro-Entregable r324_ms_snapshot_impl

## Objetivo

Implementar en `runtime/core/debug.c` las tres funciones de inspeccion de
snapshots declaradas en `runtime/core/debug.h` pero sin definicion C
(`ms_snapshot_contar_vars`, `ms_snapshot_tamano`, `ms_snapshot_contiene`),
mas el atajo `ms_diff_entre` (tambien declarado sin definicion), que
bloqueaban el enlace de `tests/test_memory_snapshots.c` con
`undefined reference`.

## Requisito 1 — contar variables en un snapshot

requisito: Manual 8 §3.4
texto: "□ **Depuración y trazabilidad**: el runtime expone API de snapshots de memoria para inspección histórica."
implementacion: `ms_snapshot_contar_vars(CadenaSegura)` cuenta las lineas no vacias con formato `nombre|tipo|valor` del snapshot; devuelve 0 para snapshot nulo/vacio.
oraculo: tests/integration/test_memory_snapshots.py (9 passed)

## Requisito 2 — tamaño del snapshot

requisito: Manual 8 §3.4
texto: "□ **Depuración y trazabilidad**: el runtime expone API de snapshots de memoria para inspección histórica."
implementacion: `ms_snapshot_tamano(CadenaSegura)` devuelve `snapshot.longitud` (0 si datos es NULL).
oraculo: tests/integration/test_memory_snapshots.py (9 passed)

## Requisito 3 — buscar variable en snapshot

requisito: Manual 8 §3.4
texto: "□ **Depuración y trazabilidad**: el runtime expone API de snapshots de memoria para inspección histórica."
implementacion: `ms_snapshot_contiene(CadenaSegura, CadenaSegura)` busca la variable por nombre y devuelve una CadenaSegura con `tipo:valor` (o NULL si no existe o nombre vacio).
oraculo: tests/integration/test_memory_snapshots.py (9 passed)

## Requisito 4 — diff entre secuencias

requisito: Manual 8 §3.4
texto: "□ **Depuración y trazabilidad**: el runtime expone API de snapshots de memoria para inspección histórica."
implementacion: `ms_diff_entre(int, int)` toma snapshots en ambas secuencias y diferencia; devuelve NULL si las secuencias son iguales o el diff queda vacio.
oraculo: tests/integration/test_memory_snapshots.py (9 passed)

## Evidencia

| check | resultado |
|---|---|
| `pytest tests/integration/test_memory_snapshots.py` | 9 passed |
| `verificar_alineacion.py` | sin brechas |
"""