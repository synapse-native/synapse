# Plan ME — Auditoría de desviaciones código ↔ manuales (ME_AUDIT_DESV)

## Propósito
Detectar y corregir toda desviación del código (compilador, runtime, nucleo, syquex,
tests) respecto a los manuales M1–M9. Es un ME transversal: los hallazgos se enrutan
a los MEs correspondientes (S*, T*, X1, 27_T*…30_T*) o a nuevos MEs si no existen.

requisito: Manual 1 §6 (Regla de hierro) + Manual 2 §5 (Contratos lógicos; la gobernanza
  AGENTS.md exige contratos requiere/garantiza en toda función pública nueva) + M1–M9 como
  fuente de verdad. NOTA: Manual 2 §12 son "Pruebas Obligatorias", NO contratos; la regla de
  contratos obligatorios proviene de AGENTS.md/GUIA_DE_GOBERNANZA, no de una sección de manual
  numerada (ver R_AUDIT_DESV.md hallazgo #4).
texto: "Los manuales son ley: el código desviado se corrige hacia el manual" (AGENTS.md /
  GUIA_DE_GOBERNANZA). "Ninguna característica nueva puede romper el bootstrap
  (etapas 0→1→2→3 con diff binario 0)" (Manual 1 §6). "Contratos requiere/garantiza en TODA
  función pública nueva" (AGENTS.md — Manual 2 §5 define la sintaxis; es opcional en EBNF,
  pero la gobernanza lo exige).
implementacion:
  1. Barrido del codebase (compilador/, pipeline.py, runtime/, nucleo/, syquex/,
     tests/) contrastándolo con M1–M9.
  2. Por cada desviación: registrar en `docs/reportes/R_AUDIT_DESV.md` con
     archivo:línea, Manual X §Y infringido, y propuesta de corrección.
  3. Corregir (hacia el manual) e integrar en el ME de feature correspondiente; si no
     hay ME, abrir uno (ej. ME_AUDIT_DESV_n).
oraculo: docs/reportes/R_AUDIT_DESV.md (registro de hallazgos + estado) +
  `auditoria/verificar_alineacion.py` 0 brechas como proxy de trazabilidad.

## Criterios de aceptación
- Reporte R_AUDIT_DESV.md con desviaciones clasificadas (crítica / alta / media / baja).
- Toda desviación crítica/alta corregida o con ME asignado y registrada en memoria.
- Sin introducir nueva deuda: cada corrección cita `Manual X §Y` en el sitio del cambio.

## Integración con el plan maestro
- Workstream F (nuevo). Alimenta a S*, T*, X1, 27_T*…30_T*: las desviaciones de
  tests/trazabilidad ya cubiertas por esos MEs; este ME cubre el código de producción
  (compilador/runtime/nucleo/syquex) que aquellos no alcanzan.
- Desviaciones de ubicación de caché (ya resueltas en ME_cache_rt / ME_cache_rt2) se
  documentan aquí como caso cerrado de referencia.
