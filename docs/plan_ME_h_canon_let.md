# Plan ME H-canon-LET — el serializador canónico pisaba la llave discriminante 'tipo' + asserts codegen alineados

**Fuente:** sesion de depuracion codegen R183e (post-R183d, base dcf9720).
**Alcance:** round-trip del JSON canonico (M2 §13) y asserts de la suite codegen
(F1.2c/F1.2d/D2/D6) que quedaron obsoletos frente a decisiones ya ratificadas
(M2 §13 formato plano; runtime real débil<T>=WeakRef de Fase 23, Manual 4 §4.2,
autorizacion Arquitecto regla 5).

## R1 — Fix de produccion: anotacion 'tipo_annot' en DeclaracionVariable
requisito: Manual 2 §13
texto: "el AST simplificado (JSON) del ejemplo completo lleva el discriminante
'tipo' como **nombre de nodo** en cada nodo ('tipo': 'Programa'/
'DeclaracionVariable'/'FuncionDef'/'Asignacion'/'LlamadaFuncion'); los
parametros son {nombre, tipo, es_transferencia}; ninguna anotacion pisa esa
llave" — el ejemplo completo de M2 §13 define el formato canonico por
precedente; el round-trip .syn.json es el consumidor (H-canon-LET).
implementacion: `compilador/canonical.py`: en
`_CAMPOS_RENOMBRAR` (linea ~193) mapear
`"DeclaracionVariable": {"tipo": "tipo_annot"}` — al serializar, la anotacion
viaja como `tipo_annot` y el discriminante 'tipo' preserva el NOMBRE DE NODO;
al deserializar (`_dict_a_nodo`, caso especial ~L328) leer `d.get("tipo_annot")`.
Paridad con el AST nativo (nucleo/ast_nodes.syn:83 campo `tipo_param`).
`// cumple Manual 2 §13` en el fix.
oraculo: tests/integration/test_codegen_embebido_d_f1c.py (test_canonico_let_delegar_serializable)

## R2 — Asserts M2 §13 alineados (formato canonico plano)
requisito: Manual 2 §13
texto: "M2 §13 (175d268): el formato canonico es plano, sin wrapper
{synapse,ast}" (precedente ya ratificado para test_canonico_let_delegar_
serializable; los otros 5 asserts quedaron en el formato anterior).
implementacion: tests/integration/test_codegen_d2_genericos.py,
test_codegen_d6_propagar.py, test_codegen_embebido_d_f1.py,
test_codegen_embebido_d_f1_4.py, test_codegen_embebido_d_f1c.py:
reemplazar `data["synapse"] == "2.0"` por `data["tipo"] == "Programa"` en
6 asserts (paridad con test_codegen_embebido_d_f1c ya alineado).
// cumple Manual 2 §13
oraculo: tests/integration/test_codegen_embebido_d_f1c.py

## R3 — Asserts débil\<T\> alineados al runtime real (Manual 4 §4.2)
requisito: Manual 4 §4.2
texto: "débil<T>/weak<T> → WeakRef (struct con header+version para
invalidacion)" (M4 §4.2, implementado en ME-F23-7=795ce6f del 2026-08-24;
el test F1.2d era placeholder ABI 'hasta Fase 23').
implementacion: tests/integration/test_codegen_embebido_d_f1d.py: los 2
asserts `void* ref/debil_ref = nulo;` → `WeakRef ref = ((WeakRef){0});` /
`WeakRef debil_ref = ((WeakRef){0});` (autorizado Arquitecto regla 5,
decision del Arquitecto en sesion R183e). El cuerpo de la funcion @export
se verifica por el patron del Lifetime Scope (`int64_t r = (a + b);` +
`return _ret_`).
// cumple Manual 4 §4.2
oraculo: tests/integration/test_codegen_embebido_d_f1d.py

## R4 — Verificacion y cierre
requisito: Manual 9 §6.1
texto: "regresion: suite afectada + verificador de alineacion SIN BRECHAS".
implementacion: pytest de test_codegen_embebido_d_f1d.py 8/8 (incluidos los
2 E2E S2 ~222 s), vecinos 46 passed, `auditoria/verificar_alineacion.py`
SIN BRECHAS, lectura Manual 2 §13 registrada (gate de lectura).
oraculo: auditoria/verificar_alineacion.py

## Nota de verificación
La suite afectada completa se corrió manualmente: test_codegen_embebido_
d_f1d.py 8/8 GREEN (incluidos los 2 E2E S2, ~222 s cada uno) y los vecinos
(D2/D6/F1/F1c/F1_4 + test_ast_serialization) 46 passed; ver registos y
memoria del proyecto para el detalle.
