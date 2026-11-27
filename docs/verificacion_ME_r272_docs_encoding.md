# Verificación ME r272 — encoding documental

- Manual 2 §1.2 CUMPLE: `verificar_manuales.py --encoding --docs` pasa sobre
  todo `docs/`; la auditoría, `R205.md` y `MEMORIA_PROYECTO.md` no tienen BOM,
  U+FFFD, C1 ni doble codificación.
- Manual 1 §7.4 CUMPLE: la auditoría y `R205.md` llevan cabecera de documento
  informativo; no se modificaron manuales de producción.

Evidencia: `tests/auditoria/test_docs_encoding_r272.py`.
