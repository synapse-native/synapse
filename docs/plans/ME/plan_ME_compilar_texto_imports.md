# Plan ME: Fix compilar_texto() resolución de imports

## Problema

`tests/conftest.py` `compilar_texto()` hace lexer→parser→analizador semántico SIN resolver
imports. Cuando un test usa `importar std.federated` (o cualquier `importar std.*`), las
funciones importadas nunca entran al AST → "Función 'X' no definida" en el analizador
semántico.

## Requisitos

requisito: Manual 1 §7.2
texto: "Todo cambio debe pasar la suite completa de pruebas. Aprobación del 100% de los tests
  unitarios, de integración y fuzzing sin regresiones."
implementacion: el fix a `compilar_texto()` debe preservar el comportamiento actual para
  tests que NO usan imports, y habilitar resolución de imports para tests que SÍ los usan.
  Regresión verificada contra los 44 archivos que usan `compilar_texto()`.
oraculo: tests/integration/test_ownership_10.py (21/21 debe seguir pasando)

requisito: Manual 2 §10.1
texto: "Categorías de error: ERR_LEX_*, ERR_SYNTAX_*, ERR_SEM_*, ERR_MEM_*"
implementacion: preservar el mapeo de errores léxicos específicos (ERR_INDENT_INVALID,
  ERR_LANG_MISSING, ERR_LEX_CHAR_UNEXPECTED) que el mapeo actual de `compilar_texto()`
  provee y que el pipeline genérico no reproduce.
oraculo: tests/integration/test_diagnostics.py

requisito: Manual 2 §10.2
texto: "El compilador nunca debe detenerse en el primer error; debe continuar analizando
  para detectar tantos errores como sea posible."
implementacion: usar `pipeline.compilar_desde_texto()` que resuelve imports y reporta
  múltiples errores, seguido de `AnalizadorSemantico` para detección de errores de
  ownership/tipos.
oraculo: tests/integration/test_ownership_10.py

## Cambios propuestos

| Archivo | Cambio |
|---|---|
| `tests/conftest.py` | `compilar_texto()`: mantener mapeo léxico, agregar `pipeline.compilar_desde_texto()` + `AnalizadorSemantico` |

## Impacto

- 44 archivos usan `compilar_texto()`
- 27 archivos usan `importar std.*`
- Regresión potencial en tests que dependen del comportamiento actual

## Validación obligatoria (Manual 1 §7.2)

1. `python -m pytest tests/unit/ -v` — 0 regresiones
2. `python -m pytest tests/integration/test_ownership_10.py -v` — 21/21
3. `python -m pytest tests/integration/test_diagnostics.py -v` — 0 regresiones
4. `python -m pytest tests/integration/test_federated_*.py -v` — verificar mejora
5. `python auditoria/verificar_alineacion.py` — 0 brechas
6. `python auditoria/contrastar.py --plan docs/plan_ME_compilar_texto_imports.md` — gate

## Estado

PENDIENTE DE APROBACIÓN DEL ARQUITECTO
