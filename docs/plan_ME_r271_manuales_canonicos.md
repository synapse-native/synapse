# Plan ME r271 — manuales canónicos, índice completo y gate de citas

**Fase del roadmap:** Frente H (release industrial), Ola H1.
**Micro-entregable:** `r271_manuales_canonicos`.
**Depende de:** D-MAN-1/2 (alias aprobado); no renombra archivos.

---

requisito: Manual 2 §1.2
texto: "Todos los archivos fuente deben estar codificados en **UTF‑8 sin BOM**."
implementacion: `auditoria/verificar_manuales.py --encoding` valida bytes UTF-8
  estrictos, ausencia de BOM, U+FFFD, controles C1 y secuencias de doble
  codificación en `docs/manuales/`; `--docs` extiende el barrido a `docs/`.
  No reescribe contenido.
oraculo: tests/auditoria/test_verificar_manuales.py

requisito: Manual 1 §7.4
texto: "Actualización de los manuales correspondientes."
implementacion: `auditoria/indice_manual.py` indexa los manuales 1–9, los alias
  temporales de Manual 31/32 y los anexos declarados (`ANEXO-MANUALES`,
  `ANEXO_INVENTARIO_ARCHIVOS`, `MTO`) con SHA-256 y secciones. `.indice.json`
  se regenera con `--generar`; `--indice` falla si quedó desactualizado.
oraculo: tests/auditoria/test_verificar_manuales.py

requisito: Manual 9 §6.1
texto: "□ **Documentación**: todos los manuales versionados y empaquetados (incluyendo el Manual 31)."
implementacion: `auditoria/verificar_manuales.py --nombres` exige el conjunto
  canónico, acepta solo alias registrados y reporta los alias temporales. El
  gate `--citas` valida `cumple Manual N §S` de producción contra el índice.
  Se cablea en `scripts/githooks/pre-commit` y en el job
  `manuales-integridad` de `.github/workflows/ci-tests.yml`.
oraculo: tests/auditoria/test_verificar_manuales.py
