# REPORTE DE PLAN DE MICRO-ENTREGABLE (MTS)
# ME: reparacion-control-calidad | FASE: 31 (post-F30) | Área: auditoría/gobernanza
#
# Contexto (verificado código real, no registros):
#  - `test_auditoria_contrastar.py::test_citas_archivo` FALLA determinísticamente.
#  - auditoria/contrastar.py:CUMPLE_RE exige el signo `§`, pero 552/588 (93.9%) de las
#    citas `// cumple Manual X Y` usan FORMATO ESPACIO (sin §).
#  - El test (oráculo inmutable, regla 5) exige que `cumple Manual 8 1.2` (espacio) se
#    parseé como ("8","1.2"). El regex es el código con fallo → se repara el regex para
#    que acepte `§` opcional y así el gate valide las 588 citas reales (hoy solo 34).
#  - Hallazgo secundario (para Arquitecto, NO ejecutado aquí): las citas semánticas
#    "Manual 2 §12 ... contratos" apuntan al § equivocado: Manual 2 §5 = "Contratos
#    lógicos" y Manual 2 §12 = "Pruebas obligatorias". Ver ME-Q3.

# --- ME-Q1: Reparar el parser de citas del gate MTS ---
requisito: Manual 1 §3.1
texto: Todo archivo de producción modificado debe cargar un comentario de cita `// cumple Manual X §Y` (formato canonical con §) para trazabilidad; el gate auditoria/contrastar.py debe poder extraerla.
implementacion: En contrastar.py, `CUMPLE_RE` pasa de exigir `§` obligatorio a aceptar `§` opcional (`§?\s*`), de modo que las citas canónicas `cumple Manual X §Y` y el formato legacy espacio `cumple Manual X Y` (93.9% del código) ambas se parsean a (manual, sección). No se modifica el test (regla 5).
oraculo: tests/test_auditoria_contrastar.py

# --- ME-Q2: Test de regresión del parser de citas (dual-format) ---
requisito: Manual 1 §3.1
texto: El gate debe distinguir y parsear correctamente ambos formatos de cita sin falsear secciones.
implementacion: Añadir tests/test_citas_formato.py que verifique `citas_archivo()` extrae § y espacio, rechaza secciones inexistentes y parsea la sección con subsección (5.7).
oraculo: tests/test_citas_formato.py

# --- ME-Q3: Corregir cita semántica de contratos §12 → §5 ---
# Hallazgo: MTO OBL-M2-02 citaba "Manual 2 §12" para contratos, pero Manual 2 §5
# es "CONTRATOS LÓGICOS (requiere/garantiza)" y §12 es "Pruebas obligatorias".
# seccion_existe("2","12")=True (header existe) → gate validaba cita SEMÁNTICAMENTE
# incorrecta. Fuente de verdad = Manual 2: §5 es contratos. Corrección hacia el manual.
# NOTA: las 12 citas `// cumple Manual 2 §12: contratos` en opensyn/principal.syn se
# dejan pendientes: ese archivo está staged por otro agente (regla: no tocar cambios
# ajenos). Se anota en bitácora para que el otro agente las corrija a §5 tras liberar.
requisito: Manual 2 §5
texto: Contratos lógicos `requiere`/`garantiza` se especifican en Manual 2 §5 (no §12); el MTO OBL-M2-02 debe referenciar §5 y un test debe asegurar la coincidencia temática.
implementacion: En MANUAL_TESTS_OBLIGATORIOS.md, OBL-M2-02 pasa de `Manual 2 §12` a `Manual 2 §5`. Añadido tests/test_obt_citas_manuales.py que verifica OBL-M2-02 cita §5, que Manual 2 §5 cabecera dice CONTRATOS y §12 dice PRUEBAS (verificación semántica el gate seccion_existe no realiza). No se toca opensyn/principal.syn (agente activo).
oraculo: tests/test_obt_citas_manuales.py
