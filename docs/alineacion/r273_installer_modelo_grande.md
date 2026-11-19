# Expediente de alineación r273_installer_modelo_grande

base: HEAD 4b91439  # commit sobre el que se leyó el manual
cambio_hash: e71dee4a8e127026

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## opensyn/installer.syn
- manual: 7
  seccion: 2.5
  cita: "Lee la lista de modelos disponibles y sus metadatos (URLs, hashes SHA‑256, tamaños) desde el archivo `modelos.toml` que se distribuye junto con el instalador (ver Manual 9, §5.6)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/installer.syn:5
  oraculo: tests/integration/test_installer_modelo_grande.py

- manual: 9
  seccion: 5.2
  cita: "| VRAM | Modelo | Cuantización | Tamaño aprox. |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/installer.syn:6
  oraculo: tests/integration/test_installer_modelo_grande.py

- manual: 9
  seccion: 5.3
  cita: "El modelo se descarga desde Hugging Face o Axon Hub, y se verifica su integridad mediante SHA‑256."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/installer.syn:148
  oraculo: tests/integration/test_installer_modelo_grande.py

- manual: 9
  seccion: 5.4
  cita: "El instalador configura `llama-server` con los parámetros óptimos:"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/installer.syn:8
  oraculo: tests/integration/test_installer_modelo_grande.py

## runtime/core/axon.c
- manual: 8
  seccion: 4.3
  cita: "El comando `synapse init` crea la siguiente estructura:"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/axon.c:6
  oraculo: tests/unit/test_axon_crypto.py

- manual: 6
  seccion: 5.1
  cita: "El formato de serialización para canales remotos es un subconjunto de MessagePack, optimizado para velocidad. **Especificación normativa:** el formato definitivo está en el Manual 5, §6.3."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/axon.c:9
  oraculo: tests/unit/test_axon_crypto.py

- manual: 9
  seccion: 5.3
  cita: "El modelo se descarga desde Hugging Face o Axon Hub, y se verifica su integridad mediante SHA‑256."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/axon.c:47
  oraculo: tests/integration/test_installer_modelo_grande.py

## runtime/core/cripto.c
- manual: 9
  seccion: 5.3
  cita: "El modelo se descarga desde Hugging Face o Axon Hub, y se verifica su integridad mediante SHA‑256."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/cripto.c:119
  oraculo: tests/integration/test_installer_modelo_grande.py

## runtime/core/hash_cache.c
- manual: 9
  seccion: 5.3
  cita: "El modelo se descarga desde Hugging Face o Axon Hub, y se verifica su integridad mediante SHA‑256."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/hash_cache.c:1
  oraculo: tests/integration/test_installer_modelo_grande.py

## runtime/core/hash_cache.h
- manual: 9
  seccion: 5.3
  cita: "El modelo se descarga desde Hugging Face o Axon Hub, y se verifica su integridad mediante SHA‑256."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/hash_cache.h:1
  oraculo: tests/integration/test_installer_modelo_grande.py

## runtime/core/modelo.c
- manual: 9
  seccion: 5.3
  cita: "El modelo se descarga desde Hugging Face o Axon Hub, y se verifica su integridad mediante SHA‑256."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/modelo.c:988
  oraculo: tests/integration/test_installer_modelo_grande.py
