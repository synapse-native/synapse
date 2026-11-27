# Blockers — Technical Debt Registry

## Status: CLEAN

No actual `TODO`, `XXX`, `FIXME`, `HACK`, `BUG`, or `WORKAROUND` markers exist in
`nucleo/`, `synapse_lsp/`, or `tests/`. The codebase is free of deferred-action
annotations.

## Minor Observations (non-blocking)

### Debug `fprintf(stderr, ...)` in production paths

These do not prevent correct operation but emit noise to stderr at runtime:

| File | Lines | Description |
|------|-------|-------------|
| `nucleo/generador/compilar.syn` | 39–45 | Prints `salida.datos` and `_out_c` after each compilation |
| `nucleo/generador/orquestador.syn` | 82–117 | Prints every function definition visited during generation |
| `nucleo/generator.syn` | 802–837 | (duplicate of orquestador — pre-refactor) |
| `nucleo/lsp.c` | 3758 | Prints lexer token assignment at line 72 |

**Recommended fix:** Either remove the `asm("fprintf(stderr, ...")` calls or wrap them
in `#ifdef DEBUG` / `if (_syn_debug_env)` guards.

## Pre-existing test skips

- `tests/integration/test_end_to_end.py::test_fixture_basico`
- `tests/integration/test_end_to_end.py::test_fixture_estructuras`

Both require full native-compiler pipeline fixtures not yet present in the repo.

---

## Tooling installed

| Tool | File | Purpose |
|------|------|---------|
| CI workflow | `.github/workflows/ci-tests.yml` | 3 jobs: lint-and-check → test (matrix) → bootstrap |
| Pre-commit hooks | `.pre-commit-config.yaml` | Blocks `_fix_*.py`, `.exe.c`, `except: pass`, `.exe` in source tree |
| Python deps | `requirements.txt` | pytest, flake8, vscode-languageclient |

### CI hardening details

The following error-masking patterns were removed from `ci-tests.yml`:
- `pip install -r requirements.txt 2>/dev/null \|\| true` → bare `pip install -r requirements.txt`

New CI checks:
- `lint-and-check` job (runs before `test`): blocks `_fix_*.py`, `.exe.c`, `except: pass`
- `bootstrap` job: compiles `tweetnacl.o` + `axon_rt.o`, runs micro-tests natively
- All jobs fail the pipeline on violation (`exit 1`)
