# Verificación — ME r331_ci_verde

CUMPLE.

## Cambios

- `std/texto.syn`: restaura la única definición pública de `cmp_texto(a, b)`
  con `requiere:`/`garantiza:`; `nucleo/lsp_v3.syn` vuelve a compilar sin los
  80 usos de un símbolo indefinido.
- `nucleo/analizador_semantico.syn`: `AnalizadorSemanticoEst.codigo_error`
  registra el primer código semántico (19 = argumentos inválidos).
- `nucleo/principal.syn`: el pipeline nativo mapea 19 → rc=7 y deja el resto
  de errores semánticos en 10, con paridad del oráculo de aridad.
- `nucleo/generador/*.syn` (8 archivos): se reinyectan los 30 contratos que el
  combinado anterior tenía y los submódulos no; `nucleo/generator.syn` se
  regenera desde esas fuentes.
- `tests/auditoria/test_r331_lsp_compila.py` (nuevo): oráculo de la regresión.
- `tests/auditoria/test_oraculos_r256_debugger.py`: el helper elige
  `synapse_stage2.exe` cuando el PE de la raíz no es ejecutable en POSIX.

## Verificación

| requisito | verificación | resultado |
|---|---|---|
| Manual 2 §5.1 — CUMPLE — `cmp_texto` contratada | `main.py nucleo/lsp_v3.syn --check --no-emit` | rc=0, 0 símbolos indefinidos |
| Manual 2 §8.1 — CUMPLE — primer código semántico | `test_oraculos_r27_ctor_aridad.py` | 4 passed, rc=7 |
| Manual 2 §8.2 — CUMPLE — generador reconciliado | `test_r301_generator_reconciliacion.py` | 4 passed |
| Manual 8 §3.4 — CUMPLE — debugger multiplataforma | `test_oraculos_r256_debugger.py` | 3 passed |

| check | resultado |
|---|---|
| `contrastar.py --plan docs/plan_ME_r331_ci_verde.md` | PASS (3 requisitos) |
| `pytest` (oráculos + backend) | 35 passed |
| `verificar_contratos.py` | 642 auditadas, 81 deuda, 0 nuevas |
| `verificar_codigo_muerto.py` | 0 muertas, 0 nuevas |
| `verificar_alineacion.py` | SIN BRECHAS |
| `verificar_manuales.py --todo` | OK |
| `verificar_encoding.py` | 2586 archivos, 0 defectos |
| `build.py --skip-test` | S2==S3 `2293eaab681d` |
| `oraculo_r252 --estricto` | PASS |
| `alineacion.py --verificar --me r331_ci_verde` | evidencia `a29e919e1c21cf61` |
