# Plan ME — Native Codegen: OpBinaria text detection fix

## Requisito
Manual 1 §3.1: El compilador nativo debe generar C paridad con el compilador Python.
Manual 2 §4.1: CadenaSegura debe manejarse correctamente en expresiones concatenadas.

## Problema
Cuando el operador `+` (tipo 30) tiene un lado que es otro `OpBinaria` con `+`,
el codegen nativo no detecta que la sub-expresión izquierda produce texto,
y envuelve el resultado en `entero_a_texto()` innecesariamente.

## Ejemplo
```synapse
texto2 = "A" + entero_a_texto(10) + "B"
```
Genera C incorrecto:
```c
concat(entero_a_texto(concat(A, entero_a_texto(10))), B)  // WRONG
```
Debería generar:
```c
concat(concat(A, entero_a_texto(10)), B)  // CORRECT
```

## Implementación
Agregar detección de `OpBinaria` con operador 30 (+) en la sección `_ix_txt`/`_dx_txt`
de `_oo_expr_a_c()` en:
- `nucleo/generator.syn` (líneas ~740-810)
- `nucleo/generador/nodos_flujo.syn` (líneas equivalentes)

Cuando `_nx0` es un `OpBinaria` con `operador->tipo == 30`:
- Si su izquierdo es `LiteralCadena` o es texto → `_ix_txt = 1`
- Si su derecho es `LiteralCadena` o es texto → `_ix_txt = 1`
- Análogo para `_nx1`

## Oráculo
- `test_concat_debug.syn` compila con ambos compiladores y produce output idéntico
- `test_battle.syn` compila con nativo sin errores de tipo
- Bootstrap S2 == S3 byte-identical
