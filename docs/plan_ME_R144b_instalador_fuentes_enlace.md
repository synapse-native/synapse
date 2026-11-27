# Plan ME-R144b: instalador distribuye fuentes y headers de enlace del compilador nativo

Contexto: test de instalación como usuario real (R144). El `synapse.exe`
instalado no puede compilar programas de usuario: el enlazador nativo
(ME-R5, `_rt_dir` = dir del exe en `nucleo/principal.syn`) invoca GCC con
fuentes relativas al exe que el instalador no distribuye. Primer bloque
corregido y verificado en `D:\SynapseTest\bin` (synapse_rt.c/.h, axon/,
vendor/, nucleo/federated.*). Este plan cubre el bloque restante detectado
en el humo post-fix: `runtime/core/*.c` incluye `librerias/embedded_libs.h`,
resuelto por `-I<_rt_dir>` (principal.syn:664), y `librerias/` solo se
distribuye al componente syquex en `{app}/lib`.

requisito: Manual 9 §2.5
texto: "Name: \"synapse\"; Description: \"Synapse (compilador, runtime, std)\"; Types: full minimal; Flags: fixed"
implementacion: el componente synapse debe ser autosuficiente. Añadir a
instaladores/windows/synapse.iss [Files]: Source librerias\* → DestDir
{app}\bin\librerias, Components: synapse, recursesubdirs (embedded_libs.h
+ librerias/compiler/*.syn usados por el pipeline instalado). Comentario
grep-chequeable "; cumple Manual 9 §2.5" en la línea añadida.
oraculo: tests/validate_installer.py

requisito: Manual 9 §2.5
texto: "Source: \"runtime\\*\"; DestDir: \"{app}\\runtime\"; Components: synapse"
implementacion: ya aplicado en el primer bloque del fix (synapse_rt.c/.h,
axon\tweetnacl.*, vendor\sqlite3\*, nucleo\federated.* hacia {app}\bin y
subdirectorios hermanos del exe); este plan no lo modifica, lo documenta
como parte del mismo requisito para el gate contrastar.
oraculo: tests/validate_installer.py

Bloque 3 (hallado en humo v3): runtime/core/{fuzz,memory}.c incluyen
synapse_rt_memory.h (raíz del proyecto, hermana de synapse_rt.h que ya se
distribuye). Misma regla §2.5: añadir Source synapse_rt_memory.h →
{app}\bin, Components: synapse.

Bloque 4 (hallazgos R144: fallo de descarga de modelo + SHA256 en máquina real):
- MODEL_SHA256_* eran el placeholder literal "TODO_ACTUALIZAR_AL_COMPILAR":
  toda descarga de modelo fallaba la verificación (§5.3: "si hash != info.sha256:
  retornar err("Checksum incorrecto")"). Reemplazados por los SHA256 reales
  (LFS oid de HuggingFace, igual a SHA256 del contenido).
- LLAMA_SERVER_SHA256 contenía el hash del ZIP (lo calculaba
  scripts/update_hashes.ps1 sobre el zip) pero el instalador verifica el EXE
  EXTRAÍDO → mismatch garantizado, abortaba antes de descargar el modelo.
  Corregido al hash del llama-server.exe extraído de b10819 (launcher 9216 B
  + llama-server-impl.dll).
- MODEL_URL_1B apuntaba a repo inexistente (TheBloke/deepseek-coder-1.3B-GGUF,
  401): el repo real es deepseek-coder-1.3b-instruct-GGUF (minúscula b).
  En modo silencioso sin Ollama se elige siempre el 1B (VRAM=-1 no detectada
  en VM) → este era el camino del fallo "no está descargando el modelo".
- DownloadFile sin curl --fail guardaba páginas de error HTTP (504/404) como
  artefacto con exit 0 (reproducido: zip de 92 B con "504 Gateway Time-out").
  Añadido --fail --connect-timeout 30.

Bloque 5 (hallado en verificación E2E v5c, 2026-09-07 12:55): el ZIP de
llama.cpp b10819 trae launcher (llama-server.exe, 9216 B) + llama-server-impl.dll
+ ggml*.dll + libomp.dll, pero ExtractLlamaServerFromZip copiaba SOLO el exe a
ia\ y borraba el temporal → el launcher instalado no puede cargar sus DLLs
(no arranca el motor IA local). Misma regla §5.3 (componentes IA funcionales):
cambiar FileCopy(exe) por DirCopy(TempDir, ia\) completo + verificación de que
DestPath existe tras la copia.

Verificación posterior: reinstalar silencioso en D:\SynapseTest, compilar
humo con el toolchain instalado desde cwd neutral, ejecutar el exe
resultante, y correr oráculos + verificar_alineacion + contrastar.
