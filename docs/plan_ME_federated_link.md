# Plan ME: Enlazado de nucleo/federated.c en pipeline y stage compiler

## Problema

`nucleo/federated.c` implementa `_syn_fed_*` (fed_iniciar, fed_cerrar, etc.) pero no está
en la línea de enlazado GCC. Programas que usan `importar std.federated` fallan en link
con "undefined reference to `_syn_fed_*`".

## Requisitos

requisito: Manual 1 §4
texto: "std/ — Librería estándar de Synapse. std/federated.syn listado como módulo."
implementacion: nucleo/federated.c agregado a _RT_FEDERATED_FUENTES en pipeline.py y a
  la línea GCC en nucleo/principal.syn (para el stage compiler nativo).
oraculo: tests/integration/test_federated_exec_10.py

requisito: Manual 5 §6.2
texto: "Federated learning: fed_iniciar, fed_cerrar, fed_ronda_fedavg, etc."
implementacion: las funciones _syn_fed_* declaradas en std/federated.syn se resuelven
  enlazando nucleo/federated.c en ambos paths (pipeline S1 y stage compiler nativo).
oraculo: tests/integration/test_federated_exec_10.py

## Cambios

| Archivo | Cambio |
|---|---|
| `pipeline.py` | Agregar `_RT_FEDERATED_FUENTES` + loop de enlazado |
| `nucleo/principal.syn` | Agregar `nucleo/federated.c` a la línea GCC del stage compiler |

## Validación

1. `./synapse_stage3.exe test_fed.syn test_fed.exe` — compila sin link errors
2. `python -m pytest tests/integration/test_federated_exec_10.py -v` — verificar mejora
3. `python auditoria/verificar_alineacion.py` — 0 brechas
4. `python auditoria/contrastar.py --plan docs/plan_ME_federated_link.md` — gate
