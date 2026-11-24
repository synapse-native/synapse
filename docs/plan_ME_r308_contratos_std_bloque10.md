# Plan ME r308 — Contratos en std/* (Bloque 10)

## Metadatos

| Campo | Valor |
|---|---|
| **ME** | r308_contratos_std_bloque10 |
| **Prioridad** | P1 — Deuda técnica activa (H-R277-1) |
| **Autor** | Agente (sesión actual, 2026-11-24) |
| **Estado** | En implementación |

---

## Requisitos MTS (bloque canónico)

### Requisito 1

```
requisito:   Manual 2 §5.1
texto:       "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
implementacion: Añadir requiere:/garantiza: con invariantes de dominio reales
                a todas las funciones públicas de std/* (44 funcs en 15 archivos).
oraculo:     auditoria/verificar_contratos.py
```
