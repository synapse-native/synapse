# Verificación — ME r311_workflow_build_canonico

CUMPLE.

## Requisitos del plan y su verificación

| requisito | verificación | resultado |
|---|---|---|
| Manual 9 §6.1 — CUMPLE — compilar en todos los targets | `pytest tests/auditoria/test_r311_workflow_build_canonico.py` | 2 passed |

## Causa y cambio

El job Windows del workflow ya superaba el setup, pero fallaba en el link:

```
undefined reference to `_syn_http_get_archivo'
undefined reference to `_syn_axon_limpiar_toml'
undefined reference to `_syn_debug_cargar_traza'
undefined reference to `_syn_diagnostic_info'
undefined reference to `_syn_health_check'
undefined reference to `_syn_lista_agregar'
undefined reference to `_syn_debug_posicion_actual'
undefined reference to `randombytes'
collect2.exe: error: ld returned 1 exit status
```

La causa es la línea `gcc` escrita a mano, que enumeraba solo
`synapse_rt.c`, `runtime/core/memory.c`, `runtime/core/concurrency.c`,
`axon/tweetnacl.c` — el resto del runtime (http, axon, debug, tracing, listas,
`randombytes`) no se compilaba. Ahora el paso ejecuta `python build.py`
(bootstrap S1→S2→S3 con el runtime modular completo de `pipeline.py`) y copia
`synapse_stage2.exe` a `dist\bin\synapse.exe`.

## Otros checks

| check | resultado |
|---|---|
| `pytest tests/auditoria/test_r311_workflow_build_canonico.py` | 2 passed |
| `contrastar.py --plan docs/plan_ME_r311_workflow_build_canonico.md` | PASS (1/1) |
| `verificar_alineacion.py` | 0 brechas |

Sin archivos de producción en el diff: `.github/` está fuera del alcance del
expediente de alineación (lo informa `alineacion.py --nuevo`).

## Limitación declarada

El link real en el runner de Windows se confirma con el run del push
siguiente; localmente `build.py` produce `synapse_stage2.exe` con el hash
esperado.
