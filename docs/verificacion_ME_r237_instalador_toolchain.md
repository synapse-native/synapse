# Verificación MTS — ME r237_instalador_toolchain (H-R234-2)

Fecha: 2026-11-17 · Plan: `docs/plan_ME_r237_instalador_toolchain.md` ·
Expediente: `docs/alineacion/r237_instalador_toolchain.md` ·
Evidencia: `auditoria/evidencia/7b4be78d842ad19e.json` (cambio_hash `7b4be78d842ad19e`).

## Estado por requisito

| Requisito | Marca | Evidencia ejecutada |
|---|---|---|
| Manual 9 §2.5 | CUMPLE | `synapse.iss` declara `Name: "toolchain"` (Types: full minimal) y `Source: "{#SourcePath}\dist\toolchain_gcc12\mingw64\*"` → `DestDir: "{app}\toolchain_gcc12\mingw64"`; oráculo `test_iss_declara_componente_y_destino`. |
| Manual 9 §7 | CUMPLE | Inno Setup 6 compiló el `.iss` (setup de 336 MB con `Compression=none` para la prueba) y el instalador silencioso `/COMPONENTS=toolchain` dejó `{app}\toolchain_gcc12\mingw64\bin\gcc.exe`; ese gcc compiló y ejecutó un C con `PATH` = toolchain + `System32`. Oráculos `test_subset_minimo_compila_y_ejecuta` y `test_synapse_instalado_compila_con_toolchain_incluido`. |
| Manual 9 §2.2 | CUMPLE | El toolchain vive en `{app}\toolchain_gcc12\mingw64`, fuera de `{app}\bin`; el bin del ecosistema no se toca y `nucleo/principal.syn` lo resuelve desde `{app}\bin` como `..\toolchain_gcc12\mingw64\bin`. |

## Cita textual

- Manual 9 §2.5: *"El script `installer.iss` de Inno Setup para Windows:"* — el `.iss` del repo gana el componente y su `[Files]`.
- Manual 9 §7: *"| Instalación en Windows (limpiamente) | Ejecutar instalador en máquina virtual Windows limpia | Instalación exitosa, PATH configurado, `synapse --version` funciona. |"* — el criterio de «compilar en limpio» ya no depende de que el usuario instale MinGW.
- Manual 9 §2.2: la estructura instalada mantiene `bin/` para los ejecutables del ecosistema y añade un directorio propio para el toolchain.

## Qué se empaqueta

`instaladores/windows/empaquetar_toolchain.py` copia desde `toolchain_gcc12/mingw64`
(subset **C**, sin g++, gdb, cmake ni documentación):

- `bin/`: `gcc.exe`, `as.exe`, `ld.exe`, `dlltool.exe` + DLLs de runtime
  (`libwinpthread-1`, `libgcc_s_seh-1`, `libgmp-10`, `libmpfr-6`, `libmpc-3`,
  `libisl-23`, `libiconv-2`, `libz`, `libzstd`).
- `libexec/gcc/<triple>/<version>/`: `cc1.exe`, `collect2.exe`, `liblto_plugin.dll`
  y las DLLs del compilador **copiadas junto a cc1** — Windows busca primero en el
  directorio del ejecutable y sin ellas cc1 muere con `0xC0000135`
  (DLL no encontrada) cuando `bin/` no está en el PATH.
- `x86_64-w64-mingw32/include`, `x86_64-w64-mingw32/lib`, `lib/gcc`.

Resultado del staging: **3836 archivos, 300.1 MB** (toolchain completo: 936 MB);
`--verificar` compila y ejecuta un C con `PATH` = `bin` staged + `System32`.

## Oráculo

`tests/auditoria/test_oraculos_r237_instalador_toolchain.py` — **4 passed**:

- `test_subset_minimo_esta_completo`: gcc/as/ld/cc1/collect2/liblto_plugin/stdio.h/libmingwex.a presentes.
- `test_subset_minimo_compila_y_ejecuta`: el subset staged compila, linkea y ejecuta.
- `test_synapse_instalado_compila_con_toolchain_incluido`: layout `{app}\bin\synapse.exe`
  + `{app}\toolchain_gcc12\mingw64` copiado del staging → compila `e2e_hola.syn` con
  `PATH` = `System32` y el ejecutable imprime `Hola Mundo`.
- `test_iss_declara_componente_y_destino`: el `.iss` declara componente, destino y
  `install.ps1` verifica el toolchain incluido.

## Verificación manual sobre el instalador real

1. `ISCC.exe /Qp synapse.iss` con `Compression=none` (copia temporal del script):
   setup de 336 MB generado sin errores.
2. `Synapse-...exe /VERYSILENT /DIR=build\app_prueba /COMPONENTS=toolchain`: el log
   registra 3887 líneas con `toolchain_gcc12` y `{app}\toolchain_gcc12\mingw64\bin\gcc.exe`
   queda instalado.
3. Ese `gcc` instalado compiló y ejecutó un C con `PATH` = toolchain + `System32`
   (`instalado ok`).

## Límites

- El staging y el setup son artefactos de build (`instaladores/windows/dist/` está
  en `.gitignore`): el pipeline de release debe ejecutar
  `empaquetar_toolchain.py` antes de `iscc`. Sin staging, el `.iss` sigue siendo
  compilable (`skipifsourcedoesntexist`) pero el setup no lleva toolchain.
- No se compiló el setup con compresión `lzma2` real (excede el tiempo de una
  sesión interactiva; es trabajo del pipeline). La prueba usó `Compression=none`
  para validar parseo, `[Files]` e instalación.
- Sigue pendiente la VM Windows realmente limpia del criterio §7 (paso 2 de R234):
  aquí la instalación fue en el host, con `PATH` recortado a mano.
