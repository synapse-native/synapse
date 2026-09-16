# Plan ME f32_3_memoria_cifrada — Memoria Persistente Cifrada

## Requisito 1: Estructuras de memoria
requisito: Manual 6 §1.1 — AST canónico unificado como representación semántica
texto: "El ecosistema Synapse se basa en un Árbol de Sintaxis Abstracta (AST) canónico y unificado denominado SemNodo[]"
implementacion: Estructuras PatronAprendido, MemoriaNegativa, EntradaCifrada, CapaMemoria
oraculo: tests/opensyn/test_memoria_cifrada.py

## Requisito 2: Inicialización con derivación de clave
requisito: Manual 2 §12 — Funciones públicas con contratos requiere/garantiza
texto: "Toda función pública debe incluir cláusulas requiere y garantiza que documenten precondiciones y postcondiciones del comportamiento observable de la función"
implementacion: memoria_inicializar() con crypto_argon2id, zeroing de clave
oraculo: tests/opensyn/test_memoria_cifrada.py

## Requisito 3: Guardar y consultar patrones
requisito: Manual 2 §12 — Funciones públicas con contratos requiere/garantiza
texto: "Toda función pública debe incluir cláusulas requiere y garantiza que documenten precondiciones y postcondiciones del comportamiento observable de la función"
implementacion: memoria_guardar_patron(), memoria_consultar_patrones()
oraculo: tests/opensyn/test_memoria_cifrada.py

## Requisito 4: Registrar y evitar fallos
requisito: Manual 2 §12 — Funciones públicas con contratos requiere/garantiza
texto: "Toda función pública debe incluir cláusulas requiere y garantiza que documenten precondiciones y postcondiciones del comportamiento observable de la función"
implementacion: memoria_registrar_fallo(), memoria_evitar_fallos()
oraculo: tests/opensyn/test_memoria_cifrada.py

## Requisito 5: Guardar proyecto cifrado
requisito: Manual 2 §12 — Funciones públicas con contratos requiere/garantiza
texto: "Toda función pública debe incluir cláusulas requiere y garantiza que documenten precondiciones y postcondiciones del comportamiento observable de la función"
implementacion: memoria_guardar_proyecto()
oraculo: tests/opensyn/test_memoria_cifrada.py

## Requisito 6: Cierre seguro con zeroing
requisito: Manual 2 §12 — Funciones públicas con contratos requiere/garantiza
texto: "Toda función pública debe incluir cláusulas requiere y garantiza que documenten precondiciones y postcondiciones del comportamiento observable de la función"
implementacion: memoria_cerrar() con crypto_memzero
oraculo: tests/opensyn/test_memoria_cifrada.py
