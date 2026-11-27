# Expediente de alineación r288_bom_sweep

base: HEAD  # commit sobre el que se leyó el manual
cambio_hash: bf639f21edb8699a

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## opensyn/bindings_generator.py
- manual: 7
  seccion: 2.1
  cita: "El orquestador es un proceso en C que gestiona el ciclo de vida del servidor de inferencia (`llama-server`)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/bindings_generator.py:561
  oraculo: auditoria/verificar_encoding.py

## opensyn/full_pipeline.py
- manual: 7
  seccion: 2.1
  cita: "El orquestador es un proceso en C que gestiona el ciclo de vida del servidor de inferencia (`llama-server`)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/full_pipeline.py:162
  oraculo: auditoria/verificar_encoding.py

## opensyn/generate_runtime_bindings.py
- manual: 6
  seccion: 3.1
  cita: "Tanto Synapse como Syquex permiten declarar funciones de C con la palabra clave `externo`."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/generate_runtime_bindings.py:1
  oraculo: auditoria/verificar_encoding.py

## runtime/core/cache.c
- manual: 5
  seccion: 11
  cita: "Con la concurrencia y comunicación cubiertas, el siguiente manual (Manual 6) se centrará en la **Integración del Ecosistema**: cómo Synapse, Syquex y OpenSyn se interconectan, la FFI, la serialización, la generación de bindings y la interoperabilidad."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/cache.c:49
  oraculo: auditoria/verificar_encoding.py

## runtime/core/cache.h
- manual: 5
  seccion: 8.1
  cita: "El scheduler de fibras utiliza un algoritmo de **work‑stealing** para balancear la carga entre hilos del sistema operativo."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/cache.h:47
  oraculo: auditoria/verificar_encoding.py

## runtime/core/cluster.h
- manual: 5
  seccion: 8.1
  cita: "El scheduler de fibras utiliza un algoritmo de **work‑stealing** para balancear la carga entre hilos del sistema operativo."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/cluster.h:104
  oraculo: auditoria/verificar_encoding.py

## runtime/core/cripto.c
- manual: 9
  seccion: 5.3
  cita: "El modelo se descarga desde Hugging Face o Axon Hub, y se verifica su integridad mediante SHA‑256."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/cripto.c:119
  oraculo: auditoria/verificar_encoding.py

## runtime/core/cripto.h
- manual: 5
  seccion: 8.1
  cita: "El scheduler de fibras utiliza un algoritmo de **work‑stealing** para balancear la carga entre hilos del sistema operativo."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/cripto.h:22
  oraculo: auditoria/verificar_encoding.py

## runtime/core/db.c
- manual: 5
  seccion: 8.1
  cita: "El scheduler de fibras utiliza un algoritmo de **work‑stealing** para balancear la carga entre hilos del sistema operativo."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/db.c:299
  oraculo: auditoria/verificar_encoding.py

## runtime/core/db.h
- manual: 5
  seccion: 8.1
  cita: "El scheduler de fibras utiliza un algoritmo de **work‑stealing** para balancear la carga entre hilos del sistema operativo."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/db.h:42
  oraculo: auditoria/verificar_encoding.py

## runtime/core/debug.h
- manual: 8
  seccion: 3.4
  cita: "El CLI unificado (`synapse`) incluye comandos para depuración:"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/debug.h:58
  oraculo: auditoria/verificar_encoding.py

## runtime/core/ffi_marshaling.c
- manual: 5
  seccion: 8.1
  cita: "El scheduler de fibras utiliza un algoritmo de **work‑stealing** para balancear la carga entre hilos del sistema operativo."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/ffi_marshaling.c:148
  oraculo: auditoria/verificar_encoding.py

## runtime/core/ffi_marshaling.h
- manual: 5
  seccion: 8.1
  cita: "El scheduler de fibras utiliza un algoritmo de **work‑stealing** para balancear la carga entre hilos del sistema operativo."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/ffi_marshaling.h:74
  oraculo: auditoria/verificar_encoding.py

## runtime/core/fuzz.c
- manual: 5
  seccion: 8.1
  cita: "El scheduler de fibras utiliza un algoritmo de **work‑stealing** para balancear la carga entre hilos del sistema operativo."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/fuzz.c:357
  oraculo: auditoria/verificar_encoding.py

## runtime/core/fuzz.h
- manual: 5
  seccion: 8.1
  cita: "El scheduler de fibras utiliza un algoritmo de **work‑stealing** para balancear la carga entre hilos del sistema operativo."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/fuzz.h:38
  oraculo: auditoria/verificar_encoding.py

## runtime/core/http.c
- manual: 5
  seccion: 8.1
  cita: "El scheduler de fibras utiliza un algoritmo de **work‑stealing** para balancear la carga entre hilos del sistema operativo."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/http.c:116
  oraculo: auditoria/verificar_encoding.py

## runtime/core/http.h
- manual: 5
  seccion: 8.1
  cita: "El scheduler de fibras utiliza un algoritmo de **work‑stealing** para balancear la carga entre hilos del sistema operativo."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/http.h:21
  oraculo: auditoria/verificar_encoding.py

## runtime/core/json.h
- manual: 5
  seccion: 8.1
  cita: "El scheduler de fibras utiliza un algoritmo de **work‑stealing** para balancear la carga entre hilos del sistema operativo."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/json.h:26
  oraculo: auditoria/verificar_encoding.py

## runtime/core/lista.c
- manual: 6
  seccion: 3.1
  cita: "Tanto Synapse como Syquex permiten declarar funciones de C con la palabra clave `externo`."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/lista.c:2
  oraculo: auditoria/verificar_encoding.py

## runtime/core/mapa.c
- manual: 6
  seccion: 3.1
  cita: "Tanto Synapse como Syquex permiten declarar funciones de C con la palabra clave `externo`."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/mapa.c:2
  oraculo: auditoria/verificar_encoding.py

## runtime/core/math.c
- manual: 5
  seccion: 8.1
  cita: "El scheduler de fibras utiliza un algoritmo de **work‑stealing** para balancear la carga entre hilos del sistema operativo."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/math.c:68
  oraculo: auditoria/verificar_encoding.py

## runtime/core/math.h
- manual: 5
  seccion: 8.1
  cita: "El scheduler de fibras utiliza un algoritmo de **work‑stealing** para balancear la carga entre hilos del sistema operativo."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/math.h:31
  oraculo: auditoria/verificar_encoding.py

## runtime/core/network.c
- manual: 5
  seccion: 8.1
  cita: "El scheduler de fibras utiliza un algoritmo de **work‑stealing** para balancear la carga entre hilos del sistema operativo."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/network.c:80
  oraculo: auditoria/verificar_encoding.py

## runtime/core/network.h
- manual: 5
  seccion: 8.1
  cita: "El scheduler de fibras utiliza un algoritmo de **work‑stealing** para balancear la carga entre hilos del sistema operativo."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/network.h:39
  oraculo: auditoria/verificar_encoding.py

## runtime/core/sistema.h
- manual: 5
  seccion: 8.1
  cita: "El scheduler de fibras utiliza un algoritmo de **work‑stealing** para balancear la carga entre hilos del sistema operativo."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/sistema.h:35
  oraculo: auditoria/verificar_encoding.py

## runtime/core/string_utils.h
- manual: 5
  seccion: 8.1
  cita: "El scheduler de fibras utiliza un algoritmo de **work‑stealing** para balancear la carga entre hilos del sistema operativo."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/string_utils.h:33
  oraculo: auditoria/verificar_encoding.py

## runtime/core/tensor.c
- manual: 5
  seccion: 8.1
  cita: "El scheduler de fibras utiliza un algoritmo de **work‑stealing** para balancear la carga entre hilos del sistema operativo."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/tensor.c:641
  oraculo: auditoria/verificar_encoding.py

## runtime/core/tensor.h
- manual: 5
  seccion: 8.1
  cita: "El scheduler de fibras utiliza un algoritmo de **work‑stealing** para balancear la carga entre hilos del sistema operativo."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/tensor.h:54
  oraculo: auditoria/verificar_encoding.py

## runtime/core/texto.h
- manual: 6
  seccion: 3.1
  cita: "Tanto Synapse como Syquex permiten declarar funciones de C con la palabra clave `externo`."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/texto.h:32
  oraculo: auditoria/verificar_encoding.py

## runtime/core/tiempo.c
- manual: 5
  seccion: 8.1
  cita: "El scheduler de fibras utiliza un algoritmo de **work‑stealing** para balancear la carga entre hilos del sistema operativo."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/tiempo.c:154
  oraculo: auditoria/verificar_encoding.py

## runtime/core/tiempo.h
- manual: 5
  seccion: 8.1
  cita: "El scheduler de fibras utiliza un algoritmo de **work‑stealing** para balancear la carga entre hilos del sistema operativo."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/tiempo.h:46
  oraculo: auditoria/verificar_encoding.py

## runtime/core/toml.c
- manual: 5
  seccion: 8.1
  cita: "El scheduler de fibras utiliza un algoritmo de **work‑stealing** para balancear la carga entre hilos del sistema operativo."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/toml.c:330
  oraculo: auditoria/verificar_encoding.py

## runtime/core/toml.h
- manual: 5
  seccion: 8.1
  cita: "El scheduler de fibras utiliza un algoritmo de **work‑stealing** para balancear la carga entre hilos del sistema operativo."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/toml.h:35
  oraculo: auditoria/verificar_encoding.py

## runtime/core/web.c
- manual: 5
  seccion: 8.1
  cita: "El scheduler de fibras utiliza un algoritmo de **work‑stealing** para balancear la carga entre hilos del sistema operativo."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/web.c:445
  oraculo: auditoria/verificar_encoding.py

## runtime/core/web.h
- manual: 5
  seccion: 8.1
  cita: "El scheduler de fibras utiliza un algoritmo de **work‑stealing** para balancear la carga entre hilos del sistema operativo."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/web.h:40
  oraculo: auditoria/verificar_encoding.py

## synapse_llvm.c
- manual: 1
  seccion: 6
  cita: "La evolución del ecosistema sigue una hoja de ruta clara, documentada en el ROADMAP.md:"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: synapse_llvm.c:299
  oraculo: auditoria/verificar_encoding.py

## synapse_llvm.h
- manual: 1
  seccion: 6
  cita: "La evolución del ecosistema sigue una hoja de ruta clara, documentada en el ROADMAP.md:"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: synapse_llvm.h:75
  oraculo: auditoria/verificar_encoding.py

## synapse_wasm.c
- manual: 1
  seccion: 6
  cita: "La evolución del ecosistema sigue una hoja de ruta clara, documentada en el ROADMAP.md:"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: synapse_wasm.c:319
  oraculo: auditoria/verificar_encoding.py

## synapse_wasm.h
- manual: 1
  seccion: 6
  cita: "La evolución del ecosistema sigue una hoja de ruta clara, documentada en el ROADMAP.md:"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: synapse_wasm.h:81
  oraculo: auditoria/verificar_encoding.py
