# Plan ME-SEC-4: Estado estático → fiber-safe (TLS/mutex)

## Estado: CERRADO (2026-08-30)
## Fecha: 2026-08-30

## Problema
`io.c` y `texto.c` tienen variables estáticas compartidas sin sincronización.
Si dos fibras/hilos acceden simultáneamente, hay data races (Manual 5 §3).

## Problemas encontrados

### io.c
| Variable | Línea | Riesgo | Fix |
|----------|-------|--------|-----|
| `static int _syn_stdout_binary_init` | 20 | Race en inicialización | `pthread_once` |
| `static char _buf[4096]` en `leer_linea` | 47 | **Crítico**: dos fibras corrompen buffer compartido | `pthread_mutex_lock` antes de usar `_buf` |

### texto.c
| Variable | Línea | Riesgo | Fix |
|----------|-------|--------|-----|
| `static char* _split_store[][]` | 19 | Race en alloc/free de splits | `pthread_mutex` global |
| `static int _split_count[]` | 20 | Race en contador | (mismo mutex) |
| `static int _split_used` | 21 | Race en contador | (mismo mutex) |

## Fix

### io.c
1. Reemplazar `static int _syn_stdout_binary_init` + check por `pthread_once`
2. Agregar `pthread_mutex_lock/unlock` en `leer_linea` alrededor de `_buf`

### texto.c
1. Agregar `static pthread_mutex_t split_mutex = PTHREAD_MUTEX_INITIALIZER`
2. Proteger `_split_alloc`, `_split_free`, y la función `dividir` con el mutex

## Contrato (Manual 2 §12)
- `requiere:任何调用者 (no necesita condiciones especiales)`
- `garantiza: llamadas concurrentes no corrompen estado interno`

## Tests TDD
1. Test C: dos hilos llaman `leer_linea` concurrentemente → sin crash
2. Test C: dos hilos llaman `_split_alloc/_split_free` concurrentemente → sin crash

## Aceptación
- tsan sin data races
- Tests concurrentes pasan sin crash
- 0 regresión en tests existentes

## Cumple
- Manual 5 §3: fibras, canales, mutex
- Manual 2 §12: contratos requiere/garantiza
- Manual 4 §2.1: funciones deben cumplir contrato
