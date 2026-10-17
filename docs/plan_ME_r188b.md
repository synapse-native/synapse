# PLAN ME r188b — receive_resultado_nativo (H-R188-2)

**Base:** 9f6b1cd (r188_deuda_cero_1). **Resolución asignada (bitácora R188):**
stage1 nativo ACEPTA la sintaxis `coincidir c ->:` (paridad de ENTRADA hecha
en r188a: parser_sentencias.syn + lexer.syn) pero su CODEGEN/semántico trata
el sujeto como struct ADT/puntero → C roto (probe nativo rc=5).
MTS: plan citando Manual X §Y, oráculo ejecutado, expediente, gates 4b+5.

## R1 — codegen nativo del sujeto receive-modo-resultado

requisito: Manual 5 §3.6 + Manual 1 §3.1 (paridad M1 Ø1: mismo semantismo en
ambos pipelines).
texto: "Cuando se cierra un canal (`cerrar()`), los receptores que intenten
recibir obtienen un `Resultado<T, Error>` que indica cierre." (M5 §3.6 ej. L220:
`coincidir c ->:` con casos `ok(valor) =>` / `err(error) =>`).
implementacion (en vuelo, working tree): parser_sentencias.syn re-embraga el
sujeto identificador tras la flecha como NODO_RECIBIR_CANAL (span del token
sujeto, paridad con parsear_recibir_canal);
generador/monomorfizacion.syn R24: ADT genéricos BUILTIN Resultado<T,E>/
Opcion<T> + ctors ok/err registrados si el usuario no los declaró (paridad S1
context.py L385/L388/L394/L399) + gen_emitir_str_typedef_instancia;
generador/nodos_flujo.syn gen_visitar_coincidir: sujeto ExprRecibirCanal →
registrar instancia Resultado<elem,texto> + typedef global + flag
_G_co_modo_resultado;
generador/expr_eval.syn: receive en modo_resultado emite statement-expression
`canal_recibir(...&_ce0)` construyendo {.tag=0,.dato.ok=_unbox(...)} /
{.tag=1,.dato.err="canal cerrado"} (paridad emit_expressions.py r188);
orquestador.syn: definición única del global _G_co_modo_resultado.
Unity generator.syn regenerada (_rebuild_generator.py) // cumple Manual 5 §3.6
oraculo: tests/auditoria/test_oraculos_r188b.py — (a) NATIVO: `coincidir co ->:`
con `{.tag=0,.dato.ok=_unbox...}` ramas ok/err compila rc=0 vía synapse_stage2 y
ejecuta ok=7 / err="cerrado" (paridad S1, MISMA salida por main.py);
(b) NATIVO: regresión de la forma histórica `coincidir r:` sobre ADT declarado
(r183/r188) sin la flecha.

## Checklist de cierre (fase 4b + 5)

- `python auditoria/alineacion.py --leer --me r188b` (sello + lectura dirigida)
- lecturas previas del día por mapa_manuales (COMAS en --archivos)
- oráculo ejecutado (nativo + S1)
- expediente --nuevo → --verificar 0 brechas (cambio_hash sobre blobs STAGED)
- `contrastar --plan docs/plan_ME_r188b.md` RC=0
- `verificar_alineacion.py` SIN BRECHAS; regla 4: revisar artefactos
