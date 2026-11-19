# Plan ME r270 — paridad de emisión bootstrap (S2 == S3)

**Fase del roadmap:** Frente H (release industrial), Ola H1.
**Micro-entregable:** `r270_bootstrap_emision_paridad` (absorbe `r252b`).
**Hallazgos:** H-R252-1 (falso positivo por artefacto stale) y H-R252-4
(enlace nativo sin `-static` en win32).

---

requisito: Manual 1 §6
texto: "Regla de hierro: Ninguna característica nueva puede romper el *bootstrap* (etapas 0→1→2→3 con diff binario 0). El determinismo se verifica obligatoriamente en la CI mediante la comparación de los hashes SHA‑256 de las etapas 2 y 3."
implementacion: `auditoria/oraculos/oraculo_r252_paridad_bootstrap.py`
  compara SHA-256 y tamaño de S2/S3 y falla si S2 es anterior a
  `nucleo/principal.syn` o si S3 es anterior a S2. El guard de frescura evita
  que un artefacto stale de una corrida modular anterior (H-R252-1) pase como
  paridad. En `nucleo/principal.syn`, el enlace nativo añade `-static` en
  win32 (`_static_flag`) para igualar la emisión S1 y no depender de DLLs del
  toolchain (H-R252-4).
oraculo: tests/auditoria/test_r270_bootstrap_paridad.py

requisito: Manual 9 §6.2
texto: "La verificación del bootstrap (diff 0 bytes)."
implementacion: El job `bootstrap` de `.github/workflows/ci-tests.yml` ejecuta
  el oráculo tras construir stage2/stage3 desde `main.py` y stage1; el mismo
  script es la única implementación del sello.
oraculo: tests/auditoria/test_r270_bootstrap_paridad.py

requisito: Manual 9 §6.1
texto: "□ **Bootstrap exitoso**: en cada target, el proceso de bootstrap de 3 etapas produce `diff 0 bytes` entre Stage 2 y Stage 3."
implementacion: `build.py` invoca el oráculo con `--artefactos` al cerrar las 3
  etapas y aborta con rc=1 si el sello falla. La corrida de comprobación produjo
  S2=S3: 2.559.482 B, SHA-256 `30C07EF61C5F25A7…`; el stage2 de 2.077.570 B era
  un artefacto stale de una emisión modular previa, no una diferencia de código.
oraculo: tests/auditoria/test_r270_bootstrap_paridad.py
