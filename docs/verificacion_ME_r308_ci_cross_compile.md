# Verificación — ME r308_ci_cross_compile

CUMPLE.

## Requisito del plan y su verificación

| requisito | verificación | resultado |
|---|---|---|
| Manual 9 §6.2 — CUMPLE — pipeline de CI/CD ejecutable | `pytest tests/auditoria/test_r308_workflows_acciones_validas.py` | 3 passed |

## Causa y cambio

`Cross-Compile Synapse` fallaba en 19 s **en `Set up job`** en cada push/PR:

```
##[error]Unable to resolve action actions/setup-clang, repository not found.
##[error]Unable to resolve action dtolnay/setup-rust, repository not found
```

GitHub resuelve las acciones antes de ejecutar pasos: el workflow no construía
nada. Se retiraron ambos pasos de `.github/workflows/cross-compile.yml`:

- `dtolnay/setup-rust@v1`: el repositorio no tiene Rust (`git ls-files '*.rs'`
  = 0).
- `actions/setup-clang@v4`: no existe; el job es Windows + MinGW y el
  toolchain ARM ya viene por la matriz de `release_matrix.yml`.

Queda documentado con `# cumple Manual 9 §6.2` en el propio workflow.

## Otros checks

| check | resultado |
|---|---|
| `pytest tests/auditoria/test_r308_workflows_acciones_validas.py` | 3 passed |
| acciones usadas | checkout@v4, setup-python@v5, upload-artifact@v4, setup-mingw@v2, action-gh-release@v1 |
| `verificar_alineacion.py` | 0 brechas |
| `contrastar.py --plan docs/plan_ME_r308_ci_cross_compile.md` | PASS (1/1) |

La corrida verde del workflow se valida en el push siguiente; su evidencia por
plataforma corresponde a **H-R276-2**, no al cierre de este ME.
