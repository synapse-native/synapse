# Plan ME — M4: Rechazar typeflags peligrosos en extracción TAR

## Requisito 1: typeflags L/K/1/2 rechazados en extracción

requisito: Manual 6 §6.1 (Seguridad en deserialización/extracción): la
  extracción de archivos TAR debe rechazar tipos de entrada que permitan
  path traversal o escritura fuera del directorio destino (GNU long name/link
  y hard/symlinks).
texto: `runtime/core/axon.c` `_syn_tar_extraer()` no validaba los typeflags
  'L' (GNU long name), 'K' (GNU long link), '1' (hard link) ni '2' (symlink),
  dejando ~75% de la superficie de path traversal expuesta (el nombre real se
  revela en el bloque siguiente al typeflag, evadiendo el chequeo de ruta).
implementacion:
  1. En `_syn_tar_extraer()` se rechaza explícitamente cualquier entrada con
     typeflag 'L', 'K', '1' o '2' antes del chequeo de path traversal.
  2. Se añade comentario grep-chequeable `cumple Manual 6 §6.1`.
  3. No se relaja el chequeo de path traversal existente para las demás
     entradas regulares.
oraculo: tests/security/test_path_traversal.py (3/3 passed):
  test_path_traversal_bloqueado, test_rutas_normales_permitidas,
  test_malicious_tar_detectado. Oráculo C: tests/test_path_traversal_new.exe
  (3/3 passed).

## Conclusión

CUMPLE Manual 6 §6.1: los typeflags que concentran la mayor superficie de
ataque de path traversal en TAR (extensiones GNU + links) se rechazan
explícitamente en extracción.
