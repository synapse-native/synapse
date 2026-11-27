# Plan ME 33.5_certificacion — Fase 33.5 (certificación de la Fase 33)

Micro-entregable final de la Fase 33 (ROADMAP.md §33.5): "Validar que el
compilador auto-alojado y sus herramientas nativas compilan y ejecutan el
subconjunto completo del ecosistema sin rutas duales."

Método de Trabajo Seguro (MTS): cada requisito cita la oración normativa
LITERAL del manual; el oráculo se EJECUTA, no se declara.

## R1 — Job CI bootstrap: sello del bootstrap de 3 etapas con diff 0 bytes
requisito: Manual 9 §6.1; Manual 9 §2.3
texto: "□ **Bootstrap exitoso**: en cada target, el proceso de bootstrap de 3
etapas produce `diff 0 bytes` entre Stage 2 y Stage 3." / "Verificar el
bootstrap (diff 0 bytes entre Stage 2 y Stage 3)." (el pipeline "se ejecuta en
GitHub Actions")
implementacion: `.github/workflows/ci-tests.yml`, job `bootstrap`: tras
generar stage1 (paso existente), añadir Etapa 2 (stage1 compila
nucleo/principal.syn → synapse_stage2.exe) y Etapa 3 (stage2 compila
nucleo/principal.syn → synapse_stage3.exe), con `sha256sum` de ambos y
fallo si difieren (grep del par + `sha256sum` con comparación exacta).
Criterio de aceptación del ROADMAP §33.5: "S2==S3 byte-idéntico en CI" y
"job bootstrap" sellado. Precedentes: scripts/bootstrap.sh/build.sh (Etapa 3
+ SHA256); reportes FASE_A_A5_D5 ("S2==S3 → IDÉNTICO").
oraculo: tests/auditoria/test_oraculos_33_5_certificacion.py

## R2 — Dispatcher nativo: orden canónico de flags en lint/fmt/test
requisito: Manual 8 §4.1
texto: "| **`synapse lint`** (Fase 31) | Ejecuta el linter nativo sobre el
código fuente. |" / "| **`synapse fmt`** (Fase 31) | Ejecuta el formateador
nativo sobre el código fuente. |" — con los ejemplos canónicos:
"synapse lint --fix main.syq" y "synapse fmt --check src/" (flags ANTES de la
ruta).
implementacion: `nucleo/principal.syn`, dispatcher del main (bloques asm de
lint/fmt/test, ~L1036-1052): hoy exigen `lint <archivo> [--fix]` /
`fmt <archivo> [--check]` (ruta primero) — con el orden canónico del manual el
flag cae en _argv(2) y la ruta en _argv(3), y el linter reporta "no se pudo
leer --check". Fix: escanear _argv(2..) clasificando flags (--fix/--check/
--junit/--json/--coverage) y tomando como ruta el primer argumento que no sea
flag (ambos órdenes aceptados; el canónico del manual primero). main() ya
propaga el rc del dispatcher (verificado: `fmt ... --check` con formato
incorrecto → rc=1).
oraculo: tests/auditoria/test_oraculos_33_5_certificacion.py

## R3 — Oráculo de certificación: bootstrap 3 etapas + matriz extendida + dispatch
requisito: Manual 9 §6.1; Manual 9 §6.2; Manual 1 §6; Manual 8 §4.1
texto: "□ **Bootstrap exitoso**: ... produce `diff 0 bytes` entre Stage 2 y
Stage 3." / "El pipeline de CI/CD ejecuta automáticamente: La suite de tests
completa en cada target. La verificación del bootstrap (diff 0 bytes)." /
regla de hierro del bootstrap (M1 §6) / comandos lint/fmt de M8 §4.1.
implementacion: `tests/auditoria/test_oraculos_33_5_certificacion.py` NUEVO
(patrones de test_oraculos_334b: `_exe_fresco()` con regeneración on-demand):
(1) bootstrap 0→1→2→3 real con sha256(S2)==sha256(S3) byte-idénticos;
(2) matriz extendida: los std que ejercitan las features 33.4 compilados +
enlazados + ejecutados rc=0 — std/debug.syn (para-en) y std/modelo.syn
(indexado xs[i]) vía el mecanismo de test_matriz_compilacion.py
(ejecutar_compilador, enlace completo no check_only);
(3) dispatch canónico: `fmt <arch> --check` Y `fmt --check <arch>` rc=0 en
archivo bien formateado / rc=1 en mal formateado (a elegir un .syn neutro en
TEMP, no del nucleo, para no depender del estado de formato de la base);
(4) anti-fabricación: el sha256 de S2 y S3 se calcula sobre los binarios
reales y el test falla si no existen.
oraculo: tests/auditoria/test_oraculos_33_5_certificacion.py

## R4 — Suite completa GREEN + reporte final de certificación
requisito: Manual 9 §6.1; Manual 9 §6.2; Manual 1 §6
texto: "□ **Compilación sin errores**..." / "□ **Tests**: ... pasan" /
"La suite de tests completa en cada target" / regla de hierro M1 §6 (ninguna
característica rompe el bootstrap).
implementacion: reconstruir unity (`_rebuild_generator.py`) tras R2; bootstrap
stage1→stage2 fresco; suite completa (unit + integration + nucleo + opensyn +
auditoria) sin regresiones; matriz 35/35 existente intacta;
`docs/reportes/FASE_33_CERTIFICACION.md` NUEVO con: compilación S1/S2 rc=0,
S2==S3 sha256, suites ejecutadas con conteos, lint/fmt medidos sobre el
código fuente (estado real documentado, no maquillado), y las desviaciones
activas listadas con su resolución asignada (criterio ROADMAP: "0 desviaciones
activas sin resolución").
oraculo: tests/auditoria/test_oraculos_33_5_certificacion.py

## Decisiones/hallazgos registrados en este plan
- H-33.5-1 (hallazgo): el job CI `bootstrap` solo ejecuta Etapa 1 — el sello
  S2==S3 de M9 §6.1 no existía; se añade en R1.
- H-33.5-2 (hallazgo): el dispatcher nativo exige `lint/fmt <archivo> <flag>`
  — el orden canónico de M8 §4.1 (`synapse lint --fix main.syq`,
  `synapse fmt --check src/`) produce "no se pudo leer --check"; se alinea el
  dispatcher a la ley en R2 (el código se corrige hacia el manual).
- Estado de lint/fmt sobre el código fuente del compilador (medido con
  stage2): 422 advertencias de lint en orquestador.syn y formato incorrecto
  en varios .syn del nucleo. La certificación los DOCUMENTA con resolución
  asignada (normalización de formato → ME futuro), no los oculta: M9 §6.1
  pide 0 errores, y forzarlos hoy rompería la regla 6 (no hardcoding).
- Los tests existentes (matriz 35/35, suites de integration) NO se modifican:
  regla 5 (tests inmutables). El oráculo de este ME es NUEVO.

## Criterios de aceptación (33.5)
1. Bootstrap 0→1→2→3 con sha256(S2)==sha256(S3) verificado por el oráculo y
   sellado en el job CI `bootstrap`.
2. Suites GREEN (unit/integration/nucleo/opensyn/auditoria) — sin skips
   nuevos; los skips legítimos documentados se listan en el reporte.
3. Matriz 35/35 + matriz extendida (std/debug.syn, std/modelo.syn) GREEN.
4. Dispatch lint/fmt acepta el orden canónico de M8 §4.1 en ambas capas donde
   exista (nativo: R2; S1 Python: cli.py no despacha lint/fmt — brecha
   documentada con resolución asignada: añadirlos al dispatcher Python es ME
   futuro, no se inventa código a medias).
5. `docs/reportes/FASE_33_CERTIFICACION.md` con evidencia real (hashes,
   conteos de tests) y 0 desviaciones activas sin resolución.
