# Plan ME r307 — Contratos en nucleo/* restantes (Bloque 9)

## Metadatos

| Campo | Valor |
|---|---|
| **ME** | r307_contratos_nucleo_bloque9 |
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
                a todas las funciones públicas de nucleo/lexer.syn (7),
                nucleo/lexer_keywords.syn (4), nucleo/principal.syn (5),
                nucleo/resolvedor_axon.syn (2), nucleo/lsp.syn (1),
                nucleo/lsp_v3.syn (1), nucleo/analizador_semantico.syn (1),
                nucleo/optimizador_ia.syn (8) — 29 funciones.
oraculo:     auditoria/verificar_contratos.py
```
