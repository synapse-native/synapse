# Plan ME-SEC-3: strtol+endptr en modelo.c

## Estado: CERRADO (2026-08-30)
## Fecha: 2026-08-30

## Problema
`modelo.c` usa `atoi()` y `atof()` para parsear metadatos GGUF. Estas funciones:
- No detectan errores de parseo ("32700abc" → 32700, silenciosamente)
- No distinguen entre "0" (valor válido) y "" (error)
- No verifican overflow
- Violan Manual 4 §2.1 (funciones deben cumplir contrato)

## Ubicación del problema
| Línea | Función | Llamada | Problema |
|-------|---------|---------|----------|
| 736 | `_syn_vocab_tamano` | `atoi(valor)` | "123abc" → 123, no error |
| 815 | `_meta_entero` | `atoi(valor)` | Igual |
| 827 | `_meta_decimal` | `atof(valor)` | "1.2.3" → 1.2, no error |
| 972 | `_bpe_crear` | `atoi(valor)` para bos_id | Igual |
| 974 | `_bpe_crear` | `atoi(valor)` para eos_id | Igual |

## Fix
Reemplazar `atoi(x)` → `strtol(x, &end, 10)` con verificación de `*end != '\0'`
Reemplazar `atof(x)` → `strtod(x, &end)` con verificación de `*end != '\0'`

## Contrato nuevo (Manual 2 §12)
- `requiere: datos_internos != NULL, clave != NULL`
- `garantiza: retorna 0 si clave no encontrada O valor no es entero válido`
- `garantiza: para _meta_decimal, retorna por_defecto si valor no es decimal válido`

## Tests TDD (Manual 3 §12.1, OBL-M7-01)
Test C directo que:
1. Construye InternalData con metadatos problemáticos
2. Llama _syn_vocab_tamano (pública) y verifica retorno
3. Falla ANTES del fix (RED), pasa DESPUÉS (GREEN)

## Aceptación
- `_syn_vocab_tamano("32700abc")` → 0 (no 32700)
- `_syn_vocab_tamano("not_a_number")` → 0
- `_syn_vocab_tamano("32700")` → 32700 (caso normal preservado)
- `_meta_decimal("12.34.56")` → por_defecto
- `_meta_decimal("12.34")` → 12.34f (caso normal preservado)
- tsan sin races

## Cumple
- Manual 2 §12: contratos requiere/garantiza
- Manual 4 §2.1: funciones deben cumplir contrato
- Manual 7 §3: metadatos GGUF parseados correctamente
