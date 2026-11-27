# Verificación MTS — ME r236_toolchain_gcc (H-R234-1)

Fecha: 2026-11-17 · Plan: `docs/plan_ME_r236_toolchain_gcc.md` ·
Expediente: `docs/alineacion/r236_toolchain_gcc.md` ·
Evidencia: `auditoria/evidencia/4871e66aeb5e856c.json` (cambio_hash `4871e66aeb5e856c`).

## Estado por requisito

| Requisito | Marca | Evidencia ejecutada |
|---|---|---|
| Manual 9 §7 | CUMPLE | `dist/bin/synapse.exe` compila `tests/e2e/e2e_hola.syn` con PATH = `System32` (sin `gcc` visible) y el `.exe` imprime `Hola Mundo`. El comando impreso es `gcc -O2 ...` y el PATH del hijo ya incluye el toolchain resuelto. |
| Manual 9 §6.2 | CUMPLE | `tests/auditoria/test_oraculos_r236_toolchain_gcc.py` 3/3: layout del checkout, layout de instalación (`bin\synapse.exe` + `..\toolchain_gcc12` por enlace de directorio) y precedencia de `SYNAPSE_GCC`. |

## Cita textual

- Manual 9 §7: *"Instalación en Windows (limpiamente) … Instalación exitosa, PATH configurado, `synapse --version` funciona"*. La cláusula de funcionamiento sin configuración externa se verificó sobre el binario distribuido.
- Manual 8 §4.2: *"`--debug` | Compila con información de depuración."* — el probe de sanitizadores de `--debug` usa el mismo `gcc` resuelto.
- Manual 8 §4.1: *"`synapse build <archivo>` | Compila el archivo (`.syn` o `.syq`) a binario."* — el comando no cambia, sólo la localización del toolchain.

## Detalle técnico

`nucleo/principal.syn` resuelve el compilador C tras emitir el C y antes de invocar `gcc`:

1. `SYNAPSE_GCC` (entorno) — precedencia explícita.
2. `gcc.exe` junto al binario.
3. `tools\mingw64\bin\gcc.exe` · `mingw64\bin\gcc.exe` (instalador).
4. `..\toolchain_gcc12\mingw64\bin\gcc.exe` (instalador) y `..\..\toolchain_gcc12\mingw64\bin\gcc.exe` (checkout `dist/bin`).
5. `gcc` del PATH (comportamiento histórico, último recurso).

El directorio resuelto se antepone al `PATH` del proceso hijo (una sola vez, sin duplicar), y el comando sigue invocando `gcc` **sin comillas**: citar el primer token junto a `-I"."` hacía que `cmd.exe` no resolviera la ruta (probado y descartado durante el ME). Así `gcc` y sus auxiliares (`as`, `ld`, DLLs de MinGW) se encuentran aunque el usuario no haya configurado nada.

## Oráculo

`tests/auditoria/test_oraculos_r236_toolchain_gcc.py` — 3 passed:

- `test_compila_con_path_sin_gcc`: `dist/bin/synapse.exe` con PATH reducido a `System32` → compila y el binario imprime `Hola Mundo`.
- `test_compila_en_layout_de_instalador`: copia de `synapse.exe` en `<tmp>/bin` + `<tmp>/toolchain_gcc12` (enlace de directorio al toolchain real) → compila igual.
- `test_synapse_gcc_tiene_prioridad`: `SYNAPSE_GCC` con ruta inexistente impide compilar (no cae silenciosamente al toolchain descubierto).

## Límites

- El instalador todavía no empaqueta MinGW (`instaladores/windows/synapse.iss` no lo incluye): en una VM limpia sin toolchain en ninguna de las rutas buscadas, el último recurso sigue siendo el `gcc` del PATH. Empaquetar el toolchain en el setup es el seguimiento de R234 (paso 2).
- El arnés de R234 (`tests/e2e/test_smoke_usuario_final.py`) queda intacto (tests inmutables); su helper `_exigir_gcc` sigue funcionando aunque ahora el binario resuelva el toolchain por sí mismo.
