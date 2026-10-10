# Plan MTS r182b — Reparación segfault frontend Syquex (bucles `para` con rango)

## Hallazgo H-R182b-1
`para i en 0..n:` / `para i = a..b [paso p]` en `.syq` segfaulteaban el frontend
(build/syq_frontend.exe, segfault 0xC0000005 → SYQ_JSON_ERROR=-3 / JSON truncado).
Deuda heredada (1F+9E en tests/syquex/test_concurrency.py + test_traductor).

## Causa raíz
El emisor JSON (syquex/syq_json.syn) reconstruye el span slot1 como
`ptr64 = (hi[i] << 32) | ptr_str[i]`, con `hi` desde `trad_hi()` que
`trad_copiar_payload` (syquex/traductor.syn L239) copia desde `sq_tokens_hi()`.
Los literales sintéticos del desugar de `para` (syquex/parser.syn: `_SQ_ONE_R`,
`_SQ_ONE`, `_LT`, `_PL`, `_SQ_INIT`) fijaban `ptr_str`/`len_str` PERO no
`sq_tokens_hi[n]` → la dirección reconstruida era inválida → lectura no mapeada.

## Implementación
- `requisito:` Manual 3 §3 secciones del bucle: el desugar del para debe poder
  emitir el SemNodo con sus spans íntegros (L132/L133 obligan `para ... = a..b [paso p]`
  y `para ... en a..b`).
  `texto:` "bucle_para_rango  ::= \"para\" IDENTIFICADOR \"en\" expresion \":\" NEWLINE INDENT bloque DEDENT"
  `implementacion:` syquex/parser.syn — cada sitio que fija `ptr_str = (int)(uintptr_t)_X`
  de un literal sintético escribe además `sq_tokens_hi[n]=(int)((uintptr_t)_X>>32)`
  (paridad con el patrón ya correcto de `_SQ_SELF`, parser.syn L768).
  `oraculo:` tests/syquex/test_concurrency.py::test_enviar_canal (para i en 0..10) rc=0
- `requisito:` Manual 1 §1.1 — backend compartido tras el traductor.
  `texto:` "Manual 1 §3.1: la salida del TRADUCTOR alimenta el backend compartido"
  (syquex/syq_json.syn L8; contrato emitir int-compilable).
  `implementacion:` comprobar probes e2e posterior al fix (rc=0 y ejecución).
  `oraculo:` python scripts/build_syquex_frontend.py + cli.py build de .syq con para.
- `requisito:` Manual 1 §5.1 — legibilidad (los comentarios R182b citan la sección).
  `texto:` "El código debe leerse casi como un lenguaje natural estructurado."
  `implementacion:` comentarios R182b en cada sitio reparado (5 sitios).
  `oraculo:` grep -c "R182b" syquex/parser.syn = 5

## Fases
1. REPAIR (gramática TDD): fix de 5 sitios + rebuild frontend ✅
2. Probes e2e (for-en / paso) → rc=0 y ejecución correcta ✅
3. Suite regresión: tests/syquex/ (279 passed) ✅
4. Oráculos + contrastar.py + verificar_alineacion (pendiente)
5. Commit + docs post-commit (pendiente)

## Bloques requisito (formato contrastar.py)

requisito: Manual 3 §3 — desugar de bucle_para/bucle_para_rango con spans íntegros
texto: bucle_para_rango ::= "para" IDENTIFICADOR "en" expresion ":" NEWLINE INDENT bloque DEDENT
implementacion: syquex/parser.syn — literales sinteticos del desugar escriben bits altos en sq_tokens_hi
oraculo: tests/syquex/test_concurrency.py  # 5 passed

requisito: Manual 1 §1.1 — backend compartido tras el traductor (spans reconstruibles)
texto: Manual 1 §3.1: la salida del TRADUCTOR alimenta el backend compartido
implementacion: syquex/parser.syn — hi bits en paso_r/expr_paso/lt/incr_val para trad_texto
oraculo: auditoria/oraculos/oraculo_r182b.py

requisito: Manual 1 §5.1 — legibilidad del código reparado
texto: El código debe leerse casi como un lenguaje natural estructurado.
implementacion: comentarios R182b en los 5 sitios (grep = 5)
oraculo: auditoria/oraculos/oraculo_r182b.py
