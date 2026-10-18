# PLAN ME r188_deuda_cero_1 — cierre H-R184-1 + H-R187-1 (mandato: cero deuda)

**Base:** 64d0923 (R187 docs). **Mandato del Arquitecto (sesión 2026-10-15):** no
quiero que nada quede como deuda, todo resuelto sin excepción, ni deuda antigua.
MTS: plan citando Manual X §Y, sellos, oráculo ejecutado, expediente, gates.

## R1 — `coincidir <expr> ->:` forma canónica M5 §3.6 en S1 Y nativo

requisito: Manual 5 §3.6 — el ejemplo normativo L220 usa `coincidir c ->:` con
la flecha de recepción ANTES de los dos puntos (el receptor de un canal cerrado
obtiene un Resultado<T, Error>; los casos usan `ok(valor) =>` /
`err(error) =>`); Manual 3 §3 — patron ::= IDENTIFICADOR "(" IDENTIFICADOR ")"
| IDENTIFICADOR | "_" | numero; Manual 1 §3.1 — pipeline compartido: la misma
gramática en S1 y nativo.
texto: S1 (compilador/parser_control.py:232-239) y nativo
(nucleo/parser_sentencias.syn:540-542) exigen SOLO ':' tras la expresión →
`coincidir c ->:` produce "se esperaba COLON, se encontró ARROW" en S1 y rc de
sintaxis en el nativo (H-R184-1, hallazgo de R184 con resolución asignada a
este ME). Los casos `ok(valor) =>` / `err(_) =>` YA son aceptados en ambos
parsers (test_listen alineado ME r184_r185_e2e). Fix MÍNIMO: la flecha es
OPCIONAL tras la expresión — acepta el `coincidir c:` histórico y el
`coincidir c ->:` canónico en AMBOS parsers; sin alternativa gramatical nueva
(la flecha marca recepción de canal; el ':' abre el bloque de casos igual
que hoy).
implementacion: compilador/parser_control.py `_parsear_coincidir`
(TokenID.ARROW posible antes de COLON) // cumple Manual 5 §3.6;
nucleo/parser_sentencias.syn `parsear_coincidir` (aceptar T_FLECHA opcional
antes de T_DOSPUNTOS, paridad exacta) // cumple Manual 5 §3.6
oraculo: tests/auditoria/test_oraculos_r188_deuda_cero_1.py — (a) S1 E2E:
probe con `coincidir c ->:` compila rc=0 vía main.py; (b) S1 E2E: la forma
histórica `coincidir c:` sigue compilando rc=0 (sin regresión); (c) NATIVO
diagnóstico ejecutado: stage1 fresco desde nucleo
(python main.py nucleo/principal.syn) compila rc=0 — la gramática compartida
acepta la flecha en el auto-hospedado; el CODEGEN/semantics del receive-resultado
en nativo NO cierra (probe E2E nativo rc=5: 'co' es puntero, .dato.ok) →
H-R188-2 NUEVA con resolución asignada al ME r188b (paridad semántica
M1 §3.1, continuación directa).

## R2 — continuación multilínea acotada por el ':' de bloque (H-R187-1)

requisito: Manual 8 §4.1 (r153 H-R153-4) — la continuación multilínea es para
llamadas PARTIDAS entre líneas dentro de paréntesis/corchetes; Manual 2 §2 — la
firma de función es UNA línea (el ':' cierra la declaración); Manual 1 §3.1 —
el lexer es fase de tokens: NO debe destruir la estructura (NEWLINE/INDENT/
DEDENT) del resto del archivo ante una firma malformada.
texto: compilador/lexer.py `_procesar_lineas`: el '(' sin cerrar de una firma
malformada (`funcion f( -> entero:`) sube `profundidad` y NUNCA baja → todas
las líneas siguientes se procesan como continuación (sin NEWLINE/INDENT/
DEDENT) → el parser ve un archivo sin estructura y el error reportado es
cascada (o verde por accidente). H-R187-1 preexistente (igual pre-lote).
Fix MÍNIMO por la ley: una línea DENTRO de paréntesis cuyo texto termina en
':' es anómala (una llamada partida nunca termina en ':' — el ':' solo cierra
firma/estructura/bloque según M2 §2): reset de profundidad=0 + EMITIR
NEWLINE → el resto del archivo conserva su estructura y el parser reporta el
error REAL en la línea de la firma. Caso sano intacto (no existe llamada
multilínea canónica que termine en ':').
implementacion: compilador/lexer.py `_procesar_lineas` (guard + reset +
NEWLINE) // cumple Manual 8 §4.1
oraculo: tests/auditoria/test_oraculos_r188_deuda_cero_1.py (comparte el
corredor con R1) — (d) S1 E2E: firma
malformada con '(' abierto seguida de `funcion principal` con cuerpo →
rc=1 con el error apuntando a la LÍNEA de la firma (no cascada de archivo
sin estructura); (e) S1 E2E: archivo sano con la llamada partida de r153
(K-L de una llamada entre líneas) sigue compilando rc=0.

## Checklist de cierre (fase 4b + 5)

- `python auditoria/alineacion.py --leer --me r188_deuda_cero_1` (sello)
- lecturas previas por archivo según mapa_manuales (COMAS en --archivos)
- oráculo ejecutado (S1 + nativo recursivo en release)
- expediente --nuevo → --verificar 0 brechas
- `contrastar --plan docs/plan_ME_r188_deuda_cero_1.md` RC=0
- `verificar_alineacion.py` SIN BRECHAS; regla 4: revisar artefactos
