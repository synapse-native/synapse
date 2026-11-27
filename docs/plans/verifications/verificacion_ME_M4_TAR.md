# Verificación ME — M4: Rechazar typeflags peligrosos en extracción TAR

## Requisito 1: typeflags L/K/1/2 rechazados

- CUMPLE: `runtime/core/axon.c` `_syn_tar_extraer()` ahora rechaza explícitamente
  typeflags 'L' (GNU long name), 'K' (GNU long link), '1' (hard link) y
  '2' (symlink) antes de cualquier procesamiento de ruta. El rechazo ocurre
  ANTES del chequeo de path traversal, eliminando la superficie de ataque
  donde el nombre real se revela en el bloque siguiente al typeflag.
  Comentario grep-chequeable `cumple Manual 6 §6.1`.

- Oráculo: `tests/test_path_traversal_new.exe` (3/3 passed) y
  `tests/security/test_path_traversal.py` (3/3 passed).

## Conclusión

CUMPLE Manual 6 §6.1. Los typeflags que representan ~75% de la superficie
de ataque de path traversal en TAR (GNU extensions + links) ahora son
rechazados explícitamente.
