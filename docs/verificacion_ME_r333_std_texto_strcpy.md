# Verificación — ME r333_std_texto_strcpy

CUMPLE.

| requisito | verificación | resultado |
|---|---|---|
| Manual 2 §5.1 — CUMPLE — `strcpy_f` con requiere/garantiza | `pytest tests/unit/test_std_contracts.py -q` | 20 passed |
| Manual 2 §5.1 — CUMPLE — API histórica de texto | `pytest tests/opensyn -q` | 137 passed, 1 skipped |
| Manual 2 §5.1 — CUMPLE — unit completa | `pytest tests/unit -q` | 515 passed, 2 skipped |
| Manual 2 §5.1 — CUMPLE — compila con `std.texto` | `python main.py /tmp/t_texto.syn` | rc=0; ejecuta rc=0 |
| Manual 2 §5.1 — CUMPLE — alineación | `alineacion.py --verificar --me r333_std_texto_strcpy` | PASS, evidencia `8e2cf4f034bd751b` |
| MTS | `contrastar.py --plan docs/plan_ME_r333_std_texto_strcpy.md` | PASS |
| Contratos | `verificar_contratos.py` | 642 auditadas, 81 deuda, 0 nuevas |
| Código muerto | `verificar_codigo_muerto.py` | 0 nuevas |

## Infraestructura de tests

- Rutas de Python y proyecto portables (`sys.executable`, `Path(__file__)`).
- `tests/conftest.py` enlaza `-lws2_32` sólo en Windows.
- `auditoria/verificar_suite.py --medir` usa `xdist --dist loadfile`.
- `ci-tests.yml` construye el nativo y ejecuta la suite una sola vez (release,
  paralela), en lugar de dos corridas seriales por job.
