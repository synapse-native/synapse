# Verificación ME r282_docs_informativos

- Manual 1 §7.4 — CUMPLE: los 22 documentos de `docs/book2-desarrollo/` llevan cabecera, mapa canónico y vigencia; las copias de los manuales 1–9 se marcan como históricas y enlazan al manual canónico.
- Manual 9 §6.1 — CUMPLE: se corrigieron las contradicciones conocidas y los enlaces muertos; `verificar_manuales.py --docs` valida cabeceras, mapas, contradicciones y enlaces, y `--todo` lo integra en el pre-commit.

## Evidencia

- `python auditoria/verificar_manuales.py --docs` → rc=0.
- `pytest tests/auditoria/test_verificar_informativos_r282.py` → 8/8.
- `python auditoria/contrastar.py --plan docs/plan_ME_r282_docs_informativos.md` → PASS.
- `python auditoria/verificar_alineacion.py` → 0 brechas.
