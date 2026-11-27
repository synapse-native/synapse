# Plan ME f32_4_pipeline_multiagente — Pipeline Multi-Agente Optimizado

## Requisito 1: Estructuras del pipeline
requisito: Manual 6 §1.1 — AST canónico unificado como representación semántica
texto: "El ecosistema Synapse se basa en un Árbol de Sintaxis Abstracta (AST) canónico y unificado denominado SemNodo[]"
implementacion: Estructuras ContextoPipeline, ResultadoPipeline, ModoOperacion
oraculo: tests/opensyn/test_pipeline_multiagente.py

## Requisito 2: Pipeline principal con 5 fases
requisito: Manual 2 §5.1 — Contratos requiere/garantiza
texto: "requiere: Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
implementacion: ejecutar_pipeline() con Explorer determinista → Architect determinista → Coder LLM → Reviewer LLM → Fixer LLM condicional
oraculo: tests/opensyn/test_pipeline_multiagente.py

## Requisito 3: Construcción de prompts para cada rol
requisito: Manual 6 §1.1 — AST canónico unificado
texto: "El ecosistema Synapse se basa en un Árbol de Sintaxis Abstracta (AST) canónico y unificado denominado SemNodo[]"
implementacion: construir_prompt_coder(), construir_prompt_reviewer(), construir_prompt_fixer()
oraculo: tests/opensyn/test_pipeline_multiagente.py

## Requisito 4: Modos de operación
requisito: Manual 6 §1.1 — AST canónico unificado
texto: "El ecosistema Synapse se basa en un Árbol de Sintaxis Abstracta (AST) canónico y unificado denominado SemNodo[]"
implementacion: ejecutar_con_modo() con Ask, Plan, Code, Debug, Orchestrator
oraculo: tests/opensyn/test_pipeline_multiagente.py

## Requisito 5: Conteo de inferencias y métricas
requisito: Manual 2 §5.1 — Contratos requiere/garantiza
texto: "requiere: Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
implementacion: ResultadoPipeline con num_inferencias, tiempo_total_ms
oraculo: tests/opensyn/test_pipeline_multiagente.py
