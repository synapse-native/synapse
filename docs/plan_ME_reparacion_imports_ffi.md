# Plan ME reparacion_imports_ffi — H-CFG-4/H-CFG-5 + MTO re-anclado (2026-09-26)

**Contexto:** barrido de deudas ordenado por el Arquitecto ("reparar y alinear
todo lo pendiente"). Dos fallos PREEXISTENTES de producción (verificados con
baseline git stash antes de tocar) + las 10 citas muertas del MTO.

## R1 — Resolución de imports con fallback a la raíz del workspace
requisito: Manual 1 §3.1
texto: "pipeline completo con resolución de imports" (M1 §3.1 — el pipeline
resuelve imports de módulos locales del ecosistema).
implementacion: `compilador/resolvedor_axon.py`: tras agotar dir_base
(axon_modules, directa, subdir, paquete local `<base>/<mod>/principal.syn`),
fallback a `_RAIZ_REPO` (misma cadena de búsquedas). `pipeline.py`: los
imports ENCADENADOS se resuelven contra el directorio del MÓDULO importado
(`dir_importado`) y no contra el dir_base del fuente raíz; el dedup R23
descarta el `principal` IMPORTADO cuando el propio archivo define el suyo
(precedencia del punto de entrada del usuario). Sintoma: test_ia_adv_10
test_opensyn_importar_compila rc=1 (E-603) — 16/16 GREEN tras el fix.
// cumple Manual 1 §3.1
oraculo: tests/auditoria/test_oraculos_reparacion_imports_ffi.py

## R2 — FFI lista/mapa: firmas únicas + casts de handle
requisito: Manual 6 §3.1; Manual 2 §4.1
texto: "externo funcion lista/mapa con handle entero" (M6 §3.1) — la
implementación C usa void*/const char* (runtime/core/lista.c:22,
mapa.c:96) y el lado Synapse declara handle `entero` (alias int64_t, M2
§4.1): el C emitido necesita casts explícitos y UNA sola declaración.
implementacion: `compilador/generator/context.py`: los FFI _syn_lista_* /
_syn_mapa_* entran a `_C_FUNCTIONS_NEED_DATOS` (visitar_externa ya no
duplica prototipos canónicos del header compartido — fin de las firmas
dobles conflicting-types). `emit_expressions.py`: casts
`(void*)(intptr_t)(h)` en handles y `(intptr_t)` en creadores en las 3 rutas
(métodos postfijo, builtins r153, llamada con externos) + `.datos` para
args char*/const char*. `generator.py`: prototipos `_syn_lista_limpiar` /
`_syn_mapa_limpiar` en el bloque canónico del header. Síntoma:
test_puente_ffi_lista_mapa test_e2e_compila_con_s1 rc=1 (conflicting types
+ int-from-pointer) — 12/12 GREEN tras el fix.
// cumple Manual 6 §3.1
// cumple Manual 2 §4.1
oraculo: tests/unit/test_puente_ffi_lista_mapa.py

## R3 — MTO: re-anclaje de citas a secciones reales
requisito: Manual 7 §4.2; Manual 6 §6.2; Manual 8 §5.4; Manual 9 §5.2 §5.3
§5.6 §2.5 §2.3 §4.1
texto: "### 4.2. Flujo de una Petición de IA con Validación" (M7 §4.2 — la
sección REAL del bucle de validación que OBL-M7-02 documenta).
implementacion: `docs/manuales/MANUAL_TESTS_OBLIGATORIOS.md`: 10 citas a
secciones inexistentes re-ancladas a las reales (M7 §6.3→§4.2, M7 §7→M6
§6.2, M8 §6.3/M7 §6.3→M8 §5.4/M7 §4.2, M9 §9→§5.2 §5.3 / §5.6 / §2.5 /
§2.3 / §4.1). D-9 ratificada en sesión 2026-09-26 por el Arquitecto
("repara y alinea todo lo pendiente"); auditar_calidad_tests --solo-mto
sin avisos de citas muertas.
oraculo: tests/auditoria/test_oraculos_reparacion_imports_ffi.py

## Archivos a modificar
- compilador/resolvedor_axon.py, pipeline.py (R1)
- compilador/generator/context.py, emit_expressions.py, generator.py (R2)
- docs/manuales/MANUAL_TESTS_OBLIGATORIOS.md (R3)

## Notas de riesgo
- El emisor cambió → regresión completa de unit ejecutada: 514/514 GREEN.
- Los casts no alteran el ABI (int64_t↔puntero mismo ancho en x86-64);
  el .o del compilador no se cachea con fuentes viejas (hash SHA-256).
- opensyn/principal.syn y dist/bin/opensyn.exe no cambian de comportamiento
  (el resolvedor solo añade búsquedas que antes fallaban).
