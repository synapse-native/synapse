# PLAN ME r198b_contratos — emisor de contratos: retorno + subcadena (cierre H-R196-3)

**Causa raíz (dos manifestaciones de la misma familia):** las cláusulas de
contrato del std/opensyn escritas bajo semánticas que no son las canónicas del
lenguaje. El emisor emite fielmente el AST (M2 §5.1: garantiza evalúa
`_resultado_` en CADA `retornar`); la desviación era del CÓDIGO del std y de
opensyn/principal.syn (precedente ratificado H-R196-1: "corregir contrato al
manual" — el runtime/emisor son la semántica canónica).

requisito: Manual 2 §5.1 — las cláusulas requiere/garantiza son expresiones
booleanas emitidas literalmente (assert_contrato) y `garantiza` se evalúa con
`_resultado_` del tipo REAL de retorno de la función; Manual 8 §1.7/r196 —
los builtins de texto son Builtin con semántica canónica (a) subcadena:
(inicio, largo) — el emisor S1 emite `_syn_texto_subcadena(t, inicio,
inicio+largo)` y el runtime es fin EXCLUSIVO (runtime/core/texto.c: clamp +
`inicio >= fin → vacío`); (b) `_resultado_` es el identificador canónico del
valor de retorno (patrón del propio archivo principal.syn L57/L91/L99 y
del manual M2 §5.1); (c) M2 §12: contratos en toda función pública — la
cláusula debe compilar (el C que no compila NO es una cláusula válida).

## R1 — std/sistema.syn `_validar_ruta_segura`: detección de absoluta (inicio, largo)

texto: la cláusula `subcadena(_resultado_, 1, 2) == ":"` asumía fin-inclusivo
(":" para "D:/...") pero (inicio,largo) produce ":/" → el garantiza abortaba
limpio (rc=0xC0000009) para toda ruta absoluta Windows validada (fallo
determinista del probe de contratos). El `si` del cuerpo compartía el patrón:
una ruta "D:/x" entraba al branch RELATIVA y se corrompía la resolución.
Fix: (1,2)→(1,1) en AMBOS sitios (1 char en posición 1 == ":", 1 char en
posición 0 == "/", UNC (0,2) ya correcta: 2 chars == "\\\\") — ancla
`// cumple Manual 2 §5.1; ME r198b`.
implementacion: std/sistema.syn (garantiza + si) // cumple Manual 2 §5.1
oraculo: tests/auditoria/test_oraculos_config_ruta.py — suite completa 5/5
(incluye roundtrip relativo + escape ../.. rechazado + fuga absoluta
rechazada: la postcondición de dominio del sandbox).

## R2 — opensyn/principal.syn: 2 cláusulas con `_resultado_` mal tipado/alias

texto: (a) `pct_contexto` (retorna entero): `longitud(_resultado_) >= 0`
aplicaba la función de TEXTO al retorno INTEGER → C no compilaba
("incompatible type for argument 1 of 'longitud'"); intención del porcentaje:
`_resultado_ >= 0`. (b) `ruta_config_absoluta` (retorna texto):
`longitud(resultado) > 0` con alias bare no existente ("did you mean
'_resultado_'"); patrón canónico del propio archivo: `longitud(_resultado_)`.
implementacion: opensyn/principal.syn (2 sitios) // cumple Manual 2 §5.1
oraculo: auditoria/oraculos/oraculo_r198b_contratos.py — (A1) la compilación
S1 de opensyn/principal.syn termina rc=0; (A2) la suite del sandbox de
contratos pasa 5/5; (A3) el oráculo r198 (cesión a campo) sigue 3/3 sin
regresión de la familia RAII.

## Checklist de cierre (fase 4b + 5)

- lecturas previas (std/sistema.syn → M2 §5.1; opensyn/principal.syn → M7)
- `alineacion.py --verificar --me r198b_contratos` 0 brechas
- `contrastar.py --plan docs/plan_ME_r198b_contratos.md` RC=0
- `verificar_alineacion.py` SIN BRECHAS
- suites afectadas: contratos (44) + config_ruta (5) + borrowing — PASAN
- commit + docs post-commit (bitácora, plan maestro, memoria)
