# Verificación ME r203 — `synapse update` nativo

Plan: `docs/plan_ME_r203_update_nativo.md`
Expediente: `docs/alineacion/r203_update_nativo.md`
Oráculo principal: `tests/integration/test_update_nativo.py` (10 passed)

## Cumplimiento (MTS)

CUMPLE Manual 9 §3.1 "Sin argumentos: actualiza a la última versión disponible."
evidencia: nucleo/actualizador.syn:351
oraculo: tests/integration/test_update_nativo.py::test_update_check_detecta_release_nuevo

CUMPLE Manual 9 §3.1 "`--version <version>`: actualiza a una versión específica."
evidencia: nucleo/actualizador.syn:346
oraculo: tests/integration/test_update_nativo.py::test_update_version_especifica

CUMPLE Manual 9 §3.1 "`--check`: solo verifica si hay actualizaciones disponibles, sin instalarlas."
evidencia: nucleo/actualizador.syn:363
oraculo: tests/integration/test_update_nativo.py::test_update_check_detecta_release_nuevo

CUMPLE Manual 9 §3.2 "1. **Verificación de versión**: Consulta el endpoint de versiones en GitHub Releases (o Axon Hub)."
evidencia: nucleo/actualizador.syn:329
oraculo: tests/integration/test_update_nativo.py::test_update_version_invalida

CUMPLE Manual 9 §3.2 "2. **Descarga de la nueva versión**: Descarga el instalador o los binarios actualizados."
evidencia: nucleo/actualizador.syn:242
oraculo: tests/integration/test_update_nativo.py::test_update_pipeline_completo_instala_con_backup

CUMPLE Manual 9 §3.2 "3. **Verificación de firma**: Comprueba la firma Ed25519 del artefacto."
evidencia: runtime/core/actualizador.c:156
oraculo: tests/integration/test_update_nativo.py::test_update_firma_invalida_no_instala

CUMPLE Manual 9 §3.2 "4. **Backup de la versión anterior**: Guarda la versión actual en `~/.synapse/backup/`."
evidencia: runtime/core/actualizador.c:246
oraculo: tests/integration/test_update_nativo.py::test_update_pipeline_completo_instala_con_backup

CUMPLE Manual 9 §3.2 "5. **Instalación de la nueva versión**: Reemplaza los binarios y archivos."
evidencia: runtime/core/actualizador.c:340
oraculo: tests/integration/test_update_nativo.py::test_update_pipeline_completo_instala_con_backup

CUMPLE Manual 9 §4.1 "Archivos de firma (`.sig`) y checksums (`.sha256`)."
evidencia: nucleo/actualizador.syn:343
oraculo: tests/integration/test_update_nativo.py::test_update_falla_cerrado_sin_firma_publicada

CUMPLE Manual 2 §5.1 "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
evidencia: nucleo/actualizador.syn:317
oraculo: tests/integration/test_contracts.py

## Notas de implementación

- ABI: los helpers C devuelven `int64_t` (no `int`) para no truncar `-1` a `4294967295` en Synapse (`entero` = 64 bits). `runtime/core/actualizador.h:20,26,31,35,39`.
- Quoting Windows: `_syn_actualizador_ejecutar()` (`runtime/core/actualizador.c:99`) usa `cmd /S /C` cuando el comando empieza por comilla, evitando el error 123 de `cmd`.
- Clave de firma: canónica embebida; `SYNAPSE_PUBLIC_KEY` (hex 64) permite espejos/rotación y que el test use un par efímero sin la clave privada del proyecto.
- Fallo cerrado: checksum o firma inválidos eliminan el artefacto y retornan 1 sin ejecutar backup/instalador.
- `--check` nunca descarga el asset ni instala: solo consulta el release y reporta.

## Evidencia ejecutada

- `tests/integration/test_update_nativo.py -v` → 10 passed.
- `tests/integration/test_cli.py tests/integration/test_contracts.py tests/integration/test_release_matrix.py -q` → 33 passed.
