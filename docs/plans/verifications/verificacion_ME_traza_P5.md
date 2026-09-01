# Verificacion ME — TRAZA P5 (Opción A: Manual 2 §4.1 + §9.1)

CUMPLE: Manual 2 §4.1 (CadenaSegura = 16 bytes) y Manual 2 §9.1 (RAII estatico, pool unico sin malloc/free del SO).

## Cambios aplicados (Opción A, aprobada por el Arquitecto)
- synapse_rt_types.h:14 — CadenaSegura reducida a 16 bytes exactos (int longitud + pad4 + const char* datos; sin es_externo). // cumple Manual 2 §4.1
- runtime/core/memory.c:457 — _syn_texto_liberar libera siempre con pool_free (sin !es_externo). // cumple Manual 2 §4.1 + §9.1
- runtime/core/string_utils.c — 11 malloc->pool_alloc, free->pool_free, 5 `.es_externo = 1` eliminados. // cumple Manual 2 §9.1
- nucleo/*.c (6 archivos, linea 19), compilador/generator/generator.py:653, tests/integration/test_cluster_handshake.c,
  tests/fuzz/tmp*.c (770) — typedef CadenaSegura alineado a 16 bytes. // cumple Manual 2 §4.1

## Evidencia de verificacion
- tests/integration/test_cluster_handshake_e2e.py: 6 passed. Prueba 5 "B verifica A" pasa;
  binario reporta "Pasados: 21 Fallos: 0" (rc=0). Corrige la corrupcion de ABI (24B vs 16B) por desborde
  de 8 bytes al devolver CadenaSegura por valor.
- Harness build/obj/lsp_harness.c vinculado al runtime 16B rebuild: items.longitud=519, resp.longitud=584,
  _syn_texto_liberar(items) y _syn_texto_liberar(resp) ejecutados sin crash, rc=0. Demuestra que las
  funciones LSP (lsp_build_completion_items / lsp_build_completion_response) ahora pool_alloc son
  liberadas por pool_free sin fallo de segmentacion.
- nucleo/lsp_v3.exe rebuild contra runtime 16B: ciclo initialize/didOpen/textDocument/completion/shutdown
  termina rc=0 (sin fallo de segmentacion). La ruta completion (nucleo/_lsp_v3.c:1748) invoca
  lsp_build_completion_items (pool_alloc).
- Regression: tests/integration/test_cluster_handshake_e2e.py + test_hello_wire.py + tests/unit/test_ast_abi.py
  = 11 passed.

CONCLUSION: CUMPLE.
