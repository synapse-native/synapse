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
estado: EN CURSO

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
estado: PENDIENTE

### ME R180 — coincidir_nativo (H-R177-2): paridad de parser nativo
requisito: Manual 2 §2 — el patrón de `coincidir` según M2 L123-127 es
IDENTIFICADOR/tag/var o "_" (wildcard). S1 además acepta literales (H-R90-6).
Decisión autorizada: implementar en el parser NATIVO el wildcard `_` y los
literales de primitivos que S1 ya acepta (paridad M1 §3.1: mismo AST canónico;
el manual define patron ::= ... | "_" para wildcard, los literales extienden
H-R90-6 vigente en S1).
implementacion: nucleo/parser_sentencias.syn (patrón: token_es_nombre OR "_" OR
literales de tokenizador), emisor NodoCoincidir nativo con case C para
literales/wildcard → default, unity si corresponde; puente de patrones.
oráculo E2E: coincidir con literal y wildcard compila y corre en nativo.
impacto: paridad total de coincidir S1↔nativo.
estado: PENDIENTE

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
estado: PENDIENTE

### ME R182+ — feature gaps (cola, una por ME con TDD)
- wasm extendido (Fase 25: i64/f64/imports/exports — 3 RED ya escritos).
- H-R90-5 (métodos sobre locales en .syq).
- ME_27/29/30 (~21 RED TDD: aiComplete/aiExplain/aiFix, federated, quantum
  build, build/release) — dependen de R181 (harness) para medirse.
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
