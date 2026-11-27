# Plan de Micro-Entregable r328_contratos_struct_nulo

## Objetivo

Restaurar la compilación nativa (stage1 → stage2 → stage3) eliminando
contratos `requiere`/`garantiza` que no son expresiones booleanas válidas en C:
comparaciones `!= nulo` sobre structs pasados por valor y tautologías
`_resultado_ == _resultado_` en funciones que retornan structs.

El barrido r307/r308 introdujo estos contratos en `nucleo/` y `std/`; stage1
los toleraba, pero stage2 emitía `assert` con operandos incompatibles
(`invalid operands to binary !=`) y el build fallaba.

## Requisito 1 - contratos con expresiones booleanas válidas

requisito: Manual 2 §5.1
texto: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
implementacion: En los archivos de producción modificados se eliminaron comparaciones `!= nulo` sobre parámetros/valores struct (no punteros) y las tautologías `_resultado_ == _resultado_`; se conservaron los contratos válidos sobre punteros, listas y escalares. Cada archivo conserva su ancla `// cumple Manual X §Y`.
oraculo: tests/auditoria/test_r328_contratos_struct_nulo.py

## Requisito 2 - build determinista

requisito: Manual 9 §6.2
texto: "La verificación del bootstrap (diff 0 bytes)."
implementacion: `python build.py --skip-test` completa stage1, stage2 y stage3 con `S2==S3` y deja `synapse_bootstrap.exe` y `principal.exe` actualizados.
oraculo: tests/auditoria/test_r328_contratos_struct_nulo.py
