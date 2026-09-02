# REPORTE ME_test_fixes - Conversión de tests a TDD RED (Manual 2 §4.2)

--- REPORTE DE MICRO-ENTREGABLE ---
TAREA: Convertir las 24 anomalías (FAILURE crudo) y 6 preexistentes a la convención TDD RED `pytest.fail("RED TDD (ME_xx_Tx): ...")` del repo, de modo que los fallos sean intencionales y trazables, no regresiones.
FASE: 27 / Fase 2 nativa (feature/fase2-nativa-hm) - ME test_fixes
MANUAL REFERENCIADO: Manual 2 §4.2 (tests TDD usan pytest.fail RED TDD), Manual 2 §10.1 (DiagnosticManager)
HASH COMMIT: d8d0ef9 (base del otro agente) + commit de terminación (este ME: conversión P1 en test_cobertura_d5.py)
COMPILACION: N/A (solo modificación de tests; el codegen S1 no se toca).
TESTS:
  - Auditoría: `pytest` sobre los 8 archivos de anomalías + 4 de preexistentes. Resultado previo: 16 failed / 24 passed / 3 skipped. Los 16 fallos ya usaban mensaje RED TDD (ya convertidos por el otro agente); el único FAILURE crudo restante era `tests/integration/test_cobertura_d5.py::test_codegen_s1_principal_retorno` (P1: codegen no captura `_rc` en main()).
  - Conversión P1: el test ahora falla con `RED TDD (D-5/P1): codegen de principal con retorno entero aun no captura _rc en main()...` (condicional: pasa si la feature se implementa). Verificado con `pytest` (1 failed con mensaje RED TDD, sin AssertionError).
  - P2 (test_cli_check) y P3 (test_lsp_native): pasan/skip (ya resueltos). P4 (test_r3_param_adt) ya es RED TDD por deuda D-2. P5/P6 (federated/quantum) ya RED TDD.
  - `python auditoria/verificar_alineacion.py` -> 0 brechas. `python auditoria/contrastar.py --plan docs/plan_ME_test_fixes.md` -> PASS.
MODIFICACIONES DE TESTS: solo `tests/integration/test_cobertura_d5.py` (test_codegen_s1_principal_retorno) convertido a RED TDD condicional. Ningún test existente debilitado; los demás ya cumplían la convención.
PROXIMO PASO: ninguno para test_fixes (0 FAILURE crudo restante; todos los fallos son RED TDD intencionales). La implementación real del codegen P1 (captura de `_rc` en main) es deuda de feature fuera de alcance de este ME.
--- FIN ---
