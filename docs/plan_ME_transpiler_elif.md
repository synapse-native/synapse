# Plan MTS — ME transpiler_elif

> Deuda documentada en R166/R167 (test_control_flow_pipeline, falla preexistente en
> base limpia). Causa raíz: `opensyn/transpiler.py` emite `sino_si` (L51/L197),
> token que la gramática no define. Origen de la desviación: R119 L60 —
> "Corregido de `sino si` (con espacio) a `sino_si` (con guión bajo)" — un
> "arreglo" de Fase 26 que invirtió la forma correcta. El transpilador gemelo
> original `opensyn/transpiler.syq` (inventario M7 §5.1) mapea `elif → "sino si"`.

requisito: Manual 6 §6.2 (Transpilación Python → Syquex — sección normativa real del transpilador)
texto: "OpenSyn puede tomar código Python y generar Syquex equivalente, mapeando tipos dinámicos a estáticos."
implementacion: opensyn/transpiler.py L51: entrada del dict MAPEO_KEYWORDS
  "elif": "sino_si" → "elif": "sino si" (paridad con transpiler.syq L92, que es
  el transpilador original del inventario: mapa.agregar(MapaPalabraClave("elif",
  "sino si"))). Comentario `# cumple Manual 6 §6.2`.
oraculo: tests/test_full_pipeline.py (oráculo canónico; la aserción exacta es
  TestCasosReales::test_control_flow_pipeline — aserción "sino si n < 0:", test
  inmutable ya existente) + tests/opensyn/test_transpile.py (oráculo de
  compilación real del .syq generado, OBL-M7-03)

requisito: Manual 6 §6.2 (Transpilación Python → Syquex)
texto: "2. Para cada nodo Python, determina su equivalente en Syquex:"
implementacion: opensyn/transpiler.py L197: re.sub(r'\belif\b', 'sino_si',
  resultado) → re.sub(r'\belif\b', 'sino si', resultado). Con la forma canónica
  el .syq generado COMPILA (el parser solo conoce si/sino: M2 §7.2 L104 y M3 §4
  L130 no definen sino_si; T_SINO | sino | else | sinon | senao). Comentario
  `# cumple Manual 6 §6.2` (ya presente en la cabecera; reafirmar en las líneas).
oraculo: tests/test_full_pipeline.py (ejecuta el compilador real sobre el .syn
  transpilado: 4 errores de sintaxis hoy, 0 tras el fix)

requisito: Manual 6 §6.2 (OBL-M7-03: "el .syq generado COMPILA" — MANUAL_TESTS_OBLIGATORIOS M7)
texto: "3. Genera código Syquex con anotaciones de tipo inferidas."
implementacion: tests/integration/test_opensyn_integration.py L120 (ÚNICO test del
  repositorio que asertaba la salida defectuosa): assert "sino_si" in syq_code →
  assert "sino si" in syq_code. AUTORIZACIÓN DEL ARQUITECTO regla 5 otorgada
  explícitamente en sesión (2026-09-30, respuesta "Autorizar test+fix") tras
  exponer: (a) la gramática no define sino_si; (b) OBL-M7-03 exige que el .syq
  generado compile y sino_si produce 4 errores reproducidos; (c) la justificación
  histórica citaba Manual 7 §5.1, sección que NO existe (M7 termina en §4; el
  ANEXO-MANUALES §3.3 ordenó insertarla y nunca se incorporó — cita fantasma);
  (d) contradice al test gemelo test_full_pipeline.py:230. La aserción corregida
  verifica el token que la gramática define — no debilita el test.
oraculo: tests/opensyn/test_transpile.py (el .syq generado COMPILA — OBL-M7-03;
  nota: el archivo del test modificado no sirve de oráculo entero por el fallo
  PREEXISTENTE test_validation_loop_syn_exists — nombre de función esperado
  validar_codigo_con_check vs validar_con_check real, deuda documentada aparte;
  la aserción L120 corregida se verificó por node ID en sesión: 2 passed en 2.71 s)

## Notas de alcance
- Radio de blast verificado: SOLO transpiler.py L51+L197 emiten sino_si; la suite
  histórica tests/test_transpiler_integration.py (48 tests) no cubre elif/sino;
  mapear_palabra_clave (dict, L146-148) no está en el camino de re.sub — se
  corrige igualmente por coherencia del dict (una sola entrada).
- transpiler.py es producción de mapa puntual (NO está en mapa_alineacion.md):
  el expediente del ME declarará 0 requisitos exigidos con anclas registradas
  (precedente: ME cli_lint_fmt, evidencia 07ba3f460c6d0bee).
- Modificación de test: SOLO la aserción L120 (sino_si → "sino si"), resto del
  archivo intocado, con autorización regla 5 documentada en este plan.
- Oráculo release para contrastar: pytest tests/test_full_pipeline.py::TestCasosReales::test_control_flow_pipeline
  + tests/integration/test_opensyn_integration.py::TestTranspilacionCompleta
  (compilación real de S1; sin --cov).
