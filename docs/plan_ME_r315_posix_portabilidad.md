# Plan de Micro-Entregable r315_posix_portabilidad

## Objetivo

`Release Matrix` falla en las tres filas no-Windows (run `45174810716`),
concretamente en `python build.py`:

```
./_principal.c:1381:17: error: implicit declaration of function '_putenv'; did you mean 'putenv'?
./_principal.c:1799:51: error: implicit declaration of function '_stricmp'; did you mean 'strncmp'?
[!] Error compilando modulo ./_principal.c (rc=1)
[ME-R2][ERROR] No se genero el ejecutable: synapse_bootstrap.exe
```

El `asm(...)` de `nucleo/principal.syn` emite C con nombres MSVC
(`_putenv`, `_stricmp`) que no existen en glibc ni en macOS, y `nucleo/cache.syn`
usa la redirección de `cmd.exe` (`2>nul`) en comandos que en POSIX crean un
archivo llamado `nul` en el cwd del bootstrap.

## Requisito 1 — el código emitido compila en todos los targets

requisito: Manual 9 §6.2
texto: "La suite de tests completa en cada target."
implementacion: en `nucleo/principal.syn`, el ajuste del `PATH` del hijo (`;` + `_putenv`) pasa a dos ramas `#ifdef _WIN32` / `#else` con `:` + `setenv`, y el recorte de la extensión `.syn` deja de usar `_stricmp` (comparación en minúsculas en C, sin `<strings.h>`).
oraculo: tests/auditoria/test_r315_posix_portabilidad.py

## Requisito 2 — sin redirecciones exclusivas de cmd.exe

requisito: Manual 9 §6.2
texto: "La verificación del bootstrap (diff 0 bytes)."
implementacion: `nucleo/cache.syn` (`mkdir -p`/`rm -rf`) y `nucleo/principal.syn` (`.axon_cache`/`axon_modules`) dejan de emitir `2>nul`; el bootstrap así no crea archivos `nul` en POSIX y no depende del shell de Windows.
oraculo: tests/auditoria/test_r315_posix_portabilidad.py

## Mapa de alineación

`nucleo/cache.syn` caía al mapa legacy y el gate lo reportaba como `Manual 2 §`,
sección inexistente. Se agrega `"nucleo/cache.syn": ["Manual 9 §6.2"]`.

## Evidencia

| check | resultado |
|---|---|
| `pytest tests/auditoria/test_r315_posix_portabilidad.py` | 4 passed |
| `build.py --skip-test` (Windows) + `S2==S3` | OK, sha `31224de52f30` |
| `alineacion.py --verificar --me r315_posix_portabilidad` | OK (`31b44bc5c1136c5f`) |
| `contrastar.py --plan docs/plan_ME_r315_posix_portabilidad.md` | PASS (2/2) |
| CI `Release Matrix` en Linux x64/ARM64 y macOS tras el push | pendiente de corrida |
