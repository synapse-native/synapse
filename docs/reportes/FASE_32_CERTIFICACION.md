// Documento informativo; la ley es docs/manuales/
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

### Actualización 2026-11-17 — H-R234-1 cerrado por el ME r236_toolchain_gcc

`synapse.exe` resuelve ahora el toolchain C por sí mismo (`SYNAPSE_GCC`, junto al
binario, `tools\mingw64\bin`, `..\toolchain_gcc12\mingw64\bin`, `..\..\toolchain_gcc12\mingw64\bin`)
y antepone su directorio al PATH del proceso hijo: compilar ya no exige configurar
MinGW. Verificado con PATH reducido a `System32` (`tests/auditoria/test_oraculos_r236_toolchain_gcc.py`
3/3) y con el binario regenerado. Queda como seguimiento H-R234-2 empaquetar el
toolchain en el instalador, para la VM totalmente limpia.

### Actualización 2026-11-17 — H-R234-2 cerrado por el ME r237_instalador_toolchain

El instalador de Windows ya entrega el compilador: el componente `toolchain`
instala `dist\toolchain_gcc12\mingw64` (subset mínimo de 300 MB: gcc, cc1, as,
ld, collect2, headers y libs) en `{app}\toolchain_gcc12\mingw64`, justo donde
`synapse.exe` lo busca. `empaquetar_toolchain.py` prepara y autoverifica ese
subset, y `install.ps1` pasa de pedir MinGW a verificar el toolchain incluido.
Oráculo `tests/auditoria/test_oraculos_r237_instalador_toolchain.py` 4/4; Inno
Setup compiló el `.iss` y una instalación silenciosa `/COMPONENTS=toolchain`
dejó un `gcc` funcional.

## Pendiente dentro de R234

1. `instaladores/test_instalador_silencioso.py`: instalación desatendida en VM limpia, PATH y `--version`.
2. ~~Cerrar H-R234-1 (resolución del toolchain desde el binario o desde el instalador).~~ → **CERRADO** (ME r236).
3. ~~Cerrar H-R234-2 (empaquetar MinGW en el instalador).~~ → **CERRADO** (ME r237). Falta ejecutar el paso 1 (VM limpia) con el setup que ya incluye toolchain.
3. Manual 7 §7.3: monitoreo de conexiones salientes durante una inferencia real + permisos mínimos del servidor.
4. Informe final de Fase 30/32.8 con las cuatro cláusulas en CUMPLE.
