# PLAN ME f14_mto_ci — cierre del lote en vuelo de la sesión anterior

**Base:** b44a96d (ME R184 abierto). **Fecha:** 2026-10-14. **Mandato:** recupera la
sesión anterior, alinea manuales, cero deuda nueva o antigua sin reparar.

El lote sin commit de la sesión anterior contiene 5 frentes. Este plan los
formaliza con citas literales del manual y oráculos ejecutados (MTS).

## R1 — lexer.py: keywords contextuales + migración del check de cuerpos (H-F1.4-1/2)

requisito: Manual 1 §3.1 — pipeline compartido: el Lexer es fase de tokens de
bajo nivel y el Parser construye el AST; la existencia de cuerpo-bloque tras
`funcion:` es verificación del parser, no del lexer. Manual 2 §3 (tabla de
palabras reservadas multi-idioma): `rc`/`modulo`/`arc` son keywords
CONTEXTUALES del Manual 2 §3 (F1.4, registro docs/reportes/F1.4.md) — en
posición de variable/parámetro conservan su lexema como nombre.
texto: H-F1.4-1 — `_validar_cuerpos` del lexer (check de bloque indentado)
emigra al parser (TestParserFunciones + RecuperacionErrores siguen activos);
H-F1.4-2 — paridad con el lexer auto-hospedado `nucleo/lexer.syn`: `modulo`/
`module`/`rc`/`arc` en contexto identificador emiten SU TokenID preservando el
lexema en .valor (no degradan a IDENTIFIER genérico que el oráculo rechaza).
Además: archivo vacío → mismo mensaje de familia "falta #lang" (M2 §2).
implementacion: compilador/lexer.py — cumple Manual 1 §3.1/§3.2. // cumple
Manual 1 §3.1
POST-PROBE (2026-10-14): el check migrado NO existía en el parser — una firma
sin cuerpo compile a rc=0 (`main.py firma.syn` GREEN, violando la gramática
M2 §2 L56 NEWLINE INDENT bloque DEDENT obligatorio); check restaurado en
`_parsear_def_funcion` (ERR_LEX portador genérico, mensaje exacto del check
original; rc=1 verificado por probe). Tests【test_lexer_cobertura】 alineados
de la forma pre-F1.4 a la ley vigente: firma sin cuerpo SE TOKENIZA (el error
es del parser) y archivo vacío usa el mensaje de familia sin-#lang; regresión
unit 514✓ / syquex 279✓ tras el cambio de parser.
oraculo: tests/integration/test_codegen_embebido_d_f1c.py (5✓ release
bootstrap) y tests/integration/test_codegen_embebido_d_f1_4.py (9✓) y
tests/unit/test_lexer.py (63✓) — ejecutados el día.

## R2 — citas MTO anexadas + test OBL-M1-01 + roto reparado

requisito: MTO (Manual Tests Obligatorios, M1 §9/§4, M3-M9 OBL-*): todo test
que cubre un OBL porta la cita `Cumple MTO OBL-MX-NN`; la deuda "GREEN sin
ocurrencia que cite" se cierra con auditoría/anexar_citas_mto.py (one-shot,
sin lógica de tests).
texto: OBL-M1-01 (M1 §4 árbol del monorepo: tests/{unit,integration,fuzz,
stress,micro_bootstrap,syquex}) testea la estructura; hallazgo del lote: el
script anexó la cita DESNUDA como prologue delante de 12 tests con shebang →
SyntaxError (deuda NUEVA) — reparación: 12 tests a comentario `# Cumple MTO…`
y parche del script (anexar como comentario cuando la 1ª línea no es `"""`).
implementacion: tests/*.py comentarios + auditoria/anexar_citas_mto.py +
tests/integration/test_obl_m1_01_estructura_tests.py. // cumple MTO OBL-M1-01
oraculo: tests/integration/test_obl_m1_01_estructura_tests.py (3✓ ejecutable).
Evidencia complementaria del día: py_compile 0 errores en todos los tests
modificados y suites re-ejecutadas (syquex+MTO 82✓/1skip, LSP/transpile/AI
31✓, cluster/canales 41✓, vscode/axon/distribución 27✓, hardware/raft/
multicast/handshake 33✓).

## R3 — release_matrix.yml real + build.py + distribuir.py

requisito: Manual 9 §4 (release multi-plataforma: 4 plataformas
linux_x64/linux_arm64/darwin_arm64/win_x64, SHA-256 por binario, SBOM SPDX,
firma Ed25519, attestation SLSA) + Manual 9 §6.2 (bootstrap reproducible de 3
etapas, S2==S3 diff 0) + Manual 9 §6.3 (sellado criptográfico) + Manual 9 §2.1
(empaquetado de artefactos por plataforma soportada).
texto: el workflow release_matrix.yml era una SPEC no-ejecutable (R176 clase
B: 10 YAML asserts sobre claves/steps inexistentes); ahora es workflow GH
Actions REAL (matrix de 4 SOs, SHA-256, SBOM, firma, validación, permisos
mínimos); build.py ejecuta el bootstrap de 3 etapas con verificación de
determinismo S2==S3; distribuir.py empaqueta dist con binario+sha256+firma
Ed25519 opcional+SBOM+attestation+scripts de instalación.
implementacion: .github/workflows/release_matrix.yml, build.py,
distribuir.py, instaladores/windows/synapse.iss. // cumple Manual 9 §4
oraculo: tests/integration/test_release_matrix.py (release: 21✓ de la familia
72✓/2skip del día; el mismo run incluye test_slsa_sbom_10,
test_sbom_slsa_release, test_release_unificado y test_artifact_signing).
Evidencia build E2E: RC=0 con determinismo S2==S3 en logs/build_inflight.log.

## R3b — distribuir.py (empaquetado + sellado criptográfico)

requisito: Manual 9 §2.1 — el proceso de empaquetado genera artefactos para
las plataformas soportadas; Manual 9 §6.3 — sellado criptográfico definitivo
(firma Ed25519, .sha256, SBOM SPDX 2.3, attestation SLSA).
texto: distribuir.py construye instaladores/dist/distribucion/ con el binario
desplegable (stage2 byte-idéntico), SHA-256 por artefacto, firma Ed25519
opcional (clave en nucleo/ed25519_signer), SBOM SPDX + attestation SLSA y los
scripts de instalación del repo (install.sh/uninstall.sh/synapse.iss).
implementacion: distribuir.py // cumple Manual 9 §2.1 + §6.3
oraculo: tests/integration/test_distribucion.py

## R4 — fixtures canónicos alineados a M2 §13

requisito: Manual 2 §13 — el JSON canónico usa llave discriminante "tipo"
(H-canon-LET 643b413: el serializador pisaba "tipo"; hoy "tipo"=nodo,
tipo_annot=anotación) y la lista del Programa es "declaraciones".
texto: los 5 fixtures tests/fixtures/valid/*.expected.json y
test_a23_parity.syn.json quedaban STALE frente al serializador vigente
("_tipo"/"sentencias"); regenerados al requerido por M2 §13.
implementacion: tests/fixtures/valid/*.expected.json +
tests/fixtures/test_a23_parity.{c,syn.json} (regenerados por las suites).
oraculo: tests/integration/test_parser_ext.py (46✓: paridad fixture↔
serializador + RecuperacionErrores). Evidencia extra: test_a23_parity.py 14✓.

## R5 — instalador/VS Code alineados

requisito: Manual 9 §2.5 (Inno Setup válido) + Manual 8 §2 (extensión VS
Code).
texto: synapse.iss y vscode-synapse/{extension.js,package.json} con cambios
del lote (verificados por las suites correspondientes: test_release_unificado,
test_installer_iss, test_vscode_commands).
oraculo: tests/integration/test_vscode_commands.py (verbatim del lote 27✓
que incluye vscode/axon/distribución).

## R6 — paridad de la 3ª copia del lexer (emisor embebido) — H-R181-3 desviada

requisito: Manual 1 §3.1 (M1, mismo AST canónico en TODAS las tuberías) +
Manual 2 §3 — el fallback de keyword en posición de nombre (H-R181-3, ME
r184_r185_e2e) debe existir en las TRES copias del lexer: S1 (lexer.py),
nativo (lexer.syn) y EMBEBIDO (emit_selfhost.py).
texto: el harness native_puente_paridad.py::test_paridad_puente_campo_a_campo
reveló divergencia `let y = 1`: nativo/S1 aceptan, la referencia _P_* (emisor
embebido, la fuente del auto-hospedado) la descartaba (anti-cuelgue) porque su
lexer mapea `y`→T_AND incondicional. Fix espejado: (a) tras T_DOT,
(b) keyword+':' simple con exclusiones sino/recuperar/inseguro + literales
verdadero/falso (H-R184-1a: nunca son nombres), (c) keyword+'=' simple (no
'==') — misma semántica exacta que lexer.py/lexer.syn.
implementacion: compilador/generator/emit_selfhost.py + rebuild
nucleo/_rebuild_generator.py (generator.syn es concatenado de generador/).
// cumple Manual 1 §3.1
oraculo: auditoria/oraculos/oraculo_f14_mto_ci.py (PASS 2/2 paridad puente
nativo). Evidencia extra del día: test_codegen_embebido_d_f1_4.py 9/9 ✓ y
test_codegen_embebido_d_f1c.py 5/5 ✓ (sin regresión del emisor embebido).

## R7 — harnesses legados A2.3/A3.1 muertos por ruta y stubs desviados

requisito: Manual 9 §6.2 (entorno de CI reproducible) + M1 §3.1.
texto: RAIZ de native_parser_paridad.py / native_puente_paridad.py apuntaba a
`tests/` (un dirname de menos) — FileNotFoundError pre-histórico; el stub
str_eq con firma `int` chocaba contra la función usuario del lexer (typedef
entero=int64_t, M2 §4.1: "Entero con signo de 64 bits") y el stub `main` del
harness duplicaba el stub `main` de biblioteca que el generador emite sin
`principal` (H-R90-8 + D-R150-4). Faltaba el stub _syn_texto_duplicar
(H-R181-1). Fix en el HARNESS (el código está alineado al manual): RAIZ a la
raíz real, str_eq lo define el propio lexer concatenado, strip del stub main
generado, stub _syn_texto_duplicar estilo runtime.
implementacion: tests/integration/native_parser_paridad.py +
native_puente_paridad.py.
oraculo: auditoria/oraculos/oraculo_f14_mto_ci.py (PASS 20/20 paridad parser
nativo A2.3 + PASS 2/2 paridad puente A3.1, release).

## Checklist de cierre (fase 4b + 5)

- expediente: `python auditoria/alineacion.py --leer --me f14_mto_ci` →
  `--nuevo` → `--verificar`
- gate MTS: `python auditoria/contrastar.py --plan docs/plan_ME_f14_mto_ci.md`
- `python auditoria/verificar_alineacion.py` — SIN BRECHAS
- artefactos regenerados que se revierten: revisar `git status` antes del
  commit (regla 4 del plan maestro)
