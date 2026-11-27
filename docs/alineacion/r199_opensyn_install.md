# Expediente de alineación r199_opensyn_install

base: HEAD  # commit sobre el que se leyó el manual
cambio_hash: a86383cf07b5e14e

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## opensyn/principal.syn
- manual: 7
  seccion: 2.1
  cita: "**Inicio:** Verifica si `llama-server` está ejecutándose en el puerto configurado (por defecto 8088). Si no, lo inicia con los parámetros adecuados."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/principal.syn:96
  oraculo: auditoria/oraculos/oraculo_r199_opensyn_install.py

- manual: 7
  seccion: 4.2
  cita: "El prompt se envía al servidor de inferencia (`llama-server`) mediante el cliente HTTP (`llama_client.c`)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/principal.syn:665
  oraculo: auditoria/oraculos/oraculo_r199_opensyn_install.py
