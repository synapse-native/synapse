# Plan ME nativa_rc5_familia — Reparación de la familia de fallos nativos rc=5/rc=0 (H-R176-1)

**Fuente:** Mandato del Arquitecto (sesión 2026-10-02): "repara y corrige todo,
incluye todo lo que encuentres, no importa de quién es la deuda o la falla,
repara y alinea todo a los manuales, no dejes deuda nueva o antigua".
**Base:** b02ba7d (R176). **Método:** MTS (`docs/gobernancia/METODO_TRABAJO.md`).
**Alcance:** 4 reparaciones de paridad S1↔nativo detectadas por
`tests/integration/test_fase2_nativa_hm.py` (familia D del re-baseline R176):
8 fallos → 1 (restante r27 requiere decisión del Arquitecto, H-R177-1).

## R1 — canal_expr_nativo: `canal(tipo, capacidad)` dentro de expresión
requisito: Manual 5 §3.2
texto: "canal_async = canal<texto>(100)    // Asíncrono (buffer de 100)" (M5 §3.2
Sintaxis — la creación de canal es una expresión válida en posición de
inicializador/argumento, con paridad compilador/parser_expressions.py L225-236).
implementacion: `nucleo/parser_expr.syn` `parsear_primario`: rama
`si t == T_CANAL y token_mirar(est) == T_PAREN_IZQ:` DENTRO de la rama genérica
de nombre (crea NODO_CANAL_CREAR con payload tipo_contenido + hijo_izq
capacidad); se elimina la rama muerta `si t == T_CANAL:` final (regla 10,
código muerto) que devolvía la llamada cruda y gcc fallaba
`'entero' undeclared` (rc=5).
// cumple Manual 5 §3.2 (ME canal_expr_nativo R1)
oraculo: tests/auditoria/test_oraculos_nativa_rc5_familia.py (test_r1: canal en
expresión + listener, probes rc=0).

## R2 — constantes_tipadas_nativo: constante de módulo con inicializador escalar
requisito: Manual 2 §2, §4.1
texto: "declaracion_constante ::= \"constante\" IDENTIFICADOR \"=\" expresion
NEWLINE" (M2 §2 L70) + "entero / int — Entero con signo de 64 bits — Alias de
`int64_t`" (M2 §4.1 tabla). Una constante con inicializador `5` es un `int64_t`:
`X + 1` es aritmética, NO concatenación de texto.
implementacion: escáner de constantes `nucleo/generador/escaneo.syn`: array
paralelo `char _G_native_consts_txt[512]` con bandera 1 por defecto, APAGADA solo
si el inicializador es LiteralNumero/LiteralDecimal/LiteralBooleano/LiteralNulo
(inversión conservadora: cadenas calculadas conservan el comportamiento antiguo).
Consumidor `nucleo/generador/expr_eval.syn` (rama `_ot == 30` de OpBinaria `+`):
exige bandera para emitir `concat`; si bandera apagada emite aritmética tipada
`(X + 1LL)`. Definición del array en `nucleo/generador/orquestador.syn` y en
`compilador/generator/generator.py` en AMBAS rutas (unity ~L1139, modular
~L1880): `ctx.write_line("char _G_native_consts_txt[512];")`. Unity
`nucleo/generator.syn` REGENERADA con `python nucleo/_rebuild_generator.py`
(patrón TRES PIEZAS, lección R163).
// cumple Manual 2 §2, §4.1 (ME constantes_tipadas_nativo R2)
oraculo: tests/auditoria/test_oraculos_nativa_rc5_familia.py (test_r2:
calcular(3) imprime 4 vía S1, no "51").

## R3 — fibra_args_pool_order: pool_destroy DESPUÉS de esperar fibras
requisito: Manual 6 §2.2
texto: "// Ejecutar programa\n    principal();\n    \n    // Esperar a que
terminen todas las fibras\n    scheduler_join();\n    \n    // Liberar
recursos\n    global_pool_free();" (M6 §2.2 L210-229 — el orden canónico es
principal → esperar fibras → liberar pool).
implementacion: `compilador/generator/generator.py` `_emit_main` (4 sitios: stub
de biblioteca H-R90-8, rama no_std, rama nulo, rama con retorno): reordenar a
`synapse_esperar_hilos(); synapse_esparar_fibras(); pool_destroy();`. Antes:
`pool_destroy()` ANTES de esperar → las fibras leían args `pool_alloc`-eados de
memoria ya liberada → `ESCAPA_DEL_ALCANCE: canal nulo en canal_enviar` ×2 →
segfault 0xC0000005 (paridad con el nativo `nucleo/generador/recorrido.syn`
L307-311, que ya emitía el orden correcto). Corrige además la cita fabricada
"Manual 6 §4.4" (sección inexistente) por §2.2.
// cumple Manual 6 §2.2 (ME fibra_args_pool_order R3)
oraculo: tests/auditoria/test_oraculos_nativa_rc5_familia.py (test_r3:
fibras esperadas antes de pool_destroy, 42/44 rc=0 sin ESCAPA_DEL_ALCANCE;
unit 544 PASSED).

## R4 — cluster_ident_type: asignación a variable nueva con RHS Identificador
requisito: Manual 2 §8.2, §4.1
texto: "Synapse utiliza un algoritmo de inferencia de tipos basado en
**Hindley‑Milner** (algoritmo W)." (M2 §8.2 L479) + M2 §4.1 (texto = CadenaSegura
16 bytes). `mensaje_nonce = nonce` con `nonce: texto` debe declarar
`CadenaSegura mensaje_nonce`, no `int64_t`.
implementacion: (a) `nucleo/generador/funciones.syn` (hoisting pre-scan, bloque
`_hvt`): rama nueva `Identificador` que hereda el tipo C YA REGISTRADO de la
variable fuente en `_G_fn_var_tipos` (el pre-scan registra en orden de cuerpo,
la fuente asignada antes ya está tipada); fallback int64_t. (b)
`nucleo/generador/nodos_flujo.syn` `gen_visitar_asignacion`: rama `_ident_type`
paritaria en la cadena de emisión y de registro (paridad S1
`tipo_de_expr` emit_expressions.py L89-93 vía `visitar_asignacion`
emit_declarations.py L142-152). Unity `nucleo/generator.syn` REGENERADA.
Bootstrap S1→S2 reconstruido y sellado.
// cumple Manual 2 §8.2 (ME cluster_ident_type R4)
oraculo: tests/auditoria/test_oraculos_nativa_rc5_familia.py (test_r4:
importar std.cluster compila y corre, 193 rc=0).

## R5 — const_macro_colision: constante de módulo deja de ser #define C
requisito: Manual 2 §2
texto: "declaracion_constante ::= \"constante\" IDENTIFICADOR \"=\" expresion
NEWLINE" (M2 §2 L70) — una constante es un IDENTIFICADOR inmutable; un
parámetro/local del mismo nombre la sombrea (innermost-first, R9). El #define
C se expande DENTRO de la firma que sombrea: `#define X (5LL)` +
`int64_t calcular(int64_t X)` → gcc "expected ')' before numeric constant"
(rc=5).
implementacion: paridad con el generador nativo (NO emite macros de usuario;
verificado en C fresco: el nativo emite la constante usada como objeto). S1
`compilador/generator/emit_declarations.py` (visitar_constante, rama módulo) y
`compilador/generator/generator.py` (_emitir_constantes_programa, header):
enteros/booleanos literales en rango int → `enum { NOMBRE = v };` (constante C
verdadera: case/asm/inicializadores sí; sombra por parámetro legal); resto →
`static const {tipo} NOMBRE = v;` (texto → char*). Guardas
`_SYN_CSTDECL_NOMBRE` contra la doble emisión entre ambos sitios. Referencias
sin cambio (nombre crudo resuelve por scoping C; asm strings intactos).
Descubridor: oracle test_r2 vía S1 — build rc=1 ANTES del fix.
// cumple Manual 2 §2 (ME nativa_rc5_familia R5)
oraculo: tests/auditoria/test_oraculos_nativa_rc5_familia.py (test_r5:
constante en expresión + texto vía S1 rc=0; bootstrap S1→S2 reconstruido
rc=0 tras el cambio de codegen).

## H-R177-2 (hallazgo, requiere Arquitecto): parser nativo de `coincidir` sin patrones literales ni wildcard
M2 L123-127 define `caso_coincidir ::= patron "=>"` con `patron ::=
IDENTIFICADOR "(" IDENTIFICADOR ")" | IDENTIFICADOR | "_"`. El S1 acepta
TAMBIÉN patrones literales para primitivos (H-R90-6: `case {patron}:` en
emit_control.py). El parser NATIVO (nucleo/parser_sentencias.syn ~L570) solo
acepta patrones que empiezan con token_es_nombre: `caso 3 =>` y `caso _ =>`
fallan con "Error de sintaxis" (probe r5_ref.syn verificado con stage2,
rc=127). Un programa que S1 parsea (H-R90-6) el nativo NO lo parsea: brecha
de paridad de PARSER (feature gap), NO falla de codegen C de la familia
H-R176-1. NO se toca en este ME (tests inmutables + riesgo de parser).
Resolución asignada: decisión del Arquitecto — (a) ME propio para añadir
patrones literales/wildcard al parser nativo + emisor NodoCoincidir, o (b)
restringir H-R90-6 en S1 para paridad estricta.

## H-R177-1 (hallazgo, requiere Arquitecto): test_r27 contradice H-R153-4b ratificada
El test `test_r27_struct_ctor_con_argumentos_rechazado` exige que el nativo
RECHACE `Punto(1,2)` con rc=7 "se esperaban 0", pero r153 ratificó H-R153-4b
(`nucleo/analizador_semantico.syn` L733-737, ancla): se RELAJÓ el check de
aridad del ctor de struct y S1 (semantic_types.py L522-538, H-R153-4) ACEPTA la
forma posicional `Punto(3,4)` con 1 argumento por campo declarado (cita Manual 2
L67 declaracion_estructura). Implantar el rechazo rompería la decisión ratificada
y la paridad S1↔nativo. REGLA: tests inmutables → DETENTE Y PREGUNTA.
Resolución asignada: decisión del Arquitecto entre (a) actualizar el test
(aprobación explícita) o (b) revertir H-R153-4/4b. NO se toca ni test ni decisión.

## Verificación global
- `.venv/Scripts/python.exe auditoria/verificar_alineacion.py` — 0 brechas.
- `python auditoria/alineacion.py --verificar --me nativa_rc5_familia`.
- Suites: unit 544✓, matriz 1✓, syquex/opensyn/axon 407✓/3✗ (wasm RED TDD
  conocido, sin cambio), fase2 familia 7✓/1✗ (r27=H-R177-1).
- Artefactos tracked regenerados por la suite → `git checkout --` antes de
  commitear (tests/fixtures/test_a23_parity.*, tests/integration/_*.c,
  _synapse_shared.h, test_cluster_handshake.c).
