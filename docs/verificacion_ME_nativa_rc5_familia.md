# Verificación ME nativa_rc5_familia — familia nativa rc=5/rc=0 (H-R176-1)

Fecha: 2026-10-03 · Verificador: `auditoria/contrastar.py` (gate MTS fase 4b)
Base: b02ba7d (R176, re-baseline 1453✓/104✗). Oráculo:
`tests/auditoria/test_oraculos_nativa_rc5_familia.py` — **GREEN 5/5** (10.7 s;
5 programas E2E compilados con main.py y ejecutados: canal en expresión,
constante escalar, fibras+pool, std.cluster, constante texto+entero).
Cambio: 4 reparaciones de paridad S1↔nativo detectadas por
`tests/integration/test_fase2_nativa_hm.py` (8 fallos de la familia → 1; el
restante r27 = H-R177-1, requiere decisión del Arquitecto).

## R1 — Manual 5 §3.2 (canal(tipo, capacidad) en EXPRESIÓN) — CUMPLE
`nucleo/parser_expr.syn` `parsear_primario`: rama `T_CANAL` + `T_PAREN_IZQ`
dentro de la rama genérica de nombre crea NODO_CANAL_CREAR (tipo contenido +
capacidad); eliminada la rama muerta de T_CANAL (código muerto). Oráculo
test_r1: `canal_async = canal<texto>(100)` en inicializador + listener
imprime 42/99, rc=0 (antes gcc rc=5 `'entero' undeclared`).

## R2 — Manual 2 §2 (constante escalar NO es texto) — CUMPLE
Escáner de constantes nativo `nucleo/generador/escaneo.syn`: array paralelo
`_G_native_consts_txt[512]` (1 por defecto, 0 solo si el inicializador es
literal numérico/bool/nulo). Consumidor `nucleo/generador/expr_eval.syn`
(rama `_ot == 30` de OpBinaria `+`): concat solo si bandera activa; si no,
aritmética tipada `(X + 1LL)`. Definición del array en
`nucleo/generador/orquestador.syn` y en `compilador/generator/generator.py`
(unity ~L1154 y modular ~L1909). Oráculo test_r2: `calcular(3)` imprime 4
vía S1 (antes "51", rc=5 en el nativo por el macro del usuario).

## R3 — Manual 6 §2.2 (orden principal → esperar fibras → liberar pool) — CUMPLE
`compilador/generator/generator.py` `_emit_main` (4 sitios: stub de
biblioteca H-R90-8, no_std, nulo, con retorno): reordenado a
`synapse_esperar_hilos(); synapse_esparar_fibras(); pool_destroy();`
(paridad con `nucleo/generador/recorrido.syn` L307-311). Corrige además la
cita fabricada "Manual 6 §4.4" (sección inexistente) por §2.2. Oráculo
test_r3: fibras 42/44 rc=0 sin `ESCAPA_DEL_ALCANCE` (antes segfault
0xC0000005 por args liberados).

## R4 — Manual 2 §8.2 (inferencia HM: RHS Identificador hereda tipo) — CUMPLE
`nucleo/generador/funciones.syn` (hoisting `_hvt`): rama Identificador hereda
el tipo C de la variable fuente en `_G_fn_var_tipos`; `nucleo/generador/
nodos_flujo.syn` `gen_visitar_asignacion`: rama `_ident_type` paritaria en
emisión y registro (paridad S1 `tipo_de_expr` L89-93). Unity
`nucleo/generator.syn` regenerada (`nucleo/_rebuild_generator.py`). Oráculo
test_r4: `importar std.cluster` compila y corre, 193 rc=0.

## R5 — Manual 2 §2 (constante de módulo: identificador sombreable, no macro C) — CUMPLE
`compilador/generator/emit_declarations.py` `visitar_constante` + 
`compilador/generator/generator.py` `_emitir_constantes_programa`: enteros/
bools literales en rango → `enum { NOMBRE = v };`; LiteralCadena →
`static const CadenaSegura` (sizeof-1); resto inicializador constante →
`static const {tipo}` con guardas `_SYN_CSTDECL_`; excepción ABI:
`T_*/NODO_*/ERR_*/_` permanecen `#define` (colisionan con
`runtime/core/ast_nodos.h`, detectado en el primer bootstrap). Helper
`cadena_c_literal` compartido en `compilador/generator/emit_expressions.py`
(escapes \xHH para control <0x20). Paridad: el nativo no emite macros de
usuario (verificado en C fresco). Oráculo test_r5: constante texto+entero
"hola"/4 rc=0 vía S1; probes nativos r9_sombra→4, r_const_uso→6/hola.

## Bootstrap y regresión (verificación global del ME)
- Bootstrap S1→S2 reconstruido con R5: stage1 rc=0 (0 errores), stage2 rc=0;
  probes nativos íntegros (r9_sombra=4, r_const_uso=6/hola).
- unit 514✓ (4:39) · micro_bootstrap+nucleo+synapse 30✓ (2:29) ·
  fase2 -k "r9 or r27 or f37 or f313" → 10✓/1✗ (r27 = H-R177-1) · matriz 35✓.
- `auditoria/verificar_alineacion.py`: 0 brechas (gate contrastar).

## Hallazgos sin resolver (DETENTE Y PREGUNTA — decisión del Arquitecto)
- **H-R177-1:** test_r27 exige rechazar `Punto(1,2)` con rc=7, pero r153
  ratificó H-R153-4b (relaja aridad de ctor, paridad S1 H-R153-4). Tests
  inmutables → no se toca ni test ni decisión ratificada.
- **H-R177-2:** el parser nativo de `coincidir`
  (`nucleo/parser_sentencias.syn` ~L570) solo acepta patrones
  `token_es_nombre`; S1 acepta además literales/wildcard (H-R90-6). Brecha de
  paridad de PARSER (feature gap), no de codegen: `caso 3 =>` y `caso _ =>`
  fallan en nativo ("Error de sintaxis", probe r5_ref.syn rc=127). NO se
  toca en este ME. Resolución asignada: (a) ME propio para patrones
  literales/wildcard en nativo, o (b) restringir H-R90-6 en S1.

## Deudas menores registradas (resolución asignada)
- stage2 sin `-o` se sobreescribe a sí mismo → documentar convención
  (compilar stage2 siempre con `-o synapse_stage2.exe`).
- Ruta modular Python no regenera `_X.c` si es más nuevo que el `.syn` →
  convención: `rm -f nucleo/_X.c` antes de recompilar (trampa confirmada).
- Pipes en bash ocultan el rc real (`cmd | tail; echo $?` = rc de tail) →
  convención: `cmd > log 2>&1; echo $?`.
