# Expediente de alineación r193_fixtures_infra

base: 40fc1cc  # commit sobre el que se leyó el manual
cambio_hash: 270133df57df7614

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## pipeline.py
- manual: 1
  seccion: 3.1
  cita: "El compilador unificado procesa código fuente de Synapse (.syn), Syquex (.syq) e incluso prompts en lenguaje natural (via OpenSyn) a través de un pipeline compartido:"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: pipeline.py:657
  oraculo: tests/auditoria/test_oraculos_r193_fixtures_infra.py

- manual: 1
  seccion: 7.2
  cita: "Todo cambio debe pasar la suite completa de pruebas:"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: pipeline.py:1195
  oraculo: tests/auditoria/test_oraculos_r193_fixtures_infra.py

- manual: 1
  seccion: 4
  cita: "El repositorio está organizado de manera modular para desacoplar el compilador, el runtime, el gestor de paquetes, el LSP, OpenSyn y los dos lenguajes."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: pipeline.py:1174
  oraculo: tests/auditoria/test_oraculos_r193_fixtures_infra.py

## Registro del ME (contexto, no requisitos)
- Rango de pruebas: `tests/**` exento del gate de lectura por
  `docs/gobernancia/mapa_manuales.md` §Exclusiones; modificación de tests
  gobernada por regla 5 con la autorización del Arquitecto registrada en
  `docs/plan_maestro_deudas.md` ("estás autorizado a tomar las decisiones
  siempre que sigas las reglas").
- El ME repara las 8 fallas del grupo A del barrido r191 (infra de
  fixtures) Y cierra H-R193-1/H-R193-2 de producción halladas en el frente
  de fixtures: PRARIDAD del enlace cacheado `[CACHE LINK]`
  (`_link_object`: dup de quantum_err_corr.o sin
  `-Wl,--allow-multiple-definition`; base_flags sin `-static`/env) y la key
  de caché de .o cruda (doble espacio) que recompilaba 46 .o en cada
  pasada (~90 s). E2E: pasada 2 de una compilación trivial 0,9 s con 0
  `[RUNTIME]` (antes ~100 s) — M1 §4 (cache.syn) operativo.
- El oráculo r193 ejecuta los 4 archivos del grupo A bajo el intérprete del
  proyecto (PASS 1/1, RC=0).
