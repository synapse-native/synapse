# ME-SEC-5 — Escape completo de string en codegen

## Meta
Que el codegen (`emit_expressions.py`) escape correctamente TODOS los caracteres especiales en literales de cadena, incluyendo `<0x20` y NUL, generando C literals válidos.

## Requisitos

### R1: Escape de NUL
requisito: Manual 2 §4.1
texto: "texto / cadena / string: Cadena UTF-8 segura (longitud + buffer). No termina en \0 internamente"
implementacion: NUL bytes en el valor del literal se escapan como `\x00` en el literal C generado, para que `strlen()` no los trunque.
oraculo: tests/test_string_escape.py

### R2: Escape de caracteres de control (<0x20)
requisito: Manual 2 §2
texto: "caracter_escapado ::= \"\\n\" | \"\\t\" | \"\\r\" | \"\\\\\" | \"\\\"\" | \"\\u\" HEX HEX HEX HEX"
implementacion: Todo carácter con valor < 0x20 (excepto \n, \r, \t que ya se manejan) se escapa como `\xHH`.
oraculo: tests/test_string_escape.py

### R3: Backslash primero (prevenir doble escape)
requisito: Manual 2 §2
texto: "caracter_escapado ::= \"\\\\\" (el backslash se escapa primero)"
implementacion: El orden de reemplazo es: `\` → `\\` primero, luego los demás escapes.
oraculo: tests/test_string_escape.py

### R4: Compilación exitosa con strings especiales
requisito: Manual 2 §2 + Manual 4 §2.1
texto: "Cadena literal válida compila a binario sin warnings ni errores"
implementacion: programa Synapse con NUL/control/comillas/backslash en strings compila y ejecuta sin crash.
oraculo: tests/test_string_escape.py

## Archivos a modificar
- `compilador/generator/emit_expressions.py` (función `expr_a_c`, caso `LiteralCadena`)

## Tests TDD
- `tests/test_string_escape.py` (nuevo)
  - TestBackslashEscape::test_backslash_before_newline
  - TestStringEscapeNul::test_nul_produces_x00
  - TestStringEscapeControlChars::test_all_control_chars_escaped
  - TestCompileValidity::test_c_literal_has_cadenasegura

## Estado: CERRADO (2026-08-31)
