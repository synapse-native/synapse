# Verificación — ME r330_contratos_wasm

CUMPLE.

## Cambios

- `nucleo/wasm_backend.syn`: los 158 comentarios/separadores `#` pasan a `//`
  (se conserva `#lang: es`); se sacan los bloques de contrato de 4 firmas
  multilínea; se corrigieron `texto(...)` → `entero_a_texto(...)` /
  `decimal_a_texto(...)` y las variables `linea`/`linea2` sin `let`; las 83
  funciones públicas declaran `requiere:` con invariantes reales
  (`est.nivel_indentacion >= 0`, `<texto>.longitud >= 0`) y conservan su
  `garantiza:`.
- `nucleo/diagnostics.syn`: se eliminan `resumen_errores` y `contar_errores`,
  sin referencias en producto, tests ni docs (Manual 1 §7.4).
- `docs/gobernancia/mapa_alineacion.md`: entrada precisa para
  `nucleo/wasm_backend.syn` (Manual 2 §1.3, §5.1, §12).
- `auditoria/contratos_baseline.txt`: 194 → 111 funciones (83 de wasm).
- `tests/auditoria/test_r330_contratos_wasm.py` (nuevo): oráculo del ME.

## Verificación

| requisito | verificación | resultado |
|---|---|---|
| Manual 2 §1.3 — CUMPLE — comentarios `//` | lexer + `test_sin_comentarios_invalidos` | 0 `#` fuera de `#lang` |
| Manual 2 §5.1 — CUMPLE — contratos booleanos | parse + semántico + generador | 0 errores, 83 `requiere:` / 83 `garantiza:`, 86 `assert_contrato` |
| Manual 2 §12 — CUMPLE — prueba de contratos | `pytest tests/integration/test_contracts.py` | 5 passed |
| Manual 1 §7.4 — CUMPLE — cero código muerto | `verificar_codigo_muerto.py` | 0 muertas, 0 nuevas |

| check | resultado |
|---|---|
| `contrastar.py --plan docs/plan_ME_r330_contratos_wasm.md` | PASS (3 requisitos) |
| `pytest tests/auditoria/test_r330_contratos_wasm.py -q` | 7 passed |
| `pytest tests/integration/test_backend_10.py -q` | 22 passed |
| `verificar_contratos.py` | 672 auditadas, 111 deuda, 0 nuevas |
| `verificar_codigo_muerto.py` | 0 muertas |
| `verificar_encoding.py` | 2580 archivos, 0 defectos, 0 NUL, 0 BOM nuevos |
| `verificar_suite.py` | 3201 tests, 246 skips, sin altas |
| `verificar_alineacion.py` | SIN BRECHAS |
| `alineacion.py --verificar --me r330` | evidencia `c899ab0edd87587e` |
