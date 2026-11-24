# Plan ME r305 — Contratos en nucleo/lifetimes.syn, diagnostics.syn, optimizador_ia.syn (Bloque 7)

## Metadatos

| Campo | Valor |
|---|---|
| **ME** | r305_contratos_lifetimes_diag_opt |
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
                las funciones públicas de nucleo/lifetimes.syn (13),
                nucleo/diagnostics.syn (10), nucleo/optimizador_ia.syn (10).
oraculo:     auditoria/verificar_contratos.py
```

### Requisito 2

```
requisito:   Manual 4 §4
texto:       "referencias débiles y prevención de ciclos."
implementacion: nucleo/lifetimes.syn ya cita Manual 4 §4 en el mapa; se asegura
                ancla CUMPLE con evidencia real.
oraculo:     auditoria/verificar_contratos.py
```
