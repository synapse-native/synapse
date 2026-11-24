# Plan ME r299d — Contratos en nucleo/generador/*.syn (Bloque 5)

## Metadatos

| Campo | Valor |
|---|---|
| **ME** | r299d_contratos_generador_submodulos |
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
                (punteros no nulos, índices >= 0, _resultado_ >= -1) a todas
                las funciones públicas de nucleo/generador/compilar.syn,
                emision_c.syn, escaneo.syn, frontend_nativo.syn, funciones.syn,
                monomorfizacion.syn, nodos_flujo.syn, orquestador.syn,
                recorrido.syn.
oraculo:     auditoria/verificar_contratos.py
```

### Requisito 2

```
requisito:   Manual 9 §6.2
texto:       "Validación cruzada en CI/CD: el bootstrap se verifica con diff 0 bytes."
implementacion: compilar.syn ya cita Manual 9 §6.2 en el mapa; las funciones
                públicas de compilar.syn (1 pendiente) reciben contratos
                requiere:/garantiza: de dominio.
oraculo:     auditoria/verificar_contratos.py
```