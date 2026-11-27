# Plan ME 33_1_paridad_nodos — H-R153-NODE (cierre con autorización del Arquitecto; 2026-09-26)

**Deuda:** la tabla canónica Manual 2 §7.2 llegaba hasta NODO_DELEGAR=55 y
además contenía ~13 valores que NO correspondían al nativo operativo
(NODO_ASIGNACION=6 vs 7 real, NODO_LLAMADA=8 vs 14 real, NODO_DELEGAR=55 vs 49
real, etc.): derivaba de un diseño anterior a la unificación del AST canónico
(H23/F1). El ME r153 emitió NODO_PARA_EN=57 y NODO_METODO=59 sin filas en la
tabla (H-R153-NODE, RATIFICADA 2026-09-25 como DESVIACION con actualización
pendiente "del Arquitecto").

**Autorización:** el Arquitecto autorizó explícitamente en sesión 2026-09-26
editar los manuales y "reparar y alinear todo lo pendiente"; los valores se
verificaron contra la fuente única `nucleo/parser_constantes.syn` (que genera
`runtime/core/ast_nodos.h`, compilado por el bootstrap operativo).

## R1 — Manual 2 §7.2: tabla corregida + filas 57/59
requisito: Manual 2 §7.2
texto: "| `NODO_METODO` | 59 | Llamada a método postfijo `obj.metodo(...)` (ME r153) |"
(fila añadida; la tabla completa re-verificada contra parser_constantes.syn).
implementacion: `docs/manuales/MANUAL 2.md` §7.2:
1. Filas NUEVAS `NODO_PARA_EN=57` y `NODO_METODO=59` con descripción.
2. 13 filas con valor INCORRECTO corregidas al valor del nativo real
   (NODO_ASIGNACION 6→7, NODO_LLAMADA 8→14, NODO_ESTRUCTURA 13→16,
   NODO_CANAL 22→41 renombrada NODO_CANAL_CREAR, NODO_LANZAR 47→18,
   NODO_ESCUCHAR 48→19, NODO_RECUPERAR 49→27, NODO_TENSOR 50→28,
   NODO_IMPORT 51→17 renombrada NODO_IMPORTAR, NODO_EXPORT 52→50,
   NODO_INSEGURO 53→24, NODO_COINCIDIR 54→38, NODO_DELEGAR 55→49) y filas
   NUEVAS NODO_EXPR=6, NODO_IDENTIFICADOR=8, NODO_ACCESO_CAMPO=31,
   NODO_INTENTO=54, NODO_LISTA_LIT=55, NODO_MAPA_LIT=56, NODO_BLOQUE_SQ=58
   (el "Extracto" ahora documenta los nodos que el código emite de verdad).
3. Nota de fuente canónica (parser_constantes.syn → gen_ast_nodos_h.py) y
   del oráculo de paridad.
oraculo: tests/auditoria/test_paridad_nodos.py

## R2 — Oráculo de paridad 3-vías
requisito: Manual 2 §7.2
texto: "| `NODO_PARA_EN` | 57 | Bucle `para-en` (iteración sobre colección; ME r153) |"
implementacion: `tests/auditoria/test_paridad_nodos.py` (NUEVO, sin skips):
(a) la tabla §7.2 contiene 57/59 con descripción; (b) paridad 3-vías:
todo NODO_* de la tabla existe con el MISMO valor en parser_constantes.syn y
ast_nodos.h; nativo == header (header regenerado de fuente única); (c) el
índice .indice.json está fresco (sha256 del manual == índice, cálculo sobre
texto utf-8 como indice_manual.py:157) y §7.2 indexa las filas nuevas; (d)
puente_canonico.py cita el nodo canónico 57 con su ancla de manual.
oraculo: tests/auditoria/test_paridad_nodos.py (auto-referencial)

## R3 — Índice de manuales regenerado
requisito: Manual 2 §7.2
texto: "### 7.2. Constantes de Tipo de Nodo (Extracto)"
implementacion: `docs/manuales/.indice.json` regenerado con
`python auditoria/alineacion.py --indice` tras editar el manual (la ley
cambió: las citas textuales del repo se validan contra el índice nuevo).
oraculo: auditoria/verificar_alineacion.py (SIN BRECHAS = 0 citas muertas
nuevas tras la corrección de la tabla)

## Archivos a modificar
- docs/manuales/MANUAL 2.md (R1 — §7.2)
- docs/manuales/.indice.json (R3)
- tests/auditoria/test_paridad_nodos.py (R2, NUEVO)

## Notas de riesgo
- El cambio es DOCUMENTAL + guard: no toca emisión de código → bootstrap
  S2==S3 sin riesgo (criterio del roadmap 33.1); se verifica collect+gates.
- H-R153-NODE pasa de DESVIACION a RESUELTA: la desviación existía porque el
  manual no documentaba los nodos; hoy la tabla == nativo == header.
- Riesgo mitigado del roadmap (editar manual dispara gate de citas muertas):
  verificar_alineacion SIN BRECHAS confirma que ninguna cita del repo
  apuntaba a los valores viejos de la tabla.
