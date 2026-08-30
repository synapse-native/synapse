# Verificación ME — A2: Fix detección VRAM en Windows via DXGI

## Requisito 1: VRAM detectada correctamente en Windows

- CUMPLE: `nucleo/detect_hardware.c` ahora usa DXGI `IDXGIFactory1` →
  `IDXGIAdapter1::GetDesc1()` → `DedicatedVideoMemory` (bytes, SIZE_T) para
  obtener la VRAM real. Se reemplazó la lectura de `WinSAT\GraphicsScore`
  (WEI score 1-9.9, NO VRAM) y el fallback `GetDeviceCaps(hdc, 120)`
  (índice indocumentado, devolvía 0). Comentario grep-chequeable
  `cumple Manual 9 §5.7`.
- Oráculo: `tests/test_detect_hardware.c` compila con `-ldxgi` y ejecuta
  43/43 tests (perfils simulados + detección real + JSON + diferenciación).
  La detección real (`test_real_hw_detection`) pasa con RAM > 0, CPUs > 0,
  modelo sugerido no vacío.

## Conclusión

CUMPLE Manual 9 §5.7. La desviación A2 del reporte R_AUDIT_DESV.md queda
corregida: VRAM ahora se detecta vía DXGI DedicatedVideoMemory (el mecanismo
correcto en Windows) en lugar de WinSAT GraphicsScore (WEI score).
