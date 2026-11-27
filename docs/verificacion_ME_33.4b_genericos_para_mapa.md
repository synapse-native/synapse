# Verificación ME 33.4b_genericos_para_mapa — Fase 33.4 (cierre de H-R153-3)

Fecha: 2026-09-28 · Verificador: `auditoria/contrastar.py` (gate MTS fase 4b)
Oráculo: `tests/auditoria/test_oraculos_334b_genericos.py` — **GREEN 6/6**
(probes E2E reales en ambas capas — S1 vía main.py y nativo vía
`synapse_stage2.exe` — para genéricos de usuario, `para k en mapa` con
`claves()` + `m[k]`, y anti-fabricación: sin instanciación genérica el unity no
emite typedef monomorfizado; `_exe_fresco()` con mtime de las fuentes).
Cambio: genéricos de usuario `estructura Caja(T):` con monomorphización
(`Caja(5)` → `Caja_entero`), `para k en mapa` (itera claves, D-R163-1:
k=claves, valor vía `m[k]` de 33.4a) y métodos `claves()`/`valores()` del Mapa.
Matriz 35/35 + unit 544/544 PASSED.

## R1 — Manual 2 §2 (gramática: `estructura Caja(T):` con paréntesis) — CUMPLE
`compilador/parser_declarations.py` `_parsear_def_estructura` (~L171) acepta el
`( IDENTIFICADOR )` opcional tras el nombre → `DefinicionEstructura.param_generico`
(`compilador/ast_nodes.py`). Lado nativo: `nucleo/parser_declaraciones.syn` (~L21)
ata NODO_PARAMETRO en hijo_der via asm; `nucleo/ast_nodes.syn` añade el campo y
`nucleo/puente_ast.syn` (~L443) lo puentea (`puente_cs_str`). Oráculo
`test_s1_generico_e2e` GREEN (`caja: 5` rc=0).

## R2 — Manual 2 §8.2 (algoritmo W: `Caja(5)` unifica T=entero) — CUMPLE
`compilador/emit_expressions.py`: `_registrar_instancia_generica` (~L361,
normaliza alias int→entero, mangle `Caja_entero`) + rama en `tipo_de_expr`
LlamadaFuncion + ctor compound literal; `_metodo_a_c` (~L449) emite el C de
métodos (quirk r153 corregido: `tipo_de_expr` rama `metodo:` devuelve TIPO).
`semantic_types.py` unifica T en el constructor y sustituye en `c.valor`
(paridad D-2 de ADT). `generator.py`: `_recolectar_instancias_genericas`
(pre-scan), typedefs alfabéticos en pre-bloque 'completo' y antes de cada
función (modular), forward decls excluye genéricas. Oráculo
`test_s1_generico_e2e` GREEN + `test_anti_fabricacion_sin_generico` GREEN.

## R3 — Manual 2 §4.3 (Mapa: `para k en mapa` itera claves; D-R163-1) — CUMPLE
`compilador/generator/emit_control.py` `_emitir_para_en` (~L106): rama `Mapa<`
ANTES de Lista — `_syn_mapa_claves(m)` → for sobre Lista<texto> con claves
encajonadas `CadenaSegura*` (deref por dirección, H-R153-2) + `_syn_lista_liberar`
al cerrar (RAII). El "par ordenado" del ROADMAP contradice M3 §3 L133 (UN
identificador) → decisión D-R163-1 pendiente de ratificación del Arquitecto.
Oráculo `test_s1_para_en_mapa_e2e` GREEN (`clave: a/b`).

## R4 — Manual 2 §2 + §4.3 (nativo: mismo contrato que S1) — CUMPLE
`nucleo/generador/monomorfizacion.syn` `gen_escanear_genericas` (3 fases:
plantillas → escaneo de instanciaciones → typedefs con campos sustituidos),
invocada por `nucleo/generador/orquestador.syn` tras `gen_escanear_adt_instancias`
(L~478); resolución de tipo en `_syn_nativo_expr_tipo_c` + alias normalizado en
los 3 puntos (scan/resolve/hoisting). `nucleo/generador/nodos_flujo.syn` rama
`Mapa<` del para-en (entre Lista y texto) con liberación tras el cierre del for
y registro del tipo real de la var de bucle. `nucleo/generador/expr_eval.syn`:
llamada genérica → compound literal `(Caja_entero){7LL}`; métodos
claves/keys/valores/values → `_syn_mapa_claves/_syn_mapa_valores`.
`runtime/core/mapa.c`: `_syn_mapa_claves` encajona como `CadenaSegura*` (heap,
paridad `_encajonar_slot`) y firmas `longitud`/`contiene` alineadas al header
ABI `synapse_rt_types.h` L254-273 (`int`, no `int64_t`). Oráculo
`test_nativo_generico_e2e` + `test_nativo_para_en_mapa_e2e` GREEN (salida
idéntica a S1 en los 3 probes).

## R5 — Manual 1 §6 (no romper el bootstrap; módulo TDD en matriz) — CUMPLE
Unity `nucleo/generator.syn` regenerada con `_rebuild_generator.py` tras cada
cambio en `nucleo/generador/*`; bootstrap stage1→stage2 reconstruido fresco
(sin timestamps stale); test TDD añadido a `tests/nucleo/test_modulos_compilan.py`
(compila el módulo de prueba 33.4b en matriz) — PASSED; matriz
`tests/auditoria/test_matriz_compilacion.py` 35/35 PASSED; regresión unit
completa 544/544 PASSED (0 brechas tras los fixes semánticos y del runtime).
El oráculo usa `_exe_fresco()` que reconstruye el bootstrap si está stale.

## Contratos y gates
- `gen_escanear_genericas` lleva contratos requiere/garantiza (M2 §12) —
  `verificar_alineacion.py` 0 brechas.
- Gate MTS `contrastar.py --plan docs/plan_ME_33.4b_genericos_para_mapa.md`:
  PASADO completo (citas válidas + oráculos ejecutados + este documento).
- Expediente `docs/alineacion/33.4b_genericos_para_mapa.md`: 0 brechas en
  `alineacion.py --verificar --me 33.4b_genericos_para_mapa` (con oráculo).
