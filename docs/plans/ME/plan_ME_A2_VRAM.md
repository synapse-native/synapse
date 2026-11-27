# Plan ME — A2: Fix detección VRAM en Windows via DXGI

## Requisito 1: VRAM detectada correctamente en Windows

requisito: Manual 9 §5.7 (Detección de hardware RAM/VRAM/CPU): "El asistente
  detecta automáticamente los recursos de hardware (RAM, VRAM, CPU) y selecciona
  el modelo codec más adecuado."
texto: En Windows, `nucleo/detect_hardware.c:49-53` lee `HKLM\...\WinSAT\GraphicsScore`
  (WEI score 1-9.9) e intenta interpretarlo como VRAM en MB (`vram_mb * 0.001`).
  GraphicsScore NO es VRAM — es una puntuación de rendimiento gráfico. El fallback
  usa `GetDeviceCaps(hdc, 120)` (índice indocumentado → devuelve 0). Resultado:
  VRAM siempre detectada como ~0 → selección de modelo incorrecta.
implementacion: Reemplazar la lectura WinSAT + fallback GetDeviceCaps por DXGI:
  1. `CreateDXGIFactory1(&IID_IDXGIFactory1, (void**)&factory)`
  2. `factory->EnumAdapters1(i, &adapter)` en bucle
  3. `adapter->GetDesc(&desc)` → `desc.DedicatedVideoMemory` (SIZE_T, bytes)
  4. Tomar la mayor VRAM de todos los adaptadores
  5. Fallback si DXGI no disponible: mantener nvidia-smi para Linux, 0 para Windows sin DXGI
  6. Enlazar con `-ldxgi` en Windows (pipeline.py linker_net + conftest _RT_BINARIOS_EXTRA)
oraculo: tests/test_detect_hardware.c compila y ejecuta (rc=0, todos los tests pasan)

## Requisito 2: detect_vram_total() accesible

requisito: Manual 1 §1.1 (OpenSyn detecta automáticamente recursos): la función
  de detección de VRAM debe ser accesible como API pública.
texto: Manual 9 §5.7 define la interfaz de detección. La función `synapse_detectar_hardware()`
  ya existe en detect_hardware.c y llena `HwProfile.vram_gb`. No se requiere una
  función separada `detect_vram_total()` si `synapse_detectar_hardware()` provee
  el valor correctamente.
implementacion: La corrección del requisito 1 ya hace que `HwProfile.vram_gb` contenga
  el valor correcto. No se necesita función adicional.
oraculo: tests/test_detect_hardware.c — test_real_hw_detection() verifica RAM > 0 y
  modelo sugerido no vacío.
