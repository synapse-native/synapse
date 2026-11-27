# Verificación ME r271 — manuales canónicos

- Manual 2 §1.2 CUMPLE: `verificar_manuales.py --todo` valida UTF-8 sin BOM,
  U+FFFD, C1 y doble codificación sobre `docs/`.
- Manual 1 §7.4 CUMPLE: `.indice.json` incluye Manual 31/32 con nombre canónico
  y anexos como apoyo citable; `--indice` detecta cualquier desactualización.
- Manual 9 §6.1 CUMPLE: gate de nombres/citas cableado en pre-commit y CI;
  D-MAN-1/2/3 ratificadas el 2026-11-19 (opción A).

Evidencia: `tests/auditoria/test_verificar_manuales.py` (7/7) y
`tests/auditoria/test_manuales_canonicos_r271.py` (2/2).
