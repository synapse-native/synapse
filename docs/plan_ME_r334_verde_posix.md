# Plan ME r334 — suite verde y portable en todos los targets

## Objetivo

Reparar la suite completa para que compile y ejecute los binarios C en
Windows, Linux y macOS sin depender de rutas o flags exclusivos de Windows.

requisito: Manual 9 §6.2
texto: "Ejecutar la suite de tests completa para cada target."
implementacion: el harness compila todos los binarios extra en POSIX (omite -Wl,--stack y -lws2_32), resuelve gcc del sistema y los tests no hardcodean toolchain_gcc12.
oraculo: tests/syquex/test_lista.py

requisito: Manual 1 §7.1
texto: "Todo cambio debe pasar la suite completa de pruebas:"
implementacion: CI construye stage2/stage3, CLI y LSP antes de ejecutar pytest, instala WABT y limpia los dumps S1 retirados.
oraculo: tests/auditoria/test_r334_ci_artefactos.py

requisito: Manual 2 §12
texto: "contratos requiere/garantiza en todas las funciones públicas"
implementacion: se conserva la API FFI de std.texto con contratos y se documenta el límite de deduplicación.
oraculo: tests/unit/test_std_contracts.py

requisito: Manual 3 §5.2
texto: "Lista<T> — lista dinámica (vector)"
implementacion: los binarios de lista/mapa enlazan sus objetos modulares y se ejecutan en POSIX; architect_det usa un símbolo propio para no colisionar con explorer_det.
oraculo: tests/opensyn/test_architect_det_comportamiento.py
