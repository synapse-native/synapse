# Verificación — ME D1_2b (weak/scope cleanup nativo)

CUMPLE.

## Cambios

- `nucleo/generador/emision_c.syn`: separa el mapeo de tipos RC/ARC
  (`void*`) del de weak (`WeakRef`) y copia `_G_scope_vars_kind[_wi]` al
  compactar el scope para que el cleanup de `débil<T>` use `rc_weak_release`.
- `nucleo/generador/orquestador.syn`: el header nativo emite `RcHeader`,
  `WeakRef` y los externs `rc_alloc`, `rc_decrementar`, `arc_alloc`,
  `arc_decrementar`, `_syn_rc_crear`, `_syn_rc_decrement`, `_syn_arc_crear`,
  `_syn_arc_decrement`, `rc_weak_ref` y `rc_weak_release`.
- `nucleo/generador/nodos_flujo.syn`: una variable `WeakRef` inicializada en
  `nulo` emite `((WeakRef){0})`.
- `nucleo/generator.syn`: regenerado con `nucleo/_rebuild_generator.py`.
- `tests/auditoria/test_d1_2b_scope_cleanup_kind.py`: oráculo estático del
  mapeo, la compactación, el header y la inicialización de `WeakRef`.

## Verificación

| requisito | verificación | resultado |
|---|---|---|
| Manual 2 §5.1 — CUMPLE — mapeo weak y compactación de `kind` | `pytest tests/auditoria/test_d1_2b_scope_cleanup_kind.py -q` | 5 passed |
| Manual 2 §5.1 — CUMPLE — cleanup RC por scope | `pytest tests/syquex/test_rc_scope_cleanup.py tests/syquex/test_rc_cleanup.py -q` | 4 passed |
| Manual 4 §4.2 — CUMPLE — weak/cleanup y paridad nativa | `pytest tests/syquex/test_weak.py tests/syquex/test_cleanup_blocks.py tests/integration/test_a23_parity.py tests/integration/test_f23_e2e.py -q` | 32 passed |
| Manual 4 §4.2 — CUMPLE — codegen embebido D-F1 | `pytest tests/integration/test_codegen_embebido_d_f1d.py tests/integration/test_codegen_embebido_d_f1_4.py -q` | 17 passed |
| Manual 2 §8.2 — CUMPLE — generador reconciliado | `build.bat bootstrap-full` | S2==S3, diff 0 bytes |
| Alineación manual↔código | `alineacion.py --verificar --me D1_2b` | PASS, evidencia `97eb6da8b4bc84ab` |
| MTS | `contrastar.py --plan docs/plan_ME_D1_2b.md` | PASS |
| Auditoría de alineación | `verificar_alineacion.py` | SIN BRECHAS |
| Contratos | `verificar_contratos.py` | 642 auditadas, 81 deuda, 0 nuevas |
| Código muerto | `verificar_codigo_muerto.py` | 0 muertas, 0 nuevas |

Suite dirigida completa: **58 passed** en 49.80 s.

## Notas

- `tests/fixtures/test_a23_parity.c` se generó durante la suite y se revirtió;
  no forma parte del cambio.
- No se cierra D-1: este ME cubre sólo el punto 1 (tipo/cleanup de `débil<T>` y
  compactación de `kind`).
