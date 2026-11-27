# Plan ME paridad_principal_syq — retirada de los stubs de principal obsoletos

**Fuente:** mandato del Arquitecto "continua hasta que todo este perfecto" (2026-10-01, tras R174).
**Base:** 121153d (1e1584b+docs).
**Alcance:** los 4 warps de tests/integration/test_paridad_syn_syq.py (el dump
.syq añade `DefinicionFuncion(nombre=principal,...)` que el .syn no tiene).
**Causa raíz (arqueología + probe):** dos workarounds heredados de ME-R90-8/8b
inyectaban un stub de `principal` cuando el fuente .syq no lo declara:
(1) pipeline.py `compilar_desde_syq` escribía un TEMPORAL con
`funcion principal() -> nulo:\n    retornar` añadido al source antes del
frontend (H-R90-8b); (2) el puente canónico añadía el stub al AST si el plano
no lo traía (ME-R90-8). El pretexto era "el runtime S1 filtra funciones
locales sin principal" — FALSO con el frontend actual: el probe ejecutó el
exe syq_frontend sobre un .syq de biblioteca sin principal y el JSON conserva
la función `area` (10 nodos, FUNCION idx 3 = "area"). El generador emite un
main de biblioteca sin entry point (H-R90-8/D-R150-4, E2E verificado: rc=0).
**Ley:** M1 §3.1 — pipeline compartido, .syn y .syq convergen al MISMO AST
canónico (paridad estructural ROADMAP F22); M3 §3 L78 — el entry point es
OPCIONAL en .syq; M2 §12 — verificación con oráculos.

## R1 — pipeline.py: retirar la inyección H-R90-8b del source
requisito: Manual 1 §3.1
texto: "El compilador unificado procesa código fuente de Synapse (.syn), Syquex (.syq) e incluso prompts en lenguaje natural (via OpenSyn) a través de un pipeline compartido:" (M1 §3.1 —
el pipeline es COMPARTIDO tras el traductor: el .syq debe producir el mismo
AST canónico que el .syn equivalente; un stub solo en el camino .syq rompe la
paridad estructural ROADMAP F22).
implementacion: `pipeline.py::compilar_desde_syq` (L597): eliminados la
lectura del fuente, la detección `tiene_principal`, el tempfile con el stub
`funcion principal()` y el comentario obsoleto; el exe del frontend recibe la
ruta REAL del usuario. Comentario de causa con ancla colectable
`cumple Manual 1 §3.1` (L605).
// cumple Manual 1 §3.1
oraculo: tests/integration/test_paridad_syn_syq.py

## R2 — puente_canonico.py: retirar el fallback ME-R90-8 del AST
requisito: Manual 1 §3.1
texto: "El compilador unificado procesa código fuente de Synapse (.syn), Syquex (.syq) e incluso prompts en lenguaje natural (via OpenSyn) a través de un pipeline compartido:" (M1 §3.1 —
el AST que devuelve el puente es la moneda común; el stub añadido en
`plano_a_programa` contaminaba el Programa canónico incluso cuando el plano
venía limpio; el entry point es OPCIONAL en .syq (M3 §3 L78) y el generador
emite main de biblioteca sin principal (H-R90-8/D-R150-4)).
implementacion: `compilador/puente_canonico.py::plano_a_programa` (L649):
eliminado el bloque que añadía
`DefinicionFuncion(nombre='principal', tipo_retorno='nulo', cuerpo=[retornar])`
cuando el plano no traía principal; comentario de causa con ancla colectable
`cumple Manual 1 §3.1` (L649). Los imports DefinicionFuncion/SentenciaRetornar
siguen en uso (L341/L357).
// cumple Manual 1 §3.1
oraculo: tests/integration/test_paridad_syn_syq.py

## R3 — paridad estructural restaurada (cierre de los 4 warps)
requisito: Manual 1 §3.1
texto: "El compilador unificado procesa código fuente de Synapse (.syn), Syquex (.syq) e incluso prompts en lenguaje natural (via OpenSyn) a través de un pipeline compartido:" (M1 §3.1 —
verificación estructural: ser(Programa_syn) == ser(Programa_syq) para los 6
pares de fixtures; sin stubs, ambos caminos producen el mismo AST).
implementacion: verificación empírica — test_paridad_syn_syq 6/6 PASSED
(antes 4 FAILED: struct_and_constant, control_flow, coincidir_basic,
test_si_sino_paridad); E2E dual: .syq con principal ejecuta rc=7 (q.x) y .syq
de biblioteca sin principal compila/enlaza/ejecuta rc=0.
// cumple Manual 1 §3.1
oraculo: tests/integration/test_paridad_syn_syq.py
