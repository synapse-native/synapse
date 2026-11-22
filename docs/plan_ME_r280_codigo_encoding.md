# Plan ME r280_codigo_encoding

**Fase del roadmap:** Frente H (sostenibilidad), P1 tras r271/r272.
**Micro-entregable:** `r280_codigo_encoding`.
**Depende de:** `r271_manuales_canonicos` (CERRADO), `r272_docs_encoding` (CERRADO).
**Manuales:** Manual 2 §1.2; Manual 1 §7.4; Manual 5 §2.1.

> Alcance real de esta sesión: corregir U+FFFD, controles C1 y secuencias de
> doble codificación en comentarios/cadenas de fuentes de producción
> (`axon/axon_rt.c`, `runtime/core/axon.h`, `runtime/core/concurrency.c`,
> `runtime/core/debug.c`, `std/texto.syn` y el fixture
> `tests/validate_distillation.c`) sin cambiar semántica. Se añade
> `auditoria/verificar_encoding.py` como gate repo-wide en bytes, con ratchet
> para el BOM histórico (`auditoria/encoding_bom_baseline.txt`, H-R280-2) y
> exenciones declaradas para los fixtures UTF-16 de rechazo (H-R280-3).

---

requisito: Manual 2 §1.2
texto: "Todos los archivos fuente deben estar codificados en **UTF‑8 sin BOM**."
implementacion: se reemplazan los caracteres de pérdida (U+FFFD), los controles C1 y las secuencias latin-1 doblemente codificadas por su texto UTF-8 real en los comentarios y cadenas de las fuentes tocadas; no se altera ninguna rama de ejecución. `auditoria/verificar_encoding.py` audita el árbol versionado en bytes (`git ls-files`), falla con U+FFFD/C1/mojibake/UTF-8 inválido/BOM nuevo y deja `--json` como evidencia. El BOM preexistente se congela en un baseline con ratchet (H-R280-2) y `--estricto` exige cero BOM; los fixtures UTF-16 de rechazo quedan exentos y documentados (H-R280-3).
oraculo: auditoria/verificar_encoding.py

requisito: Manual 1 §7.4
texto: "Aprobación del 100% de los tests unitarios, de integración y fuzzing sin regresiones."
implementacion: la corrección es solo de encoding (comentarios/cadenas); se ejecuta la regresión dirigida de los módulos tocados —gate de encoding, `test_axon_e2e.py`, `test_concurrency_10.py` y `test_oraculos_r222_std_texto.py`— y se reconstruye con `build.py --skip-test` para descartar cualquier regresión de compilación. La suite completa sigue siendo el gate de CI.
oraculo: tests/integration/test_axon_e2e.py

requisito: Manual 5 §2.1
texto: "Pila propia (tamaño configurable, por defecto 64 KB)."
implementacion: los comentarios de `runtime/core/concurrency.c` que describen las fibras, el scheduler M:N y la pila de 64 KB se normalizan a UTF-8 sin tocar el código de fibras; la regresión de concurrencia verifica que el comportamiento (creación, ejecución y cierre de fibras) no cambió.
oraculo: tests/integration/test_concurrency_10.py

## Criterio de cierre

1. `python auditoria/verificar_encoding.py` → `OK: encoding ... 0 U+FFFD, 0 C1,
   0 doble codificación, 0 BOM nuevos` sobre el árbol versionado.
2. `pytest tests/auditoria/test_verificar_encoding.py` 7/7 y regresión dirigida
   (`test_axon_e2e.py` 5/5, `test_concurrency_10.py` 17/17,
   `test_oraculos_r222_std_texto.py` 4/4).
3. `python build.py --skip-test` rc=0 (los cambios no alteran semántica).
4. `python auditoria/contrastar.py --plan docs/plan_ME_r280_codigo_encoding.md`
   PASS y `python auditoria/verificar_alineacion.py` 0 brechas.
5. Documentar en `docs/reportes/R280.md` el alcance, la deuda de BOM congelada
   (H-R280-2) y las exenciones de fixtures (H-R280-3).
