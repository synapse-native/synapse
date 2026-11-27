# Plan ME r272 — encoding documental y cabecera informativa

**Fase del roadmap:** Frente H (release industrial), Ola H1.
**Micro-entregable:** `r272_docs_encoding`.
**Depende de:** `r271_manuales_canonicos` (CERRADO).

---

requisito: Manual 2 §1.2
texto: "El lexer rechazará cualquier archivo que contenga caracteres no válidos en UTF‑8."
implementacion: `verificar_manuales.py --encoding --docs` recorre todos los `.md`
  versionados y rechaza BOM, U+FFFD, controles C1 y doble codificación. r272
  verifica por bytes la auditoría canónica, `R205.md` y `MEMORIA_PROYECTO.md`;
  no reescribe manuales de producción ni normaliza archivos sanos.
oraculo: tests/auditoria/test_docs_encoding_r272.py

requisito: Manual 1 §7.4
texto: "Actualización de los manuales correspondientes."
implementacion: se añade la cabecera visible de documento informativo a la
  auditoría de alineación y al reporte histórico R205, sin tocar su contenido
  normativo ni los manuales. El cierre exige evidencia de bytes y conservación
  de las 1.275 líneas originales de la auditoría.
oraculo: tests/auditoria/test_docs_encoding_r272.py
