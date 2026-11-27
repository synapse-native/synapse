# Plan de Micro-Entregable r311_workflow_build_canonico

## Objetivo

El job Windows de `Cross-Compile Synapse` ya pasa el setup, pero falla al
enlazar: arma `dist\bin\synapse.exe` con una línea `gcc` escrita a mano que
lista solo cuatro fuentes del runtime:

```
gcc -O2 -static -o dist\bin\synapse.exe synapse_unity.c synapse_rt.c \
    runtime/core/memory.c runtime/core/concurrency.c axon/tweetnacl.c
```

El link falla con `undefined reference` a `_syn_http_get_archivo`,
`_syn_axon_limpiar_toml`, `_syn_debug_cargar_traza`, `_syn_diagnostic_info`,
`_syn_health_check`, `tr_total_eventos`, `_syn_lista_agregar`,
`_syn_debug_posicion_actual`, `rp_retroceder` y `randombytes` (tweetnacl).

El runtime modular completo lo compila `pipeline.py` y el binario distribuible
lo produce el build canónico de tres etapas (`build.py`), que además verifica
S2==S3. El workflow duplicaba ese trabajo con una lista incompleta.

## Requisito 1 — construir con el build canónico

requisito: Manual 9 §6.1
texto: "□ **Compilación sin errores**: todos los targets (Windows, Linux, macOS, WASM) compilan sin errores ni warnings."
implementacion: el paso de link de `.github/workflows/cross-compile.yml` ejecuta `python build.py` (bootstrap S1→S2→S3 + runtime modular completo vía `pipeline.py`), valida que exista `synapse_stage2.exe` y lo copia a `dist\bin\synapse.exe`; se elimina la línea `gcc` manual con la lista parcial de fuentes.
oraculo: tests/auditoria/test_r311_workflow_build_canonico.py

## Evidencia

| check | resultado |
|---|---|
| `pytest tests/auditoria/test_r311_workflow_build_canonico.py` | 2 passed |
| CI `Cross-Compile Synapse` tras el push | pendiente de corrida |
| `contrastar.py --plan docs/plan_ME_r311_workflow_build_canonico.md` | PASS (1/1) |
