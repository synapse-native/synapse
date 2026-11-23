# Plan de Micro-Entregable r321_weak_darwin

## Objetivo

Séptima vuelta sobre `Release Matrix`. Con r320 el linker ya no ve el flag GNU,
pero el enlace de macOS destapa el motivo por el que ese flag existía: el C
emitido redefine 23 símbolos que también viven en el runtime (run `45217779214`,
job `137843493888`):

```
duplicate symbol '_escribir_linea' in:
    .../synapse_unity.c.o
    /Users/runner/.synapse/cache/runtime_obj/io.o
duplicate symbol '_str_eq' in:
    .../synapse_unity.c.o
    /Users/runner/.synapse/cache/runtime_obj/sistema.o
ld: 23 duplicate symbols
```

GNU ld toleraba los duplicados con `--allow-multiple-definition` (gana la
primera definición). En darwin se consigue el mismo resultado emitiendo las
definiciones del fuente como `__attribute__((weak))`: clang/ld64 aceptan varias
definiciones weak y resuelven a la primera. En Windows/ELF el atributo es vacío,
así que el C emitido y el hash del bootstrap no cambian.

Linux x64/ARM64 y Windows siguen fallando solo en la firma Ed25519 (H-R276-2).

## Requisito 1 — el generador Python emite weak en darwin

requisito: Manual 9 §6.2
texto: "La suite de tests completa en cada target."
implementacion: `compilador/generator/emit_declarations.py` calcula `weak` con `sys.platform == "darwin"` y lo intercala en la firma de `visitar_funcion`; fuera de darwin la línea emitida es idéntica.
oraculo: tests/auditoria/test_r321_weak_darwin.py

## Requisito 2 — el generador autohospedado hace lo mismo

requisito: Manual 9 §6.2
texto: "La suite de tests completa en cada target."
implementacion: `nucleo/generador/funciones.syn` agrega `_weak_attr` (vacío, `__attribute__((weak))` bajo `#ifdef __APPLE__`) y lo inserta en el `snprintf` de la firma, para que las etapas S1→S2→S3 enlacen igual.
oraculo: tests/auditoria/test_r321_weak_darwin.py

## Evidencia

| check | resultado |
|---|---|
| `pytest tests/auditoria/test_r321_weak_darwin.py` | 3 passed |
| `build.py --skip-test` (Windows) + `S2==S3` | OK, sha `8e9e60f83c39` (idéntico) |
| `alineacion.py --verificar --me r321_weak_darwin` | OK (`01820e03d39931d7`) |
| `contrastar.py --plan docs/plan_ME_r321_weak_darwin.md` | PASS |
| CI `Release Matrix` macOS tras el push | pendiente de corrida |
