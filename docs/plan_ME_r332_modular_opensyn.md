# Plan de Micro-Entregable r332_modular_opensyn

## Objetivo

Cerrar H-R331-1: el build modular de `opensyn/principal.syn` fallaba en CI
porque `longitud(texto)` se usaba sin prototipo (gcc C99+ lo rechaza) y
`longitud(tensor)` se emitía como una llamada sin firma C. Además, el smoke de
release en Linux/macOS no encontraba el ejecutable porque el compilador usa
`<base>.exe` también en POSIX.

## Requisito 1 - prototipo verificable de longitud(texto)

requisito: Manual 2 §5.1
texto: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
implementacion: `compilador/generator/generator.py` emite `int64_t longitud(CadenaSegura)` en `_synapse_shared.h`; `_modelo.c` deja de compilar con declaración implícita y el build modular enlaza `_texto.c` con `_modelo.c`.
oraculo: tests/auditoria/test_oraculos_opensyn_exe.py

## Requisito 2 - longitud(tensor) con tipo C real

requisito: Manual 2 §12
texto: "| Contratos requiere/garantiza | `pytest tests/integration/test_contracts.py -v` | 100% pass |"
implementacion: `compilador/generator/emit_expressions.py` traduce `longitud(tensor)` a `filas * columnas`, en vez de una llamada `longitud(tensor)` sin firma; los contratos de `std/modelo.syn` y `std/tensor.syn` quedan tipados.
oraculo: tests/auditoria/test_oraculos_opensyn_exe.py

## Requisito 3 - smoke POSIX acepta la salida .exe

requisito: Manual 9 §6.1
texto: "□ **Instalador unificado**: probado en sistemas limpios (sin instalación previa) y funciona correctamente."
implementacion: `scripts/verificar_release_limpio.py` busca `<fuente>` y `<fuente>.exe` en POSIX, ejecuta la que exista y limpia ambas; el job `smoke_release_limpio` de Linux deja de fallar por nombre de salida.
oraculo: tests/auditoria/test_r276_release_limpio.py
