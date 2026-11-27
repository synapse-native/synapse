# Verificación — ME r299_codigo_muerto

CUMPLE (con un hallazgo preexistente registrado, H-R299-1).

## Requisitos del plan y su verificación

| requisito | verificación | resultado |
|---|---|---|
| Manual 1 §7.4 — CUMPLE — DoD sin código muerto | `python auditoria/verificar_codigo_muerto.py --estricto` | 346 funciones en 32 módulos, 0 muertas |
| Manual 1 §7.4 — suite sin regresiones | `pytest tests/auditoria/test_codigo_muerto.py` | 4 passed |
| Manual 1 §7.4 — corpus de backends intacto | `pytest tests/integration/test_backend_10.py` | 22 passed |
| Manual 1 §7.4 — módulos del build compilan | `pytest tests/nucleo/test_modulos_compilan.py` | green |
| Manual 1 §6 / Manual 9 §6.2 — bootstrap determinista | `python build.py --skip-test` | S2==S3 `f3ad54ee8861`, 2136557 bytes |
| Manual 2 §5.1 — CUMPLE — contratos conservados | revisión de `cache.syn`/`formatter.syn` + oráculo | CUMPLE |
| Manual 1 §7.1 — estilo | `synapse fmt --check nucleo/cache.syn` | rc=0 |
| Gate de alineación | `python auditoria/verificar_alineacion.py` | 0 brechas |
| Encoding (Manual 2 §1.2) | `python auditoria/verificar_encoding.py --estricto` | OK, 2373 archivos |
| Gate MTS | `python auditoria/contrastar.py --plan docs/plan_ME_r299_codigo_muerto.md` | PASS (2 requisitos, oráculo ejecutado) |
| Expediente | `python auditoria/alineacion.py --verificar --me r299_codigo_muerto` | OK, evidencia `auditoria/evidencia/c6b794309fe9df2c.json` |

## NO CUMPLE / deuda registrada

- **H-R299-1** (preexistente, no de este ME): `test_nucleo_formateado` marca
  `nucleo/generator.syn`, `nucleo/lint.syn` y `nucleo/lsp_v3.syn` como mal
  formateados con el binario actual; el contenido de HEAD de esos archivos
  falla igual. Resolución asignada al ME `r300_formatter_comentarios`.
