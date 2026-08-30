# Verificación ME — Enlazado de nucleo/federated.c

## Requisito 1: std/federated enlazado en pipeline S1 (Manual 1 §4)

- CUMPLE: `pipeline.py` incluye `_RT_FEDERATED_FUENTES = ("nucleo/federated.c",)` y
  loop de enlazado que compila y agrega `federated.o` al link.
  - archivo: pipeline.py:121-125 (_RT_FEDERATED_FUENTES), pipeline.py:813-819 (loop)
  - evidencia: `federated.o` visible en línea GCC del stage1

## Requisito 2: std/federated enlazado en stage compiler nativo (Manual 5 §6.2)

- CUMPLE: `nucleo/principal.syn` agrega `nucleo/federated.c` a la línea GCC + flag
  `-Wl,--allow-multiple-definition` para resolver colisión con wrappers de std/federated.syn.
  - archivo: nucleo/principal.syn:700-701
  - evidencia: `nucleo/federated.c` visible en línea GCC del stage3

## Requisito 3: bootstrap S2==S3 (Manual 9 §9.7)

- CUMPLE: S2==S3 byte-idéntico (MD5: 4aa2b25baba0fe77a3d91adc8a3f9457).

## Requisito 4: importar std.federated compila desde nativo

- CUMPLE: `synapse_stage3.exe test_fed.syn test_fed.exe` → "Compilacion nativa exitosa".
  - oráculo: tests/integration/test_federated_exec_10.py
