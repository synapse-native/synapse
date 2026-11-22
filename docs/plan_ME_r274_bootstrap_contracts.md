# Plan ME r274_bootstrap_contracts — desbloqueo del build + contratos válidos

Corrige dos desviaciones detectadas al desbloquear el build de `nucleo/principal.syn`
(R274): (a) el bloque del subcomando `observability` estaba escrito como C crudo
sin `asm(...)`, rompiendo el lexer; (b) cinco cláusulas de contrato usaban
sintaxis inválida (`=>`, `->`, `&&`, `garantiza:` vacío, precondiciones falsas)
que el lexer/parser no aceptan según Manual 2 §5.1.

## Requisito 1 — contratos con semántica formal válida

requisito: Manual 2 §5.1
texto: **`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas.
implementacion: Se reescriben las cláusulas inválidas a gramática válida del Manual 2 (§5.1): implicación `A => B` como `¬A o B`, `->` como `.`, `&&` como `y` (T_AND), y se eliminan/neutralizan (`verdadero`) `garantiza:` vacíos y precondiciones imposibles sobre parámetros por valor (`est != nulo`, entradas nulas/vacías), en nucleo/analizador_semantico.syn, nucleo/generator.syn y nucleo/generador/emision_c.syn.
oraculo: tests/integration/test_contracts.py

## Requisito 2 — subcomandos del CLI emiten desde el binario sin romper el lexer

requisito: Manual 8 §4.1
texto: `synapse build <archivo>` | Compila el archivo (`.syn` o `.syq`) a binario.
implementacion: El despacho del subcomando `observability` en nucleo/principal.syn se envuelve en `asm("...")` (con `inseguro:`), de modo que el compilador de Synapse pueda lexear/parsear `nucleo/principal.syn` y producir el binario `synapse`, en lugar de interpretar C crudo como fuente.
oraculo: tests/auditoria/test_r274_observability_asm.py
