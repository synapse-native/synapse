# PLAN MAESTRO DE DEUDAS — mandato "repara todas las deudas, nunca deuda nueva o antigua"

**Fecha:** 2026-10-03 · **Base:** 4ebd025 (R177) · **Autoridad:** Arquitecto —
"estas autorizado a tomar las decisiones siempre que sigas las reglas".
**Regla de dirección del Arquitecto (sesión 2026-10-03):** los tests SOLO se
modifican para ALINEARLOS al manual. Si el código está alineado y el test no,
se modifica el test aplicando TDD (RED→GREEN) y verificando con MTO.
Todo ME sigue el ciclo MTS completo (plan → leer → codificar → oráculo →
gates → commit → docs post-commit) y cita Manual X §Y en cada archivo tocado.

## Cola de MEs (prioridad por radio/costo, actualizable)

### ME R178 — check_cli (H-R176-2) — `synapse check` en cli.py
requisito: Manual 8 §4 (+ subfase 26.1 del ROADMAP: flag `--check`/`--no-emit`
para validación rápida usada por el LSP/OpenSyn).
texto: el test test_cli_check (3 fallos) declara en su propio mensaje
"Binario synapse no encontrado — implementar CLI (M8 §4)" — feature gap
DECLARADO. El dispatcher Python no implementa `check` (valida sintaxis +
semántica sin generar código).
implementacion: cli.py despacha `check` al backend (validación sin emitir
binario, paridad con `--check`/`--no-emit` existente en pipeline.py/ principal.syn
según lo que el test exija); oráculo E2E tests/auditoria/test_oraculos_check_cli.py.
impacto: cierra 3 fallos de integración.
estado: COMPLETADO (R178 95b2374 — H-R176-2 cerrada, oráculo 4/4, OBL-M8-16)

### ME R179 — h_r177_1 test_r27: alinear test↔manual↔código (aridad de ctor)
requisito: Manual 2 (declaracion_estructura / instanciación: constructor con
argumentos por campo). Ley: Manual 2 L67 define el ctor posicional.
Decisión autorizada: el CÓDIGO vigente (H-R153-4b ratificada en r153: se RELAJÓ
el check de aridad aceptando ctor posicional con 1 arg por campo, paridad
S1↔nativo) está ALINEADO al Manual 2 (la gramática del ctor posicional existe
en el manual y S1+nativo la implementan de forma paritaria). El test
test_r27_struct_ctor_con_argumentos_rechazado espera el comportamiento PRE-r153
(rechazo rc=7) que ya NO es la ley vigente.
implementacion (TDD/MTO con autorización de dirección del Arquitecto):
invertir la aserción del test a la semántica ACEPTADA por el manual (o
reemplazarla por el caso que sí se rechaza según M2) — RED primero: el test
nuevo falla contra el código actual solo si el código desviara al manual;
GREEN con el código alineado vigente. Verificación MTO del requisito.
impacto: cierra r27 (último fallo de la familia nativa rc=5/rc=0 → familia en CERO).
estado: COMPLETADO (R179 0faea8e — H-R177-1 cerrada, oráculo 4/4, OBL-M2-05)

### ME R180 — coincidir_nativo (H-R177-2): paridad de parser nativo
requisito: Manual 2 §2 — el patrón de `coincidir` según M2 L123-127 es
IDENTIFICADOR/tag/var o "_" (wildcard). S1 además acepta literales (H-R90-6).
Decisión autorizada: implementar en el parser NATIVO el wildcard `_` y los
literales de primitivos que S1 ya acepta (paridad M1 §3.1: mismo AST canónico;
el manual define patron ::= ... | "_" para wildcard, los literales extienden
H-R90-6 vigente en S1).
implementacion: nucleo/parser_sentencias.syn (patrón: token_es_inicio_patron =
token_es_nombre OR T_NUMERO — el wildcard `_` ya lexea como T_IDENTIFICADOR),
emisor NodoCoincidir nativo con case C para literales/wildcard → default
(gen_visitar_coincidir: switch sobre VALOR si dígito en patrones o tipo C
exacto int64_t/int/bool — espejo PRIMITIVOS de emit_control.py; ruta ADT
.tag byte-idéntica), S1 _parsear_coincidir acepta TokenID.NUMERO; puente de
patrones intacto (el patrón sigue siendo un span de texto).
oráculo E2E: coincidir con literal y wildcard compila y corre en nativo.
impacto: paridad total de coincidir S1↔nativo (para patrones numero/wildcard;
residuales: patrón cadena — C no soporta case string, falla igual en ambas
tuberías — y forma de BLOQUE en nativo → ME R183).
estado: COMPLETADO (R180 be5d447 — H-R177-2 cerrada, oráculo 4/4 273.75 s,
OBL-M3-06; H-R180-3 lección TDD: heurística invertida detectada por el
oráculo r4 y corregida a tipo C exacto; H-R180-2 lección de cadena:
rebuild generator.syn SIEMPRE tras editar generador/ y antes de bootstrapear)

### ME R181 — harness_gcc (H-R176-1): entorno de integración
requisito: Manual 9 §6.2 (entorno de CI reproducible: los tests del repo no
pueden depender de exes/objetos inexistentes ni de rutas de include rotas).
Diagnóstico previo (R176): embedded_libs.h no resuelto desde tests/, link del
runtime completo con --allow-multiple-definition, 21 RED TDD exigen artefactos
que nadie construye.
implementacion: reparar el comando gcc del harness (rutas -I, orden de objetos,
targets on-demand para los artefactos que los RED exigen — construcción real,
no stubs). Los tests NO se tocan (no es su deuda).
impacto: ~27 fallos de una vez + habilita medir los RED TDD de verdad.
estado: COMPLETADO (R181 9657482 — H-R176-1 cerrada: CPATH raíz + quantum .o on-demand + shim weak GNUC S1/nativo; oráculo 5/5; quantum 8/8; TestEjecucionReal migrado a exit code via MTO; bootstrap 3 etapas stage2==stage3 c2889554…c91d43; deudas NO-harness halladas en el camino a filas R184/R185/R186)

### ME R184 — lexer_y_keyword (H-R181-3, hallado en R181)
requisito: Manual 2 §2/§3 — la gramática de parámetros acepta IDENTIFICADOR; el
lexer debe clasificar `y` como AND SOLO en posición de operador (o el parser
debe reconocer `y` como nombre de parámetro). Ley: identifiers suelen ir en L21
del lexer (y=keyword AND).
hallazgo: `crear_punto(x: entero, y: entero)` no se parsea porque `y` es
keyword AND del lexer S1 (lexer.py L21, ruta keywords L630-650) — el test
test_programa_estructura_ejecuta (TestEjecucionReal, aserción MTO rc==55) queda
RED por esta deuda, no por su aserción.
implementacion: análisis de contexto del lexer (operador binario vs posición de
nombre: tras `:` o `,` es identificador) o reorden de tabla de keywords; TDD
con el checksum de estructura como GREEN.
impacto: cierra el RED de estructura; desbloquea programas con `y` como
nombre.
estado: PENDIENTE (registrado 2026-10-06 en R181 9657482)

### ME R185 — stdlib_colision_generador (H-R181-4, hallado en R181)
requisito: Manual 2 §9.1/§12 — el C generado debe ser válido; los nombres de
funciones de usuario no pueden colisionar con la stdlib cuyo header se incluye
incondicionalmente.
hallazgo: una función usuario `abs(x: entero)` genera `int64_t abs(int64_t);`
en conflicto con `int abs(int)` de stdlib.h (incluida incondicionalmente) →
gcc error "conflicting types for 'abs'"; afecta a min/max/exit/cualquier
nombre stdlib.
implementacion: prefijado de símbolos usuario (paridad con el mangle de
monomorfos) o no-emisión de prototipos innecesarios cuando la función es local
al modulo; TDD con test_programa_si_sino_ejecuta (aserción MTO rc==5) como
GREEN.
impacto: cierra el RED de si_sino; elimina una clase entera de colisiones.
estado: PENDIENTE (registrado 2026-10-06 en R181 9657482)

### ME R186 — toml_raii_runtime (H-R181-1, hallado en R181)
requisito: Manual 5 §5 (toml del runtime) + Manual 2 §9.1 — el test
test_toml_compile_and_run exige compilar, Y ejecutar la escritura/lectura toml
RAII.
hallazgo: tras R181 el test COMPILA Y ENLAZA (CPATH + shim weak) pero el exe
falla en runtime (salida vacía / segfault 0xC0000005 con toolchain canónico):
deuda funcional RAII/toml del path standalone (probe de R181).
implementacion: diagnóstico del segfault (determinar si es del código toml
embebido o del runtime RAII en el path standalone de la suite), reparación y
paridad S1↔nativo.
impacto: cierra el último RED de la familia que era de enlace-ahora-runtime
toml.
estado: PENDIENTE (registrado 2026-10-06 en R181 9657482)

### ME R182+ — feature gaps (cola, una por ME con TDD)
- wasm extendido (Fase 25: i64/f64/imports/exports — 3 RED ya escritos).
- H-R90-5 (métodos sobre locales en .syq).
- ME_27/29/30 (~21 RED TDD: aiComplete/aiExplain/aiFix, federated, quantum
  build, build/release) — R181 (harness) COMPLETADO: ya medibles.
- YAML de CI release (10): signing/SLSA — infraestructura, requiere secretos →
  documentar como deuda de infra con resolución asignada si no es local.
- ~46 asserts residuales por familia (axon, borrowing, debug CLI, escuchar,
  serialización embebida, lexer rc/modulo, salida_metal.c) tras R181.
estado: PENDIENTE

## Reglas transversales del plan
1. Cada ME: plan citando Manual X §Y → `alineacion.py --leer --me <id>` →
   codificar con `// cumple Manual X §Y` → oráculo E2E → unit/regresión →
   expediente + contrastar + verificar_alineacion → commit → docs post-commit.
2. Tests: solo para alinearlos al manual (dirección test→código o código→test
   según dónde viva la verdad, con TDD RED→GREEN y MTO). NUNCA relajar un test
   que codifica el manual vigente.
3. Deuda hallada en el camino: se repara o se registra con resolución asignada
   (cero deuda sin seguimiento). Deuda antigua del mismo archivo/área: misma
   oportunidad de reparación (mandato "no importa de quién es").
4. Antes de commitear: artefactos regenerados por suites → `git checkout --`.
5. Prohibido --no-verify; los 7 gates del pre-commit mandan.

### ME R183 — coincidir_bloque_nativo (H-R180-1, hallazgo de R180)
requisito: Manual 3 §3 L140 — `caso ::= patron "=>" ( sentencia | NEWLINE
INDENT bloque DEDENT )`: la segunda alternativa (cuerpo en bloque) ES ley
(y S1 la implementa: r5_ref compila y corre `tres/hola/4`).
hallazgo: el pipeline NATIVO falla con `Error Fatal Generador: Nodo tipo
[DefinicionFuncion] no reconocido` para CUALQUIER coincidir con cuerpos-bloque,
INCLUSO patrones ADT pre-existentes (bisección R180: sin coincidir pasa;
una-línea pasa; bloque-literal y bloque-ADT fallan igual) — el problema está
en la construcción del AST del caso con cuerpo-bloque o en el walk del
generador nativo, no en los literales.
implementacion: rastrear parsear_coincidir nativo (parser_sentencias.syn: rama
NEWLINE-INDENT del cuerpo del caso) y el walk del generador (recorrido.syn /
nodos_flujo.syn) hasta la divergencia; TDD con probe bloque-ADT (bisect_d de
/tmp/probe_lf) como RED.
oráculo: bloque-ADT y bloque-literal compilan rc=0 y ejecutan en nativo con
paridad S1.
impacto: cierra la segunda forma del caso en nativo (paridad total M3 §3).
estado: PENDIENTE (registrado 2026-10-05 en R180 be5d447)
