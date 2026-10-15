# Expediente de alineación f14_mto_ci

base: HEAD  # commit sobre el que se leyó el manual
cambio_hash: e1df969a904e3db5

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## build.py
- manual: 9
  seccion: 6.2
  cita: "La verificación del bootstrap (diff 0 bytes)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: build.py:3
  oraculo: tests/integration/test_build_py.py

- manual: 9
  seccion: 2.3
  cita: "Verificar el bootstrap (diff 0 bytes entre Stage 2 y Stage 3)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: build.py:4
  oraculo: tests/auditoria/test_oraculos_f14_mto_ci.py

## compilador/generator/emit_selfhost.py
- manual: 2
  seccion: 3
  cita: "El lexer utiliza diccionarios por idioma. Los TokenID son universales, lo que permite la arquitectura poliglota del ecosistema."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/generator/emit_selfhost.py:5
  oraculo: auditoria/oraculos/oraculo_f14_mto_ci.py

- manual: 1
  seccion: 3.1
  cita: "El compilador unificado procesa código fuente de Synapse (.syn), Syquex (.syq) e incluso prompts en lenguaje natural (via OpenSyn) a través de un pipeline compartido:"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/generator/emit_selfhost.py:3
  oraculo: tests/auditoria/test_oraculos_f14_mto_ci.py

## compilador/lexer.py
- manual: 1
  seccion: 3.1
  cita: "El compilador unificado procesa código fuente de Synapse (.syn), Syquex (.syq) e incluso prompts en lenguaje natural (via OpenSyn) a través de un pipeline compartido:"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/lexer.py:358
  oraculo: tests/auditoria/test_oraculos_f14_mto_ci.py

## compilador/parser_declarations.py
- manual: 2
  seccion: 2
  cita: "La gramática de Synapse se define mediante una notación EBNF extendida."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/parser_declarations.py:159
  oraculo: tests/auditoria/test_oraculos_f14_mto_ci.py

## distribuir.py
- manual: 9
  seccion: 6.3
  cita: "Cada artefacto se firma con la clave privada Ed25519 del proyecto."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: distribuir.py:3
  oraculo: tests/integration/test_distribucion.py

- manual: 9
  seccion: 2.1
  cita: "El proceso de empaquetado genera artefactos para las plataformas soportadas:"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: distribuir.py:4
  oraculo: tests/integration/test_release_unificado.py

