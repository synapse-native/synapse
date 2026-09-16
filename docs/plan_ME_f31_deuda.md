# Plan ME: f31_deuda — Cierre de deuda técnica Fase 31

> **Manual de referencia:** Manual 2 §12, Manual 3 §12, Manual 8 §4.4
> **Fecha:** 2026-09-15
> **Base de verificación:** commit ba2c5ee

---

## Contexto

Tras la corrección de gaps (commit ba2c5ee), quedan 3 deudas técnicas menores:

1. Tests doc-only: no ejecutan lint_archivo/fmt_archivo sobre código real.
2. lint_nombres no está en el dispatcher de lint_programa().
3. Tests de integración CLI inexistentes.

## Requisitos (MTS)

requisito: Manual 2 §12
texto: nucleo/lint.syn debe detectar errores reales en código fuente (lint_archivo retorna Lista<Advertencia>)
implementacion: Test TDD que ejecuta lint_archivo sobre .syn con errores y verifica detección
oraculo: tests/nucleo/test_lint.py

requisito: Manual 2 §12
texto: lint_programa() debe llamar a lint_nombres() para verificar snake_case
implementacion: Agregar lint_nombres al dispatch en lint_programa()
oraculo: tests/nucleo/test_lint.py

requisito: Manual 2 §12
texto: nucleo/formatter.syn debe verificar formato real de archivos (.syn) con verificar_formato()
implementacion: Test TDD que ejecuta verificar_formato sobre .syn y retorna booleano
oraculo: tests/nucleo/test_fmt.py

requisito: Manual 8 §4.4
texto: lockfile parsing debe validar que el hash tiene formato sha256 hex de 64 caracteres
implementacion: Test que verifica que hash inválido es rechazado en axon.lock
oraculo: tests/axon/test_workspace.py
