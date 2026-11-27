# Plan ME f32_5_verificacion_aot — Verificación AOT con Auto-Refutación

## Requisito 1: Estructuras de verificación
requisito: Manual 6 §1.1 — AST canónico unificado como representación semántica
texto: "El ecosistema Synapse se basa en un Árbol de Sintaxis Abstracta (AST) canónico y unificado denominado SemNodo[]"
implementacion: Estructuras CasoLimite, ResultadoCaso, Verificacion
oraculo: tests/opensyn/test_verificacion_aot.py

## Requisito 2: Verificación de caso límite con timeout
requisito: Manual 2 §5.1 — Contratos requiere/garantiza
texto: "requiere: Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
implementacion: verificar_caso_limite() con compilación AOT 30s timeout, ejecución 5s timeout
oraculo: tests/opensyn/test_verificacion_aot.py

## Requisito 3: Generación automática de casos límite
requisito: Manual 6 §1.1 — AST canónico unificado
texto: "El ecosistema Synapse se basa en un Árbol de Sintaxis Abstracta (AST) canónico y unificado denominado SemNodo[]"
implementacion: generar_casos_limite() parsea AST y genera casos por tipo (entero, texto, decimal)
oraculo: tests/opensyn/test_verificacion_aot.py

## Requisito 4: Verificación completa con auto-refutación
requisito: Manual 2 §5.1 — Contratos requiere/garantiza
texto: "requiere: Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
implementacion: verificar_codigo_generado() orquesta compilación + contratos + casos límite
oraculo: tests/opensyn/test_verificacion_aot.py
