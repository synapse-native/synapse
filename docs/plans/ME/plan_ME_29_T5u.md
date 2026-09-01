# Plan ME_29_T5u — Instalación de Modelo + Configuración OpenSyn

## Bloque MTS (método de trabajo seguro)

requisito: Manual 9 §5.3
texto: "El modelo se descarga desde Hugging Face o Axon Hub, y se verifica su integridad mediante SHA‑256"
implementacion: implementar instalar_modelo(hw: HardwareInfo) -> Resultado<texto, texto> en opensyn/installer.syn — selecciona modelo por VRAM, llama descargar_modelo(info)
oraculo: tests/opensyn/test_download.py

requisito: Manual 9 §5.4
texto: "config.toml con [general] idioma/editor, [modelo] nombre/ruta/n_ctx/n_threads/n_gpu_layers, [server] puerto/host/timeout"
implementacion: implementar ConfigInfo struct, generar_config(hw, ruta) -> ConfigInfo, escribir_config(config) -> logico en opensyn/installer.syn + _syn_escribir_archivo en runtime/core/modelo.c
oraculo: tests/opensyn/test_download.py

requisito: Manual 9 §5.6
texto: "El instalador lee modelos.toml para obtener URLs, hashes SHA-256 y tamaños de modelos disponibles"
implementacion: opensyn/modelos.toml ya existe (5 modelos con url/sha256/tam) — usado por seleccionar_modelo
oraculo: tests/opensyn/test_download.py

requisito: Manual 7 §2.3
texto: "opensyn/installer.syn compila y ejecuta, detecta hardware, selecciona modelo por VRAM, descarga con SHA-256"
implementacion: principal() orquesta detectar_hardware + instalar_modelo + generar_config + escribir_config
oraculo: tests/opensyn/test_installer.py
