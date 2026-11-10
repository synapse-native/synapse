# Verificación ME r205 — Grafo de conocimiento real

Plan: `docs/plan_ME_r205_grafo_conocimiento.md`.
Expediente: `docs/alineacion/r205_grafo_conocimiento.md`.
Oráculo: `tests/opensyn/test_grafo_comportamiento.py`.

- Manual 32 §2.1 grafo dirigido desde el AST canónico durante el pipeline — CUMPLE (`nucleo/grafo_conocimiento.syn:112`).
- Manual 32 §2.4 estructuras y seis pasadas del grafo — CUMPLE (`nucleo/grafo_conocimiento.syn:123`).
- Manual 32 §2.5 persistencia JSON y reutilización por hash — CUMPLE (`nucleo/grafo_conocimiento.syn:433`).
- Manual 32 §2.6 determinismo SHA-256 del mismo AST — CUMPLE (`nucleo/grafo_conocimiento.syn:366`).
- Manual 6 §1.1 AST canónico unificado (`NodoSemantico`/`RegistroAST`) — CUMPLE (`nucleo/grafo_conocimiento.syn:189`).
- Manual 2 §5.1 contratos `requiere`/`garantiza` en funciones públicas — CUMPLE (`nucleo/grafo_conocimiento.syn:112`).
- Manual 2 §7.3 AST aplanado y adaptador desde el registro ABI — CUMPLE (`nucleo/grafo_conocimiento.syn:189`).

## Oráculos ejecutados

- `python main.py nucleo/grafo_conocimiento.syn --check --no-emit` → rc 0.
- `pytest tests/opensyn/test_grafo.py tests/opensyn/test_grafo_comportamiento.py -v` → 14 passed.
- `pytest tests/integration/test_compilacion_fase32.py -v` → 2 passed (grafo retirado del baseline).
- `python auditoria/alineacion.py --verificar --me r205_grafo_conocimiento` → sin brechas.
- `python auditoria/contrastar.py --plan docs/plan_ME_r205_grafo_conocimiento.md` → sin brechas.
