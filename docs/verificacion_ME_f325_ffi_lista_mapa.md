# Verificación ME f325 — Puente FFI lista/mapa

> Formato: cada requisito con `CUMPLE` o `NO CUMPLE`, con `archivo:linea`.

## Manual 6 §3.1 CUMPLE — externo funcion para listas y mapas (nucleo/puente_ffi_lista_mapa.syn:27-46)
## Manual 6 §3.2 CUMPLE — FFI en bloque inseguro (nucleo/puente_ffi_lista_mapa.syn:54-59)
## Manual 2 §5.1 CUMPLE — contratos requiere/garantiza en funciones wrapper (nucleo/puente_ffi_lista_mapa.syn:55-58)
## Manual 6 §1.1 CUMPLE — SemNodo[] AST canónico unificado (nucleo/puente_ffi_lista_mapa.syn:2)

## Detalle por bloque

### Manual 6 §3.1 — Declaración de funciones externas
- CUMPLE — nucleo/puente_ffi_lista_mapa.syn:27 (`externo funcion _syn_lista_crear() -> entero`)
- CUMPLE — nucleo/puente_ffi_lista_mapa.syn:39 (`externo funcion _syn_mapa_crear() -> entero`)
- CUMPLE — nucleo/puente_ffi_lista_mapa.syn:41 (`externo funcion _syn_mapa_poner(m: entero, k: texto, v: entero) -> nulo`)
- CUMPLE — handle `entero` mapea a int64_t (tabla Manual 6 §3.1)

### Manual 6 §3.2 — Bloque inseguro
- CUMPLE — nucleo/puente_ffi_lista_mapa.syn:59 (`inseguro:` en lista_crear)
- CUMPLE — nucleo/puente_ffi_lista_mapa.sin:130 (`inseguro:` en mapa_crear)

### Manual 2 §5.1 — Contratos requiere/garantiza
- CUMPLE — nucleo/puente_ffi_lista_mapa.syn:54-55 (`requiere:` en lista_crear)
- CUMPLE — nucleo/puente_ffi_lista_mapa.syn:57-58 (`garantiza:` en lista_crear)
- CUMPLE — nucleo/puente_ffi_lista_mapa.syn:125-126 (`requiere:` en mapa_crear)
- CUMPLE — nucleo/puente_ffi_lista_mapa.syn:128-129 (`garantiza:` en mapa_crear)

### Manual 6 §1.1 — SemNodo[] AST canónico unificado
- CUMPLE — nucleo/puente_ffi_lista_mapa.syn:2 (comentario cumple + SemNodo[] referenciado)

## Oráculos ejecutados (release)
- tests/unit/test_puente_ffi_lista_mapa.py — 12/12 PASS

## Evidencia de ejecución
- Compilación S1: `python main.py nucleo/puente_ffi_lista_mapa.syn` → rc=0 (exitosa)
- Tests: `pytest tests/unit/test_puente_ffi_lista_mapa.py -v` → 12 passed
- Oráculo contraste: `python auditoria/contrastar.py --plan docs/plan_ME_f325_ffi_lista_mapa.md` → 0 brechas
- Gate alineación: `python auditoria/alineacion.py --verificar --me f325 --exigir-sello` → OK
- Gate verificación: `python auditoria/verificar_alineacion.py` → 0 brechas
