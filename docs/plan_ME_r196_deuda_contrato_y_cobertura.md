# ME r196_deuda_contrato_y_cobertura — 2 fallos deterministas del barrido r195

**Fecha:** 2026-10-23 · **Fase:** POST-FASE 33 — deuda cero · **Base:** 8a90bdf
**Origen:** barrido r195 (`logs/barrido_r195.log`): 1569✓/25skip/**6✗**; los 3+
4 del grupo A pasan aislados (infra del barrido masivo); quedan **2
deterministas** que este ME repara.

## R1 — `test_string_utils.py::TestContiene::test_contiene_subcadena_vacia`

**Causa raíz:** el contrato `requiere: longitud(subcadena) > 0` en
`std/texto.syn` (contiene e indice_de) — añadido por el barrido de cláusulas
r192 sin ratificación — hace que el runtime ABORTE (rc=127, "Fallo en
contrato: requiere", `_texto.c:33`) con la subcadena vacía. El runtime C
(`texto.c`) ya maneja la subcadena vacía correctamente (probe rc=0, 2026-10-23).

**Decisión del Arquitecto (sesión 2026-10-23, ratificada):** "Corregir
contrato al manual" — M8 §1.7.3 declara los bindings como `externo funcion
contiene(texto: texto, subcadena: texto) -> entero` SIN precondición, y solo
"Verificación de subcadena". El `requiere` prohibiendo la cadena vacía era una
desviación no mandada por el manual (H-R196-1). El test (inmutable) es la voz
del manual aquí.

## R2 — `test_syquex_coverage.py::TestSyquexCoverage::test_cobertura_total_minima`

**Causa raíz:** cobertura total del S1 = 44.72% (8265 stmts, 4569 miss) <
UMBRAL_TOTAL 45% (test inmutable, M3 §3). La suite fija de cobertura
(`tests/syquex/` + cert_1..3) no ejercita el código nuevo del compilador
(sandbox H-CFG-2 de r194 en `emit_expressions.py`/`generator.py`).
Reparación: tests NUEVOS en `tests/syquex/` (el patrón de comando del medidor
es fijo) que compilen probes `.syn` reales ejercitando las rutas nuevas,
levantando stmts cubiertos por encima del umbral (~24 stmts necesarios).

## Bloque MTS

requisito: Manual 8 §1.7.3 + Manual 2 §5.1
texto: "Las funciones `contiene`, `indice_de` y `reemplazar` se implementan
como builtins en C y se exponen en Synapse" — bindings `externo funcion
contiene(texto: texto, subcadena: texto) -> entero` sin cláusula requerida
por el manual; y "**`requiere`:** Se evalúa antes de la primera instrucción
del cuerpo. Todas las expresiones deben ser booleanas." (M2 §5.1 exige
booleanidad de la cláusula, no su existencia).
implementacion:
- (a) `std/texto.syn`: retirar `requiere: longitud(subcadena) > 0` de
  `contiene` e `indice_de` (garantiza se mantiene). # cumple Manual 8 §1.7.3
  (ME r196). Semántica del runtime ya vista por probe (contiene("hola",""))
  → 1; indice_de("hola","") → 0.
- (b) `tests/syquex/test_sandbox_coverage_r196.py` (NUEVO, TDD RED→GREEN):
  compila probes `.syn` con `leer_archivo` dentro del cwd (permitido) y
  fuera (rechazado sin crash) vía el compilador S1, ejercitando la ruta del
  sandbox en emit_expressions.py/generator.py (líneas r194 sin cubrir).
oraculo: tests/auditoria/test_oraculos_r196_contrato_cobertura.py
  (probe directo de contiene/indice_de con vacía rc=0 + los 2 tests falsos
  del barrido en rc=0 aislados).
