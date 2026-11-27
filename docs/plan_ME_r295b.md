# Plan ME r295b — Contratos reales en std/ restantes (Bloque 2, tanda 2)

## Metadatos

| Campo | Valor |
|---|---|
| **ME** | r295b_contratos_std_resto |
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
                (no verdadero) a todas las funciones públicas de std/ai.syn,
                std/atp_engine.syn, std/dist_orchestrator.syn, std/net.syn,
                std/proof_bridge.syn, std/quantum.syn, std/symbolic_exec.syn,
                std/tensor.syn.
oraculo:     auditoria/verificar_contratos.py
```

### Requisito 2

```
requisito:   Manual 2 §4.1
texto:       "Tipos primitivos canónicos en minúsculas; la coerción entero→decimal
             es implícita en la llamada FFI."
implementacion: Contratar atp_engine y symbolic_exec (Manual 2 §4.1) con
                requiere:/garantiza: de dominio, manteniendo la coerción implícita.
oraculo:     auditoria/verificar_contratos.py
```

### Requisito 3

```
requisito:   Manual 9 §6.1
texto:       "Compilación sin errores: todos los targets compilan sin errores."
implementacion: Contratar quantum.syn manteniendo el ancla Manual 9 §6.1.
oraculo:     auditoria/verificar_contratos.py
```