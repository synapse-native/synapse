# Plan ME-r192 — Barrido total de deuda (cierre de R192)

## Ley citada (MTS: requisito / texto / implementacion / oraculo)

requisito: Manual 2 §5.1 (requiere y garantiza: cláusulas booleanas; garantiza se evalúa inmediatamente antes de cada `retornar`) y Manual 2 §5.2 (ejemplo) — emisión de aserciones en el cuerpo generado
texto: "Requiere garantiza ... `assert((expr) && \"Fallo en contrato: ...\");` antes de la ejecución del cuerpo."
texto: "Errores de contrato generan `assert((garantiza) && \"Fallo en contrato: garantiza\");`"
implementacion: S1 y nativo emiten `assert_contrato(<expr-c>, "Fallo en contrato: requiere|garantiza")` vía macro definida en emit_contracts.py `assert((expr) && msg)`, y en release `-DNDEBUG` (cumple Manual 2 §5.3, Modos de Compilación: "release | Se define `#define NDEBUG` en el C generado. Las aserciones se eliminan (costo cero).") la aserción se compila a vacío — sesión paridad emit_declarations.py/nativo.
oraculo: auditoria/oraculos/oraculo_r192_contracts.py — test_cobertura_d5 con_contrato: el C generado incluye `assert(...) && "Fallo en contrato: requiere"` y la ejecución del `con_contrato` reproduce el mensaje de contrato en stderr.

requisito: Manual 2 §5.1 (semántica garantiza evaluada anticipadamente en cada salida, `_resultado_` contiene el valor a retornar)
texto: "Al emitir `retornar`, se asigna `_resultado_` y se retornan, con la garantía `assert(...) && \"Fallo en contrato: garantiza\");` a continuación."
implementacion: emit_declarations.py emit_declaraciones: emitir asserts de garantiza tras la asignación `_resultado_` antes de `return _resultado_;`.
oraculo: tests/integration/test_contracts_e2e.py — 1c1044c mantiene rc=25 con garantiza; aserción visible en C generado.

requisito: Manual 2 §5.3 (Modos de Compilación, release = NDEBUG)
texto: "`release` | Se define `#define NDEBUG` en el C generado. Las aserciones se eliminan (costo cero)."
implementacion: transición: cada pipeline emite su macro, no se añade incognito re-declaración de `SYNAPSE_RELEASE` que no matchea -DNDEBUG; emit_contracts.py ya no define variantes.
oraculo: auditoria/oraculos/oraculo_r192_bootstrap.py — bootstrap S2==S3 hashes + verificación de que en release (`-DNDEBUG`) los asserts desaparecen del binario (objdump sin símbolo `Fallo en contrato`).

## Requisitos / decisión pendiente D-27_T3 (revisión)
- Nativos nucleo/generador/{funciones,nodos_flujo}.syn: reactivar el emisor de `garantiza` dejándolo deshabilitado por comentario previo (ME-27_T3 — sin ratificación en bitácora D-*, desviación del M2 §5.2).
- S1 compilador/generator/emit_declarations.py: re-habilitar la emisión con el macro común; emit_contracts.py se redefinirpor a macro emitida por el C nativo.

## Alcance
- contratos R (2 pipelines) + unity regenerada (`nucleo/generator.syn`, 4 copias)
- fixtures residual `_G_co_modo_resultado` (auditoriales compartidos, conexión r188b H-3)
- R192 test fixes del barrido: fase2_hm ×2, binario_real ×2 re-probe, grupo A (axon/cache/opensyn)
- bootstrap S2==S3, gates MTS, commit, docs

## No-go / riesgos
- Los tests son inmutables salvo desalineación con respecto a manual/convención ratificada (r192 grupo C ya alineado con esa regla).
- breakage del orden de inclusión `<assert.h>` ya emitido en nativo (nucleo/generator.syn L4811) y en S1 (header user C).
