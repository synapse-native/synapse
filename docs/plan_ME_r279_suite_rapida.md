# Plan ME r279_suite_rapida

**Fase del roadmap:** Frente H (sostenibilidad), Ola H3 — P1 tras r280.
**Micro-entregable:** `r279_suite_rapida`.
**Depende de:** `r273_installer_modelo_grande` (CERRADO), `r274_gates_independientes` (CERRADO), `r280_codigo_encoding` (CERRADO).
**Manuales:** Manual 1 §7.2; Manual 9 §6.2.
**Origen:** `docs/gobernancia/PLAN_MEJORAS_ECOSISTEMA_R270_R284.md` §r279;
`docs/gobernancia/PLAN_MAESTRO_INDUSTRIAL.md` (fila r279).

> Alcance real de esta sesión: hacer medible y acotada la suite sin tocar
> ninguna aserción. La suite completa tarda más de dos horas y arrastra fallos
> ambientales; el problema no es que corra lento, es que **nadie mide** cuántos
> tests corre ni cuántos se saltan. Se entrega un gate con ratchet de
> composición (barato, en cada PR), medición cronometrada por suite (cara, en
> CI), shards de CI y el marcador `network` como opt-in explícito.
> **No se modifica ningún test**: sólo infraestructura de tests.

---

requisito: Manual 1 §7.2
texto: "Todo cambio debe pasar la suite completa de pruebas:"
implementacion: la suite se ejecuta por suites acotadas (`unit`, `integration`, `auditoria`, `opensyn`, `syquex`, `e2e`, `security`, `fuzz`, `stress`, `nucleo`) y su composición queda congelada en `auditoria/suite_baseline.json` (3078 tests recolectados, 243 skips declarados). `auditoria/verificar_suite.py` falla si una suite pierde tests o gana skips (`pytest.mark.skip`, `skipif`, `pytest.skip`), y `--medir` cronometra `passed`/`skipped`/`failed` por suite con `--comparar` contra la línea base medida. Los tests marcados `network` quedan opt-in (`-m "not network"` por defecto) y el marcador se declara en `pytest.ini`. El CI gana el job `suite-rapida` (matriz de shards, sin red, `PYTHONHASHSEED=0`) y `suite-ratchet` (recolección + ratchet).
oraculo: auditoria/verificar_suite.py

requisito: Manual 9 §6.2
texto: "La suite de tests completa en cada target."
implementacion: el job `test` de `ci-tests.yml` conserva la suite completa en la matriz 3×3 de SO/Python (no se sustituye por los shards: los shards son la señal temprana y el job completo sigue siendo el gate por target). El ratchet de composición se ejecuta además en cada push/PR, así que una suite que encoge o gana skips se ve antes de la matriz larga. La recolección se compara en la plataforma donde se generó la línea base (recuento exacto) y en el resto sólo se exige que ninguna suite registrada quede en cero, porque los módulos importables dependen del SO.
oraculo: tests/auditoria/test_verificar_suite.py

## Criterio de cierre

1. `python auditoria/verificar_suite.py --resumen` → `OK: suite — 3078 tests
   recolectados en 10 suites, 243 skips declarados (sin altas)`.
2. `pytest tests/auditoria/test_verificar_suite.py` 4/4 (verde, falla si
   desaparecen tests o aparece un skip nuevo, y `--medir` deja recuentos).
3. `python auditoria/verificar_suite.py --medir --suite e2e --guardar-medido`
   registra `passed`/`skipped`/`failed` y segundos reales en el baseline.
4. `python auditoria/contrastar.py --plan docs/plan_ME_r279_suite_rapida.md`
   PASS y `python auditoria/verificar_alineacion.py` 0 brechas.
5. Documentar en `docs/reportes/R279.md` los tiempos medidos, la línea base y
   los límites (la corrida completa cronometrada queda en CI).

## Política

Tests inmutables: este ME sólo añade infraestructura (`pytest.ini`, gate,
baseline, jobs de CI, oráculo nuevo). No se oculta ningún fallo con `-k` ni
`--ignore`; el job completo sigue corriendo la suite entera.
