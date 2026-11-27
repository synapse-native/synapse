# Verificación MTS — ME r234_certificacion_usuario_final

**Paso 1 de R234** (arnés de humo de usuario final). Fecha: 2026-11-17.
Plan: `docs/plan_ME_r234_certificacion_usuario_final.md`.

## Estado por requisito

| Requisito | Marca | Evidencia |
|---|---|---|
| Manual 9 §7 | NO CUMPLE (parcial) | `tests/e2e/test_smoke_usuario_final.py` 7/7 sobre `dist/bin`: `synapse --version` y `synapse check` con PATH sin Python ni GCC, compilación + ejecución de `.syn` y `.syq`, `opensyn --version`/`status`, LSP nativo `initialize`. Faltan la instalación silenciosa limpia (`instaladores/test_instalador_silencioso.py`) y la corrida en máquina sin toolchain (ver H-R234-1). |
| Manual 7 §7.3 | NO CUMPLE (parcial) | El arnés verifica que `opensyn status` no declare endpoints remotos (solo modelo/servidor local) y que la CLI funcione aislada de red externa en su arranque. Falta el monitoreo de conexiones salientes durante una inferencia real y la verificación de permisos mínimos del servidor. |

## Detalle de la cita textual

- Manual 9 §7 (texto del plan): *"Instalación en Windows (limpiamente) | Ejecutar instalador en máquina virtual Windows limpia | Instalación exitosa, PATH configurado, `synapse --version` funciona"*. Lo verificado aquí es la cláusula final (`synapse --version` funciona) sobre los binarios distribuidos y su autonomía de Python/GCC; la instalación silenciosa en VM limpia queda pendiente.
- Manual 7 §7.3 (texto del plan): *"Cero telemetría: Verificado con monitoreo de red (sin conexiones salientes). / Sandboxing: El servidor de inferencia se ejecuta con permisos mínimos."* El arnés no mide conexiones salientes todavía; no se declara cumplido.

## Hallazgo abierto

- **H-R234-1 (ALTO):** `dist/bin/synapse.exe` invoca `gcc` desde el PATH y no resuelve el toolchain del repo (`toolchain_gcc12/mingw64/bin`). En una máquina limpia sin GCC la compilación nativa falla (`GCC no se reconoce...` + `ERROR: GCC fallo con codigo 1`) aunque `--version` y `check` funcionen. El arnés exige el toolchain y falla con ese mensaje explícito (`_exigir_gcc`).
