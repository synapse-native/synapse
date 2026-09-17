# Plan ME f325 — Puente FFI lista/mapa

## Objetivo
Crear `nucleo/puente_ffi_lista_mapa.syn` con las declaraciones `externo funcion`
para listas y mapas del runtime C (`runtime/core/lista.c`, `runtime/core/mapa.c`),
cumpliendo el tipo de handle `entero` y la regla de `inseguro`.

## Archivos a modificar
- `nucleo/puente_ffi_lista_mapa.syn` (NOVO — código de producción)

## Archivos de test
- `tests/unit/test_puente_ffi_lista_mapa.py` (NOVO — oráculo)

---

## 1. Declaraciones FFI (Símbolos)

requisito: Manual 6 §3.1
texto: "Tanto Synapse como Syquex permiten declarar funciones de C con la palabra clave `externo`."
implementacion: nucleo/puente_ffi_lista_mapa.syn:27-46 — 11 declaraciones `externo funcion` para _syn_lista_* y _syn_mapa_*, cada una con `// cumple Manual 6 §3.1`
oraculo: tests/unit/test_puente_ffi_lista_mapa.py

requisito: Manual 6 §3.1
texto: "| entero | int64_t | entero | Tamaño fijo de 64 bits |"
implementacion: nucleo/puente_ffi_lista_mapa.syn — todos los handles usan `entero` (no `Lista*` ni `Mapa*`); la tabla de tipos Manual 6 §3.1 confirma el mapeo entero↔int64_t
oraculo: tests/unit/test_puente_ffi_lista_mapa.py

requisito: Manual 6 §3.1
texto: "| texto | CadenaSegura (struct) | texto | Longitud + buffer |"
implementacion: nucleo/puente_ffi_lista_mapa.syn:18-20 — las claves de mapa usan `texto` (no `entero`), mapeado a CadenaSegura en C
oraculo: tests/unit/test_puente_ffi_lista_mapa.py

---

## 2. Bloque inseguro (Símbolos)

requisito: Manual 6 §3.2
texto: "Las llamadas a FFI se consideran inseguras y deben encapsularse en un bloque inseguro."
implementacion: nucleo/puente_ffi_lista_mapa.syn:59 — todas las funciones wrapper envuelven el FFI en `inseguro:`
oraculo: tests/unit/test_puente_ffi_lista_mapa.py

---

## 3. Contratos (Símbolos)

requisito: Manual 2 §5.1
texto: "requiere: Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
implementacion: nucleo/puente_ffi_lista_mapa.syn:55 — todas las funciones wrapper públicas llevan `requiere:` y `garantiza:`
oraculo: tests/unit/test_puente_ffi_lista_mapa.py

---

## 4. Oráculo de alineación (Símbolos)

requisito: Manual 6 §1.1
texto: "El ecosistema Synapse se basa en un Árbol de Sintaxis Abstracta (AST) canónico y unificado denominado SemNodo[]."
implementacion: nucleo/puente_ffi_lista_mapa.sin:2 — importa `parser_constantes` y comenta `// cumple Manual 6 §1.1`
oraculo: tests/unit/test_puente_ffi_lista_mapa.py
