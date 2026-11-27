# Expediente de alineación f32_3_memoria_cifrada

base: HEAD
cambio_hash: d74d14020e758c25

## opensyn/memoria_persistente_cifrada.syn
- manual: 6
  seccion: "1.1"
  cita: "El ecosistema Synapse se basa en un **Árbol de Sintaxis Abstracta (AST) canónico y unificado** denominado `SemNodo[]`."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/memoria_persistente_cifrada.syn:1
  oraculo: tests/opensyn/test_memoria_cifrada.py
- manual: 2
  seccion: "5.1"
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/memoria_persistente_cifrada.syn:61
  oraculo: tests/opensyn/test_memoria_cifrada.py
