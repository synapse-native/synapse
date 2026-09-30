# Plan MTS — ME validation_loop_fix

> Deuda documentada en R168: `test_validation_loop_syn_exists` (única aserción rota
> de TestBucleValidacion, test_opensyn_integration.py:217). Arqueología: e8d148a
> (2026-08-26, ME-F26-13) creó validation_loop.syn con `validar_codigo_con_check`;
> 65b505e (ME-F26-14) creó el test afirmando ese nombre (coherente entonces);
> 7824e5d (2026-09-12, ME-4 R4+R5+R10) RENOMBRÓ la función a `validar_con_check`
> sin actualizar el test. Hoy el nombre viejo solo vive en esa 1 aserción.

requisito: Manual 7 §4.2 (el LSP orquesta el bucle de validación — OBL-M7-02)
texto: "El LSP es el responsable de orquestar el bucle de validación (descrito en la sección 6.3)."
implementacion: tests/integration/test_opensyn_integration.py L217 — aserción de
  PRESENCIA (el test no ejecuta código; lee el .syn como texto): `funcion
  validar_codigo_con_check` → `funcion validar_con_check`, el nombre definido en
  validation_loop.syn:51. Ningún manual nombra ninguna de las dos funciones
  (grep exhaustivo docs/manuales) → no hay norma que defienda el nombre viejo;
  TODO el ecosistema vivo usa el nuevo: 3 llamadas internas en
  validation_loop.syn (bucle_validacion L172/L186, review_compilar L129) + suite
  ME-4 test_ai_correction_opensyn.py (51/51 GREEN) que afirma `funcion
  validar_con_check(` en L134/L232/L244. La aserción corregida RESTAURA la
  intención original del test (presencia de la pieza validadora del bucle), no
  lo debilita. AUTORIZACIÓN EXPLÍCITA DEL ARQUITECTO (regla 5, sesión
  2026-09-30, Opción A "alinear test" tras diagnóstico con opciones A/B/C).
oraculo: tests/integration/test_opensyn_integration.py

requisito: Manual 8 §5.4 (el bucle valida con el compilador — la pieza validadora
  debe afirmarse con el nombre que TODO el ecosistema usa)
texto: "Cuando OpenSyn genera código, el LSP lo valida automáticamente usando el compilador con el flag `--no-emit`."
implementacion: coherencia entre suites: hoy conviven dos suites que afirman
  nombres distintos de la MISMA función (el test viejo de F26 con el nombre
  abandonado y el suite ME-4 con el nombre vigente). La corrección elimina la
  única contradicción; test_opensyn_integration.py queda 18/18 y el archivo
  vuelve a ser ejecutable completo como oráculo.
oraculo: tests/integration/test_ai_correction_opensyn.py

## Notas de alcance
- ME SOLO-TESTS: 0 archivos de producción → expediente de alineación sin anclas
  (gate de lectura previa no aplica — precedente ME fixture_syquex_timeout).
- No se toca código de producción (renombrar código rompería/obligaría a editar
  51 tests del suite ME-4 que afirman el nombre vigente — Opción B descartada).
- Deuda de anclaje SEPARADA documentada: M7 §6.3 NO existe (M7 termina en §4)
  pero es citada por referencias internas del propio manual (L24, L627), por el
  ANEXO-MANUALES y por comentarios `// cumple Manual 7 §6.3` de producción en
  validation_loop.syn; el anclaje normativo real del bucle es M7 §4.2 +
  M8 §5.2–§5.4 (precedente D-ALINEACION-F31).
- Modificación de test: SOLO la aserción L217 + comentario justificativo, con
  autorización regla 5 documentada en este plan.
