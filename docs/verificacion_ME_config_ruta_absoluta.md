# Verificación ME config_ruta_absoluta — H-EOF-3

**Fecha:** 2026-09-26
**Plan:** docs/plan_ME_config_ruta_absoluta.md
**Expediente:** docs/alineacion/config_ruta_absoluta.md
**Oráculo:** tests/auditoria/test_oraculos_config_ruta.py (5 GREEN, 0 skips)

## R1 — Manual 5 §1 — separador de plataforma en `_syn_normalizar_ruta` — CUMPLE
- Implementación: runtime/core/sistema.c:44 (`sep = '\\'` bajo `_WIN32`,
  `'/'` en POSIX), emisión `normalized[nlen++] = sep` y recorte final con
  `sep`. Comentario `// cumple Manual 5 §1` en línea 44.
- Evidencia: oráculo OBL-CFG-R1a GREEN (estructural) + debug E2E: cwd crudo
  `C:\...` normaliza byte-idéntico y el prefijo matchea.

## R2 — Manual 5 §1 — borde de componente y punto de montaje en `_syn_ruta_en_directorio` — CUMPLE
- Implementación: runtime/core/sistema.c:125 (comparación por componente con
  tolower solo en Windows, borde `nx == '/' || nx == '\\'`, montaje por
  primera letra). Comentario `// cumple Manual 5 §1` en línea 123.
- Evidencia: oráculo OBL-CFG-R1a GREEN; probe E2E: `../fuera.txt` resuelve a
  `..\fuera.txt` → fuera del prefijo → rechazado; escape `../..` → rc -1.

## R3 — Manual 2 §5.1 — resolución relativa→absoluta + contratos — CUMPLE
- Implementación: std/sistema.syn:18-39 (cwd NORMALIZADO, ruta relativa
  detectada por ausencia de `X:`/`/`/`\\` y resuelta `cwd + "/" + ruta`
  ANTES de normalizar; `..` sobre raíz relativa conservado → comparador lo
  rechaza). Contratos requiere/garantiza (M2 §5.1) en líneas 25-29 con
  comentario `// cumple Manual 2 §5.1`.
- Evidencia: oráculo OBL-CFG-R1b + OBL-CFG-R2 GREEN (probe real compilado
  con main.py: roundtrip relativo OK, escape rechazado, escritura absoluta
  fuera del cwd rechazada).

## R4 — Manual 7 §2.1 — config del cwd resuelta a absoluta en leer y guardar — CUMPLE
- Implementación: opensyn/principal.syn:209 `ruta_config_absoluta()`
  (requiere/garantiza, caso raíz de unidad sin duplicar separador), usada en
  `leer_modo_config` (:243) y `guardar_modo_config` (:295).
  Comentarios `// cumple Manual 7 §2.1` en 213/221/294.
- Evidencia: oráculo OBL-CFG-R1c + OBL-CFG-R3 GREEN: OpenSyn compilado E2E
  con config relativa `modo_oraculo=falso` en cwd temporal → entra en Modo
  Lenguaje Puro sin menú ni fallbacks (atribución válida: el fallback PF de
  esta máquina dice `modo_oraculo=verdadero`, haría fallar el test si la
  lectura relativa rompiera).

## R5 — Manual 9 §6.2 — Oráculo E2E sin skips — CUMPLE
- tests/auditoria/test_oraculos_config_ruta.py: 3 estructurales anti-sniff +
  probe E2E + E2E OpenSyn. 5/5 GREEN, SIN skips (lección R155: SKIP != 
  oráculo ejecutado). Ejecutado en modo release por contrastar.py.

## R6 — Manual 2 §5.1 — mapa de alineación: entrada explícita std/sistema.syn — CUMPLE
- docs/gobernancia/mapa_alineacion.md: `"std/sistema.syn": ["Manual 2 §5.1"]`
  (la parte C del sandbox vive en runtime/core/sistema.c, mapeada aparte).
- Evidencia: verificar_alineacion.py SIN BRECHAS.

## Hallazgos del ME
- **H-EOF-3a (RESUELTO):** normalizador emitía `/` vs cwd `\` → sandbox
  teatro; hoy separador de plataforma.
- **H-EOF-3b (RESUELTO):** comparador memcmp ciego sin borde de componente →
  `proyecto_evil` pasaba como hijo; hoy borde + montaje + tolower Win.
- **H-CFG-1 (RESUELTO en este ME):** el normalizador retrocedía el componente
  equivocado al resolver `..` cuando el carácter previo era el separador
  recién emitido: `X/../Y` normalizaba a `XY` (fusión) y `..` podía
  sobrevivir literal. Reescrito con pila de componentes (`.` descarta, `..`
  desapila, `..` sobre raíz relativa se conserva para que el sandbox lo
  rechace). Detectado por el debug E2E del propio ME (clase de bug del
  normalizador, no del caso config).
- **H-CFG-2 (REGISTRADO, no se repara aquí):** `leer_archivo`/`existe_archivo`
  son BUILTINS del S1 Python (compilador/semantic_scope.py:53-56, decisión
  ratificada H-R153-2 citando Manual 2 §4.3) que delegan directo en
  `_syn_leer_archivo` SIN sandbox; `escribir_archivo`/`eliminar_archivo` sí lo
  pasan. Consecuencia: la LECTURA fuera del cwd no está protegida por el
  sandbox en el pipeline Python. Los tests (especificación) no se tocan
  (regla 5); la corrección exige ratificación del Arquitecto (quitar del
  builtin o enraizar el sandbox en el runtime). Resolución asignada: ME
  futuro de hardening del sandbox tras ratificación.
- **H-CFG-3 (RESUELTO, infraestructura de tests):** `test_tiempo` enlazaba
  `tiempo.o` sin `synapse_rt_memory.o` (tiempo.c usa pool_alloc) → 15 errores
  de link preexistentes (verificados con baseline git stash). Fix en
  tests/conftest.py (harness, NO el test); 15/15 GREEN.

## Estado final
- Oráculo 5/5 GREEN sin skips.
- Regresión: test_math/test_texto/test_path_traversal_security 37 GREEN;
  test_tiempo 15 GREEN (reparado); oráculos eof_* 8 GREEN + 1 skip
  preexistente de datos de máquina (test E2E del MENÚ inmutable, regla 5).
- verificar_alineacion.py: SIN BRECHAS; contrastar.py: PASA;
  alineacion --verificar --me: PASA (evidencia 5d6724dfb03b5f9d).

CUMPLE
