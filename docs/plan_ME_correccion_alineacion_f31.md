# Plan ME — Corrección de alineación f31_deficiencias

Micro-entregable: Corrección de alineación manual↔código
Fecha: 2026-09-15

## requisito:
Corregir el expediente de alineación f31_deficiencias.md para lograr 0 brechas de alineación manual↔código.

## texto:
El expediente de alineación tenía 24 brechas porque: (1) secciones del manual sin oraciones indexadas (Manual 6 §5, Manual 5 §2, Manual 1 §1, Manual 1 §5), (2) comentarios cumple Manual en código no coincidían con secciones del mapa, (3) citations paraphraseadas no literales.

## implementacion:
1. Actualizar mapa_alineacion.md: §5→§5.1, §2→§2.1
2. Actualizar mapa_manuales.md: syquex/parser.syn → §1.1, §5.1
3. Actualizar comentarios cumple Manual en 6 archivos
4. Reescribir expediente con citas LITERALES del índice
5. Ratificar D-ALINEACION-F31 en MEMORIA

## oraculo:
tests/auditoria/test_auditoria_alineacion.py

## Archivos modificados:
- compilador/generator/emit_declarations.py — cumple Manual 2 §1.3
- compilador/generator/emit_expressions.py — cumple Manual 2 §12
- compilador/generator/generator.py — cumple Manual 2 §5.1
- compilador/parser_control.py — cumple Manual 2 §1.3
- compilador/puente_canonico.py — cumple Manual 3 §11.1, Manual 6 §5.1, Manual 2 §12
- axon/axon_rt.c — cumple Manual 8 §4.3, Manual 6 §5.1
- axon/axon_rt.h — cumple Manual 6 §5.1
- runtime/core/axon.c — cumple Manual 8 §4.3, Manual 6 §5.1
- runtime/core/concurrency.c — cumple Manual 5 §2.1
- synapse_rt_types.h — cumple Manual 2 §4.1, Manual 2 §12
- syquex/expr.syn — cumple Manual 3 §3
- syquex/parser.syn — cumple Manual 1 §1.1, Manual 1 §5.1, Manual 2 §12, Manual 3 §3
