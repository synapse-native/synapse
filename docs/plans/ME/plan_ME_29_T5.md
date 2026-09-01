requisito: Manual 7 §2.3 — opensyn/installer.syn implementa instalación
texto: Crear opensyn/installer.syn con detección de hardware y selección de modelo
implementacion: opensyn/installer.syn + tests/opensyn/test_installer.py
oraculo: tests/opensyn/test_installer.py

requisito: Manual 2 §3 — tipos primitivos (texto/struct por nombre) en generador C
texto: Fix bug tipo_de_expr en ExprAccesoCampo sobre tipos Synapse sin prefijo struct
implementacion: compilador/generator/emit_expressions.py
oraculo: tests/opensyn/test_installer.py

// Cambios aplicados bajo MTS:
// 1. H-F29-T5a (corregido): tipo_de_expr en compilador/generator/emit_expressions.py:84-93
//    caia en 'int' para ExprAccesoCampo sobre tipos Synapse sin prefijo 'struct '
//    -> concat("...", entero_a_texto(hw.arquitectura)) -> error C incompatible type.
//    Fix: aceptar tanto "X" como "struct X" (Manual 2 §3 tipos).
// 2. H-F29-T5b (registrado, no resuelto en este ME): bug RAII preexistente en
//    concatenacion multiple de campos struct texto: runtime/core/sistema.c:24 concat()
//    falla con "malloc fallo" cuando el campo es CadenaSegura retornada por FFI
//    (hw.arquitectura = _syn_arquitectura()). El codegen emite copia shallow de
//    16 bytes; el literal estático retornado por FFI no es movible, y concat()
//    anidado libera el pool antes de usarlo. Workaround: installer imprime prefijos
//    como literales separados (cumple oraculo del test).
// 3. Cambios ortograficos del installer.syn para alinearse a la gramatica del
//    Manual 2 §2 (sin literales {campo: valor}, sin sino si, con let x: T explicito).