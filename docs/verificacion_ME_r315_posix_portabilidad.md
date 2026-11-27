# Verificación — ME r315_posix_portabilidad

CUMPLE.

## Requisitos del plan y su verificación

| requisito | verificación | resultado |
|---|---|---|
| Manual 9 §6.2 — CUMPLE — compila en cada target | `pytest tests/auditoria/test_r315_posix_portabilidad.py` | 4 passed |
| Manual 9 §6.2 — CUMPLE — sin redirecciones de cmd.exe | idem | 4 passed |

## Causa y cambio

1. **`_putenv` (MSVC).** El `asm` que antepone el directorio del toolchain al
   `PATH` del hijo emitía `snprintf("PATH=%s;%s")` + `_putenv`, exclusivos de
   Windows. Ahora hay rama `#ifdef _WIN32` (idéntica) y rama `#else` con
   separador `:` y `setenv(3)`.
2. **`_stricmp` (MSVC).** El recorte de la extensión `.syn` comparaba con
   `_stricmp`, inexistente en glibc/macOS. Se reemplazó por una comparación en
   minúsculas en C puro (4 caracteres), sin depender de `<strings.h>`.
3. **`2>nul` (cmd.exe).** `nucleo/cache.syn` (`mkdir -p`/`rm -rf`) y
   `nucleo/principal.syn` (`.axon_cache`, `axon_modules`) redirigían con la
   sintaxis de `cmd.exe`; en POSIX eso crea un archivo llamado `nul` en el cwd.
   Se quitó la redirección (la salida de error ya no se silencia, no afecta el
   resultado de `system`).

Sin esto, `python build.py` del job `Bootstrap compiler (critical path)` moría
con `[!] Error compilando modulo ./_principal.c (rc=1)` y
`[ME-R2][ERROR] No se genero el ejecutable: synapse_bootstrap.exe` en
`ubuntu-latest`, `ubuntu-24.04-arm` y `macos-latest` (run `45174810716`).

## Otros checks

| check | resultado |
|---|---|
| `pytest tests/auditoria/test_r315_posix_portabilidad.py` | 4 passed |
| `build.py --skip-test` (Windows) | S2==S3, sha `31224de52f30` |
| `alineacion.py --verificar --me r315_posix_portabilidad` | OK, evidencia `31b44bc5c1136c5f` |
| `verificar_alineacion.py` | SIN BRECHAS |
| `contrastar.py --plan docs/plan_ME_r315_posix_portabilidad.md` | PASS (2/2) |

## Limitación declarada

La comprobación en Linux/macOS la hace la matriz de CI tras el push: aquí solo
se verificó Windows (build determinista) y que el C emitido contiene ambas ramas
(`setenv` presente en `synapse_unity.c`).
