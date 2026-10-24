# Expediente de alineación r196_deuda_contrato_y_cobertura

base: HEAD  # commit sobre el que se leyó el manual
cambio_hash: e6682be16415e284

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## std/texto.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: std/texto.syn:15
  oraculo: tests/auditoria/test_oraculos_r196_contrato_cobertura.py
  nota: H-R196-1 (decisión Arquitecto ratificada 2026-10-23, "Corregir contrato al manual"). Comentarios: el barrido r192 añadió `requiere: longitud(subcadena) > 0` a contiene/indice_de sin mandato del manual, ya que M8 §1.7.3 declara los bindings "externo funcion contiene(...)" SIN precondición ("Verificación de subcadena", y §1.7.4 "Búsqueda de primera ocurrencia"). El "requiere" prohibidor abortaba el runtime (rc=127, "Fallo en contrato: requiere") con subcadena vacía, rompiendo el test inmutable tests/integration/test_string_utils.py::test_contiene_subcadena_vacia. ME r196 retira la cláusula en 4 sitios: contiene×2, indice_de×2 (el emisor deduplica a 1 def C por función); TODAS las cláusulas vigentes del archivo son booleanas (M2 §5.1). Anclas gemelas de implementación en std/texto.syn:29, :122 y :134 con el comentario "cumple Manual 2 §5.1 (ME r196)". Oráculo 4/4 con la E2E de contiene→1, indice_de→0 y rc=0, más tests de regressión (13 de test_string_utils y suite de cobertura nueva con 2/2).

### R2 (cobertura total >= 45%) — texto sin anclas parseables

Test inmutable: tests/integration/test_syquex_coverage.py::test_cobertura_total_minima
Estado: CUMPLE.
Evidencia de ejecución: logs/verifica_coverage_r196.log (rc=0 aislado 2026-10-23) y la medición .coverage_tmp.json con TOTAL 51.228% >= 45% (8265 stmts, 4031 miss; antes 44.719%/4569 miss).
Causa: la suite fija del medidor no ejercitaba el código nuevo del compilador (sandbox H-CFG-2 de r194 en emit_expressions.py/generator.py).
Reparación (sin tocar tests): tests/syquex/test_sandbox_cover_r196.py (TDD RED→GREEN) compila probes .syn por el pipeline real; alcanzó 538 stmts nuevos cubiertos (4569→4031 miss).
Oráculo: tests/syquex/test_sandbox_cover_r196.py (2/2 GREEN) + oráculo r196 4/4 + verificación aislada del test inmutable PASSED.
