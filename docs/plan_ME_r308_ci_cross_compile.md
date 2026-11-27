# Plan de Micro-Entregable r308_ci_cross_compile

## Objetivo

El primer push tras el cierre de deudas reveló que `Cross-Compile Synapse`
falla en **19 s, en `Set up job`**, en cada push y PR:

```
##[error]Unable to resolve action actions/setup-clang, repository not found.
##[error]Unable to resolve action dtolnay/setup-rust, repository not found
```

`cross-compile.yml` referencia dos acciones inexistentes. GitHub resuelve las
acciones antes de ejecutar pasos, así que el workflow **nunca** construye el
instalador ni valida la estructura fuente; el job fallback de Ubuntu tampoco
aporta evidencia porque el workflow entero queda en rojo. No hay Rust en el
repositorio (`git ls-files '*.rs'` = 0) y el job es Windows + MinGW, así que
ambos pasos sobraban.

Esto bloquea el camino de **H-R276-2** (evidencia de CI por plataforma).

## Requisito 1 — pipeline de CI/CD ejecutable

requisito: Manual 9 §6.2
texto: "El pipeline de CI/CD ejecuta automáticamente:"
implementacion: se eliminan de `.github/workflows/cross-compile.yml` los pasos `dtolnay/setup-rust@v1` y `actions/setup-clang@v4` (acciones inexistentes), dejando el build Windows/MinGW que sí corresponde; el paso retirado queda documentado con la cita `# cumple Manual 9 §6.2`.
oraculo: tests/auditoria/test_r308_workflows_acciones_validas.py

## Evidencia

| check | resultado |
|---|---|
| `pytest tests/auditoria/test_r308_workflows_acciones_validas.py` | 3 passed |
| `gh run list` tras el push | workflow ejecutable (evidencia de plataformas en H-R276-2) |
| `verificar_alineacion.py` | 0 brechas |
| `contrastar.py --plan docs/plan_ME_r308_ci_cross_compile.md` | PASS (1/1) |
