# FASE 33 — CERTIFICACIÓN DEL COMPILADOR AUTO-ALOJADO (Fase 33.5, ME 33.5_certificacion)

Fecha: 2026-09-29 · Base: `cdbfd86` · Verificación: `docs/verificacion_ME_33.5_certificacion.md`
Plan MTS: `docs/plan_ME_33.5_certificacion.md` · Oráculo: `tests/auditoria/test_oraculos_33_5_certificacion.py` (5/5 GREEN)

Criterio del ROADMAP §33.5: "Validar que el compilador auto-alojado y sus
herramientas nativas compilan y ejecutan el subconjunto completo del
ecosistema sin rutas duales", con suite completa, bootstrap S2==S3
byte-idéntico sellado en CI y matriz extendida.

## 1. Bootstrap de 3 etapas — sello S2==S3 (Manual 9 §6.1, Manual 1 §6)

| Etapa | Comando | rc | Artefacto |
|---|---|---|---|
| 1 | `python main.py nucleo/principal.syn -o synapse_stage1.exe` | 0 | 2,097,097 bytes |
| 2 | `./synapse_stage1.exe nucleo/principal.syn -o synapse_stage2.exe` | 0 | 2,484,016 bytes |
| 3 | `./synapse_stage2.exe nucleo/principal.syn -o synapse_stage3.exe` | 0 | 2,484,016 bytes |

- **S2==S3 byte-idénticos:** sha256 de ambos =
  `36b82c4d40968ffc67d80999b060fae01f8ce3aa551dcb442509e2d56daddf9c`.
- **Determinismo:** el mismo hash S2==S3 se obtuvo en TRES regeneraciones
  independientes (28-09 oráculo, 29-09 regeneración manual, 29-09 oráculo
  post-edición) → `diff 0 bytes` real, no coincidencia puntual.
- **Sello en CI (R1, cierra H-33.5-1):** el job `bootstrap` de
  `.github/workflows/ci-tests.yml` solo ejecutaba Etapa 1; ahora ejecuta
  Etapa 2 + Etapa 3 y compara `sha256sum` de S2 y S3 con fallo explícito si
  difieren (comentario `# cumple Manual 9 §6.1`).

## 2. Dispatcher nativo lint/fmt/test — orden canónico de Manual 8 §4.1 (cierra H-33.5-2)

`nucleo/principal.syn` (~L1034-1060): los bloques del dispatcher exigían
`lint <archivo> <flag>`; el orden canónico de la ley
(`synapse lint --fix main.syq`, `synapse fmt --check src/`) dejaba el flag en
`_argv(2)` y la ruta en `_argv(3)` → "no se pudo leer --check". Ahora
clasifican flags (`--fix`/`--check`/`--junit`/`--json`/`--coverage`) y toman
como ruta el primer argumento que no sea flag — aceptan AMBOS órdenes, error
"[Lint/Fmt/Test] ERROR: falta el archivo" si no hay ruta, rc propagado por
`main()`. Probes contra `synapse_stage2.exe` regenerado:
`fmt --check <arch>` rc=0 · `fmt <arch> --check` rc=0 · `lint <arch>` rc=0
limpio / rc=1 con advertencias / rc=1 inexistente · `test --json <arch>` rc=0.

## 3. Suites ejecutadas (reconstrucción fresca tras cada edición — sin exes stale)

| Suite | Resultado | Duración | Regresiones |
|---|---|---|---|
| tests/unit | **514/514 PASSED** | 281 s | 0 |
| tests/nucleo | **30/30 PASSED** | 148 s | 0 |
| Matriz std↔runtime | **35/35 PASSED** | 66 s | 0 |
| Matriz extendida (std/debug.syn para-en, std/modelo.syn indexado) | **2/2 rc=0** (oráculo) | — | 0 |
| Oráculo certificación 33.5 | **5/5 GREEN** | 84 s | 0 |
| tests/syquex + tests/opensyn | 397 ✓ / 4 ✗ / 2 skip | 80 s | **0** (los 4 idénticos en base, medidos con stash) |
| tests/integration | 1435 ✓ / 120 ✗ / 36 skip | 2:19:19 | **0** (114 idénticos en base + 1 flaky de timing GREEN aislado + 5 ambiente syquex_coverage) |

**Metodología anti-regresión:** los 48 archivos de integration con fallos se
ejecutaron dos veces (~110 min c/u): con el WIP del ME y sobre la base
`cdbfd86` (stash + rebuild stage1 desde fuente base). Resultado: 115 vs 114
fallos; el único delta (`test_syquex_benchmarks::test_fibonacci_30`,
benchmark con umbral de tiempo) **PASA aislado con el WIP (2.90 s)** → flaky
de timing bajo carga, no regresión. Los 114 restantes son idénticos en ambos
estados: deuda preexistente documentada (RED TDD de MEs antiguos como
`test_quantum_exec_10`, asserts sobre YAML de workflows de release, exes de
tests stale como `test_wasm_extended.exe`, wrappers `.bat` ausentes, timeouts
de red), fuera del alcance de este ME.

## 4. Estado lint/fmt del código fuente — medido, sin maquillar (H-33.5-3)

- **Lint: FUNCIONA.** `synapse lint nucleo/generador/orquestador.syn` reporta
  **422 advertencias** (WARN_LINT_DOUBLE_SPACE u otras reglas) y rc=1 —
  detecta el estado real del fuente.
- **Fmt: viciado por H-33.5-3 (NO arreglado en este ME, resolución asignada).**
  El C generado de `normalizar_espacios` (`_formatter.c` ~L155) perdió la
  rama `si c == " "` (colapso de espacios dobles): el .syn tiene 3 ramas
  (espacio/coma/otro) y el C solo 2 → `fmt --check`/`fmt` (write) retornan
  "formato correcto" FALSO sobre archivos mal formateados y no reescriben.
  Fix (emisor del formatter + normalización del formato del nucleo) → ME
  futuro; regla 6: no parches a mitad de certificación.
- La meta "0 errores" de M9 §6.1 se registra como estado objetivo; forzarla
  hoy con hardcoding violaría la regla 6 y el estado real del repo.

## 5. Desviaciones activas — todas con resolución asignada (criterio ROADMAP §33.5)

| ID | Estado | Resolución |
|---|---|---|
| D-R163-1 | `para k en mapa` itera claves (M3 §3) | Pendiente ratificación Arquitecto (documentada en bitácora/plan) |
| H-CFG-2 | Deuda registrada | Resolución asignada en CANON_DEUDAS/bitácora |
| H-R144-3 | Deuda registrada | Resolución asignada en bitácora |
| 3 SIN_CITA Fase 32 | Deuda de citación registrada | Resolución asignada (Fase 32, R155+) |
| H-33.5-3 | Rama `si c == " "` no llega al C del formatter | ME futuro: fix emisor + normalización de formato |
| cli.py sin lint/fmt Python | Brecha documentada (el dispatcher Python no despacha lint/fmt) | ME futuro: añadirlos al dispatcher Python, no se inventa código a medias |
| test_syquex_coverage timeout 600>300 | Inconsistencia fixture vs pytest.ini | ME futuro: ajustar timeout del fixture o umbral global |

## 6. Criterios de aceptación §33.5 — checklist

1. ✅ Bootstrap 0→1→2→3 con sha256(S2)==sha256(S3) verificado por el oráculo
   y sellado en el job CI `bootstrap` (R1).
2. ✅ Suites GREEN sin regresiones nuevas: unit 514/514, nucleo 30/30,
   matriz 35/35, extendida 2/2, syquex+opensyn 397✓ (4 fallos preexistentes
   idénticos en base), integration 1435✓ (114 preexistentes idénticos en
   base + 1 flaky GREEN aislado + 5 ambiente); skips legítimos documentados
   arriba y en la verificación ME.
3. ✅ Matriz 35/35 + matriz extendida (std/debug.syn, std/modelo.syn) GREEN.
4. ✅ Dispatch lint/fmt acepta el orden canónico de M8 §4.1 en la capa nativa
   (R2); la brecha de cli.py queda documentada con resolución asignada.
5. ✅ Este reporte con evidencia real (hashes, conteos) y 0 desviaciones
   activas sin resolución.

## 7. Conclusión

La Fase 33 queda **CERTIFICADA con condiciones documentadas**: el compilador
auto-alojado reconstruye su propia cadena de bootstrap con sello S2==S3
determinista (ahora también en CI), las herramientas nativas lint/fmt/test
obedecen la ley de M8 §4.1, y las features de la fase (33.1-33.4b: paridad
de nodos, coverage de aristas, indexado, genéricos de usuario y para-en mapa)
están cubiertas por la matriz 35/35 + extendida. El estado lint/fmt del
propio compilador queda medido y publicado (422 advertencias; formatter
viciado por H-33.5-3) con resolución asignada — la certificación documenta
el estado real, no lo maquilla.

El hash del feat de este ME queda registrado en `docs/reportes/R164.md`
(post-commit, procedimiento de la GUIA).
