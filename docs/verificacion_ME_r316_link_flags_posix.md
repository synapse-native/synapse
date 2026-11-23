# Verificación — ME r316_link_flags_posix

CUMPLE.

## Requisitos del plan y su verificación

| requisito | verificación | resultado |
|---|---|---|
| Manual 9 §6.2 — CUMPLE — enlace del bootstrap por plataforma | `pytest tests/auditoria/test_r316_link_flags_posix.py` | 3 passed |
| Manual 9 §6.2 — CUMPLE — Axon/librerías/sanitizadores | idem | 3 passed |

## Causa y cambio

Run `45179123189`, job `release_matrix (ubuntu-latest, linux_x64)`:

```
/usr/bin/x86_64-linux-gnu-ld.bfd: unrecognized option '--no-insert-timestamp'
[Synapse] ERROR: GCC fallo con codigo 256
[build][ERROR] rc=5: ['./synapse_stage1.exe', 'nucleo/principal.syn']
```

- `nucleo/principal.syn` emitía el comando de enlace con
  `-Wl,--no-insert-timestamp -Wl,--stack,8388608` y `-lws2_32` fijos. Ahora esos
  fragmentos viven en `_win_ld`/`_win_libs` bajo `#ifdef _WIN32`; en Windows el
  comando resultante es byte-idéntico (mismo orden y espacios).
- `nucleo/generador/compilar.syn` (enlace del Axon) tenía el mismo patrón y se
  corrigió igual.
- `librerias/compiler/generator.c` bifurca el `snprintf` del enlace con
  `#ifdef _WIN32` / `#else` (sin `--no-insert-timestamp` ni `-lws2_32` en POSIX).
- `cli.py` agrega `-lws2_32` a los enlaces con sanitizadores sólo si
  `sys.platform == "win32"`.

## Otros checks

| check | resultado |
|---|---|
| `pytest tests/auditoria/test_r316_link_flags_posix.py` | 3 passed |
| `pytest test_r313_link_flags + test_r315_posix_portabilidad` | 6 passed |
| `build.py --skip-test` (Windows) | S2==S3, sha `9382d8d9c234` |
| `alineacion.py --verificar --me r316_link_flags_posix` | OK, evidencia `4d6c9a16972af6fc` |
| `contrastar.py --plan docs/plan_ME_r316_link_flags_posix.md` | PASS (2/2) |

## Limitación declarada

El enlace real en Linux/macOS lo valida la matriz de CI tras el push: aquí sólo
se verificó que Windows sigue enlazando (build determinista S2==S3) y que ningún
flag de MinGW queda fuera de una rama Windows (oráculo estático).
