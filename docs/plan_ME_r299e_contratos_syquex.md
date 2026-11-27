# Plan ME r299e — Contratos en syquex/*.syn (Bloque 6)

## Metadatos

| Campo | Valor |
|---|---|
| **ME** | r299e_contratos_syquex |
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
                (punteros no nulos, índices >= 0, _resultado_ >= -1) a todas
                las funciones públicas de syquex/parser.syn, syquex/expr.syn.
oraculo:     auditoria/verificar_contratos.py
```

### Requisito 2

```
requisito:   Manual 3 §3
texto:       "La gramática de Syquex es más expresiva que la de Synapse."
implementacion: syquex/parser.syn y syquex/expr.syn ya citan Manual 3 §3;
                se asegura ancla CUMPLE con evidencia real.
oraculo:     auditoria/verificar_contratos.py
```

### Requisito 3

```
requisito:   Manual 1 §1.1
texto:       "El ecosistema Synapse es una plataforma de desarrollo completa y unificada."
implementacion: syquex/parser.syn ya cita Manual 1 §1.1; se asegura ancla CUMPLE.
oraculo:     auditoria/verificar_contratos.py
```

### Requisito 4

```
requisito:   Manual 1 §5.1
texto:       "nucleo del compilador Synapse."
implementacion: syquex/parser.syn ya cita Manual 1 §5.1; se asegura ancla CUMPLE.
oraculo:     auditoria/verificar_contratos.py
```

