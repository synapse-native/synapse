# Plan ME r304 — Contratos en syquex/lexer.syn y syquex/traductor.syn (Bloque 6)

## Metadatos

| Campo | Valor |
|---|---|
| **ME** | r304_syquex_contratos |
| **Prioridad** | P1 — Deuda técnica activa (Bloque 6, syquex/*) |
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
                 (punteros no nulos, índices >= 0, _resultado_ >= 0 o != nulo)
                 a todas las funciones públicas sin contrato de syquex/lexer.syn
                 (23 funciones: str_len, str_eq, str_eq_sq, sq_buffers, sq_reset,
                 sq_total, sq_hay_error, sq_fijar_linea, sq_linea_actual,
                 sq_idioma_actual, sq_decodificar_cadena, sq_push_valor, sq_push,
                 sq_push_punt, sq_error, sq_es_digito, sq_es_letra, sq_es_alnum,
                 sq_keyword_heredado, sq_keyword, sq_detectar_idioma,
                 sq_procesar_indentacion, sq_tokenizar_linea) y de
                 syquex/traductor.syn (18 funciones: trad_hi, trad_s2p,
                 trad_s2h, trad_s2l, trad_meta, trad_arena, trad_arena_usada,
                 tr_lo, tr_hi, tr_len, tr_tipo, tr_lin, tr_col, tr_vi,
                 tr_hizq, tr_hder, tr_herm, tr_extra).
oraculo:     auditoria/verificar_contratos.py
```

### Requisito 2

```
requisito:   Manual 2 §12
texto:       "Todo archivo de producción modificado lleva un comentario
             // cumple Manual X §Y (grep-chequeable)."
implementacion: Añadir // cumple Manual 2 §5.1 a syquex/lexer.syn y
                 syquex/traductor.syn tras las citas de cabecera existentes.
oraculo:     auditoria/verificar_contratos.py
```
