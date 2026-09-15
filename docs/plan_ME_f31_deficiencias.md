# Plan ME: f31_deficiencias — Cierre de brechas de Alineación Fase 31

> **Manual de referencia:** Manual 6 §5, Manual 9 §6.2, Manual 3 §12, Manual 2 §5, Manual 2 §12
> **Fecha:** 2026-09-14
> **Base de verificación:** commit a7f0b3b

---

## Contexto

La Fase 31 fue marcada COMPLETA en MEMORIA_PROYECTO.md, pero verificación directa del
código fuente reveló 3 deficiencias:

1. `axón_rt.h` no existe (Manual 31 §2.3 lo exige).
2. `escribir_reporte` es función nueva sin contrato (Manual 2 §12).
3. 6 suites de test obligatorias (§8) no existen.

Los módulos 31.2 (lib/pruebas.syq), 31.3 (lint.syn), 31.4 (formatter.syn) y el resto
de 31.5 (generar_junit/coverage/json) verificados como implementados en código.

---

## Requisitos

requisito: Manual 6 §5
texto: axón_rt.h debe declarar las funciones de workspace isolation (cache_path, crear, resolver)
implementacion: Crear axón/axon_rt.h con guards de compilación y declaraciones para las 3 funciones
oraculo: tests/axon/test_workspace.py

requisito: Manual 2 §12
texto: Toda función pública nueva debe tener requiere/garantiza (Manual 2 §12)
implementacion: escribir_reporte en nucleo/principal.syn ya tiene requiere/garantiza con longitud(ruta) > 0
oraculo: tests/integration/test_reports.py

requisito: Manual 9 §6.2
texto: synapse test --junit/--coverage/--json generan reportes estandar (Manual 31 §5/§6)
implementacion: generar_junit, generar_coverage, generar_json existen en nucleo/reports.syn; escribir_reporte nueva con contrato en nucleo/principal.syn
oraculo: tests/integration/test_reports.py

requisito: Manual 3 §12
texto: lib/pruebas.syq con assert/assert_eq/test/suite (Manual 31 §3)
implementacion: Verificar implementacion existente de lib/pruebas.syq
oraculo: tests/syquex/test_pruebas.py

requisito: Manual 6 §5
texto: Nucleo/lsp.syn y nucleo/lint.syn implementan linter sobre AST (Manual 31 §4)
implementacion: Verificar nucleo/lint.syn con 5 reglas y estructura Advertencia
oraculo: tests/nucleo/test_lint.py

requisito: Manual 2 §5
texto: nucleo/formatter.syn reescribe codigo segun reglas de estilo (Manual 31 §5)
implementacion: Verificar nucleo/formatter.syn con reglas de estilo
oraculo: tests/nucleo/test_fmt.py

requisito: Manual 8 §4.3
texto: runtime/core/axon.c debe citar secciones validas (no Manual 31 inexistente)
implementacion: Corregir referencia de "Manual 31 §2" a "Manual 8 §4.3-8.4.4" en runtime/core/axon.c generar_etapa
oraculo: auditoria/verificar_alineacion.py

requisito: Manual 9 §5.7
texto: runtime/core/sistema.c implementa operaciones de sistema (_syn_listar_directorio, _syn_capturar_comando, _syn_sha256_archivo)
implementacion: Corregir cita de "Manual 7 8" a "Manual 9 §5.7" en runtime/core/sistema.c
oraculo: auditoria/verificar_alineacion.py
