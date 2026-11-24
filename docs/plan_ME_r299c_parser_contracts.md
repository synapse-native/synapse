# Plan ME r299c — Contratos en nucleo/parser*.syn (Bloque 4)

## Metadatos

| Campo | Valor |
|---|---|
| **ME** | r299c_parser_contracts |
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
                (ParserEst no nulo, índices >= 0, _resultado_ >= -1) a todas
                las funciones públicas de nucleo/parser.syn, parser_base.syn,
                parser_canales.syn, parser_declaraciones.syn, parser_expr.syn,
                parser_sentencias.syn, parser_stmt.syn.
oraculo:     auditoria/verificar_contratos.py
```
