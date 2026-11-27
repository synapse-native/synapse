# BRANCH PROTECTION — Cierre del bypass por push directo (H3)

## Problema

Todos los gates locales se pueden saltar con `--no-verify`, y el CI solo
bloquea en `pull_request` → `main`. Un push directo a `main` o `release/*`
integra código sin que NINGÚN gate corra de forma bloqueante sobre él.
`CODEOWNERS` existe pero es consultivo sin branch protection con revisión
requerida.

## Configuración requerida (GitHub → Settings → Branches → Add rule)

Aplicar a `main` y a `release/**`:

| Regla | Valor |
|-------|-------|
| Require a pull request before merging | ✅ (o, mínimo, los checks de abajo como requeridos) |
| Require review from Code Owners | ✅ (usa `.github/CODEOWNERS`: auditoria/, workflows/, tests/, manuales/) |
| Require status checks to pass | ✅ |
| Checks requeridos | `lint-and-check`, `test` (matriz), `fuzz`, `bootstrap`, `calidad-tests`, `trazabilidad-codigo`, `lectura-previa`, `auditoria`, `mts-contraste`, `alineacion` |
| Require branches to be up to date | ✅ |
| Do not allow bypassing the settings | ✅ (incluye administradores) |
| Restrict force pushes / deletions | ✅ |

## Aplicación automatizada

`scripts/enable_branch_protection.ps1` ya existe en el repo; verificar que:
1. Usa `X-GitHub-Api-Version: 2022-11-28` (error 400 si no — MEMORIA §2.3).
2. Declara TODOS los checks de la tabla como `required_status_checks.context`.
3. Incluye `"enforce_admins": true` — sin esto, el bypass de administrador
   reabre el hueco H3.

## Cadena resultante (defensa en profundidad)

```
commit local      → pre-commit (6 gates; saltar sólo con --no-verify)
push / PR         → CI bloqueante: test + fuzz + sanitizers + 6 gates de gobernanza
merge             → branch protection: checks requeridos + CODEOWNERS + admins incluidos
```

Con las tres capas activas no existe vía de integración sin verificación:
`--no-verify` lo cubre el CI, y el push directo lo cubre el branch protection.
