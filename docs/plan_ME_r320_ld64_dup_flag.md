# Plan de Micro-Entregable r320_ld64_dup_flag

## Objetivo

Sexta vuelta sobre `Release Matrix` (run `45213218955`, job `137827294530`).
macOS ya compila el runtime y los módulos, pero el **link** muere:

```
ld: unknown options: --allow-multiple-definition
collect2: error: ld returned 1 exit status
[!] Link modular fallo (rc=1) — intentando unity fallback
ld: unknown options: --allow-multiple-definition
```

`--allow-multiple-definition` es de GNU ld. El linker de Apple no lo conoce y,
al repetirse en el unity fallback, tampoco hay segunda oportunidad. El flag
existe porque la compilación modular emite helpers duplicados entre módulos
(`desde_texto` en `_json.c` y `_toml.c`, `contiene` en `_texto.c`/`_reports.c`),
confirmado localmente al quitarlo.

Linux x64/ARM64 y Windows siguen fallando solo en la firma Ed25519 (H-R276-2).

## Requisito 1 — macOS enlaza el bootstrap

requisito: Manual 9 §6.2
texto: "La suite de tests completa en cada target."
implementacion: `pipeline.py` calcula `_ld_dup_flag` vacío en darwin y mantiene `-Wl,--allow-multiple-definition` fuera de darwin; en darwin limpia `_module_asts` para enlazar en unity (sin definiciones duplicadas); el enlace de caché (`link_align`) usa el mismo criterio; `nucleo/principal.syn` usa `_dup_flag`, vacío bajo `#ifdef __APPLE__`.
oraculo: tests/auditoria/test_r320_ld64_dup_flag.py

## Requisito 2 — Windows sigue byte-determinista

requisito: Manual 9 §6.2
texto: "La suite de tests completa en cada target."
implementacion: en win32 `_dup_flag` conserva el flag GNU y el enlace sigue pasando `-lws2_32`; `build.py --skip-test` mantiene `S2==S3`.
oraculo: tests/auditoria/test_r320_ld64_dup_flag.py

## Evidencia

| check | resultado |
|---|---|
| `pytest tests/auditoria/test_r320_ld64_dup_flag.py` | 4 passed |
| `build.py --skip-test` (Windows) + `S2==S3` | OK, sha `8e9e60f83c39` |
| `alineacion.py --verificar --me r320_ld64_dup_flag` | OK (`805b73291a740ffd`) |
| `contrastar.py --plan docs/plan_ME_r320_ld64_dup_flag.md` | PASS |
| CI `Release Matrix` macOS tras el push | pendiente de corrida |
