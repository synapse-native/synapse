# Plan ME-4: Formateador Nativo (Fase 31.4)

## Manual referenciado
Manual 31 §5 — Módulo 31.4: Formateador Nativo (`synapse fmt`)

## Requisito
- `nucleo/formatter.syn`: formateador que reescribe código según reglas de estilo
- Función `formatear_programa(programa: Programa) -> texto`
- Reglas: indentación 4 espacios, espacios operadores, comas con espacio, líneas vacías entre funciones
- Flags: --check (exit 1), --dry-run (muestra sin escribir)

## Archivos a modificar
- `nucleo/formatter.syn` (nuevo)

## Oráculos
- `pytest tests/unit/ -v` — 111 tests pasan
- `python auditoria/verificar_alineacion.py` — 0 brechas
