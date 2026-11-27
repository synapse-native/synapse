# Verificación ME r180_coincidir_nativo (R180) — H-R177-2

**Base:** 3f8c34d (R179). **Commit:** (post-commit). **Método:** MTS + TDD + MTO.

## Marcas por requisito

- Manual 3 §3 R1 parser nativo acepta numero y wildcard como inicio de patrón (`patron ::= ... | numero`): `nucleo/parser_base.syn` `token_es_inicio_patron` + `nucleo/parser_sentencias.syn` `parsear_coincidir` (evidencia nucleo/parser_base.syn:302, oráculo test_oraculos_r180_coincidir_nativo.py r1/r4, probes p_b1 `dos|siete`): CUMPLE
  - Contratos requiere/garantiza añadidos (Manual 2 §12): `token_es_inicio_patron` clasificador puro. El guard anti-cuelgue R11 (avance con tokens no-nombre) queda SIN cambiar; los literales entran por la rama de caso antes del guard.

- Manual 3 §3 R2 emisor nativo: switch sobre VALOR para primitivos + `case <lexema>` / `default:` (paridad S1 emit_control.py H-R90-6): `nucleo/generador/nodos_flujo.syn` `gen_visitar_coincidir` (evidencia nucleo/generador/nodos_flujo.syn:1353, oráculo test_oraculos_r180_coincidir_nativo.py r1/r3/r4, probes p_b1 `dos|siete`, p_b2_wildprim `otro`): CUMPLE
  - Decisión por TIPO C exacto (`int64_t`/`int`/`bool`) o dígito en patrones; la ruta ADT (`.tag` + binding `.dato.<tag>`) queda byte-idéntica.

- Manual 1 §3.1 R3 paridad S1: pipeline compartido, `_parsear_coincidir` acepta TokenID.NUMBER como patrón (evidencia compilador/parser_control.py:255, oráculo test_oraculos_r180_coincidir_nativo.py r2, probe_h2 `10/0` idéntico en ambas tuberías): CUMPLE
  - `tok_patron` conservado para la columna que usa R22 (anti UnboundLocalError).

- Manual 3 §3 R4 test alineado TDD/MTO + oráculo E2E: `test_r11_patron_literal_no_cuelga` pasa de rc=5 (gap provisional) a compila rc=0 + salida `10/0` con mapeo OBL-M3-06; oráculo nuevo 4/4 GREEN en 273.75 s (evidencia tests/auditoria/test_oraculos_r180_coincidir_nativo.py:1, tests/integration/test_fase2_nativa_hm.py::test_r11_patron_literal_compila_y_ejecuta PASSED): CUMPLE

## Bootstrap y regresión ejecutada

- **LECCIÓN DE CADENA (H-R180-2):** `nucleo/generador/nodos_flujo.syn` es submódulo concatenado en `nucleo/generator.syn` via `python nucleo/_rebuild_generator.py`; sin el rebuild el bootstrap compila el combinado STALE (costó un ciclo S1→S2 inútil y probes con el fix ausente).
- Bootstrap final: S1 rc=0 06:45 (Oct 5), S2 rc=0 06:47 (auto-compilación pasa con contratos y fix por tipo). Probes re-verificados contra stage2 06:47: p_b1 `dos|siete`, p_b2_wildprim `otro`.
- Regresión: oráculo 4/4 (273.75 s); fase2 `-k r11` 5/5 (298.60 s) y `-k "r20 or r9"` 7/7 (291.86 s); unit 514✓ (296 s); micro+nucleo+synapse 30✓ (152 s); matriz 35✓ (71 s).
- Gates: verificar_alineacion SIN BRECHAS; alineacion --verificar --me r180_coincidir_nativo PASS (evidencia auditoria/evidencia/bdf56b5aea7c6db9.json).

## Hallazgos del ME

- **H-R180-1 (abierto, ME dedicado en plan_maestro):** la forma de BLOQUE del caso (`3 =>` NEWLINE INDENT bloque DEDENT, M3 §3 segunda alternativa) falla en el pipeline NATIVO con `Error Fatal Generador: Nodo tipo [DefinicionFuncion] no reconocido` TAMBIÉN para patrones ADT pre-existentes (bisección: probe sin coincidir pasa; una-línea pasa; bloque-literal y bloque-ADT fallan igual). Bug pre-existente del generador nativo con cuerpos-bloque, ajeno a R180 (el probe D no tiene literales). La forma canónica de una línea funciona en ambas tuberías.
- **H-R180-3 (cerrado en este ME, lección TDD):** la primera heurística del emisor ("tipo C no empieza con `struct ` ⇒ valor") era INCORRECTA: las instancias ADT monomorfizadas se registran en `_G_fn_var_tipos` con el nombre C SIN prefijo (`Resultado_entero_texto`) y había invertido los coincidir ADT a `switch ((r))` (GCC "switch quantity not an integer"). El oráculo r4 (ADT sin regresión) la detectó; regla final por tipo C exacto (espejo del set PRIMITIVOS de S1).

## Deuda bloqueada restante (decisión Arquitecto)

- Patrón `cadena` en switch (M3 §3): C no soporta `case "..."`; falla igual en ambas tuberías hoy — residual documentado, sin brecha de paridad. Se resolverá con dispatch strcmp si el Arquitecto lo prioriza (fila en plan_maestro).
