# Plan MTS — ME fixture_syquex_timeout

> Última deuda de `docs/reportes/FASE_33_CERTIFICACION.md` §5 y de los MEs
> heredados (R164): el fixture `tests/integration/test_syquex_coverage.py`
> lanza un subprocess interno (pytest completo de tests/syquex + certs + fuzz +
> benchmarks con `--cov=compilador`) con timeout INTERNO de 600 s, pero el
> timeout GLOBAL de pytest.ini (300 s) lo mataba antes y ABORTABA la sesión
> pytest completa. Autorización explícita del Arquitecto (regla 5) concedida
> en sesión 2026-09-29 (elección "Autorizar fixture").

requisito: Manual 9 §6.2 (validación cruzada CI/CD)
texto: "synapse test --junit --coverage"
implementacion: tests/integration/test_syquex_coverage.py — pytestmark = [
  pytest.mark.integration, pytest.mark.timeout(660)]: techo de tiempo de los 5
  tests del fixture a 660 s > 600 s del subprocess interno (invariante exterior
  > interior preservada); el timeout GLOBAL de pytest.ini (300 s) queda intacto
  como tripwire para el resto de la suite (no se relaja ninguna otra prueba).
  Aserciones y umbrales de cobertura SIN cambios — la modificación es SOLO el
  techo de tiempo, con autorización explícita del Arquitecto (regla 5).
oraculo: tests/integration/test_syquex_coverage.py

requisito: Manual 3 §3 (gramática formal de Syquex — la ley que el test ancla)
texto: "La gramática de Syquex es más expresiva que la de Synapse, incorporando elementos de programación orientada a objetos (estructuras"
implementacion: PRESERVACIÓN de la ley anclada: las 5 aserciones del fixture
  (cobertura total >= 45%, lexer.py >= 50%, puente_canonico.py >= 50%,
  generator.py >= 50%) quedan byte-idénticas; el ME corrige el ENTORNO de
  ejecución (techo de tiempo), no el contrato validado. Verificado empíricamente:
  5/5 GREEN en 398.75 s con el marker (antes: killed por el global de 300 s).
oraculo: tests/integration/test_syquex_coverage.py

## Medición del cuello de botella (evidencia, sesión 2026-09-29)
- Suite interna sin benchmarks, con --cov=compilador: 476.54 s (4F preexistentes
  de syquex, 319 passed, 1 skipped).
- Benchmarks con cov: 23.52 s (8 passed — el flaky test_fibonacci_30 pasó).
- Suite completa sin cov: 394.22 s → el costo del coverage es ~100 s (25%).
- Total con cov ≈ 500-503 s: imposible bajo el global de 300 s → el fixture no
  es ineficiente (1 subprocess cacheado para 5 tests); el conflicto es de TECHO
  DE TIEMPO global vs interno.
