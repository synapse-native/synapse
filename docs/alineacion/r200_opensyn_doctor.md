# Expediente de alineación r200_opensyn_doctor

base: HEAD  # commit sobre el que se leyó el manual
cambio_hash: e13f4308e5c35e65

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
  evidencia: opensyn/principal.syn:1925
  oraculo: auditoria/oraculos/oraculo_r200_opensyn_doctor.py

- manual: 7
  seccion: 4.2
  cita: "El prompt se envía al servidor de inferencia (`llama-server`) mediante el cliente HTTP (`llama_client.c`)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/principal.syn:689
  oraculo: auditoria/oraculos/oraculo_r200_opensyn_doctor.py

- manual: 7
  seccion: 6.1
  cita: "Al finalizar, se ejecuta una prueba de humo."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/principal.syn:1926
  oraculo: auditoria/oraculos/oraculo_r200_opensyn_doctor.py
