# Plan MTS — Fixes FFI lista/mapa (int→int64_t + OOM safety + claves/valores)

## Requisito 1
requisito: tipo retorno FFI C vs declaración .syn
texto: "El handle `entero` es un puntero opaco (void*) reinterprettado como int64_t por el codegen S1"
implementacion: _syn_lista_longitud, _syn_mapa_longitud, _syn_mapa_contiene ahora retornan int64_t en vez de int
oraculo: tests/unit/test_puente_ffi_lista_mapa.py

## Requisito 2
requisito: OOM safety en mapa.c
texto: strdup puede retornar NULL en OOM
implementacion: check NULL después de strdup en _syn_mapa_poner
oraculo: tests/unit/test_puente_ffi_lista_mapa.py

## Requisito 3
requisito: wrappers para claves y valores de mapa
texto: "Las claves de mapa son `texto` (→ CadenaSegura en C)"
implementacion: wrappers mapa_claves() y mapa_valores() con contratos requiere/garantiza + inseguro
oraculo: tests/unit/test_puente_ffi_lista_mapa.py
