# Plan ME r151_linea_base — Alinear los 4 fallos de línea base de la suite (MTO)

Ratificación del Arquitecto (2026-09-19): "si el código está alineado y el test no,
ajusta los tests siguiendo el manual MTO (TDD)". El código NO se toca en este ME
(la reparación de producción que este ME destapó vive en docs/plan_ME_r152_bootstrap_link.md).

Diagnóstico verificado (tests ejecutados):
1. `test_no_soportados_fallan_rapido` espera PuenteError para 54/57, pero
   `compilador/puente_canonico.py:548-550` los traduce (INTENTO→SentenciaRecuperar,
   PARA_EN→SentenciaMientras). Solo 55 (LISTA_LIT) y 56 (MAPA_LIT) siguen sin
   equivalente (backend Fase 24).
2. `test_categorization_completa_de_nodos` tiene 54/57 fuera del set `explicitos`.
3. `test_r3_param_adt_s1` fallaba porque `synapse_stage1.exe` no existe (el hook
   pre-commit lo borra como artefacto efímero, Manual 9 §5 nota de caché) y el
   mensaje del test afirmaba falsamente "feature sin código" (D-2 está CERRADA en
   CANON_DEUDAS; test_r3_param_adt_s2 PASA). Además la construcción on-demand
   destapó H-R151-3 (bootstrap no enlaza — reparado por ME r152).
4. `test_latencia_meta` (a) hace pytest.fail sin servidor (suite CI roja siempre);
   (b) el benchmark es degenerado (mide perf_counter() dos veces sin request);
   (c) cita "Manual 7 §7.2" — Manual 7 termina en §4.2, sección inexistente
   (H-R151-1, fabricación heredada de plan_ME_29_T3 cuyo `texto:` es igualmente
   inexistente). El MTO (OBL-MCTRL-03) exige Manual § real.

Bloques MTS (requisito/texto/implementacion/oraculo):

## R1 — puente_canonico: fail-fast solo para nodos SIN equivalente
requisito: Manual 6 §1.3
texto: "El traductor (`syquex/traductor.syq`) convierte el AST de Syquex en `SemNodo[]`. La traducción es **biyectiva en cuanto a semántica**: todo concepto de Syquex tiene un equivalente en el AST canónico." + "| `Intento` | `NODO_INTENTO` | Se traduce al modelo de `Resultado` y `?` (Manual 3 §7)."
implementacion: `test_no_soportados_fallan_rapido` (tests/unit/test_puente_canonico.py): el bucle solo itera (55, 56) — LISTA_LIT y MAPA_LIT siguen sin equivalente (backend Fase 24). 54 y 57 se eliminan del set de "no soportados" porque el puente ya los traduce (puente_canonico.py:548-550, coherente con el encabezado del archivo: "INTENTO(54) → SentenciaRecuperar (Manual 6 §1.3 L111); PARA_EN(57) → SentenciaMientras (Manual 3 §3 L133)"). Docstring citado a Manual 6 §1.3.
oraculo: tests/unit/test_puente_canonico.py

## R2 — categorization: 54/57 con handler explícito
requisito: Manual 3 §11.1
texto: "### 11.1. Mapeo de Nodos Clave — | Nodo Syquex | Nodo Synapse (SemNodo) |" + `bucle_para_rango  ::= "para" IDENTIFICADOR "en" expresion ":" NEWLINE INDENT bloque DEDENT   (* Iteración sobre lista o rango *)` (Manual 3 §3 L133)
implementacion: `test_categorization_completa_de_nodos` (tests/unit/test_puente_canonico.py): agregar 54 y 57 al set `explicitos` (manejados en puente_canonico.py:548-550). El test sigue exigiendo que TODOS los 58 nodos estén categorizados (invariante intacto). Docstring citado a Manual 3 §11.1.
oraculo: tests/unit/test_puente_canonico.py

## R3 — r3_param_adt_s1: construir stage1 on-demand (bootstrap)
requisito: Manual 1 §6
texto: "**Regla de hierro:** Ninguna característica nueva puede romper el *bootstrap* (etapas 0→1→2→3 con diff binario 0). El determinismo se verifica obligatoriamente en la CI mediante la comparación de los hashes SHA‑256 de las etapas 2 y 3."
implementacion: `tests/unit/test_r3_param_adt.py`: si `synapse_stage1.exe` no existe, el test lo construye on-demand con `python main.py nucleo/principal.syn -o synapse_stage1.exe` (mismo comando que el job bootstrap del CI y scripts/bootstrap_d12.ps1; Manual 1 §6: etapa 0→1 del bootstrap). stage2 ya existe en el árbol. Se elimina la afirmación falsa "feature sin código" (D-2 está CERRADA en CANON_DEUDAS: monomorfización A5; test_r3_param_adt_s2 PASA). Mensajes de fallo actualizados a causa real (artefacto ausente / rc de compilación). NOTA (2026-09-20): la construcción on-demand destapó H-R151-3 (enlace roto) — el TDD RED se cierra en el ME r152Bootstrap reparando producción, sin tocar este test.
oraculo: tests/unit/test_r3_param_adt.py

## R4 — latencia: cita real (M7 §2.2), skip sin servidor, benchmark real
requisito: Manual 7 §2.2
texto: "El cliente HTTP se encarga de enviar prompts al servidor de inferencia y recibir respuestas. Soporta timeouts, reintentos y manejo de errores." + "int port;                   // 8088" + "int llama_client_completion(LlamaClient* client, const char* prompt, int max_tokens, float temperature, char** response);"
implementacion: `tests/opensyn/test_inference.py::TestInferencia::test_latencia_meta`: (1) eliminar la cita fabricada "Manual 7 §7.2" de docstring/encabezado/constante (Manual 7 termina en §4.2; H-R151-1) y citar Manual 7 §2.2 (API real, puerto 8088); (2) sin llama-server en :8088 → `pytest.skip` con motivo claro (dependencia externa de entorno, convención MTO plan_ME_29_T3: "mock o skip"; la suite CI queda en verde; con servidor se mide de verdad); (3) benchmark REAL: POST http://127.0.0.1:8088/v1/chat/completions (mismo endpoint OpenAI-compat que usa el cliente C) con prompt corto y medición time.perf_counter() alrededor del request; assert latencia < 1.0 s (umbral autorizado por MTO plan_ME_29_T3, sin ancla manual — registrado en H-R151-1). El oráculo del plan es el CONTRATO ejecutable sin servidor (suite verde + exactamente 1 skipped + guardia anti-fabricación OBL-MCTRL-03); con servidor el benchmark corre de verdad.
oraculo: tests/auditoria/test_oraculos_r151.py

## Oráculo global del ME
.venv/Scripts/python.exe -m pytest tests/unit/test_puente_canonico.py tests/unit/test_r3_param_adt.py tests/opensyn/test_inference.py -v

## Archivos a modificar (solo tests + docs; producción NO se toca en r151)
- tests/unit/test_puente_canonico.py (R1, R2)
- tests/unit/test_r3_param_adt.py (R3)
- tests/opensyn/test_inference.py (R4)
- tests/auditoria/test_oraculos_r151.py (oráculo del contrato R4, nuevo)
- docs/plan_ME_r151_linea_base.md (este plan)

## Hallazgos registrados
- H-R151-3 (RESUELTO por ME r152Bootstrap — producción): desde `ba2c5ee` (Fase 31,
  2026-09-15) el bootstrap S1 NO enlaza: `python main.py nucleo/principal.syn -o
  synapse_stage1.exe` falla en link (rc=1) — (a) 5 externs de subcomandos
  lint/fmt/test que NUNCA existieron y (b) par F5-1 sin definición en la ruta
  unity. Causa raíz y reparación documentadas en docs/plan_ME_r152_bootstrap_link.md.
  Impacto mientras estuvo roto: job bootstrap de CI (ci-tests.yml:268) y workflows
  de release que compilan principal.syn. Evidencia: logs/r151_s1_probe.log.
- H-R151-1: citas fabricadas heredadas — "Manual 7 §7.2" (test_inference.py y
  plan_ME_29_T3 `texto:`/`requisito:`), "Manual 7 §7" (encabezado test_inference;
  M7 termina en §4.2) y "Manual 2 §12" como fuente del desugaring PARA_EN
  (puente_canonico.py:72; §12 es PRUEBAS OBLIGATORIAS). Resolución: R4 elimina las
  del test; las de producción (puente_canonico.py comentarios) NO se corrigen en
  este ME (el Arquitecto ratificó no tocar código) — deuda con resolución asignada
  a un ME de comentarios de producción.
- H-R151-2 (observación): plan_ME_29_T3.md contiene `texto:` inexistente (M7 §7.2)
  — plan histórico, se deja como evidencia del origen; no se reescribe.
  (Verificación de símbolos: `git log -S fmt_check_c` → solo ba2c5ee.)
