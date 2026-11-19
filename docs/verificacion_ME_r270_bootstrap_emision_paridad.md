# Verificación ME r270 — paridad bootstrap

- Manual 1 §6 CUMPLE: el oráculo compara SHA-256, tamaño y frescura; el enlace
  nativo usa `-static` en win32 (H-R252-4) y S2/S3 coinciden en
  `30C07EF61C5F25A7…` (2.559.482 B).
- Manual 9 §6.2 CUMPLE: job `bootstrap` de CI ejecuta el oráculo; `--estricto`
  confirma que `synapse.exe` y `dist/bin/synapse.exe` corresponden a S2.
- Manual 9 §6.1 CUMPLE: `build.py` aborta si el sello falla; H-R252-1 se
  explicó como stage2 stale (2.077.570 B) y H-R252-4 quedó resuelto con
  `-static`.

Evidencia: `tests/auditoria/test_r270_bootstrap_paridad.py`.
