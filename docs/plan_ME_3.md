# Plan ME-3: Linter Nativo (Fase 31.3)

## Manual referenciado
Manual 31 §4 — Módulo 31.3: Linter Nativo (`synapse lint`)

## Requisito
- `nucleo/lint.syn`: linter que procesa el AST unificado (`SemNodo[]`) y emite advertencias
- Struct `Advertencia`: tipo, mensaje, linea, columna, archivo
- Función `lint_programa(programa: Programa) -> Lista<Advertencia>`
- 5 reglas: UNUSED_VAR, NO_CONTRACT, INDENT, NAMING, DEAD_CODE

## Archivos a modificar
- `nucleo/lint.syn` (nuevo)

## Oráculos
- `pytest tests/unit/ -v` — 111 tests pasan
- `python auditoria/verificar_alineacion.py` — 0 brechas
