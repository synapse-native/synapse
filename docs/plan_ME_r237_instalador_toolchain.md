# Plan ME r237 — toolchain MinGW empaquetado en el instalador (H-R234-2)

## Contexto

`r236_toolchain_gcc` hizo que `synapse.exe` resuelva el compilador C por sí mismo
(`SYNAPSE_GCC` → junto al binario → `tools\mingw64\bin` → `mingw64\bin` →
`..\toolchain_gcc12\mingw64\bin` → `..\..\toolchain_gcc12\mingw64\bin` → PATH).
Falta que ese `..\toolchain_gcc12\mingw64` exista en la máquina del usuario: el
instalador sólo copia `scripts/install.ps1`, que se limita a comprobar el `gcc`
del PATH y avisar (H-R234-2).

## Requisitos

requisito: Manual 9 §2.5 — el instalador declara componentes y sus `[Files]`
texto: "Name: \"tools\"; Description: \"Herramientas nativas (lint, fmt, test)\"; Types: full minimal; Flags: fixed"
implementacion: `instaladores/windows/synapse.iss` gana el componente `toolchain` (Types: full minimal) y una entrada `[Files]` que copia `dist\toolchain_gcc12\mingw64\*` a `{app}\toolchain_gcc12\mingw64` con `recursesubdirs createallsubdirs`, exactamente el directorio que el resolver de `nucleo/principal.syn` busca desde `{app}\bin` (`..\toolchain_gcc12\mingw64\bin`).
oraculo: tests/auditoria/test_oraculos_r237_instalador_toolchain.py

requisito: Manual 9 §7 — instalación en Windows limpia
texto: "Instalación en Windows (limpiamente) | Ejecutar instalador en máquina virtual Windows limpia | Instalación exitosa, PATH configurado, `synapse --version` funciona."
implementacion: `instaladores/windows/empaquetar_toolchain.py` prepara el subset mínimo de MinGW (`gcc.exe`, `cc1.exe`, `as.exe`, `ld.exe`, `collect2.exe`, DLLs de runtime, headers y libs de `x86_64-w64-mingw32`, `lib/gcc/.../libgcc.a`) en `instaladores/windows/dist/toolchain_gcc12/mingw64`, y `install.ps1` verifica el toolchain incluido (`gcc --version` sobre `{app}\toolchain_gcc12\mingw64\bin\gcc.exe`) en lugar de pedirle MinGW al usuario.
oraculo: tests/auditoria/test_oraculos_r237_instalador_toolchain.py

requisito: Manual 9 §2.2 — estructura del instalador
texto: "├── bin/\n│   ├── synapse (o synapse.exe)"
implementacion: el toolchain se instala en `{app}\toolchain_gcc12\mingw64\...` (fuera de `bin/`, sin pisar los artefactos del ecosistema); `{app}\bin` sigue conteniendo sólo `synapse.exe`, `opensyn.exe`, `synapse_lsp.exe` y sus fuentes de enlace.
oraculo: tests/auditoria/test_oraculos_r237_instalador_toolchain.py

## Cambios

1. `instaladores/windows/empaquetar_toolchain.py` (nuevo): copia el subset mínimo
   desde `toolchain_gcc12/mingw64` a `instaladores/windows/dist/toolchain_gcc12/mingw64`,
   con `--origen`, `--destino`, `--verificar` (compila `hola.c` con `PATH=System32`
   usando sólo lo staged) y `--limpiar`. Imprime nº de archivos y MB.
2. `instaladores/windows/synapse.iss`: componente `toolchain` + `[Files]` del
   directorio staged (`skipifsourcedoesntexist` para que el `.iss` siga siendo
   compilable sin staging) y comentario del handshake con `nucleo/principal.syn`.
3. `instaladores/windows/scripts/install.ps1`: verifica el toolchain incluido y
   sólo avisa del camino manual si no está.
4. `.gitignore`: `instaladores/windows/dist/` (el staging es un artefacto de build).
5. `tests/auditoria/test_oraculos_r237_instalador_toolchain.py` (nuevo).

## Límites

- El subset mínimo cubre C (lo que `synapse` usa); no incluye `g++`, `gdb`,
  `cmake` ni documentación de MinGW, que el compilador no necesita.
- El staging no se commitea: lo genera el pipeline de release antes de `iscc`.
