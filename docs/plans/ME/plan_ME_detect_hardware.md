# Plan ME — detect_hardware (M4.1 / Manual 9 §5.7)

requisito: Manual 9 §5.7 (detección de hardware/GPU del otro agente): el runtime
  debe detectar RAM, VRAM, CPUs y sugerir config (tier/modelo/ctx/threads/ngl)
  para OpenSyn (Hallazgo A2: WinSAT GraphicsScore y GetDeviceCaps no reportan
  VRAM real; DXGI DedicatedVideoMemory es la fuente correcta).

texto: nucleo/detect_hardware.c implementa synapse_detectar_hardware (DXGI
  DedicatedVideoMemory en Windows, nvidia-smi en Linux), detect_vram_total,
  synapse_hw_sugerir_config, synapse_hw_imprimir_perfil y synapse_hw_to_json.
  CLI: nucleo/detect_hardware_cli.c. El oráculo (tests/test_detect_hardware.c,
  43 asserts) estaba HUÉRFANO: solo corría manualmente, no vía la suite.

implementacion: nucleo/detect_hardware.c + nucleo/detect_hardware.h (cumple
  Manual 9 §5.7) + CLI. TDD: tests/test_detect_hardware.c verifica
  diferenciación 8GB/16GB/32GB/64GB y serialización JSON. Se cablea en la
  suite vía tests/integration/test_detect_hardware.py (build: test_detect_hardware.c
  + nucleo/detect_hardware.c, link -lgdi32 -ldxgi -lole32 -luuid).

oraculo: tests/test_detect_hardware.c imprime "43 passed" + "TODOS LOS TESTS DE
  HARDWARE PASARON" con rc=0; pytest tests/integration/test_detect_hardware.py PASS.
  Bootstrap S1==S2/S3 intacto (nada de esto afecta el compilador).
