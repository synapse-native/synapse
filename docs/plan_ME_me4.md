# plan_ME_me4 — Pago de deuda: fortalecer oráculos de test (M7 §2.3 / M3 §12.1)

Método de Trabajo Seguro (MTS, docs/METODO_TRABAJO.md). Cada requisito incluye
oráculo ejecutable y el código lleva cita grep-chequeable.

Contexto: el commit `6ceb4c0` (R122) insertó `pytest.skip('ME-4: Refactor pendiente
a validación funcional')` en ~100 funciones de test de content-sniff/smoke, bajo
autorización puntual ARQ-2026-08-27 (ver MEMORIA_PROYECTO.md). Este plan EJECUTA
ME-4: reemplazar cada skip por un assert de salida real, módulo por módulo. Al
cerrar ME-4 se elimina la entrada ARQ-2026-08-27 de la bitácora.

## Requisito 1 — test_transpile: el .syq generado compila y mapea tipos (M7 §7, M7 §2.3)

requisito: Manual 7 §7 ("Código generado compila") + Manual 7 §2.3 (mapeo int→entero,
float→decimal, str→texto, list→Lista<T>).
texto: "Transpilación Python → Syquex — Código generado compila" y "Mapeo de tipos
(int→entero, float→decimal, str→texto, list→Lista<T>)".
implementacion: en tests/opensyn/test_transpile.py, reemplazar los `pytest.skip`
por una llamada real a `opensyn.transpiler.transpilar_codigo_python` sobre un
fragmento Python, compilar el .syq resultante con `compilar_texto` (Synapse, idioma
'es') y afirmar `diag.hay_errores() == False` (oráculo de compilación real) más la
presencia del mapeo (`entero`, `texto`, `retornar`). Ya verificado empíricamente:
`def suma(a,b): return a+b` → 0 errores de compilación.
oraculo: tests/opensyn/test_transpile.py

## Requisito 2 — test_rag: verificar la API RAG real implementada (M7 §2.3)

requisito: Manual 7 §2.3 (Pipeline RAG inyecta reglas/contexto; 30% n_ctx / 70% generación).
texto: "Pipeline RAG (contexto estático) — Prompt incluye reglas de Synapse/Syquex"
y división 30%/70% de n_ctx.
implementacion: en tests/opensyn/test_rag.py, reemplazar los `pytest.skip` por
asserts de CONTRATO reales sobre la API ya implementada en `nucleo/synapse_rag.c`/`.h`:
(a) `synapse_rag_extraer_contexto` declarada en `.h` y definida en `.c` (paridad
declaración/definición, detecta regresiones de la API pública); (b) `RAG_RATIO_INYECCION_DEFAULT`
definida como `0.3f` en `.h` (oráculo de la división 30%/70% real); (c) `synapse_rag_construir_prompt`
definida en `.c` (el constructor de prompt existe y usa `contexto_archivo`). Se evita
el content-sniff débil previo (grep de "reglas"/"contexto") por chequeo de símbolos
reales. NOTA: las literals "REGLAS DE SYNAPSE" / "INSTRUCCION" no existen hoy en el
fuente → esa carencia es deuda de FEATURE surfaced por ME-4; el oráculo piloto valida
la API existente y se amplía a test funcional (compilar+ejecutar C) en ME-4 profundo.
oraculo: tests/opensyn/test_rag.py

## Notas de alcance

- ME-4 abarca ~100 tests; este plan es el PILOTO (2 módulos). El resto de módulos se
  convierte incrementalmente con su propio `plan_ME_me4_<mod>.md` o ampliación de este.
- Los tests modificados son de la carpeta `tests/` (excluidos de producción por el gate
  MTS); la exención ARQ-2026-08-27 autoriza tocarlos para ENDURECERLOS (no para
  debilitarlos), según regla 5 de gobernanza.
