# Plan ME-5: CI/CD Reporting (Fase 31.5)

## Manual referenciado
Manual 31 §6 — Módulo 31.5: CI/CD Reporting Mejorado

## Requisito
- `nucleo/reports.syn`: generación de reportes JUnit XML, HTML coverage, JSON
- Función `generar_junit(resultados: Lista<ResultadoTest>) -> texto`
- Función `generar_json(resultados: Lista<ResultadoTest>) -> texto`
- Función `generar_coverage(cubiertas: entero, total: entero) -> texto`
- Estructuras: ResultadoTest, ResultadoSuite, ResultadoGlobal

## Archivos a modificar
- `nucleo/reports.syn` (nuevo)

## Oráculos
- `pytest tests/unit/ -v` — 111 tests pasan
- `python auditoria/verificar_alineacion.py` — 0 brechas
