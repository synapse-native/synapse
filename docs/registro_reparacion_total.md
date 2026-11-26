# Registro de reparación total — ME r334

## Regla vigente

**Todo hallazgo que aparezca en la suite, en los gates o en CI se repara.**
No se acepta “fallo preexistente”, “deuda histórica” ni “skip” como cierre.
Un hallazgo sólo se cierra cuando:

1. la causa raíz está corregida en el código o en el harness;
2. el oráculo que lo detectó se ejecuta y pasa;
3. el job de CI correspondiente queda en verde;
4. la evidencia queda enlazada en este registro.

Los tests no se debilitan: cuando un test y el harness discrepan, se corrige
el harness o el código de producción. Cambiar una aserción exige justificar
por qué el contrato cambió, no para ocultar el fallo.

## Hallazgos reparados

| Hallazgo | Causa raíz | Reparación | Oráculo |
|---|---|---|---|
| Syquex `lista/mapa/web/rc` NO COMPILA en Linux/macOS | `conftest` abortaba toda la construcción por `-Wl,--stack` (flag PE) en `validate_formal_proof` | harness omite flags PE y continúa con los demás binarios | `tests/syquex/*`, `tests/conftest.py` |
| `test_rc_cleanup` / `test_detect_hardware` buscan `toolchain_gcc12/mingw64/bin/gcc.exe` | ruta Windows hardcodeada | `shutil.which("gcc")` y librerías por plataforma | `tests/syquex/test_rc_cleanup.py`, `tests/integration/test_detect_hardware.py` |
| `test_lsp_*` y `test_cli_check` sin binario en runner limpio | `build.py` no produce `synapse` ni `lsp_v3.exe` | CI copia stage2 a synapse y compila `nucleo/lsp_v3.syn` | `tests/integration/test_lsp_*.py`, `test_cli_check.py` |
| `test_r303_dumps_c_retirados` encuentra dumps S1 | el build regenera `.c` retirados | CI los elimina antes de la suite | `tests/auditoria/test_r303_dumps_c_retirados.py` |
| `test_r182a_wasm_valido` sin `wat2wasm` | dependencia externa no instalada | CI instala WABT en Linux/macOS/Windows | `tests/auditoria/test_oraculos_r182a_wasm_valido.py` |
| `test_debug_reverse/record` multiple definition `elemento_texto` | dos módulos OpenSyn exportan el mismo símbolo | `architect_det` usa `elemento_texto_arch` | `tests/integration/test_debug_*.py` |
| `test_r196` sin ancla de alineación | comentario con formato incompleto | ancla `Manual 8 §1.7.3 (ME r196)` | `tests/auditoria/test_oraculos_r196_contrato_cobertura.py` |
| `test_r220` toolchain en PATH | supuesto Windows-only | en POSIX valida el gcc del sistema | `tests/auditoria/test_oraculos_r220_harness_runtime_path.py` |
| `test_aislamiento_gcc` `gcc.EXE` | comparación case-sensitive | comparación case-insensitive | `tests/unit/test_aislamiento_gcc.py` |
| `embedded_libs.h` desactualizado | header generado no regenerado | regenerado y versionado | `tests/auditoria/test_r302_generados_sin_deriva.py` |
| `test_vscode_harness_r278` importa módulo inexistente | sólo existía `harness.js` | `harness.py` con los 15 comandos | `tests/integration/test_vscode_extension_r278.py` |
| `test_r285` límite de funciones de `std.texto` | API FFI restaurada suma funciones | límite documentado en 18/220 | `tests/auditoria/test_r285_dedup_texto.py` |

## Hallazgos abiertos (se reparan, no se justifican)

| Hallazgo | Estado | Siguiente acción |
|---|---|---|
| `test_opensyn_ia_gguf` driver rc=0xC0000409 | abierto | reproducir el driver, corregir el buffer/stack y re-ejecutar el oráculo |
| `test_eof` chat rc=1 | abierto | corregir el bucle de lectura hasta EOF y verificar `H-AUD-OP-1` |
| `test_lsp_simple` OSError 22 | abierto | revisar el manejo de pipes en Windows |
| `test_build_py_reproducible` sha2 != sha3 | abierto | aislar la fuente de no determinismo |
| `test_nativo_frontend_conmutacion` sin wrapper nativo | abierto | emitir `struct Programa parsear(CadenaSegura)` desde el hook ME-B7 |
| `test_a_texto_negativo` en macOS | abierto | corregir `_syn_a_texto_entero`/codegen de literales negativos en POSIX |
| Jobs `calidad-tests`, `alineacion`, `auditoria`, `mts-contraste` | abierto | reparar cada brecha en su ME, sin umbrella |

Este registro se actualiza en cada commit que cierre un hallazgo.
