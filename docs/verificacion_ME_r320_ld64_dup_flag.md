# Verificación — ME r320_ld64_dup_flag

CUMPLE.

## Causa y cambio

Run `45213218955`, job `137827294530` (macos-latest):

```
ld: unknown options: --allow-multiple-definition
collect2: error: ld returned 1 exit status
[!] Link modular fallo (rc=1) — intentando unity fallback
ld: unknown options: --allow-multiple-definition
```

El flag es de GNU ld y estaba en las dos rutas de enlace (modular y unity).

- `pipeline.py`: `_ld_dup_flag` vacío en darwin; `link_align` del enlace de
  caché con el mismo criterio; en darwin se limpia `_module_asts` para ir al
  unity (los helpers duplicados desaparecen).
- `nucleo/principal.syn`: `_dup_flag` con `#ifdef __APPLE__` vacío; la cola de
  enlace usa `%s%s` (`_win_libs`, `_dup_flag`). En win32 el comando queda igual.

## Requisitos y verificación

| requisito | verificación | resultado |
|---|---|---|
| Manual 9 §6.2 — CUMPLE — macOS enlaza el bootstrap | `pytest tests/auditoria/test_r320_ld64_dup_flag.py` | 4 passed |
| Manual 9 §6.2 — CUMPLE — Windows sigue determinista | `build.py --skip-test` | S2==S3 `8e9e60f83c39` |

| check | resultado |
|---|---|
| `alineacion.py --verificar --me r320_ld64_dup_flag` | OK, evidencia `805b73291a740ffd` |
| `contrastar.py --plan docs/plan_ME_r320_ld64_dup_flag.md` | PASS |

## Limitación declarada

Sin toolchain darwin local: el enlace real de macOS lo decide `Release Matrix`.
Se verificó en Windows que el hash cambió de forma determinista (S2==S3) y que
el camino win32 conserva el flag GNU.
