# Expediente de alineación r334_verde_posix

base: HEAD
cambio_hash: 042cae457a01ca31

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.

## opensyn/architect_det.syn
- manual: 6
  seccion: 1.1
  cita: "El ecosistema Synapse se basa en un **Árbol de Sintaxis Abstracta (AST) canónico y unificado** denominado `SemNodo[]`."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/architect_det.syn:3
  oraculo: tests/opensyn/test_architect_det_comportamiento.py

- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/architect_det.syn:5
  oraculo: tests/opensyn/test_architect_det_comportamiento.py

## std/texto.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: std/texto.syn:16
  oraculo: tests/unit/test_std_contracts.py
