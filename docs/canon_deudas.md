# Canon de deudas (regla 11)
# Formato: - D-XX | CERRADA|PENDIENTE | resolucion
#
# Fuente de verdad del verificador auditoria/verificar_alineacion.py.
# Antes este canon estaba hard-codeado dentro del script; ahora vive aqui para
# no acoplar la politica de gobernanza al codigo de control. Toda deuda nueva
# debe anadirse a este archivo (y mencionarse en la bitacora), o el verificador
# la reporta como brecha (regla 11: nada queda sin seguimiento).

- D-F1 | CERRADA | F1.2c+F1.2d+F1.4 (keywords del Manual 2 §3)
- D-1 | PENDIENTE | Fase 23 (modelo de memoria Syquex: arenas/RC/alcance)
- D-2 | CERRADA | A5 monomorfización (Opción A del Arquitecto)
- D-3 | CERRADA | A5 hoisting FIFO + = {0};
- D-4 | CERRADA | A5 verificador_formal.syn + verificador_formal.py (19 tests security); AST leak F5-1 cerrado; 34 tests D5+security pass
- D-5 | CERRADA | A5 cobertura generator.py 58%→95%
- D-6 | CERRADA | A5 operador ? postfijo
- D-7 | CERRADA | A5 ABI entero→int64_t / decimal→double
- D-8 | CERRADA | sin acción (por diseño, Manual 2 §2: cadenas multi-línea)
- D-9 | CERRADA | R42: D-9(d) corte 6 CERRADA COMPLETA; (a) parser.syn CERRADA en R29; (b) lexer_keywords.syn CERRADA en R32; (c) emit_selfhost.py CERRADA en R33 (podado emitir_generar); (d) synapse_rt.c 7.882->1.769 L, runtime/core/ 20+ modulos; (e) NodoID/TokenID: tabla canonica unica runtime/core/ast_nodos.h (gen desde nucleo/parser_constantes.syn; generator.py emite #include; 9 archivos C/H migrados; tests cross-language 1:1; gen_ast_nodos_h.py --check en CI)
- H12 | CERRADA | std/oraculo.syn sin duplicar generar_texto (2026-08-26, commit 1a4b4e1)
- R3 | CERRADA | tests/unit/test_r3_param_adt.py + fixtures: S1/S2 compilan y ejecutan parámetros ADT instanciados (Resultado<entero,texto> -> Resultado_entero_texto)
