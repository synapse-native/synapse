# Plan ME r219_verificacion_aot

Origen: `ROADMAP.md` Fase 32.5 - Verificación AOT con auto-refutación.

## Requisito 1 - validación sintáctica con --check

requisito: `Manual 7 §4.2` - validación del código generado antes de mostrarlo.

texto: "**Validación (paso crítico):** El LSP toma el código generado y ejecuta el compilador de Synapse/Syquex en modo `--check` (solo validación, sin generar binario)."

implementacion: `opensyn/verificacion_aot.syn` valida el código con `synapse check --no-emit` y timeout de 30 s antes de generar los casos límite; si falla, devuelve `err` sin ejecutar nada.

oraculo: tests/integration/test_verificacion_aot_e2e.py

## Requisito 2 - bucle de validación y corrección

requisito: `Manual 7 §6.3` - bucle de validación y corrección automática.

texto: "Dado que OpenSyn no es perfecto y puede generar código con errores sintácticos o semánticos, se implementa un **bucle de validación y corrección automática** orquestado por el LSP"

implementacion: `verificar_codigo_generado` genera hasta 5 casos límite, los compila y ejecuta con timeouts de 30 s/5 s, y agrega el estado de cada caso a `Verificacion`; los fallos se reportan sin abortar el proceso.

oraculo: tests/integration/test_verificacion_aot_e2e.py

## Requisito 3 - contratos públicos

requisito: `Manual 2 §5.1` - contratos `requiere`/`garantiza` en funciones públicas.

texto: "`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."

implementacion: las funciones públicas de `opensyn/verificacion_aot.syn` declaran contratos booleanos; `verificar_contratos` comprueba que cada función generada tenga `requiere:` y `garantiza:` antes de auto-refutar.

oraculo: tests/opensyn/test_verificacion_aot.py

## Requisito 4 - AST canónico compartido

requisito: `Manual 6 §1.1` - AST canónico y unificado.

texto: "El ecosistema Synapse se basa en un **Árbol de Sintaxis Abstracta (AST) canónico y unificado** denominado `SemNodo[]`."

implementacion: la verificación AOT consume el código generado por el pipeline que ya opera sobre `SemNodo[]`; `generar_casos_limite` recorre declaraciones de función y tipos sin introducir un segundo parser semántico.

oraculo: tests/opensyn/test_verificacion_aot.py
