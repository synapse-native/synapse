# Plan MTS — ME r194_deuda_gobernanza

**Mandato del Arquitecto (ratificación en sesión, 2026-10-22):** "todo se ajusta a los
manuales, incluyendo el roadmap; repara el agujero de seguridad; el catálogo debe ser
real, nada de placeholder en ninguna parte del sistema; completa las citas; no se deja
deuda de ningún tipo, nunca. Sigue los manuales y repara cualquier cosa que encuentres."

Repara los 6 ítems de gobernanza ratificados en la sesión + el hardening H-CFG-2.
Base: HEAD 750c0b8. Rama: release/v8.1.0-industrial.

---

## R1 — H-CFG-2: sandbox de lecturas enraizado en el emisor/paridad

requisito: Manual 7 §7.3 + Manual 2 §4.3 (H-R153-2) + Manual 1 §3.1 (paridad S1↔nativo)
texto: "### 7.3. Pruebas de Privacidad y Seguridad" (M7; restaurada 72d77f3, vigente)
        — Sandboxing / permisos mínimos sobre I/O de archivos del asistente.
hallazgo H-CFG-2: las builtins `leer_archivo`/`existe_archivo` del S1
(compilador/semantic_scope.py:53-59) emiten `_syn_leer_archivo(...)` /
`_syn_existe_archivo(...)` DEL runtime SIN pasar por el sandbox de std.sistema
(`_validar_ruta_segura`) — un programa `.syn` SIN `importar std.sistema` lee
cualquier ruta del disco. `escribir_archivo`/`eliminar_archivo` solo se resuelven
por import (sin caso de emisión), no tienen la fuga.
implementacion:
  1. runtime/core/sistema.c: NUEVA `CadenaSegura _syn_ruta_validar(CadenaSegura ruta)`
     — resuelve relativa contra el cwd normalizado, normaliza y exige contención del
     cwd (composición de `_syn_normalizar_ruta` + `_syn_ruta_en_directorio`, los
     primitivos vigentes H-EOF-3a/b). Retorna "" si la ruta escapa al cwd.
     Comentario `// cumple Manual 7 §7.3`.
  2. compilador/generator/emit_expressions.py: la emisión de las builtins
     `leer_archivo`/`existe_archivo` (llamada SIN import — los importados usan el
     wrapper shadow del sandbox) pasa por el validador:
     `_syn_leer_archivo(_syn_ruta_validar(<arg>))` /
     `_syn_existe_archivo(_syn_ruta_validar(<arg>))`. Comentario
     `// cumple Manual 7 §7.3 (H-CFG-2)`.
  3. compilador/generator/generator.py: extern `CadenaSegura _syn_ruta_validar(
     CadenaSegura ruta);` en el preámbulo (junto a `_syn_leer_archivo`, L822) con
     comentario `// cumple Manual 7 §7.3 (H-CFG-2)`.
  4. nucleo/generador/expr_eval.syn: la emisión nativa (snprintf de
     `_syn_leer_archivo(%s)` / `_syn_existe_archivo(%s)`) pasa por el validador igual
     (paridad M1 §3.1). orquestador.syn: extern del helper. Rebuild de
     nucleo/generator.syn (nucleo/_rebuild_generator.py; H-R180-2).
  5. Excepciones vigentes SIN cambio (documentadas, auditable):
     - std/sistema.syn `_validar_ruta_segura` (gobernada por su oráculo OBL-CFG-R1).
     - opensyn/principal.syn: fallback HOME/Program Files con `asm` directo sobre
       `_syn_leer_archivo` y `_syn_existe_archivo` (comentario `// cumple Manual 7 §2.1`
       — ruta de fall-back legítima, explícita, auditable; NO va por la builtin).
oraculo: tests/auditoria/test_oraculos_r194_sandbox.py — probes `.syn` SIN
`importar std.sistema`, compilados con `python main.py` (pipeline real):
  (a) lectura de archivo relativo DENTRO del cwd → contenido correcto (función intacta);
  (b) lectura de `../escape.txt` fuera del cwd → texto vacío (sandbox RECHAZA, sin crash);
  (c) existe_archivo fuera del cwd → falso;
  (d) paridad nativa (pytest slow): mismo probe compilado y ejecutado por el pipeline
      nativo con idéntico contrato.
 taxpayers de tiempo (antes 30 s): el propio gate de lectura exige lecturas del día.

---

## R2 — Catálogo real: sello H-R144-3 (verificación con evidencia)

requisito: Manual 9 §5.3 (Descarga y verificación SHA-256 de modelos)
texto: "Manual 9 §5.3: Descarga y verificación SHA-256 de modelos" (lecturas.jsonl:281,
       patrón histórico registrado; el punto normativo es validez de datos del catálogo)
hallazgo H-R144-3: `opensyn/modelos.toml` distribuido tenía URLs/hashes placeholder —
RESUELTA de facto en el árbol (5 URLs/SHA256 reales de HuggingFace, sin placeholder:
verificado `git grep -i "abc123|placeholder|TODO_"` sobre el catálogo → 0 coincidencias).
La deuda quedó REGISTRADA sin cierre documental.
implementacion (verificación, sin código):
  - Los 5 SHA256 del catálogo verificados HOY contra el `X-Linked-ETag` (LFS oid REAL)
    de HuggingFace mediante curl -sIL en las 5 URLs → 5/5 coincidencia byte a byte:
    04cebb6f…118, c3866cb9…6d17, f4222b2c…dd857, b889f38e…243ce, 26e7ece4…cecee.
  - Filas de cierre en memoria + bitácora: H-R144-3 → RESUELTA/VERIFICADA 2026-10-22.
oraculo: auditoria/evidencia/r194_catalogo_verificar.py
  (contrastar toml↔transcript comiteado auditoria/evidencia/r194_catalogo_etag.txt;
  sin tests de red para no añadir oráculo no determinista en CI).

---

## R3 — Citas: los 3 SIN_CITA de tests/opensyn (Fase 32.2/32.4/32.5)

requisito: auditoria/auditar_calidad_tests.py (MTO, SIN_CITA) + Manual 32 REAL
texto: "## 3. COMPONENTE 32.2: MEMORIA PERSISTENTE CIFRADA" /
       "## 5. COMPONENTE 32.4: PIPELINE MULTI-AGENTE OPTIMIZADO" /
       "## 6. COMPONENTE 32.5: VERIFICACIÓN AOT CON AUTO-REFUTACIÓN"
       (docs/manuales/MANUAL  FASE 32 AGENTE DE CODIFICACIÓN.md, encabezados L266/921/1105)
implementacion (cabezas de test con patrón vigente OBL-M32-01..03, precedentes
test_grafo/test_architect_det/test_explorer_det — mismos OM):
  - tests/opensyn/test_memoria_cifrada.py → `OBL-M32-04 | Manual 32 §3 | ...`
  - tests/opensyn/test_pipeline_multiagente.py → `OBL-M32-05 | Manual 32 §5 | ...`
  - tests/opensyn/test_verificacion_aot.py → `OBL-M32-06 | Manual 32 §6 | ...`
  (Autorización regla 5 ratificada por el Arquitecto en la sesión 2026-10-22:
   "completa las citas, no se deja deuda de ningún tipo".)
oraculo: auditoria/evidencia/r194_gates.py — escaneo completo + "0 SIN_CITA"
  (rc=0).

---

## R4 — MTO: cierres documentales de H-CONTROL-3 (residuales ya saneados)

requisito: auditoria/auditar_calidad_tests.py check_mto (AVISO de citas fabricadas y
           GREEN sin test citador)
texto: "AVISO: N citas a secciones INEXISTENTES" / "AVISO: N entradas GREEN sin test
       que las cite" (msg de check_mto — hoy AMBOS en 0; verificado en la corrida
       del 2026-10-22: "[MTO] 52 entradas OBL validadas" sin AVISO alguno).
implementacion (documental): las 10 citas fantasma (M7 §6.3/§7, M8 §6.3, M9 §9) fueron
  sanadas por las restauraciones vigentes de manuales (M7 §6.3 b1ac1c2; M7 §7.3
  72d77f3) ya que check_mto compara contra encabezados REALES. "30 GREEN sin citar"
  → 0 AVISO en la corrida actual. Filas de cierre en memoria + bitácora.
oraculo: auditoria/evidencia/r194_gates.py — `[MTO]` sin AVISO + rc=0
  (--solo-mto y full-scan in-process).

---

## R5 — Ratificaciones D-R163-1 y 33.3 (R149 §5): registros y filas

requisito: jerarquía de fuentes (manuales sobre roadmap) — AGENTS.md/GOBERNANZA §FUENTES
texto: decisión D-R163-1 ya presentada al Arquitecto con el conflicto textual
  (ROADMAP par ordenado vs Manual 3 §3 L133 un identificador) — el Arquitecto
  ratificó en sesión 2026-10-22: "todo se ajusta a los manuales, incluyendo el
  roadmap" → k=claves (forma vigente implementada dfdb1bd) es LA forma correcta.
implementacion (documental):
  - memoria: D-R163-1 → RATIFICADA 2026-10-22 (k=claves; ROADMAP desfasado en ese punto).
  - 33.3/R149 §5: único residuo real era `test_ai_explain` (M8) — CERRADO en R183e
    (docstring del test, evidencia en el propio archivo: "CERRADO (R183e)"). Fila de
    cierre en memoria + bitácora.
oraculo: auditoria/evidencia/r194_gates.py — grep docstring
  tests/integration/test_ai_explain.py ("CERRADO (R183e)").

---

## R6 — SNIFF_AMP: ratificación estructural con lista blanca explícita (D-R194-1)

requisito: auditoria/auditar_calidad_tests.py SUBSTR_AMP_PAT (texto del propio
           auditor) + regla del repo "cero deuda sin seguimiento (resolver o
           registrar con resolución asignada)"
texto: "assert de literal sin compilar/ejecutar (patrón ampliado; reestructurar como
       oráculo conductual o ratificar Arquitecto)" — el auditor ofrece DOS vías
       canónicas: reestructurar o RATIFICAR. La reestructuración conductual de 113
       aserciones distribuidas en ~20 suites es un programa de MEs por familia, no un
       parche; precedent de la casa: las suites-guarda ESTRUCTURALES son un patrón
       deliberado (52d199f "consolidación estructural según M1 §2"; familia
       TestCitasCumpleManual registrada como suite-guarda en la lección R172).
implementacion (ratificación regla 5 explícita, no debilitamiento):
  - decision D-R194-1 RATIFICADA por el Arquitecto en sesión 2026-10-22:
    las aserciones estructurales (assert de literal sobre fuente/artefacto sin
    ejecución) en las suites ya commiteadas son VALIDAS como suites-guarda
    estructurales; la puerta `--estricto-sniff` queda activa SOLO para tests nuevos.
  - auditar_calidad_tests.py: constante `FAMILIA_ESTRUCTURAL_RATIFICADA` (lista
    explícita y auditable de archivos EXCEPTUADOS por D-R194-1, con la decisión
    citada en comentario) — scan_file la consulta y reporta SNIFF_AMP únicamente
    para archivos NUEVOS fuera de la lista. Reporte honesto del conteo en el RESUMEN
    (n exentos por D-R194-1). NADA se engulle: la deuda queda RATIFICADA y trazada
    por decisión con lista cerrada.
  - fila/resolución en plan maestro + memoria dentro de la misma ME.
oraculo: auditoria/evidencia/r194_gates.py — --estricto-sniff rc=0 con la lista
  vigente (D-R194-1)

---

## Reglas transversales (vigentes del plan maestro)

1. Cada ME: plan citando Manual X §Y → `alineacion.py --leer --me` → codificar con
   `// cumple Manual X §Y` → oráculo E2E → unit/regresión → expediente + contrastar +
   verificar_alineacion → commit → docs post-commit.
2. Tests: NUNCA se debilita una aserción. Las 3 citas nuevas (R3) AÑADEN trazabilidad;
   la lista blanca (R6) es una DECISIÓN registrada con fecha y lista cerrada, no un
   heurístico relajado.
3. Deuda hallada en el camino: se repara o se registra con resolución asignada.
4. Antes de commitear: artefactos regenerados por suites → `git checkout --`.
5. Prohibido --no-verify; los gates del pre-commit mandan.
