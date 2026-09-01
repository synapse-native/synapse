# Plan ME — TRAZA: Opción A (Manual 2 §4.1 + §9.1) — CadenaSegura 16 bytes + pool_alloc

## Requisito: CadenaSegura son 16 bytes y toda devolución usa pool_alloc (RAII)

requisito: Manual 2 §4.1 (Tipos Primitivos, tabla Tamaño ABI): "`texto` / `cadena` /
  `string` | Cadena UTF-8 segura (longitud + buffer) | 16 bytes | No termina en `\0`
  internamente, se convierte para FFI". Manual 2 §9.1 (Reglas de Posesión): "Cuando el
  propietario actual sale de su ámbito de visibilidad (scope), el compilador inyecta de
  forma automática y determinista el código de liberación en el emisor C (RAII estático)."
  Consecuencia: el runtime NO puede introducir campos extra (es_externo) que inflen la
  ABI a 24 bytes, ni devolver punteros malloc() que el RAII liberaría con pool_free().
texto: El runtime define CadenaSegura con `uint8_t es_externo` (24 bytes por
  alineamiento de puntero), desviándose de Manual 2 §4.1. Eso rompe el ABI con el test
  inmutable (16 bytes) y con el generador C (nucleo/generator.c emite 16 bytes). La
  desviación también obligó a devolver punteros malloc() con es_externo=1 en
  string_utils.c para evitar pool_free(malloc) en el RAII — violando Manual 2 §9
  (prohibición de malloc/free y soberanía del pool). Prueba 5 del handshake falla
  (pa.longitud pisado a 0 por desbordamiento de 8 bytes al devolver CadenaSegura por
  valor: pb es contigua a pa en el frame, offset 16, y la escritura de 24 bytes cero
  los 8 bytes de padding que contienen pa.longitud). Root cause confirmado con gdb.
implementacion: Opción A APROBADA por el Arquitecto. Cambios aplicados:
  1. synapse_rt_types.h:14 — eliminar `uint8_t es_externo;` de CadenaSegura (queda
     16 bytes exactos: int4 + pad4 + ptr8). // cumple Manual 2 §4.1
  2. runtime/core/memory.c:457 — `_syn_texto_liberar`: quitar `!s.es_externo`, liberar
     siempre con pool_free. // cumple Manual 2 §4.1 + §9.1
  3. runtime/core/string_utils.c — convertir TODAS las devoluciones CadenaSegura de
     malloc() a pool_alloc() (11 sitios) y free() a pool_free(); eliminar los 5
     `.es_externo = 1`. // cumple Manual 2 §9.1 (pool único, sin malloc del SO)
  4. nucleo/*.c (6 archivos, línea 19) — typedef CadenaSegura a 16 bytes (sin es_externo).
  5. nucleo/generator.c — typedef interno (línea 19) + emisión (líneas 1504, 2500) a 16B.
  6. compilador/generator/generator.py:653 — emisión a 16 bytes (sin es_externo).
  7. tests/fuzz/tmp*.c (generados) — typedef a 16 bytes (bulk replace) para alineación.
  Al alinear runtime+generadores+tests en 16 bytes se cumple synapse_rt_types.h:13
  ("debe coincidir exactamente con las emitidas por el generador") y se corrige P5.
oraculo: tests/test_cluster_handshake_e2e.c Prueba 5 — "B verifica A" debe pasar
  (rc == 0) y la suite "Pasados: 21 Fallos: 0". Además el servidor LSP
  (nucleo/lsp_v3.exe) debe ejecutar completion sin fallo de segmentación: las
  devoluciones de lsp_build_completion_items / lsp_build_completion_response usan
  pool_alloc y el RAII las libera con pool_free sin crash (ya no hay puntero malloc).
