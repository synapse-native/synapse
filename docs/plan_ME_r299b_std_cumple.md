# Plan ME r299b — Contratos cumple/garantiza en std/ (hardening)

## Metadatos

| Campo | Valor |
|---|---|
| **ME** | r299b_std_cumple |
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
implementacion: Añadir ancla `// cumple Manual 2 §5.1` y garantiza: de dominio
                a las funciones públicas de std/cripto.syn, std/debug.syn,
                std/json.syn, std/math.syn, std/mem.syn, std/oraculo.syn,
                std/sistema.syn, std/texto.syn, std/tiempo.syn, std/toml.syn.
oraculo:     auditoria/verificar_contratos.py
```
