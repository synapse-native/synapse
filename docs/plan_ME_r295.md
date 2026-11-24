# Plan ME r295 — Contratos reales en std/ (Bloque 2)

## Metadatos

| Campo | Valor |
|---|---|
| **ME** | r295_contratos_std_avanzado |
| **Prioridad** | P1 — Deuda técnica activa (H-R277-1) |
| **Autor** | Agente (sesión actual, 2026-11-24) |
| **Estado** | En implementación |

---

## Requisitos MTS (bloque canónico)

### Requisito 1

```
requisito:   Manual 2 §5.1
texto:       "Toda función pública debe declarar requiere y garantiza con
             expresiones booleanas que describan precondiciones y poscondiciones
             de dominio."
implementacion: Añadir requiere:/garantiza: con invariantes de dominio reales
                (no verdadero) a todas las funciones públicas de std/modelo.syn,
                std/atp_engine.syn, std/symbolic_exec.syn, std/dist_orchestrator.syn,
                std/proof_bridge.syn, std/quantum.syn, std/quantum_err_corr.syn,
                std/surface_code.syn, std/quantum_memory.syn, std/federated.syn,
                std/tensor.syn, std/ai.syn, std/net.syn, std/simd.syn.
oraculo:     auditoria/verificar_contratos.py
```

### Requisito 2

```
requisito:   Manual 2 §12
texto:       "Los contratos son parte del diseño por contrato obligatorio en
             Synapse; su ausencia en funciones públicas es infracción de primer
             nivel."
implementacion: Todo archivo de producción modificado lleva comentario
                "// cumple Manual 2 §5.1" dentro de las 25 líneas posteriores
                a cada definición de función modificada.
oraculo:     auditoria/verificar_contratos.py
             std/symbolic_exec.syn std/dist_orchestrator.syn std/proof_bridge.syn
             std/quantum.syn std/quantum_err_corr.syn std/surface_code.syn
             std/quantum_memory.syn std/federated.syn std/tensor.syn std/ai.syn
             std/net.syn std/simd.syn → al menos 1 coincidencia por archivo.
```

---

## Archivos de producción modificados

| Archivo | Cambio | Cita MTS |
|---|---|---|
| `std/modelo.syn` | Reemplaza contratos placebo y añade los faltantes | Manual 2 §5.1 |
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
