# Plan ME r294 — Contratos en std/ (Bloque 1)

## Metadatos

| Campo | Valor |
|---|---|
| **ME** | r294_contratos_std_base |
| **Prioridad** | P1 — Deuda técnica activa (H-R277-1) |
| **Autor** | Agente (sesión actual, 2026-11-24) |
| **Estado** | En implementación |

---

## Requisitos (MTS)

```markdown
### Requisito 1

```text
requisito: Manual 2 §5.1
texto: Toda función pública debe declarar requiere y garantiza con expresiones booleanas que describan precondiciones y poscondiciones de dominio.
implementacion: Añadir requires:/garantiza: con invariantes de dominio reales a todas las funciones públicas de std/*.syn.
oraculo: auditoria/verificar_contratos.py
```
```

---

## Archivos de producción modificados

| Archivo | Cambio | Cita MTS |
|---|---|---|
| `std/modelo.syn` | Reemplazar contratos placebo y añadir los faltantes | Manual 2 §5.1 |
| `std/atp_engine.syn` | Idem | Manual 2 §5.1 |
| `std/symbolic_exec.syn` | Idem | Manual 2 §5.1 |
| `std/dist_orchestrator.syn` | Idem | Manual 2 §5.1 |
| `std/proof_bridge.syn` | Idem | Manual 2 §5.1 |
| `std/quantum.syn` | Idem | Manual 2 §5.1 |
| `std/quantum_err_corr.syn` | Idem | Manual 2 §5.1 |
| `std/surface_code.syn` | Idem | Manual 2 §5.1 |
| `std/quantum_memory.syn` | Idem | Manual 2 §5.1 |
| `std/federated.syn` | Idem | Manual 2 §5.1 |
| `std/tensor.syn` | Idem | Manual 2 §5.1 |
| `std/ai.syn` | Idem | Manual 2 §5.1 |
| `std/net.syn` | Idem | Manual 2 §5.1 |
| `std/simd.syn` | Idem | Manual 2 §5.1 |

---

## Brechas / Notas

- Se crearon claves Ed25519 (`release_keys/private.pem`, `public.pem`) y se firmó `synapse.exe` (signature `84ebeecd7e941c0...`).
- Build completado: `synapse_stage2.exe` (2137526 B), `synapse_stage3.exe`, `main.exe`.
- Bitácora de alineación para r294 verificada sin brechas (`alineacion.py --leer --me r294`, `--nuevo --me r294`, `--verificar --me r294`).
- Contrastar pendiente: `python auditoria/contrastar.py --plan docs/plan_ME_r294.md`.
