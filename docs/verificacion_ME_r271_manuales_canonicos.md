# Verificación ME r271 — manuales canónicos

- Manual 2 §1.2 CUMPLE: `verificar_manuales.py --todo` valida UTF-8 sin BOM,
  U+FFFD, C1 y doble codificación sobre `docs/`.
- Manual 1 §7.4 CUMPLE: `.indice.json` incluye Manual 31/32 (alias) y anexos;
  `--indice` detecta cualquier desactualización.
- Manual 9 §6.1 CUMPLE: gate de nombres/citas cableado en pre-commit y CI;
  los alias temporales quedan visibles hasta D-MAN-1.

Evidencia: `tests/auditoria/test_verificar_manuales.py` (7/7).
