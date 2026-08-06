# REPORTE FASE A — ETAPA A2.0: VALIDACIÓN DE BASELINE Y PREPARACIÓN DEL ENTORNO

> Micro-entregable A2.0 de la FASE A (plan aprobado: `docs/FASE_A_PLAN.md`; Etapa A1 completada
> en `docs/reportes/FASE_A_A1.md`).
> Fuente de verdad: `GUIA_DE_GOBERNANZA.md` §PROTOCOLO DE ENTREGA, `docs/AUDITORIA_ALINEACION_MANUALES.md`
> (reglas 1-11; FASE A en curso — Etapa A2), `docs/manuales/MANUAL 9.md` §9.7 (determinismo bootstrap),
> `docs/manuales/MANUAL 2.md` §2 (gramática objetivo del port).
> Fecha: 2026-08-05. Criterio A2.0 (definido por el Arquitecto): *bootstrap-full diff 0 bytes S2 vs S3
> con el working tree actual; tests del frontend embebido verdes; espejo `_G_fp*` sincronizado*.

---

## REPORTE DE MICRO-ENTREGABLE

```
--- REPORTE DE MICRO-ENTREGABLE ---
TAREA: FASE A - Etapa A2.0 — Validación de baseline y preparación del entorno para la
       Etapa A2 (port del frontend embebido _P_* al frontend nativo nucleo/lexer.syn +
       nucleo/parser*.syn). Se verifica que el punto de partida es estable: bootstrap
       S1->S2->S3 con diff 0 bytes (Manual 9 §9.7), tests del frontend embebido verdes
       y espejo _G_fp* sincronizado, con el working tree actual (incluye el ensayo A5.1
       del D-7 SIN commitear, decisión del Arquitecto: se integra formalmente en A5).
FASE: FASE A (migración frontend embebido -> frontend nativo) - Etapa A2.0.
MANUAL REFERENCIADO: Manual 9, Seccion 9.7 (determinismo: bootstrap de 3 etapas con
       diff 0 bytes entre Stage 2 y Stage 3 — evidencia L123/L450/L475); Manual 2,
       Seccion 2 (gramatica EBNF completa L36-200: declaracion_tipo L74, delegar L132,
       declaracion_variable L134 — objetivo del port A2.1-A2.4).
HASH COMMIT: pendiente (sin commit en esta etapa: es validación de baseline; los cambios
       A5.1 del D-7 permanecen en el working tree sin commitear por decisión del Arquitecto).
COMPILACION: build.sh bootstrap-full S1->S2->S3:
       - Etapa 1: python main.py nucleo/principal.syn -> synapse_stage1.exe OK
       - Etapa 2: synapse_stage1.exe -> synapse_stage2.exe OK (1262664 bytes)
       - Etapa 3: synapse_stage2.exe -> synapse_stage3.exe OK (1262664 bytes)
       - Verificacion: SHA256 S2 == S3 == 585799d3164eb9bf83f60b9c9525df5a6f42bedb4e1f1b785ab11febf2ef6b59
         => diff 0 bytes (BOOTSTRAP VERIFIED)
TESTS: tests/test_frontend_embebido_d_f1.py + test_codegen_embebido_d_f1c.py +
       test_codegen_embebido_d_f1d.py + test_codegen_embebido_d_f1_4.py:
       23 passed (baseline del frontend embebido intacto).
COBERTURA: sin medicion en este ME (D-5 se cierra al final de FASE A).
MODIFICACIONES DE TESTS: ninguna (regla 5).
MODULARIZACION: ninguna.
RIESGOS IDENTIFICADOS (nuevos, no anticipados por el plan):
  - El ensayo A5.1 del D-7 (firmas decimal_a_texto(double)/entero_a_texto(int64_t)) ya
    está aplicado en el working tree y el bootstrap con él es determinista (diff 0).
    Riesgo bajo: al integrarlo formalmente en A5 habrá que revisar la paridad de los
    formatos %lld/%f en los e2e (ver docs/D7_ABI_IMPACTO.md, pasos A5.1-A5.6).
  - El espejo _G_fp* se regenera desde emit_selfhost.py: cualquier cambio futuro en A2
    que toque el frontend embebido exige regenerar frontend_p.syn + _rebuild_generator.py
    y re-verificar bootstrap (mismo flujo que F1.2c/F1.2d/F1.4).
PROXIMO PASO: Etapa A2.1 — port del tokenizador: nucleo/lexer.syn debe emitir
       T_NUMERO/T_FLOTANTE/T_CADENA con valor (hoy consume sin token, P0-A1), escapes,
       UTF-8 (H26), keywords rc/arc/debil/modulo/let/delegar/export activadas y token '@',
       con paridad contra _P_tokenizar (emit_selfhost.py gen_tok_c) y el lexer Python S1.
--- FIN ---
```

---

## 1. RESUMEN EJECUTIVO

La Etapa A2.0 confirma que el repositorio está en un **punto de partida estable** para
ejecutar la Etapa A2 (port del frontend). Resultados:

1. **Bootstrap determinista**: `build.sh bootstrap-full` (S1→S2→S3) termina con **diff
   0 bytes** entre Stage 2 y Stage 3 (SHA256 idéntico `585799d3…`), cumpliendo el
   criterio del Manual 9 §9.7 — **con el working tree actual**, que incluye el ensayo
   A5.1 del D-7 sin commitear. Esto demuestra que los cambios ABI aplicados no rompen
   el determinismo del auto-hospedaje.
2. **Frontend embebido intacto**: los 23 tests que validan `_P_*` (parseo de
   `declaracion_tipo`, `let`, `delegar`, `@export`, `rc/modulo`, codegen e2e S1/S2/S3)
   pasan en verde.
3. **Espejo sincronizado**: `_rebuild_generator.py` reconstruye `nucleo/generator.syn`
   byte-idéntico (0 líneas de diff; 283742 caracteres) y `_gen_frontend_p.py` reporta
   `frontend_p.syn sin cambios (149157 caracteres)`. No hay desincronización entre
   `emit_selfhost.py` y el espejo `_G_fp*`/`_G_tk*`.
4. **Sin cambios de código en esta etapa** (validación pura) y **sin deuda nueva**
   (regla 9): el ensayo A5.1 del D-7 queda registrado con resolución asignada (Etapa A5).

## 2. EVIDENCIA EJECUTADA (check de puntos resueltos)

| Punto del criterio A2.0 | Check ejecutado | Evidencia | Estado |
|---|---|---|---|
| `bootstrap-full` produce `diff 0 bytes` entre Stage 2 y Stage 3 | `./build.sh` (pipeline S1→S2→S3 del Manual 9 §9.7) | SHA256 S2 == S3 == `585799d3164eb9bf83f60b9c9525df5a6f42bedb4e1f1b785ab11febf2ef6b59`; `BOOTSTRAP VERIFIED` (1262664 bytes c/u) | ✅ VERIFICADO |
| Los 23 tests del frontend embebido siguen pasando | `python -m pytest tests/test_frontend_embebido_d_f1.py tests/test_codegen_embebido_d_f1c.py tests/test_codegen_embebido_d_f1d.py tests/test_codegen_embebido_d_f1_4.py -q` | `23 passed in 239.07s` | ✅ VERIFICADO |
| El espejo `_G_fp*` permanece sincronizado | `python nucleo/_rebuild_generator.py` + `diff` contra el `generator.syn` previo | diff 0 líneas; `generator.syn` = 283742 chars reconstruido byte-idéntico | ✅ VERIFICADO |
| `frontend_p.syn` sin cambios | `python nucleo/_gen_frontend_p.py` | `[OK] frontend_p.syn sin cambios (149157 caracteres)` | ✅ VERIFICADO |

**Check 4/4 PASS.**

## 3. REGISTRO DE DEUDA Y DECISIONES

- **Ensayo A5.1 del D-7 en el working tree (SIN commitear)**: por decisión del Arquitecto
  (2026-08-05) los cambios ABI (`decimal_a_texto(double)`/`entero_a_texto(int64_t)` en
  `emit_selfhost.py`, `generator.py`, `orquestador.syn`, `generator.syn`,
  `principal.syn.json`, `synapse_rt.c/h` y tests regenerados) **no se integran en A2**
  para no añadir ruido; se integran formalmente en la **Etapa A5** siguiendo los pasos
  A5.1-A5.6 de `docs/D7_ABI_IMPACTO.md`. El baseline A2.0 queda registrado **con** esos
  cambios presentes (el bootstrap ya es determinista con ellos).
- **Sin deuda técnica nueva** (regla 9): todos los hallazgos de esta etapa tienen
  resolución asignada (A2.1-A2.4 para las brechas P0/P2 de la matriz A1; A5 para D-7).
- **Regla 7 (orden del roadmap)**: esta etapa no adelanta fases posteriores.

## 4. PUNTO DE PARTIDA DE LA ETAPA A2 (registrado)

| Componente | Estado en A2.0 | Firma/evidencia |
|---|---|---|
| `compilador/generator/emit_selfhost.py` | VIVO (frontend `_P_*` S2/S3), con ensayo A5.1 aplicado | 1487 líneas; `emitir_parsear`/`gen_tok_c`/`gen_parse` |
| `nucleo/generador/frontend_p.syn` | Espejo `_G_fp*`/`_G_tk*` sincronizado | 149157 chars; 0 diff tras regenerar |
| `nucleo/generator.syn` | Reconstruible byte-idéntico | 283742 chars; 0 diff |
| `nucleo/lexer.syn` | Código muerto en runtime; **NO emite literales** (P0) | 827 líneas |
| `nucleo/parser*.syn` (parser, parser_base, parser_expr, parser_stmt, parser_constantes) | Código muerto; `NodoAST[]` plano (P0) | 2688 líneas totales (con lexer) |
| `nucleo/tokens.syn` / `nucleo/ast_nodes.syn` | Canónicos (TokenID 1-73; structs tipados) | Fuente del port |
| Stage binaries | `synapse_stage1/2/3.exe` (diff 0 S2==S3) | SHA256 `585799d3…` |
| Suite frontend embebido | 23/23 verde | `test_frontend_embebido_d_f1*.py` |

## 5. PRÓXIMO PASO

**Etapa A2.1 — Tokenizador nativo** (`nucleo/lexer.syn`): emitir tokens con valor para
literales (T_NUMERO/T_FLOTANTE con `.` / T_CADENA con escapes `\n \t \r \\ \" \' \0`),
soportar UTF-8 en identificadores (H26), activar keywords contextuales
(`rc`/`arc`/`débil`/`modulo`/`let`/`delegar`/`export`) y el token `@`→`@export`,
con **paridad contra `_P_tokenizar`** (gen_tok_c de `emit_selfhost.py`) y el lexer
Python S1 (`compilador/lexer.py`). Criterio de la sub-etapa: un harness C que compare
la secuencia de tokens del lexer nativo con la del `_P_*` para un programa que
ejercite todos los casos (literales, UTF-8, keywords, `@export`).

---

*Fin del reporte A2.0 — baseline estable verificado; siguiente hito: Etapa A2.1 (tokenizador).*
