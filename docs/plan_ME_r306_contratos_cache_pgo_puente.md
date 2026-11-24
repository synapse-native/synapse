# Plan ME r306 — Contratos en nucleo/cache.syn, generator_pgo.syn, puente_ast.syn (Bloque 8)

## Metadatos

| Campo | Valor |
|---|---|
| **ME** | r306_contratos_cache_pgo_puente |
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
                a todas las funciones públicas de nucleo/cache.syn (8),
                nucleo/generator_pgo.syn (14), nucleo/puente_ast.syn (9).
oraculo:     auditoria/verificar_contratos.py
```

### Requisito 2

```
requisito:   Manual 9 §6.2
texto:       "La verificación del bootstrap (diff 0 bytes)."
implementacion: nucleo/cache.syn ya cita Manual 9 §6.2 en el mapa; se asegura
                ancla CUMPLE con evidencia real.
oraculo:     auditoria/verificar_contratos.py
```

### Requisito 3

```
requisito:   Manual 2 §7
texto:       "el arbol de sintaxis abstracta (ast)."
implementacion: nucleo/puente_ast.syn ya cita Manual 2 §7 en el mapa; se asegura
                ancla CUMPLE con evidencia real (§7.2).
oraculo:     auditoria/verificar_contratos.py
```
