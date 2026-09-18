# Expediente de alineación f32_1_grafo

base: HEAD
cambio_hash: 3f372acaabfc07a3

## nucleo/grafo_conocimiento.syn
- manual: 6
  seccion: 1.1
  cita: "El ecosistema Synapse se basa en un Árbol de Sintaxis Abstracta (AST) canónico y unificado denominado SemNodo[]."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/grafo_conocimiento.syn:1
  oraculo: tests/opensyn/test_grafo.py

- manual: 2
  seccion: 12
  cita: "Lexer multi‑idioma | `pytest tests/unit/test_lexer.py -v` | 100% pass, >95% cobertura |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/grafo_conocimiento.syn:1
  oraculo: tests/opensyn/test_grafo.py
