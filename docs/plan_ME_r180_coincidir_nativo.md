# Plan ME r180_coincidir_nativo — paridad de `coincidir` sobre primitivos (H-R177-2)

**Fuente:** plan maestro `docs/plan_maestro_deudas.md` ME R180 (mandato
Arquitecto: "repara y corrige todo; los tests solo se modifican si es para
alinear al manual; si el código está alineado y el test no, se modifica el test
aplicando TDD y MTO"). **Base:** 3f8c34d (R179). **Método:** MTS + TDD + MTO.

**TDD (probes ejecutados 2026-10-04, /tmp/probe_r180 y /tmp/probe_lf):**
`coincidir x:` con patrones literales (`1 =>`, `2 =>`) y wildcard (`_ =>`)
sobre `entero`: (a) NATIVO stage2: rc=8 "Error de sintaxis" (el caso literal
se descarta por el anti-cuelgue R11 — `token_es_nombre(T_NUMERO)==0` — y el
`caso`/`_` siguiente se corrompe); con SOLO wildcard el emisor emite
`switch ((x).tag)` sobre un primitivo → C inválido; (b) S1
(parser_control.py `_parsear_coincidir`): "Se esperaba ARROW_RIGHT, se
encontró 'NUMBER'" — el parser S1 también lo rechaza; (c) el EMISOR S1
(emit_control.py visitar_coincidir) YA soporta primitivos/literales (H-R90-6,
f758556) pero solo llega por el camino .syq (fixture test_r90_compila.syq:
`0 => ... _ => ...`). Divergencia de paridad en TODAS las rutas .syn.

**Decisión (ratificada en plan_maestro + ley textual):** M3 §3 L143 define
`patron ::= IDENTIFICADOR "(" IDENTIFICADOR ")" | IDENTIFICADOR | "_" | numero | cadena`
— los literales SON gramática de Syquex; M2 §2 L127 define el wildcard `"_"`
para Synapse. H-R90-6 (ratificada) ya ejecuta primitivos por valor en S1.
Se implementa `numero` (funcional) y wildcard en AMBOS parsers y el emisor
nativo (paridad M1 §3.1: pipeline compartido). `cadena` queda como residual
documentado: el switch de C no soporta `case "..."` (requeriría cadena de
strcmp) y hoy falla en ambas tuberías por igual — sin brecha de paridad.

## R1 — parser_nativo_patron: el bucle de casos acepta numero y wildcard
requisito: Manual 3 §3
texto: "patron ::= IDENTIFICADOR \"(\" IDENTIFICADOR \")\" | IDENTIFICADOR | \"_\" | numero | cadena (Literales)" (M3 §3 L141-143; el wildcard "_" también es ley Synapse en M2 §2 L127: `patron ::= ... | "_" (* wildcard *)`).
implementacion: (a) `nucleo/parser_base.syn`: nueva funcion
`token_es_inicio_patron(t)` = `token_es_nombre(t) || t == T_NUMERO` (el
wildcard `_` ya lexea como T_IDENTIFICADOR porque es_letra(95)==1); (b)
`nucleo/parser_sentencias.syn` `parsear_coincidir`: la entrada del caso y el
span del patrón usan `token_es_inicio_patron` (el span de `1` captura el
lexema "1"; el anti-cuelgue R11 conserva el avance para tokens no-patrón).
El payload NODO_CASO no cambia (el patrón sigue siendo un span de texto).
// cumple Manual 3 §3 (ME r180_coincidir_nativo R1)
oraculo: tests/auditoria/test_oraculos_r180_coincidir_nativo.py

## R2 — emisor_nativo_primitivos: switch sobre valor + case literal
requisito: Manual 3 §3
texto: "coincidir ::= \"coincidir\" expresion \":\" NEWLINE INDENT { caso } DEDENT; caso ::= patron \"=>\" ( sentencia | NEWLINE INDENT bloque DEDENT )" (M3 §3 L139-140; el emisor debe ejecutar el caso cuyo patrón coincide — sobre primitivos el sujeto es el VALOR, paridad S1 emit_control.py H-R90-6 "tipos primitivos no tienen .tag — switch sobre el valor directo").
implementacion: `nucleo/generador/nodos_flujo.syn` `gen_visitar_coincidir`:
pre-escaneo de los casos + sujeto — el switch se emite sobre el VALOR
`switch ((expr))` si (a) algun patron no-wildcard comienza con digito (literal
numero) o (b) el TIPO C del sujeto en `_G_fn_var_tipos` es exactamente
`int64_t`/`int`/`bool`; si no, ADT `switch ((expr).tag)` (byte-identico al
comportamiento actual). NOTA TDD (oraculo r4): la primera heuristica
(no-`struct ` => valor) era INCORRECTA — las instancias ADT monomorfizadas se
registran en `_G_fn_var_tipos` con el nombre C sin prefijo `struct `
(`Resultado_entero_texto`, idem R18 que lo compara con
`_G_native_adt_inst_c`) y habian invertido los coincidir ADT a
`switch ((r))` (GCC "switch quantity not an integer"); el oraculo r4 la
detecto y la regla final es por tipo C exacto (espejo del PRIMITIVOS set de
S1). En el bucle: patron `_` -> `default:` (igual); patron literal ->
`case <lexema>:` (sin binding de variable — no hay parens); patron tag ->
ruta existente `_G_native_adt_ctr_info` + `case %d:` intocada.
// cumple Manual 3 §3 (ME r180_coincidir_nativo R2)
oraculo: tests/auditoria/test_oraculos_r180_coincidir_nativo.py

## R3 — parser_s1_paridad: `_parsear_coincidir` acepta numero (M1 §3.1)
requisito: Manual 1 §3.1
texto: "El compilador unificado procesa código fuente de Synapse (.syn), Syquex (.syq) e incluso prompts en lenguaje natural (via OpenSyn) a través de un pipeline compartido" (M1 §3.1 L77 — mismo AST canónico; un .syn debe parsear idéntico en S1 y nativo; M3 §3 L143 define numero como patrón).
implementacion: `compilador/parser_control.py` `_parsear_coincidir`: si el
token actual es TokenID.NUMBER, se consume y su lexema (valor entero
str-ingificado) es el nombre del patrón; si no, ruta `_esperar_identificador`
existente. El patrón sin parens evita la rama LPAREN (guardada por mirar).
// cumple Manual 3 §3 (ME r180_coincidir_nativo R3)
oraculo: tests/auditoria/test_oraculos_r180_coincidir_nativo.py

## R4 — test_alineado_TDD_MTO: r11_patron_literal pasa de rc=5 a la ley + oráculo E2E
requisito: Manual 3 §3
texto: "patron ::= IDENTIFICADOR \"(\" IDENTIFICADOR \")\" | IDENTIFICADOR | \"_\" | numero | cadena (Literales)" (M3 §3 L143 — el test test_r11_patron_literal_no_cuelga codificaba el gap provisional "rc=5 esperado hoy: GCC sin codegen para patrones literales (pendiente residual, reporte §13.5)"; implementada la ley, la aserción se alinea: compila rc=0, ejecuta y produce la salida del caso literal).
implementacion: (a) `tests/integration/test_fase2_nativa_hm.py`
test_r11_patron_literal_no_cuelga: aserción rc=5 → rc=0 + salida `10`
(propiedad anti-cuelgue preservada en docstring; mapeo MTO OBL-M3-06); (b)
NUEVO `tests/auditoria/test_oraculos_r180_coincidir_nativo.py`: (r1) nativo
stage2 coincide literal+wildcard sobre entero compila rc=0 y corre
`dos|siete`; (r2) paridad S1 misma salida; (r3) wildcard-only sobre
primitivo `default:` rc=0; (r4) ADT ok/err sin regresión (switch .tag)
+ anti-cuelgue. Entrada MTO OBL-M3-06 (Manual 3 §3) en
docs/manuales/MANUAL_TESTS_OBLIGATORIOS.md.
// cumple Manual 3 §3 (ME r180_coincidir_nativo R4)
oraculo: tests/auditoria/test_oraculos_r180_coincidir_nativo.py

## Verificación
- `rm -f nucleo/_analizador_semantico.c nucleo/_analizador_semantico.c.o synapse_stage1.exe synapse_unity.c && .venv/Scripts/python.exe main.py nucleo/principal.syn -o synapse_stage1.exe` (rc=0, timestamp fresco)
- `rm -f synapse_stage2.exe synapse_unity.c && ./synapse_stage1.exe nucleo/principal.syn -o synapse_stage2.exe` (rc=0 ~90 s — AUTO-COMPILACIÓN con los cambios)
- **LECCION DE CADENA:** `nucleo/generador/nodos_flujo.syn` es submódulo concatenado en `nucleo/generator.syn` via `python nucleo/_rebuild_generator.py` — sin el rebuild, el bootstrap compila el combinado STALE (costo: un ciclo S1→S2 inutil, probes con el fix ausente).
- Probes /tmp/probe_r180 (post-fix 20:12): p_b1 (literal+wildcard) nativo rc=0 `dos|siete`; p_b2_wildprim rc=0 `otro`; paridad S1 `dos|siete` verificada (probe_h2 `10/0` ambas).
- `.venv/Scripts/python.exe -m pytest tests/auditoria/test_oraculos_r180_coincidir_nativo.py -v` → 4/4 GREEN en 273.75 s (el r4 detecto la heuristica invertida; re-ejecutado tras el fix por tipo exacto).
- `.venv/Scripts/python.exe -m pytest tests/integration/test_fase2_nativa_hm.py -k "r11 or r20 or r9" -v` → sin regresión
- Regresión: unit 514, micro+nucleo+synapse 30, matriz 35.

## Hallazgo H-R180-1 (fuera de alcance R180 — registrar en plan_maestro)
La forma de BLOQUE del caso (`3 =>` NEWLINE INDENT `retornar "tres"` DEDENT,
M3 §3 segunda alternativa de `caso ::= patron "=>" ( sentencia | NEWLINE
INDENT bloque DEDENT )`) falla en el pipeline NATIVO con
`Error Fatal Generador: Nodo tipo [DefinicionFuncion] no reconocido`
TAMBIEN para patrones ADT pre-existentes (biseccion: probe A sin coincidir
pasa; probe B una-linea pasa; probe C bloque-literal y probe D bloque-ADT
fallan igual). Bug pre-existente del generador nativo con cuerpos-bloque,
AJENO a R180 (los literales no intervienen: D no tiene literales). La forma
canonica de una linea (la que ejercitan tests y nucleo) funciona en ambas
tuberias. Resolucion: fila en plan_maestro_deudas (ME dedicado) + bitacora.
Hallazgos con fecha: S2 con heuristica invertida opero ~20:12 menos una
ventana minima; corregido y re-verificado el mismo dia.
