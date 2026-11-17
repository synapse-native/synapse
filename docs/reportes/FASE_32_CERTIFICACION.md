# Certificación de usuario final — Fase 32.8 (en curso)

**ME:** r234_certificacion_usuario_final · **Fecha:** 2026-11-17 · **Estado:** paso 1 de 4 completado

Arranca el arnés automatizado de humo post-instalación: `tests/e2e/test_smoke_usuario_final.py`,
que ejerce **solo** los binarios de `dist/bin` como lo haría un usuario final (sin `main.py`
ni imports del compilador).

## Resultado del paso 1 — 7/7

| Chequeo | Qué prueba | Entorno |
|---|---|---|
| `test_binarios_de_usuario_final_presentes` | `synapse.exe`, `opensyn.exe`, `synapse_lsp.exe` en `dist/bin` | — |
| `test_synapse_version_sin_python_ni_gcc` | `synapse --version` → `Synapse Compiler 8.1.0-industrial` | PATH = `dist/bin` + `System32` |
| `test_synapse_check_sin_python_ni_gcc` | `synapse check e2e_hola.syn` → `[Check] validacion exitosa` (rc=0) | PATH = `dist/bin` + `System32` |
| `test_compila_y_ejecuta_synapse` | compila `e2e_hola.syn` y el `.exe` imprime `Hola Mundo` | toolchain + `dist/bin` |
| `test_compila_y_ejecuta_syquex` | compila `examples/syquex/04_resultado.syq` → `10/3 = 3` + error controlado de división por cero | toolchain + `dist/bin` |
| `test_opensyn_cli_version_y_estado_local` | `opensyn --version` = `OpenSyn 1.1.0`; `opensyn status` reporta servidor/modelo y ningún endpoint remoto | PATH = `dist/bin` + `System32` |
| `test_lsp_nativo_responde_initialize` | `synapse_lsp.exe` responde `initialize` (`capabilities`, `synapse-lsp-native 0.3.0`) con framing LSP | — |

Duración del arnés: ~4 min (dos compilaciones nativas completas).

## Hallazgo H-R234-1 (ALTO) — la compilación depende de `gcc` en el PATH

`dist/bin/synapse.exe` emite `gcc ... -o "<salida>"` y espera encontrarlo en el PATH.
Con PATH limpio (sin toolchain) el resultado es:

```
"gcc" no se reconoce como un comando interno o externo...
[Synapse] ERROR: GCC fallo con codigo 1
Error de compilacion
```

Es decir: en una máquina limpia sin MinGW instalado, el usuario puede validar (`check`) pero
**no compilar**. Para certificar "instalación exitosa ... `synapse --version` funciona" en VM
limpia hace falta que el instalador resuelva el toolchain (PATH del instalador o resolución
interna del binario). Asignado a la cola: `docs/plan_maestro_deudas.md` (H-R234-1).

## Pendiente dentro de R234

1. `instaladores/test_instalador_silencioso.py`: instalación desatendida en VM limpia, PATH y `--version`.
2. Cerrar H-R234-1 (resolución del toolchain desde el binario o desde el instalador).
3. Manual 7 §7.3: monitoreo de conexiones salientes durante una inferencia real + permisos mínimos del servidor.
4. Informe final de Fase 30/32.8 con las cuatro cláusulas en CUMPLE.
