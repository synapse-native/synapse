# Verificación - ME r323b_gdir_escaping

CUMPLE.

## Cambios

- `nucleo/principal.syn`: la extracción de `_gdir` usa cuatro barras invertidas
  en la fuente Synapse, que el lexer decodifica a `'\\'` en C (un backslash);
  así `strrchr` encuentra el separador tanto en POSIX (`/`) como en Windows
  (`\`) y el PATH del hijo se ajusta correctamente.

## Verificación

| requisito | verificación | resultado |
|---|---|---|
| Manual 9 §6.2 - CUMPLE - bootstrap determinista | `pytest tests/auditoria/test_r323b_gdir_escaping.py` | 1 passed |
| Manual 9 §6.2 - CUMPLE - citas y anclas | `alineacion.py --verificar --me r323b_gdir_escaping` | OK, evidencia `49935b87ae35cf16` |
| Manual 9 §6.2 - CUMPLE - plan/código/oráculo | `contrastar.py --plan docs/plan_ME_r323b_gdir_escaping.md` | PASS |
