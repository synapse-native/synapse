# Plan ME r282_docs_informativos

**Fase del roadmap:** Frente H (sostenibilidad), P2 tras r280/r281.
**Micro-entregable:** `r282_docs_informativos`.
**Depende de:** `r271_manuales_canonicos` (CERRADO), `r272_docs_encoding` (CERRADO).
**Manuales:** Manual 1 §7.4; Manual 9 §6.1.

> Alcance de esta sesión: barrido único de `docs/book2-desarrollo/` (D-MAN-3
> opción A). Se añade la cabecera de documento informativo, el mapa canónico y
> la marca de vigencia a los 22 `.md`; se corrigen las contradicciones visibles
> (lista de manuales, títulos y enlaces muertos de `SUMMARY.md` y `roadmap.md`)
> y se marca lo histórico como histórico. No se reescriben los manuales ni los
> reportes históricos.

---

requisito: Manual 1 §7.4
texto: "Actualización de los manuales correspondientes."
implementacion: cada `.md` de `docs/book2-desarrollo/` recibe la cabecera `> Documento informativo. La fuente de verdad es docs/manuales/.`, una línea `**Mapa canónico:**` con enlace a la sección o manual que resume, y una marca de vigencia. Las copias de los manuales 1–9 se declaran copias históricas y enlazan al `MANUAL N` canónico; no se altera su cuerpo. `SUMMARY.md` se reescribe como índice de documentos existentes y `presentacion.md` corrige la lista a los 11 manuales vigentes.
oraculo: tests/auditoria/test_verificar_informativos_r282.py

requisito: Manual 9 §6.1
texto: "Documentación: todos los manuales versionados y empaquetados (incluyendo el Manual 31)."
implementacion: se eliminan las contradicciones conocidas del barrido (fuente de verdad local, “9 manuales”, títulos de Manual 6/7/8/9 y enlaces a archivos inexistentes). El gate `verificar_manuales.py --docs` valida cabecera, mapa canónico, contradicciones y resolución de enlaces relativos; `--todo` lo integra en el pre-commit.
oraculo: auditoria/oraculos/oraculo_r282_docs_informativos.py

## Criterio de cierre

1. `python auditoria/verificar_manuales.py --docs` rc=0.
2. `pytest tests/auditoria/test_verificar_informativos_r282.py` 8/8.
3. `python auditoria/contrastar.py --plan docs/plan_ME_r282_docs_informativos.md` PASS.
4. `python auditoria/verificar_alineacion.py` 0 brechas.
5. Reporte `docs/reportes/R282.md` con el hash real y actualización de
   `MEMORIA_PROYECTO.md` y de la bitácora canónica.
