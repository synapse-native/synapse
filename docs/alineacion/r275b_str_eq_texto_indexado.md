# Expediente de alineación r275b_str_eq_texto_indexado

base: HEAD  # commit sobre el que se leyó el manual
cambio_hash: d41891ec4639a785

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## nucleo/generator.syn
- manual: 2
  seccion: 8.2
  cita: "Synapse utiliza un algoritmo de inferencia de tipos basado en **Hindley‑Milner** (algoritmo W)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generator.syn:5838
  oraculo: auditoria/oraculos/oraculo_r275b_texto_indexado.py

## nucleo/principal.syn
- manual: 9
  seccion: 6.2
  cita: "La verificación del bootstrap (diff 0 bytes)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:32
  oraculo: auditoria/oraculos/oraculo_r252_paridad_bootstrap.py

- manual: 8
  seccion: 4.2
  cita: "| `--check` / `--no-emit` | **Modo de validación:** Solo verifica la sintaxis y semántica, sin generar código de salida. Útil para el bucle de corrección de OpenSyn. |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:88
  oraculo: tests/integration/test_cli_check.py

- manual: 8
  seccion: 4.1
  cita: "| `synapse build <archivo>` | Compila el archivo (`.syn` o `.syq`) a binario. |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:187
  oraculo: auditoria/oraculos/oraculo_r275b_texto_indexado.py

## opensyn/permisos.syn
- manual: 7
  seccion: 1.1
  cita: "**Completamente local:** Los modelos se descargan y ejecutan en el hardware del usuario. No hay dependencia de la nube."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/permisos.syn:4
  oraculo: auditoria/oraculos/oraculo_r275b_texto_indexado.py

- manual: 7
  seccion: 7.3
  cita: "**Sandboxing:** El servidor de inferencia se ejecuta con permisos mínimos."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/permisos.syn:3
  oraculo: auditoria/oraculos/oraculo_r275b_texto_indexado.py
