# Plan ME r236 — Resolución del toolchain C por el propio binario (H-R234-1)

**Contexto.** El arnés de certificación de R234 (`tests/e2e/test_smoke_usuario_final.py`)
destapó H-R234-1: `dist/bin/synapse.exe` construye el comando con el literal `gcc` y
delega en el PATH. En una máquina limpia sin MinGW el usuario puede `synapse check`
pero la compilación nativa falla (`"gcc" no se reconoce...` → `ERROR: GCC fallo con
codigo 1`), aunque el toolchain esté junto al binario o en el árbol del proyecto.
El runtime sí se resolvía por cercanía al ejecutable (`GetModuleFileNameA`), pero el
compilador C no.

## Requisitos (MTS)

requisito: Manual 9 §7
texto: "| Instalación en Windows (limpiamente) | Ejecutar instalador en máquina virtual Windows limpia | Instalación exitosa, PATH configurado, `synapse --version` funciona. |"
implementacion: `nucleo/principal.syn` resuelve la ruta del compilador C antes de invocar `gcc`, en este orden: `SYNAPSE_GCC` (entorno) → `gcc.exe` junto al binario → `tools\mingw64\bin\gcc.exe` → `mingw64\bin\gcc.exe` → `..\toolchain_gcc12\mingw64\bin\gcc.exe` (layout del instalador) → `..\..\toolchain_gcc12\mingw64\bin\gcc.exe` (checkout: `dist/bin` → raíz) → `gcc` del PATH como último recurso. La ruta resuelta se usa entrecomillada tanto en el comando de compilación como en el probe de sanitizadores de `--debug`, de modo que la instalación funciona sin configurar el PATH.
oraculo: tests/auditoria/test_oraculos_r236_toolchain_gcc.py

requisito: Manual 9 §6.2
texto: "- La suite de tests completa en cada target."
implementacion: oráculo automatizado que ejecuta `dist/bin/synapse.exe` con un PATH reducido a `System32` (sin ningún `gcc` visible), compila y ejecuta un programa `.syn` en el layout del checkout y repite la prueba en un layout de instalación simulado (`bin\synapse.exe` + `..\toolchain_gcc12\mingw64\bin`), además de `SYNAPSE_GCC` apuntando a un compilador inexistente para verificar el orden de precedencia.
oraculo: tests/auditoria/test_oraculos_r236_toolchain_gcc.py

## Archivos

- `nucleo/principal.syn` — resolución del toolchain (`_gcc_exe`) + uso en comando y probe.
- `tests/auditoria/test_oraculos_r236_toolchain_gcc.py` — oráculo nuevo (PATH sin gcc, layout de repo, layout de instalador, precedencia `SYNAPSE_GCC`).
- `docs/alineacion/r236_toolchain_gcc.md` — expediente MTS.
- `docs/verificacion_ME_r236_toolchain_gcc.md` — verificación CUMPLE/NO CUMPLE.
- `dist/bin/synapse.exe` — regenerado localmente (artefacto, `dist/` gitignored).

## Riesgos

- Si un `gcc.exe` incompleto está junto al binario, se prefiere sobre el del PATH; se documenta y se deja `SYNAPSE_GCC` como escape explícito.
- El instalador todavía no empaqueta MinGW: la resolución desde el binario cubre el checkout y cualquier instalador que coloque el toolchain en las rutas buscadas (seguimiento en R234 paso 2 de empaquetado).
