# Verificación — ME r321_weak_darwin

CUMPLE.

## Causa y cambio

Run `45217779214`, job `137843493888` (macos-latest), tras quitar el flag GNU:

```
duplicate symbol '_escribir_linea' in:
    .../synapse_unity.c.o
    /Users/runner/.synapse/cache/runtime_obj/io.o
duplicate symbol '_str_eq' in:
    .../synapse_unity.c.o
    /Users/runner/.synapse/cache/runtime_obj/sistema.o
ld: 23 duplicate symbols
[ME-R2][ERROR] No se genero el ejecutable: synapse_bootstrap.exe
```

El C emitido redefine helpers que ya existen en el runtime; GNU ld lo toleraba
con `--allow-multiple-definition` (gana la primera definición). En darwin la
definición se emite `__attribute__((weak))`, que ld64 resuelve igual sin flags.

- `compilador/generator/emit_declarations.py`: `weak` según `sys.platform`.
- `nucleo/generador/funciones.syn`: `_weak_attr` bajo `#ifdef __APPLE__` en el
  `snprintf` de la firma (etapas S1→S2→S3).
- En win32/ELF el atributo es cadena vacía: C emitido idéntico.

## Requisitos y verificación

| requisito | verificación | resultado |
|---|---|---|
| Manual 9 §6.2 — CUMPLE — generador Python | `pytest tests/auditoria/test_r321_weak_darwin.py` | 3 passed |
| Manual 9 §6.2 — CUMPLE — generador autohospedado | idem | 3 passed |

| check | resultado |
|---|---|
| `build.py --skip-test` (Windows) | S2==S3 `8e9e60f83c39` (sin cambios) |
| `alineacion.py --verificar --me r321_weak_darwin` | OK, evidencia `01820e03d39931d7` |
| `contrastar.py --plan docs/plan_ME_r321_weak_darwin.md` | PASS |

## Limitación declarada

El enlace real de macOS lo valida `Release Matrix` tras el push; la cadena
S1→S2→S3 en darwin no se puede reproducir en Windows.
