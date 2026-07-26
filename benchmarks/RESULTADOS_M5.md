# REPORTE DE SINCRONIZACIÓN SYNAPSE — Iteración M5.1

## [ESTADO ACTUAL]
Suite M5.1 operativa con 3 vectores. V2 Tensor compila y corre con 0 errores.
V1 JSON requiere strings in-place para vencer a Python.

## [CÓDIGO IMPLEMENTADO]

| Archivo | Cambio | Estado |
|---------|--------|--------|
| `compilador/generator/generator.py` | Eliminados `extern _syn_simd_disponible` y `extern _syn_simd_tipo` duplicados | ✅ |
| `compilador/generator/emit_expressions.py` | Fix `ExprIndice`: solo añade `.datos` si el tipo base es texto/cadena (elimina doble `.datos`) | ✅ |
| `synapse_rt.c` | `_syn_simd_tipo()` retorna `CadenaSegura` (no `const char*`) | ✅ |
| `synapse_rt.c` | Forward declarations SIMD: `static` → `extern` (linkeables desde código generado) | ✅ |
| `synapse_rt.c` | Guarda SIMD: `#ifdef __SSE__` → `#ifdef __AVX2__` (compatible MinGW-w64) | ✅ |
| `synapse_rt.c` | Arena JSON: `_json_arena` (65536 NodoJson), `_json_arena_alloc()`, `_json_nodo_liberar` no-op | ✅ |
| `synapse_rt.c` | NodoArr/ParArr: `malloc/free` → `pool_alloc/pool_free` (slab allocator) | ✅ |
| `pipeline.py` | `-O2` → `-O3` | ✅ |
| `tests/smoke_tensor.syn` | Indentación multilínea corregida | ✅ |

## [ERRORES/BLOQUEOS]

| # | Gravedad | Descripción | Estado |
|---|----------|-------------|--------|
| 1 | 🔴 | **V1 JSON**: 222ms vs Python ~188ms. `_parse_string_value` aún usa `malloc(len+1)` por cada string (50K allocs). Requiere strings in-place para < 100ms. | Pendiente |
| 2 | 🟡 | `#include <immintrin.h>` duplicado (línea ~672 y ~1367) | Benigno |
| 3 | 🟡 | Warning `fprintf` en `_synapse_box_float` inline | Cosmético |

## [VALIDACIÓN REALIZADA]

| Vector | Resultado | vs Anterior | vs Python |
|--------|-----------|-------------|-----------|
| V1 JSON (pool_alloc arrays) | **222 ms**, 225K obj/s | 231ms → 222ms (4% ↑) | ❌ 1.18× más lento que Python |
| V2 Tensor SIMD | **2 ms**, 256×256 matriz | ✅ CORRECTO | N/A (C puro) |
| V3 Concurrencia | **62 ms** | ✅ | 🟢 33× más rápido |

## [PRÓXIMO PASO]
1. Implementar strings in-place en `_parse_string_value`: null-terminar el buffer de entrada, CadenaSegura apunta directamente al input. Elimina 50K mallocs/iteración.
2. Eliminar `#include <immintrin.h>` duplicado en `_skip_ws()`.
3. Eliminar `inline` de `_synapse_box_float` para suprimir warning.
4. Estimar: con strings in-place, V1 JSON debería bajar a ~80-100ms (< Python).
