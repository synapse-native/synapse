# 🧠 MEMORIA DEL PROYECTO SYNAPSE

> **Formato optimizado para agentes.**
> - 🚦 **Sección 1 — Dashboard actual** (léase primero, < 30 segundos).
> - 💡 **Sección 2 — Errores recurrentes** (patrones a evitar siempre).
> - 📚 **Sección 3 — Lecciones clave** (reglas de arquitectura/tacticas).
> - 📜 **Sección 4 — Historico detallado (F1–F27)** — conserva el conocimiento profundo del proyecto.
> - 📋 **Sección 5 — Checklist de verificación** (validar antes de commitear).
>
**2026-11-20 (H-R275-1 y H-R275-2 RESUELTOS — ME `r275b_str_eq_texto_indexado`, commit `aa83822`):** el emisor autohospedado S2 emitía `texto[i]` como `int64_t` en las tres rutas de valor y —lo que faltaba— en la rama de **declaración** de `gen_visitar_declaracion`, así que `let c = ruta[n]` quedaba tipado entero y `str_eq` no compilaba: de ahí que `opensyn/permisos.syn` no compilara con `dist/bin/synapse.exe` y la sonda E2E de r275 cayera a S1 con `[R275][WARN]`. Se infiere y emite `CadenaSegura` en las cuatro rutas (Manual 2 §4.1, §8.2) sin tocar el fuente ni el test inmutable. Segundo defecto del mismo síntoma: S2 resolvía módulos y fuentes del runtime **sólo** desde el cwd (el E2E compila en `tmp_path`); `nucleo/principal.syn` los busca ahora junto al ejecutable y sus padres, conservando el orden previo (Manual 8 §4.1, Manual 9 §6.2). Tercero, **H-R275-2**: el sello de frescura del bootstrap quedaba en punto muerto para cualquier edición de `nucleo/principal.syn` (no certificaba y `--sellar` no re-sellaba); ahora re-sella si la etapa 2 es posterior a la fuente y `S2==S3`, y un artefacto stale sigue fallando (regresión `test_oraculo_r252_resellado.py` 3/3). Medido: `build.py --skip-test` rc=0 con `S2==S3 644ec933740c921a` (2.574.175 B), `synapse.exe`/`dist/bin/synapse.exe` == etapa 2; oráculo nuevo `oraculo_r275b_texto_indexado.py` rc=0 (texto indexado y sandbox con S2: editar dentro=ASK, fuera=DENY, leer dentro=ALLOW); `oraculo_r275` rc=0 **sin** `[R275][WARN]` con el GGUF local; `contrastar` 6/6, `alineacion --verificar` evidencia `d41891ec4639a785`, `verificar_alineacion` 0 brechas, 53 tests dirigidos en verde. **Lección:** un `[WARN]` de paridad no siempre delata al fuente que se cita; aquí había tres defectos en cadena (tipo emitido, resolución de rutas y sello del gate) y el que impedía medir era el tercero. Reporte: `docs/reportes/R275b.md`.

**2026-11-20 (ME `r277_contracts_audit` CERRADO con deuda medida — commit `3eff2fa`):** Manual 2 §5.1 y §12 hacen de los contratos una promesa central y les asignan prueba obligatoria, pero no había ninguna medición. La primera medición real: **600 funciones públicas de producción sin `requiere` + `garantiza`** en 68 archivos (1.161 auditadas, 561 `externo` FFI exentas; mayores: `nucleo/generator.syn` 36, `nucleo/analizador_semantico.syn` 34, `nucleo/lexer.syn` 26). Nuevo `auditoria/verificar_contratos.py` con **ratchet**: deuda congelada en `auditoria/contratos_baseline.txt`, falla ante cualquier función pública nueva sin ambos contratos, `--estricto` es la meta de deuda cero, `--resumen` la desglosa y `--json` deja evidencia; job `contratos` en `ci-tests.yml`; regresión nueva `tests/auditoria/test_verificar_contratos.py` 4/4 y `tests/integration/test_contracts.py` 5/5 sin tocarlo; `contrastar` 2/2 y `verificar_alineacion` 0 brechas. **H-R277-1 abierto** con la deuda y su quema por archivo. **Lección:** cuando el requisito es “0 infracciones” y el pasivo es grande, lo honesto es medir, congelar y prohibir el crecimiento; los contratos de relleno serían mentira documentada. Reporte: `docs/reportes/R277.md`.

**2026-11-20 (ME `r276_multiplataforma_release` CERRADO con límite — commit `197d469`):** el release podía publicarse con un bundle roto: la matriz construía, firmaba y verificaba firmas, pero **nadie ejecutaba el binario distribuido**. Se añade `scripts/verificar_release_limpio.py` (artefactos obligatorios, integridad SHA-256 contra sidecars y manifiesto, `.sig` Ed25519 de cada artefacto y del manifiesto, y smoke real: `--version`, compilar/ejecutar `Hola Mundo`, `opensyn --version`) y el job `smoke_release_limpio` en cuatro runners de `release_matrix.yml`, del que ahora **depende** `create_release`. Medido en Windows: `PASS: release limpio win_x64 — 19 artefactos, 7 firmas Ed25519, smoke: OK`; en copias manipuladas el gate devuelve rc=1 por byte alterado y por firma ausente; regresión nueva `tests/auditoria/test_r276_release_limpio.py` 5/5; `contrastar` 5/5; `verificar_alineacion` 0 brechas. **Límite (H-R276-2):** Linux x64/ARM64, macOS y VM Windows limpia no se midieron desde esta máquina; la evidencia quedará en los artefactos `smoke-<plataforma>` del run de CI. **Lección:** un release sin smoke del artefacto que descarga el usuario es un manifiesto de intenciones; el gate tiene que poder fallar y se prueba rompiendo copias. Reporte: `docs/reportes/R276.md`.

**2026-11-20 (ME inventado `r276_hardware_detector` RETIRADO — H-R276-1):** el plan y el oráculo creados en `0426ab4`/`1518eb4` no aportaron código de producción y el oráculo no verificaba nada: devolvía `[OK]` y rc=0 en un directorio vacío, sin `dist/bin/synapse.exe` ni sello (`--estricto: Artifact consistency check passed (no stale stamp)`), con `--mutar` informativo y `--e2e` de «placeholder»; su fila de memoria citaba `docs/reportes/R276.md`, que no existía. Se eliminaron plan y oráculo y se retiró la fila falsa. La detección de hardware y la selección de modelo son reales desde Fase 29 (`runtime/core/detect_hardware.c`, `opensyn/installer.syn`, `std/os.syn`) y están cubiertas por `tests/opensyn/test_installer.py` (1 passed); el id `r276` queda reservado a `r276_multiplataforma_release`. **Lección:** un oráculo que imprime `[OK]` sin medir convierte el gate en teatro; si no puede fallar, no es evidencia. Siguiente del frente: `r276_multiplataforma_release` (P0).
>
**2026-11-19 (FRENTE H — r270b CERRADO, commit 84f67ba):** `r270b_guard_frescura_contenido` cerró H-R252-5: el guard de frescura del oráculo del bootstrap comparaba **mtime** contra `nucleo/principal.syn`, así que un `checkout` o un guardado del editor ponía el sello en rojo con el mismo hash y obligaba a reconstruir la cadena (pasó al verificar r270: fuente 02:26 vs etapa 2 02:19). Ahora el oráculo escribe `synapse_stage2.stamp` con el SHA-256 del contenido de la fuente mediante `--sellar` (invocado por `build.py` y el job `bootstrap` de CI) y certifica por contenido; si la fuente cambió desde el build falla nombrando ambos hashes, y sin sello (checkout limpio) conserva el criterio de mtime con aviso `[WARN]`, por lo que los 13 tests de r252/r270 siguen pasando **sin cambios**. Tests nuevos `test_r270b_frescura_contenido.py` 5/5 (total 18/18 con los existentes); end-to-end sobre artefactos reales: sello `9e72e10c716dfc01…`, `touch` de la fuente y `--estricto` sigue `RC=0`. Gates: `contrastar` 3/3 PASS, `alineacion --verificar` evidencia `907b8c3cf9d31fb5`, `verificar_alineacion` sin brechas, lectura Manual 1 §6 + Manual 9 §6.2 registrada. **Lección:** un guard por mtime mide el reloj, no la procedencia del artefacto; se sella el contenido y lo sella el mismo componente que verifica. Reporte: `docs/reportes/R270b.md`. Siguiente: los MEs r272–r284 del Frente H.

**2026-11-19 (FRENTE H — r270 CERRADO, r271 CERRADO, commits 82fb4c4 + d3613bb):** `r270_bootstrap_emision_paridad` cerró H-R252-1 (stage2 stale: 2.077.570 B era etapa 1 mal rotulada) y H-R252-4 (enlace nativo win32 sin `-static`): `nucleo/principal.syn` añade `_static_flag`, S2=S3 `30C07EF61C5F25A7…` (2.559.482 B), `synapse.exe`/`dist/bin/synapse.exe` al día y `--estricto` PASS. El oráculo ahora compara hash + tamaño y rechaza S2/S3 anteriores a `nucleo/principal.syn`; `build.py` y CI usan el mismo sello. `r271_manuales_canonicos` queda CERRADO: D-MAN-1/2/3 ratificadas (opción A) el 2026-11-19; Manual 31/32 renombrados a `MANUAL 31.md`/`MANUAL 32.md` con alias histórico, anexos como apoyo citable sin número y barrido único de `book2` fijado para r282. `.indice.json` v2 indexa 11 manuales y 3 anexos (395 secciones, 1.649 oraciones); `verificar_manuales.py --todo` pasa y está cableado en pre-commit/CI. Se retiró BOM de 15 docs y se corrigió la cita `Manual 9 §6.1` del workflow. Tests: `test_verificar_manuales.py` 7/7, `test_manuales_canonicos_r271.py` 2/2, `test_r270_bootstrap_paridad.py` 4/4, `test_oraculos_r252` 9/9; `contrastar` r270/r271 PASS; `verificar_alineacion` 0 brechas. Reportes: `docs/reportes/R270.md` y `R271.md`. Commits `82fb4c4` (gate) y `d3613bb` (D-MAN-1/2/3). **Verificación independiente de H-R252-4 (2026-11-19):** al comprobarlo, `--estricto` estaba en rojo por frescura (etapa 2 anterior a `nucleo/principal.syn`, mismo hash); la cadena reconstruida con `build.py --skip-test` reproduce `30c07ef61c5f25a7` / 2.559.482 B, `--estricto` `RC=0`, tests 13/13 y `objdump -p` sólo lista DLL del sistema (sin DLL del toolchain) — el `-static` hace lo que el hallazgo pedía. Se registra **H-R252-5 (BAJA)**: el guard de frescura compara mtime y da falso rojo al tocar la fuente sin cambiar contenido; resolución asignada: sellar hash de contenido en un `.stamp`.

**2026-11-18 (AUDITORÍA CRÍTICA + FRENTE H REGISTRADO):** se auditó la ley, el encoding y los planes. Los 9 manuales de `docs/manuales/` son UTF-8 válido, sin BOM, sin U+FFFD/C1 y sin mojibake real: NO reescribir. La corrupción real estaba en `docs/auditorias/AUDITORIA_ALINEACION_MANUALES.md` (doble codificación; reparada a UTF-8, 1.275 líneas conservadas, 0 U+FFFD/C1) y en ejemplos históricos de `docs/reportes/R205.md`/MEMORIA (normalizados a notación U+). Se creó `docs/gobernancia/POLITICA_MANUALES.md` (invariantes, protocolo D-MAN y gate `verificar_manuales.py`) y `docs/gobernancia/PLAN_MEJORAS_ECOSISTEMA_R270_R284.md` con 15 MEs ejecutables r270–r284; se incorporó como §3.2 Frente H en el Plan Maestro Industrial y como FRENTE H en `docs/plan_maestro_deudas.md`. `r252b_emision_paridad` queda absorbido por `r270_bootstrap_emision_paridad`; H-R252-1 sigue crítico. `verificar_alineacion` 0 brechas. Decisiones D-MAN-1/2/3 pendientes del Arquitecto; sin commit.

**2026-11-18 (R249/r252 PARCIAL - 8aaab43):** ME r252_bootstrap_parity: el sello S2==S3 pasa a ser un oraculo propio (`auditoria/oraculos/oraculo_r252_paridad_bootstrap.py`) con modos `--artefactos` (sha256 etapa 2 vs etapa 3 — lo usan `build.py` y el job `bootstrap` de CI, que deja de duplicar el calculo con `sha256sum`), `--construir` (lanza build.py y compara) y `--estricto` (falla si `synapse.exe` o `dist/bin/synapse.exe` no corresponden a la etapa 2 — el guard que faltaba contra binarios stale). Oraculo NUEVO `tests/auditoria/test_oraculos_r252_paridad_bootstrap.py` 9/9; `contrastar` 3 requisitos PASS; `alineacion --verificar` 1 archivo (evidencia `88cc362b09839fe1`); `verificar_alineacion` 0 brechas. **HALLAZGO H-R252-1 (CRITICO, medido):** el bootstrap NO cierra — etapa 2 `737a4000dabccbea` (2.077.570 B, construida por S1 **modular con `-static`**) vs etapa 3 `b032e2ddc78dd235` (2.558.970 B, construida por S2 **unity sin `-static`**, `nucleo/principal.syn:764`); 2.0 de 2.1 MB difieren, no es ruido de timestamps. Mientras S1 emita modular y S2 unity la regla de hierro de Manual 1 §6 no puede cumplirse; el job `bootstrap` de CI nunca lo detecto porque no se ejecuto con el estado actual de la rama. Registrado en `docs/plan_maestro_deudas.md` con resolucion asignada al ME `r252b_emision_paridad` (unificar la invocacion de GCC de S1 y S2 o decidir la canonica con el Arquitecto). **Leccion H-R252-2:** un gate que solo vive dentro de un script de build no es un gate. Reporte: `docs/reportes/R249.md`. Siguiente: `r252b_emision_paridad` (alta prioridad: sin bootstrap que cierre, todo gate S2 es fragil).

**2026-11-18 (R248/r244 COMPLETADO - a4b6f6d):** ME r244_paridad_lint_fmt_test (pendiente #2 del plan industrial): `lint`/`fmt`/`test` nativos con paridad S1↔S2 sobre Fase 32. D1 (M9 §6.2/M8 §4.1): el parser de `lint` trata como flag todo token con `-` inicial y como ruta el primero sin guion — `synapse lint --check <archivo>` deja de responder "no se pudo leer --check". D2 (M9 §6.2): `lint_doble_espacio` se acota al CODIGO (corta en `//` fuera de literal, recorta el hueco final, maquina de estados de cadenas): los 23 falsos positivos de `router.syn` desaparecen y el corpus queda 15/15 rc=0. D3 (M8 §5.5): el parser de `fmt` usa la misma regla y una ruta ilegible da rc=1 (antes `[Fmt] formato correcto`; `fmt_archivo()` no distingue "sin cambios" de "no se pudo leer"). D4 (M7 §4.3): `ahora_ms_router`/`ahora_ms` emiten `#ifdef _WIN32` con `GetTickCount64` y conservan `clock_gettime` en POSIX, asi que `synapse test` compila, enlaza y EJECUTA un driver que importa `opensyn/router.syn` (antes `'CLOCK_MONOTONIC' undeclared`). Oraculo NUEVO `tests/integration/test_paridad_lint_fmt_test_fase32.py` 10/10; regresion dirigida 89/89; `contrastar` 4 requisitos/1 oraculo release PASS; `alineacion --verificar` 4 archivos (evidencia `1bc8ef6e8cca3984`); `verificar_alineacion` 0 brechas. Binarios regenerados (`synapse_bootstrap.exe` rc=0, copiado a `synapse.exe` y `dist/bin/synapse.exe`). **Leccion H-R244-1:** el filtro del oraculo debe mirar solo lineas con `WARN_LINT`; `[Lint] Sin advertencias` tambien empieza por `[Lint]` y transforma un caso verde en fallo del arnes. **Leccion H-R244-2:** `synapse check` no emite C, asi que un modulo con codigo POSIX sin guarda valida rc=0 y solo rompe al compilar quien lo importa: la paridad de una herramienta se demuestra con `test` (compila y ejecuta), no con `check`. Reporte: `docs/reportes/R248.md`. Siguiente: siguiente ME de la Ola 4 en §3.1 del plan maestro.

**2026-11-18 (R247/r243 COMPLETADO - 379d978):** ME r243_native_fase32 (pendiente #1 del plan industrial): el compilador nativo (S2) valida los modulos de Fase 32 y reporta la causa de cada fallo. R1 (M2 §1.1/§10.2): `lexer_error` imprime linea/columna/mensaje (antes fallaba en silencio) y la directiva `#lang` se evalua normalizando un BOM inicial. R2 (M2 §1.2): BOM UTF-8 retirado de `opensyn/chat.syn`, `opensyn/verificacion_aot.syn` y `nucleo/grafo_conocimiento.syn` (rompia `lexer_detectar_idioma`). R3 (M2 §4.2): `Resultado`/`Opcion` entran a `_prim` (antes `Resultado<texto, texto>` era "tipo no definido"). R4 (M8 §4.2): `fallo_etapa(cod)` traduce el codigo de etapa a causa legible y `cli_check` reporta rc=1. R5 (M9 §6.2): `importar` se resuelve contra el directorio del modulo importador (pila `_dirstk`). Oraculo NUEVO `tests/integration/test_compilacion_fase32_s2.py` 8/8; gate S1 2/2; `contrastar` 6 requisitos/1 oraculo release PASS; `alineacion --verificar` 6 archivos (evidencia 6b9cac6ac1d3cdbc); `verificar_alineacion` 0 brechas. Binarios regenerados (`synapse_bootstrap.exe` 5m50s, copiado a `synapse.exe` y `dist/bin/synapse.exe`). **Leccion H-R247-1:** el oraculo resuelve el binario en orden `dist/bin` → raiz → bootstrap; con `dist/bin` stale "verifica" un binario viejo — refrescar los tres antes del gate. **Leccion H-R247-2:** `mapa_alineacion.md` contiene dos bloques JSON con claves duplicadas y gana la ultima (editar ambas); `Manual 2 §8` no indexa oraciones citables, se ancla en §8.1. Reporte: `docs/reportes/R247.md`. Siguiente: pendiente #2 del plan industrial.

**2026-11-18 (R241/r256 REBANADA 2 COMPLETADA - 3536d48):** ME r256_debugger (r241_debugger): persistencia de posicion entre invocaciones del depurador. debug.c gana `_syn_debug_guardar_traza`/`_syn_debug_guardar_pos`/`_syn_debug_leer_pos`/`_syn_debug_leer_traza` (archivos `.synapse/debug_traza` y `.synapse/debug_pos`); `_syn_debug_cargar_traza` inicializa posicion 0. debug.h declara `_syn_debug_posicion_actual`/`_syn_debug_posicion_guardar`. principal.syn: `--step`/`--reverse` usan posicion persistida. Oraculo test_oraculos_r256_debugger.py 3/3. Gates: evidencia c3be53831d302078, contrastar PASS, verificar_alineacion 0 brechas. Limitacion: funciones C dedicadas (avanzar/retroceder/breakpoint/snapshots) y VS Code siguen pendientes para cerrar r241.

**2026-11-18 (R241/r256 PRIMERA REBANADA COMPLETADA - 0c25e46):** ME r256_debugger (r241_debugger): subcomando synapse debug con --load/--step/--reverse/--snapshots/--help, delegando a runtime C existente (tr_*, rp_*, _syn_debug_cargar_traza nueva en runtime/core/debug.c). Build nativo OK (synapse_bootstrap.exe), binarios synapse.exe/dist/bin/synapse.exe actualizados. Oraculo nuevo tests/auditoria/test_oraculos_r256_debugger.py 3/3 (help, snapshots, load). Gates: evidencia f69654dc0f0870b2, contrastar PASS, verificar_alineacion 0 brechas. Reporte: docs/reportes/R246.md. Limitacion: solo expone primitivos existentes; faltan funciones dedicadas y persistencia de posicion para cerrar r241.

**2026-11-18 (R230 COMPLETADO — commit `fa3349f`):** ME r230_opensyn_contratos_mocks: `opensyn/validation_loop.syn` agrega `ERR_RESPUESTA_VACIA` y `es_codigo_vacio()`; `bucle_validacion_detallado` intercepta la respuesta vacia del LLM (intento inicial y reintentos) antes de `validar_con_check`, cuyo `requiere: longitud(codigo) > 0` abortaba el proceso. `opensyn/pipeline_multiagente.syn` hace lo mismo en `validation_loop_corregir` (entrada y respuesta del Fixer). Los mocks existentes ya usaban codigo invalido no vacio; se agregaron 3 oraculos E2E: vacio inicial, vacio en correccion y pipeline con Coder vacio. Gates: evidencia `6950a8a8421573ce`, `contrastar` PASS (3 requisitos, oraculos en release), `alineacion --verificar` OK, `verificar_alineacion` 0 brechas. Regresion `tests/opensyn`: 136 passed, 1 skipped, 1 failed (`test_installer_opensyn` por timeout de 10 s ante un GGUF local de 873 MB; preexistente y ajeno). Manual 7 §6.3, Manual 2 §5.1, Manual 6 §1.1. Reporte: `docs/reportes/R230.md`. Siguiente: R231 o resolver el timeout del instalador.

**2026-11-17 (R227b COMPLETADO — commit `a76e546`):** hotfix del smoke real de R227: `runtime/core/ollama.c` deja de girar en CPU cuando un CRLF de chunk chunked queda partido entre dos lecturas TCP. `_oll_dechunk` retorna al entrar en fase 5 sin reentrar y `_syn_ollama_stream_leer` lee más red cuando la fase no es 1 (tramas parciales en fases 0/3/4), en lugar de reintentar sobre el byte pendiente. Oráculo nuevo `tests/auditoria/test_oraculos_r227b_stream_chunk_split.py` 1/1 (servidor chunked que envía `payload + \r`, pausa y luego `\n`); regresión R227+R235+R227b 6/6. Gates: evidencia `8d697386e8e7dfef`, contrastar PASS, verificar_alineacion 0 brechas. Smoke real con `llama-server` b10819 + `deepseek-coder-1.3b-Q4_K_M.gguf`: `CONSULTA` y `STREAM` con contenido en 7036 ms; servidor detenido. Manual 7 §2.2. Reporte: `docs/reportes/R227b.md`. Siguiente: chat E2E completo de OpenSyn o R230 con aprobación.

**2026-11-17 (R245 COMPLETADO — commit `92f5298`):** ME r255_lsp_ai (reasignado de r219_lsp_ai): `nucleo/lsp_v3.syn` `handle_ai_status` ahora refleja el servidor real (consulta `_syn_ollama_modelos`); ancla Manual 8 §1.1; `tests/integration/test_ai_commands_opensyn.py` deja de tener los 5 skips TDD (5/5); dispatch 5/5; build LSP OK. Gates: evidencia `a8cbf72acbcb1bfc`, contrastar PASS, verificar_alineacion 0 brechas. Reporte: `docs/reportes/R245.md`. Siguiente: r240_vscode_ai (r256) o r245_e2e_llama_server.

**2026-11-17 (R244 COMPLETADO — commit `a04d424`):** ME r254_sesiones_undo (reasignado de r218_sesiones_undo): cablea `run_manager` al loop vivo de `opensyn/principal.syn` con sesiones reanudables: importa run_manager; helpers `sesion_archivo`/`sesion_run_id_activo`/`sesion_activar`/`sesion_limpiar`/`sesion_marcar_paso`; comandos `/sesion`, `/reanudar`, `/revertir`, `/sesion-fin`; marca cada TOOL como paso en tui_agente; `run_manager.syn` gana `deshacer_ultimo_paso`. Oraculo nuevo `tests/opensyn/test_sesiones_undo_comportamiento.py` 1/1; regresion `test_run_manager_comportamiento` 1/1; build `opensyn/principal.syn` OK. Gates: evidencia `d02e0967b131eb7a`, contrastar PASS, verificar_alineacion 0 brechas. Reporte: `docs/reportes/R244.md`. Siguiente: r219_lsp_ai (r255) o r245_e2e_llama_server.

**2026-11-17 (R217_LOOP_INTEGRACION COMPLETADO — commit R243 (r217_loop_integracion)):** `opensyn/principal.syn` cablea `validation_loop` y `pipeline_multiagente` al loop vivo del agente: importa ambos modulos (retirando las redeclaraciones `externo` de `_syn_ollama_consultar`/`_syn_ollama_modelos` que colisionaban), helper `validar_fuente_si_aplica` que valida con `validar_con_check` tras `TOOL editar/escribir/aplicar_patch` sobre `.syn/.syq` y anexa el resultado para auto-correccion (editar->compilar->corregir), y comandos `/validar` y `/pipeline`. Gates: `main.py opensyn/principal.syn` OK, oraculos `test_validation_loop_comportamiento` + `test_pipeline_multiagente_comportamiento` 5/5, `verificar_alineacion` 0 brechas, `alineacion --verificar` evidencia `5b8fcdeac6889e14`, `contrastar --plan` PASS. Reporte pendiente. Siguiente: r218/r219/r245.

**2026-11-17 (R242 COMPLETADO — commit `616e321`):** el binario nativo despacha `synapse opensyn <sub>` (criterio de cierre 6 del PLAN MAESTRO INDUSTRIAL). `nucleo/principal.syn` gana la rama `opensyn` ANTES del prescan de flags y de `generar_etapa()`: antes `argv(1)=="opensyn"` caía a la pipeline («Compilando archivo: opensyn … Error de compilacion»), así que el producto instalado sin Python no exponía OpenSyn. `opensyn`/`--help` listan los cinco subcomandos de Manual 8 §4.1; `status`/`doctor` delegan en `opensyn.exe` resuelto desde `argv(0)` (una sola fuente de verdad del diagnóstico local, Manual 7 §2.1); `download`/`finetune` y `bindings`/`transpile` fallan con error honesto (servidor `:8088` / toolchain Python) sin fingir éxito; desconocido rc=1. Oráculo nuevo `tests/auditoria/test_oraculos_r242_opensyn_nativo.py` **8/8** (incluye paridad del juego de subcomandos con `cli.py` y guarda de `opensyn.exe` ausente → rc=1); regresión dirigida **71/71**. Gates: evidencia `4437bc919e048bd1`, `contrastar` 2 requisitos, `verificar_alineacion` 0 brechas. **Lección:** en este repo `%%s` dentro de `asm()` emite un `%s` LITERAL (el bloque `axon` lo sufre hoy: `synapse axon` imprime «Uso: %s axon fetch»); en C embebido hay que usar `%s` simple. Reporte: `docs/reportes/R242.md`. Siguiente: `r217_loop_integracion` o `r219_lsp_ai`.

**2026-11-17 (reconciliación del PLAN MAESTRO INDUSTRIAL):** `docs/gobernancia/PLAN_MAESTRO_INDUSTRIAL.md` gana §3.1 con el estado real ME a ME verificado con comandos (no estimado): Frente A CERRADO (r205-r212 + r213→r219 + baseline vacío y `test_compilacion_fase32.py` 2/2), Frente B 2/4 (r217/r218 no cableados: `validation_loop`/`pipeline_multiagente` no se invocan desde ningún principal), Frentes C-G 0/3,0/3,0/4,0/3,0/2 con detalle PARCIAL/HECHO. Pruebas directas usadas: `synapse opensyn status` y `synapse doctor` fallan en el nativo (tratan el subcomando como archivo), 5 `pytest.skip` siguen en `test_ai_commands_opensyn.py`, `instaladores/{linux,macos}` + matriz CI existen sin evidencia de ejecución. Criterios de cierre §5: 1 y 3 cumplidos, 2/4/5/6/7/8 abiertos, 9 a medias. Lección: el plan quedó desfasado porque los ids r218/r219 se consumieron con otros MEs (bootstrap_json, verificacion_aot) — antes de retomar hay que reasignar ids libres.

**2026-11-17 (R237 COMPLETADO — cierra H-R234-2, commit `7c7382b`):** el instalador de Windows empaqueta el toolchain C. `instaladores/windows/empaquetar_toolchain.py` (nuevo) stagea el subset mínimo de MinGW en `instaladores/windows/dist/toolchain_gcc12/mingw64` (**3836 archivos, 300 MB** de los 936 MB del toolchain completo: gcc, as, ld, dlltool, cc1, collect2, liblto_plugin, DLLs del compilador, `x86_64-w64-mingw32/{include,lib}` y `lib/gcc`) y se autoverifica compilando+ejecutando un C con PATH = bin staged + System32. `synapse.iss` gana el componente `toolchain` (Types: full minimal) + `[Files]` hacia `{app}\toolchain_gcc12\mingw64` (el directorio que `nucleo/principal.syn` busca desde `{app}\bin`), y `scripts/install.ps1` deja de pedir MinGW: verifica el toolchain incluido. **Lección:** `cc1.exe` vive en `libexec/gcc/<triple>/<ver>/` y Windows busca DLLs primero en el directorio del ejecutable — con las DLLs sólo en `bin/`, gcc devuelve rc=1 sin mensaje y cc1 muere con `0xC0000135`; hay que copiarlas junto a cc1. Oráculo nuevo `tests/auditoria/test_oraculos_r237_instalador_toolchain.py` **4/4** (subset completo, compilación+ejecución, `{app}\bin\synapse.exe` compilando `e2e_hola.syn` con el toolchain incluido y PATH=System32, y validación estática del `.iss`). **Prueba real:** ISCC 6 compiló el `.iss` (setup 336 MB con `Compression=none`) y `Synapse-...exe /VERYSILENT /COMPONENTS=toolchain` instaló un gcc que compila y ejecuta sin gcc del sistema. Gates: `alineacion --verificar` evidencia `7b4be78d842ad19e`, `verificar_alineacion` 0 brechas, `contrastar --plan` PASS; `mapa_alineacion.md` gana entradas puntuales (`empaquetar_toolchain.py`, `install.ps1`) porque el fallback `*.py → Manual 1` (sin sección) lo rechaza el gate. Reporte: `docs/reportes/R237.md`. Queda el paso 2 de R234: VM Windows limpia con el setup completo.

**2026-11-17 (R236 COMPLETADO — cierra H-R234-1):** `nucleo/principal.syn` resuelve el compilador C antes de invocarlo: `SYNAPSE_GCC` → `gcc.exe` junto al binario → `tools\mingw64\bin` → `mingw64\bin` → `..\toolchain_gcc12\mingw64\bin` → `..\..\toolchain_gcc12\mingw64\bin` (checkout) → PATH como último recurso, y antepone el directorio resuelto al PATH del proceso hijo (una sola vez). Lección: citar el ejecutable entre comillas en el primer token rompe `cmd.exe` cuando le siguen `-I"."` y rutas citadas (`El sistema no puede encontrar la ruta especificada.`), así que el comando sigue invocando `gcc` sin comillas y lo que se ajusta es el PATH. Con PATH reducido a `System32`, `dist/bin/synapse.exe` compila `e2e_hola.syn` y el binario imprime `Hola Mundo`. Oráculo nuevo `tests/auditoria/test_oraculos_r236_toolchain_gcc.py` **3/3** (checkout sin gcc, layout de instalador con `..\toolchain_gcc12` por enlace de directorio, precedencia de `SYNAPSE_GCC` inválido). Gates: `alineacion --verificar` evidencia `4871e66aeb5e856c`, `verificar_alineacion` 0 brechas, `contrastar --plan` PASS. `nucleo/principal.syn` pasó a 1244 líneas → registrado en D-9 (`docs/decisiones/MODULOS_D9.md`). Reporte: `docs/reportes/R236.md`. Seguimiento **H-R234-2:** el instalador sigue sin empaquetar MinGW.

**2026-11-17 (R234 EN CURSO — paso 1 de 4 entregado):** arnés de certificación de usuario final `tests/e2e/test_smoke_usuario_final.py` **7/7** usando SOLO `dist/bin` (sin `main.py`): `synapse --version` y `synapse check` con PATH reducido a `dist/bin`+`System32` (autonomía de Python), compilación+ejecución de `e2e_hola.syn` (`Hola Mundo`) y de `examples/syquex/04_resultado.syq` (`10/3 = 3`), `opensyn --version`/`status` (OpenSyn 1.1.0, servidor y modelo locales, sin endpoint remoto) y `synapse_lsp.exe` respondiendo `initialize` (`capabilities`, `synapse-lsp-native 0.3.0`). Reporte: `docs/reportes/FASE_32_CERTIFICACION.md`. **Hallazgo H-R234-1 (ALTO):** `dist/bin/synapse.exe` busca `gcc` en el PATH y no resuelve `toolchain_gcc12/mingw64/bin`, así que en máquina limpia sin MinGW se puede `check` pero no compilar; el arnés falla explícito (`_exigir_gcc`). Pendiente: instalador silencioso en VM limpia, cierre de H-R234-1 y Manual 7 §7.3 (conexiones salientes + permisos mínimos); ambos requisitos marcados NO CUMPLE (parcial) en `docs/verificacion_ME_r234_certificacion_usuario_final.md`.

**2026-11-17 (R235 COMPLETADO — commit `c04c9f0`):** `runtime/core/ollama.c` agrega `_oll_contenido_util()`: un `content`/`completion` solo con blancos o marcadores de plantilla (`<|im_end|>`, `<|im_start|>`, `<|endoftext|>`, `<|eot_id|>`, `<|EOT|>`, `<s>`, `</s>`) ya no cuenta como respuesta, así que `_syn_ollama_consultar` sí reintenta `POST /completion`; el fallback Ollama `/api/chat` devuelve cadena vacía si tampoco hay texto útil. Oráculo nuevo `tests/auditoria/test_oraculos_r235_fallback_blanco.py` 3/3 (blanco, marcadores, texto real sin fallback); regresión oráculo R227 2/2. Gates: `verificar_alineacion` 0 brechas, `alineacion --verificar` evidencia `8bffa132a1f1f3df`, `contrastar --plan` PASS, pre-commit (MTO 55, lectura, header) OK. Smoke REAL con `llama-server` b10819 + GGUF instruct y la plantilla vacía que reproducía el defecto: probe `CONSULTA:Hola!` (antes dos saltos), proxy ve `/v1/chat/completions` → `/completion`, y el chat de `dist/bin/opensyn.exe` responde contenido en lugar del error. **H-R221-1-R1 RESUELTO y H-R221-1 CERRADO.** Reporte: `docs/reportes/R235.md`.

**2026-11-17 (SMOKE REAL R227 / H-R221-1 — NO CERRADO):** `llama-server` b10819 real + GGUF `deepseek-coder-1.3b-Q4_K_M` sobre :8088, con probe compilado por el pipeline real y un proxy TCP que solo registra paths. (a) REFUTADA la hipótesis del GGUF base: `general.name = deepseek-ai_deepseek-coder-1.3b-instruct`. (b) Configuración distribuida: consulta por `/v1/chat/completions` con texto limpio, streaming por `/completion` con prompt `### System/Instruction/Response` (`ESTADO:0`, `ERROR:` vacío); con `dist/bin/opensyn.exe` regenerado (estaba STALE del 2026-11-15) el chat conecta y responde. (c) HALLAZGO NUEVO H-R221-1-R1 (ALTO): si `/v1/chat/completions` devuelve `content: "\n\n"` (defecto original reproducido con `--chat-template-file`), `_syn_ollama_consultar` lo acepta por `longitud > 0` y **no** reintenta `/completion`; el chat de usuario muestra "[Error] No hubo respuesta del servidor IA local". Fix propuesto (recortar blancos/descartar `<|im_end|>` antes del fallback) asignado al **ME r235_fallback_blanco**; `runtime/core/ollama.c` quedó intacto. Registro: `docs/reportes/R227_smoke_real.md` + fila de deuda en `docs/plan_maestro_deudas.md`.

**2026-11-17 (R227 COMPLETADO — commit `24a7feb`):** `runtime/core/ollama.c` reintenta `POST /completion` cuando `/v1/chat/completions` devuelve contenido vacío por plantilla ChatML; normaliza el prompt instruct (`### Instruction`/`### Response`), extrae `content`/`completion`/`error`, y el streaming usa `/completion` hasta `stop:true`. Oráculo mock 2/2; regresión dirigida 26 passed/1 skipped; E2E `e2e_hola.syn` compila y ejecuta. Evidencia `562bf8f4ab0371e0`; `contrastar` PASS, `alineacion` PASS, `verificar_alineacion` 0 brechas. Límite: no se levantó `llama-server` real; H-R221-1 queda parcialmente resuelto hasta el smoke real con GGUF instruct.

**2026-11-17 (R229 COMPLETADO — commit `6a5176b`):** `pipeline.py` ya no crea caché persistente fuera de `~/.synapse/cache/`; si no es escribible avisa y compila en `build/obj/runtime_ephemeral` con memo en proceso. `tests/unit/test_cache_fallback.py` 3/3; `test_cache_audit` 4/4; `test_release_flags`+`test_cache_adv_10` 18/18; E2E `e2e_hola.syn` compila y ejecuta. Gates: `contrastar.py --plan docs/plan_ME_r229_cache_resiliencia.md` PASA (tras desstagear temporalmente `runtime/core/ollama.c` de R227 para evitar falso cruce de planes), `verificar_alineacion.py` 0 brechas, `alineacion.py --verificar` evidencia `72f57ee447e56c67` (re-sellada tras corregir la cita inválida `Manual 9 §9.5` del probe de sanitizers a `Manual 9 §6.1`). Correcciones de citas: `Manual 9 §9` no existe (Manual 9 termina en §7); `Manual 1 §9` es “SIGUIENTES PASOS”, no empaquetado; `Manual 7 §7.3` sí existe. Planes R229 y R234 corregidos (`Manual 9 §1`, `Manual 1 §3.1`, `Manual 9 §7`). R227 se cerró después en `24a7feb`; siguiente: R230 con aprobación para tocar mocks/tests.

**2026-11-16 (Plan Maestro de Mejoras R229-R234 REGISTRADO):** Se formula e incorpora a repositorio el plan de continuidad, robustez y certificación final en `docs/plan_MEJORAS_ARQUITECTURA_R229_R233.md`: R229 (resiliencia de caché), R230 (normalización contratos/mocks), R231 (subfase 32.5 auto-refutación por contratos AST), R232 (subfase 32.6 RAG con memoria cifrada y firma AST), R233 (driver nativo en `synapse.exe`), y **R234 (certificación E2E y smoke test de usuario final en máquina limpia**, `docs/plan_ME_r234_certificacion_usuario_final.md`, Fases 30 y 32.8). Registrado también en `docs/plan_maestro_deudas.md`.

**2026-11-15 (R222b COMPLETADO - regresion funcional R222):** `ebc1dd6` elimina los helpers de texto duplicados en `opensyn/router.syn` y `nucleo/lsp_v3.syn` que R222 dejo en conflicto con `std.texto`; vacia el baseline de Fase 32. `test_compilacion_fase32.py` 2/2, oraculo R222b 3/3, `build.py` S2==S3 `327fc514adb5`, unit+syquex 795 passed/1 skip/0 fail, dirigida router/LSP/contratos 57/57. Evidencia `74f53ae26613e627`; gates 0 brechas. El plan industrial fue renumerado r220-r233 -> r240-r253 para eliminar colisiones con la cola de deuda. Smoke operativo: `stage2 check` router/lsp rc=0; `e2e_hola.syn` y `examples/syquex/04_resultado.syq` compilan y ejecutan; LSP nativo responde `initialize`; `synapse opensyn` nativo sigue ausente (r242). Distribucion firmada (`SIGNATURE_VALID=YES`, SHA `327fc514adb5`), `dist/bin` refrescado e instalador Windows recompilado; `opensyn doctor` rc=0 tras instalar `llama-server` b10819 en `dist/opensyn/ia`; `/v1/models` y `/v1/chat/completions` responden y `opensyn status` detecta el servidor activo. Hallazgo H-R221-1 (R227): el GGUF local parece base/no-instruct y `_syn_ollama_consultar` devuelve vacio por `<|im_end|>` inicial; falta validar con el GGUF instruct correcto.

**2026-11-15 (R220/R222/R223 COMPLETADOS):** `1319d82` R220 harness PATH/FFI dirigido (oraculo 4/4; 15+4+38+11 GREEN); `805ab8d` R222 `std/texto.syn` restaura 7 envoltorios con contratos y `contiene` con `requiere: verdadero` sin revertir H-R196-1 (contratos 20/20, oraculo 4/4); `63aefa3` R223 fix doble en Syquex: `importar std` sin punto leia `nodos[sub]` sin inicializar y `T_CANAL` no era primario (`sq_args(-1)`), cerrando 10 RED (concurrency 5/5, result 5/5; unit+syquex 795 passed/1 skip/0 fail); `af8e0e6` sella evidencia. `tests/auditoria` 230: run completo >30 min; 6 RED ambientales/prexistentes (exe stale, OpenSyn sin GGUF, contrato `_resultado_`) asignados a R226/R227/R228. Gate de lectura exige lecturas del dia: las de 11-14 no cubren commits del 15.

Última actualización: **2026-11-13** (R219 26e4cf8 COMPLETADO - ME r219_verificacion_aot: validacion AOT con auto-refutacion real, `synapse check --no-emit` + hasta 5 casos, H-R219-1/H-R219-2 resueltos (`_syn_strcpy` en `sha256_texto` y copia en `elemento_texto`), oraculo E2E nuevo 2/2 + estructural 13/13 = 15 passed, gates 0 brechas, evidencia c0a201a1ecbe7d72; antes R216 7adc440 COMPLETADO - ME r216_tool_ejecutar: TOOL ejecutar con allowlist y timeout, Windows CreateProcessA/POSIX execvp sin shell, oraculo nuevo 4/4, regresion 49/49 + control 24/24, gates 0 brechas, evidencia 36ff59676065b465; antes R215 c1d051d COMPLETADO - ME r215_tool_patch: TOOL aplicar_patch con sandbox y aprobacion, parser de diff unificado, oraculo nuevo 3/3, regresion escritura+permisos 46/46, gates 0 brechas; antes R218 e2ec33f COMPLETADO - ME r218_bootstrap_json: bootstrap S2 con std.json/std.texto y buffer de emision de 4 MB, inferencia nativa OpBinaria/llamadas/acceso a campo, S2==S3 sha 950AA09B...A71B2A, 16/16 oraculos de auditoria, gates 0 brechas; antes R217 6497e80 COMPLETADO - ME r217_integracion_determinista: pipeline reutiliza explorer/architect deterministas, probe modular con ambos imports, pipeline existente + E2E 16/16, architect existente + E2E 12/12, gate Fase 32 2/2, regresion combinada 114/114; antes R211 b3180ed COMPLETADO - ME r211_architect_det: architect determinista compilable con DFS invertido, contratos criticos, ciclos y metricas, oraculo E2E 1/1, gate Fase 32 2/2, regresion combinada 114/114; antes R210 990aedb COMPLETADO - ME r210_explorer_det: explorer determinista compilable con BFS, oraculo E2E 1/1, gate Fase 32 2/2, regresion combinada 102/102; antes R209 3064d40 COMPLETADO - ME r209_router_chat: router y chat compilables con extraccion/validacion de codigo, oraculo E2E 1/1, gate Fase 32 2/2, regresion 75/75; antes R208 95ea023 COMPLETADO - ME r208_run_manager: run manager reanudable con checkpoints, timeout y límites, oráculo E2E 1/1, regresión de runs 70/70, gate Fase 32 2/2; antes R207 a578e03 COMPLETADO - ME r207_pipeline_multiagente: pipeline compilable y E2E con LLM y compilador real, oráculo E2E 1/1, pipeline existente 15/15, gate Fase 32 2/2; antes R206 7f17dec COMPLETADO - ME r206_validation_loop: bucle de validación y corrección automática con compilador real, oráculo E2E 4/4, regresión 85/85; antes R205b 5935a5d COMPLETADO — ME r205b_lsp_v3: reparación de compilación, ownership y protocolo del LSP nativo, 13 tests verdes; antes R205 b1e9959 COMPLETADO — ME r205_grafo_conocimiento: grafo de conocimiento real desde AST canónico, determinista, con persistencia JSON y oráculo E2E; antes R204 f018957 COMPLETADO — ME r204_tools_escritura: TOOL escribir/editar con sandbox y aprobación, gate de compilación Fase 32; antes R203 d865ab9 + R202 f1a4a02 + R201 c653fff + R200 f3b7268, ver dashboard; antes R199 a2d0ca3 + r198b3; antes R196 ME r196_deuda_contrato_y_cobertura d022ad8 COMPLETADO —
 cierre de los 2 fallos DETERMINISTAS del barrido r195 (1569✓/25skip/6✗;
 los 5 del grupo A pasaban aislados, infra del barrido):
 (R1/H-R196-1 decisión Arquitecto ratificada "corregir contrato al manual")
 std/texto.syn: retirado `requiere: longitud(subcadena)>0` de contiene/indice_de
 (4 sitios — las 12 funciones del std están DUPLICADAS en 2 bloques completos,
 H-R196-2; el emisor deduplica a 1 def C y la última copia gana, verificado en
 el C generado); M8 §1.7.3 declara los bindings SIN precondición y la cláusula
 del barrido r192 abortaba rc=127 ("Fallo en contrato: requiere") con subcadena
 vacía; E2E: contiene("hola","")→1, indice_de("hola","")→0; test_string_utils
 13/13. (R2) cobertura S1 44.719%→51.228% ≥45% (test inmutable
 test_syquex_coverage::test_cobertura_total_minima, verificado aislado rc=0)
 con tests NUEVOS tests/syquex/test_sandbox_cover_r196.py (probes .syn por el
 pipeline real: sandbox H-CFG-2 leer/existe dentro-fuera + builtins de texto;
 +538 stmts cubiertos); oráculo NUEVO r196 4/4; gates MTS: expediente sellado
 (re-sello cambio_hash contra el INDEX tras normalización CRLF del add —
 lección d948cab: cmd_verificar auto-escribe el hash en el working tree y el
 hook lo compara contra el index), contrastar RC=0 2× en hook hook,
 verificar_alineacion SIN BRECHAS, gate de lectura exige la cita EXACTA del
 MAPA (Manual 2 §5.1 para std/texto.syn, no la del requisito M8 §1.7.3);
 deudas NUEVAS a cola maestro: H-R196-2 (dedupe std/texto.syn), H-R196-3
 (frontend Syquex SEGFAULT 0xC0000005 compilando .syq con
 Resultado/err/ok/abrir/atrapar — 10 fallos del medidor de coverage
 test_result×5 + test_concurrency×5 — tests/syquex está FUERA del barrido de
 integración; repro aislado "Formato canónico no reconocido"; familia H-R182b);
 lección: no filtrar output de background por tail (se perdieron 7 de 10
 FAILED del medidor hasta el re-run; logs/media_coverage_r196.log completo);
 reporte docs/reportes/R196.md. antes: (R183e ME h_canon_let 643b413 COMPLETADO —
 cierre del bug H-canon-LET: el serializador canónico
 `compilador/canonical.py` pisaba la llave discriminante "tipo" del
 JSON con la anotación del `let` (round-trip .syn.json corrupto);
 fix: anotación viaja como `tipo_annot` en paridad con
 nucleo/ast_nodes.syn:83 — Manual 2 §13; 6 asserts codegen alineados a
 M2 §13, 2 asserts débil<T> al runtime real Fase 23 WeakRef (Manual 4
 §4.2) por autorización Arquitecto regla 5 + 1 aserción de cuerpo
 @export al patrón Lifetime Scope; mapa_alineacion con entrada puntual
 canonical.py→M2 §13 (H-R183e-1 RESUELTA: entrada puntual en
 mapa_alineacion (canonical.py→M2 §13) + mapa legacy
 `compilador/*→Manual 1` documentado como FALLBACK in situ
 (mecanismo previsto por mapa_alineacion; sin cambios de
 conducta del gate; verificador SIN BRECHAS tras el comentario));
 verificación: f1d 8/8 (2 E2E S2 ~222 s), vecinos 46✓, gates MTS
 (contrastar PASA 3 requisitos, expediente h_canon_let 0 brechas
 evidencia ad34c2eb084787cf, verificar_alineacion SIN BRECHAS,
 lectura M2 §13/M1 §3.1 del día); lecciones: M2 §13 indexa solo prosa
 (el JSON del ejemplo va citado en el plan MTS), el parser del
 expediente limpia solo comillas dobles, --verificar no reescribe el
 cambio_hash (tras editar producción: hash a mano + re-sello), las
 lecturas del día se exigen por working tree no por staged, pre-commit
 con oráculos 2× excede 600 s → commit en background;
 reportes docs/reportes/R190.md + R191.md (mandato deuda-cero
 2026-10-18, commits 78b8947/621051a — COLA CERRADA: R190 debug CLI M8
 §3.4: ayuda rc=0 sin sesión, navegación sin traza rc≠0 contrato r150,
 tests con traza TRACE v1 real — conflicto de dos tests resuelto por
 mandato TDD: el oráculo inmutable r150 codifica el manual y el test de
 integración se alineó; lección: sello .antes.json con el nombre del
 ME derivado del plan no el alias; sesiones debug globales → patrón
 respaldo/limpiar/restaurar. R191 deuda cero del lote baseline: pgo
 aserción al rc de ley 1c1044c (principal→42), checker S1 aplica M2
 §9.3 (retornar &local → MISMATCH con línea §10.1; retorarnar x de &T
 con tipo crudo —el auto-deref M4 §4.2 no aplica en posición de
 retorno—; rastreo de préstamos por llamadas _locales_vivos/_refs_de;
 consumo por valor de prestado → MISMATCH), ErrorCodes LIFETIME
 completos + plantillas 6 idiomas; federated con `nulo` canónico M2
 §4.3 (7 sitios); lecciones: doblefuente de verdad (strings vs enum)
 viola la taxonomía única, sello stale tras editar producción →
 re-sello '#', cada archivo producción cita una sección del plan
 (R187), --nuevo 'sin archivos de producción' no impide que el hook
 exija el expediente); expedientes 63f5b931dae/94adcc427ab93c59;
 antes:
 reporte docs/reportes/R189.md (r188b 2202cce COMPLETADO 2026-10-17 —
 H-R188-2 CERRADA: codegen NATIVO del receive-modo-resultado M5 §3.6
 con paridad S1: parser_sentencias.syn re-wrapea sujeto como
 NODO_RECIBIR_CANAL, monomorfizacion.syn R24 ADT builtin
 Resultado/Opcion + ctors ok/err (paridad context.py) +
 gen_emitir_str_typedef_instancia (M2 §12), nodos_flujo.syn instancia
 Resultado<elem,texto> + typedef + flag _G_co_modo_resultado,
 expr_eval.syn statement-expression canal_recibir(...&_ce0) con
 {.tag=0,.dato.ok=_unbox}/{.tag=1,.dato.err="canal cerrado"}, global
 único orquestador+generator_constants+generator.py (H-R151-3); hallazgos
 en vuelo H-r188b-1/2/3 cerrados: typedef de la instancia DENTRO del
 bloque del coincidir (el pre-bloque D-2 no ve el tipo invisible), temp
 _mv_r única, global compartido unity↔python; oráculo
 test_oraculos_r188b.py 3/3 (nativo ok=7/cerrado-2 con ok-2 inalcanzable,
 histórica sin regresión — la declaración del usuario gana sobre el
 builtin R24, paridad S1 misma salida); bootstrap S2==S3 2534e776…;
 regresión 15/15; unit 514✓; expediente r188b 0 brechas (evidencia
 c661ce1d660ed5b4, cambio_hash sobre blobs staged); contrastar RC=0;
 verificar_alineacion SIN BRECHAS; lecciones: verificacion_ME_<id>.md
 exige LÍNEA 'Manual N §S … CUMPLE' (encabezado ## no matchea el hook),
 contratos dentro de las 25 líneas POSTERIORES a la definición de la
 función, el hook del pre-commit elige el ME activo del PRIMER
 plan_ME_*.md stageado alfabéticamente (stagear SOLO el plan del ME en
 curso en el commit de producción; el plan de cierre del ME previo va al
 commit de docs), cita del expediente = oración literal indexada
 (paráfrase → brecha);
 reporte docs/reportes/R188.md (r188_deuda_cero_1 9f6b1cd COMPLETADO
 2026-10-16 — H-R184-1 CERRADA en S1: flecha opcional M5 §3.6 con
 desugar minimalista: ast_nodes campo modo_resultado, parser_control
 TokenID.ARROW opcional, semantic_types Resultado<elem,texto>,
 context.registrar_instancia_adt + emit_control sujeto/typedef/
 compound + emit_expressions canal_recibir(&&ce0) ADT; oráculo
 test_oraculos_r188_deuda_cero_1.py 4/4 (E2E ok=7/cerrado-2, histórica
 sin regresión); nucleo/parser_sentencias.syn+lexer.syn paridad de
 ENTRADA (stage1 rc=0); foco 65✓, unit 514✓; expediente evidencia
 a2bbf48eec3e5708/2afa8c33ad689160 0 brechas; H-R188-1 native → r188b
 (codegen nativo rc=5, sujeto ADT); lecciones: ancla literal ±3,
 cambio_hash se sella sobre BLOBS STAGED (add-posterior invalida),
 re-sello = cambiar expediente e --verificar tras el último git add,
 lecturas del día COMA-separadas y re-registro al cruzar medianoche,
 pre-commit oráculos 2× → commit en background); antes: (2026-10-11 R183d ME
 f14_mto_ci 75dc6cf (R187, 2026-10-14) COMPLETADO — cierre del lote en vuelo de la sesión anterior: F1.4 check de cuerpo tras 'funcion:' en el PARSER (M2 §2 L56/L60, rc=1 firma sin cuerpo; _validar_cuerpos del lexer eliminado, M1 §3.1); release_matrix.yml real (4 SOs, SHA-256, SBOM, firma, SLSA) + build.py S2==S3 determinético + distribuir.py sellado; fixtures canónicos M2 §13; paridad emisor embebido H-R181-3 (emit_selfhost fallback kw-identificador con exclusiones); harnesses paridad RAIZ+stubs; oráculo executor 20/20+2/2; contrastar RC=0 en el hook; expediente 0 brechas evidencia e1df969a904e3db5; H-R187-1 (preexistente): '(' abierto en firma malformada suprime NEWLINE/INDENT del resto del archivo (r153); lección: parsear_plan toma solo la PRIMERA sección del bloque requisito (el archivo cita su sección en 1ª posición); cambio_hash stale tras editar producción (procedimiento d948cab); pre-commit oráculos 2× → commit en background. Reporte docs/reportes/R187.md; antes: (r183d_flags_debug 0528b7a COMPLETADO — cierre de los hallazgos UX de R182c: (1) synapse.exe --version/--help rc=0 (versión desde archivo VERSION, REAL-1) y prescan de flags --target/--release/--debug/--safe/--output/-o ANTES de tratar argv(1) como archivo (REAL-4b "Archivo no encontrado: wasm"); (2) fallback de salida `<archivo>.exe` NUNCA synapse_stage2.exe (compilar sin -o ya no destruye el compilador autoalojado); (3) --debug en ambos backends: MinGW-w64 no distribuye libasan/libubsan → detección con probe de LINK real (compilar miente, linkear no) + degradación documentada a -O0 -g (Manual 9 §6.1; arqueología de la cita fantasma §9.5: M9 va hasta §7); oráculo NUEVO oraculo_r183d.py 11/11 PASS + oraculo_determinismo_r183d.py; bootstrap S2==S3 byte-identical sha c3231f34; unit+syquex 793 passed; gates: expediente 0 brechas evidencia bf54ba579129ed4c, contrastar PASA, verificar_alineacion SIN BRECHAS; lecciones: detector de sanitizers con probe de link (TDM 10.3 y MinGW 16.1 aceptan -fsanitize pero el ld falla), el fallback de la salida de un compilador autoalojado NO puede ser el propio compilador, citas fantasma del expediente se re-anclan a la sección REAL del manual (grep "^## "/"^### " del manual antes de citar); antes: (R182c ME r182c_canal_vivir 057d072 COMPLETADO — pruebas de operación como usuario real hallaron H-R182c-1: el programa canónico M3 §8.1 de canales compilaba rc=0 pero ejecutaba basura (1933533161441) + segfault rc=139 — causa raíz: cleanup final emitia canal_destruir INcondicional para canales cedidos a fila/listener (use-after-free); fix: set _channel_vars_cedidas + marcar en visitar_escuchar/visitar_lanzar + filtro en cleanup (oráculo oraculo_r182c.py PASS, 42/100 rc=0); hallazgos UX adicionales: synapse.exe --version/--help rc=2 (dispatcher nativo no implementa flags), --target wasm solo tras subcomando build; lecciones: el cleanup RAII global de un lenguaje de propiedad=manual necesita mirar la cesión (transfer de ownership), las pruebas usuario E2E destapan bugs que las suites de compilación no (rc=0 ≠ funciona); antes: (R182b ME r182b_frontend_para_rango 24d3912 COMPLETADO — H-R182a-1 CERRADA (deuda 1F+9E test_traductor/test_concurrency desde c2cd52e): el frontend Syquex segfaulteaba compilando .syq con bucles `para` de rango (para i en 0..n / para i = a..b paso p) — causa raíz: los 5 literales sintéticos del desugar ("__init__", paso 1 ×2, "<", "+") fijaban ptr_str/len_str pero NO los bits altos en sq_tokens_hi[n], y el emisor JSON reconstruye el span como hi<<32|ptr → dirección inválida → segfault; fix paridad con _SQ_SELF (L768): 5 sitios escriben hi=(int)((uintptr_t)_X>>32); regresión tests/syquex 279 passed / 1 skipped; oráculo NUEVO auditoria/oraculos/oraculo_r182b.py PASS; expediente 0 brechas evidencia 37994ff3735a2c44.json; contrastar PASA; verificar_alineacion SIN BRECHAS; lecciones: buscar el patrón canónico del mismo archivo (hi já se escribía para _SQ_SELF) antes de replicar un bug; canal <- i era incidental (el test lo usa DENTRO de un para con rango); antes: (R182a ME r182a_wasm_f25_funcional 0c74d80 COMPLETADO — Fase 25 "genera WASM válido" OPERATIVA de punta a punta (M1 §3.2/M8 §4.2): levantamiento reveló que los "3 RED del plan" ya verdes (test C autocontenido no cubre el pipeline); RED REAL confirmado compilando probe .syn --target wasm y validando con wat2wasm (emsdk wabt 1.0.39 fuera de PATH) — el WAT emitía call sin import, sin locals, sin drop, result nulo->i32 sin retorno: todo módulo rechazado; fix: wat_generator con _firma_llamada_externa (import "env" automático determinista por primera aparición), _declarar_locals recursivo, drop en llamada-sentencia, export principal/main, nulo sin result, default inalcanzable con result (implicit return de WASM), fase 1/2/3 en generar() (imports ANTES de toda definición, incluso memory), pipeline resuelve wat2wasm en emsdk; oráculo NUEVO test_oraculos_r182a_wasm_valido.py 4/4 (wat2wasm rc=0 + magic 0asm + determinismo byte a byte 986b7154dc1b318f ×2); unit 514✓; lecciones: ancla "cumple Manual N §S" literal ±3 de la evidencia (5 brechas 1er intento por evidence drift), las oraciones del Generador viven en M1 §3.2 NO §5 (cita textual por buscar_seccion), contrastar exige "oraculo: <ruta>" como primer token, "--target wasm" escribe artefactos junto a la FUENTE; H-R182a-1 NUEVA (1F+9E pre-existente test_traductor/test_enviar_canal, bisección por stash en c2cd52e) → ME cola R182+; antes:  (R183 ME r183_coincidir_bloque_nativo 70ca347 COMPLETADO — H-R180-1 CERRADA: 2+ casos con cuerpo-bloque en coincidir nativo con paridad S1 (M3 §3) — el anti-cuelgue R11 del bucle de casos corría tras un caso parseado y se comía el DESINDENTAR del bloque (b4: `funcion principal` expuesto como def anidada → rc=1 "DefinicionFuncion no reconocido") o el patrón numérico del caso siguiente (b1/exotic → rc=8); b2/b5/b3 pasaban POR AZAR; fix: flag caso_parseado — anti-cuelgue solo si la iteración no produjo caso; oráculo NUEVO test_oraculos_r183_coincidir_bloques.py 7/7 con RED 5/2 confirmado (bug del propio oráculo: f(2)=2*20=40, derivar la salida del programa no de la nota); bootstrap S2==S3 d8493487…397a944 (exe fresco: el sello determinista no cambia con comentarios); expediente huella 19d51d2bf8e46079; MTO OBL-M3-07; unit 510/510; lecciones: el expediente M2 §1.3 auto-generado exige ancla literal ±3 líneas (cita honesta del estilo de comentario), el índice de M3 §3 no contiene bloques EBNF (precedente R180 cita la prosa), editar producción tras --verificar muta el blob → re-sellar ~9 min (planificar ediciones ANTES), pre-commit excede 600 s (oráculo 2×) → commit en background, commit interrumpido deja COMMIT_EDITMSG previo (verificar git log antes de reintentar); antes: R184-R186 ME r184_r185_e2e e4e4022 COMPLETADO — H-R181-3/H-R181-4/H-R186-1/H-R181-1/H-R188-1 CERRADAS en un ME de front+codegen+runtime: lexer keyword+':' degrada a identificador con literales excluidos (H-R184-1a detectada por el propio bootstrap: 263 errores 'verdadero no declarada'), mangle _syn_usuario_ de colisiones stdlib con tabla paridad 50 (falta de _G_native_funcdefs en preámbulos Python detectada por el enlace del bootstrap), _syn_texto_duplicar para literales→RAII texto, params struct ownership en PRÉSTAMO (doble free 0xC0000374 diagnosticado con bisect toml_dbg+stub), conftest rt_objs pre-colección; lecciones: indentación .syn ES estructura (8→4 espacios = 248 errores asm cascada, H-R184-3), .o del runtime core viven en la RAÍZ y mtime stale salta recompilación, oráculo propio tenía bug de regex contra comillas escapadas del asm (H-R184-2a), expediente MTS: sección '?' → DESVIACION con correccion sobre el frente opuesto S1↔nativo, contratos garantiza con 'es' dan E-703 (usar ==), gate de lecturas exige cita por archivo según mapa_manuales y --archivos con comas; oráculo 5/5 (212 s); bootstrap S2==S3 cdcc5262…ac4600; gates 0 brechas evidencia cadad4c1f803af4c; antes: R181 ME r181_harness_gcc 9657482 COMPLETADO — H-R176-1 CERRADA: el entorno de la suite resuelve solo sus artefactos (M9 §6.2/M2 §5.1/M1 §3.1/M8 §4) — conftest CPATH raíz + _QUANTUM_OBJS_R181 on-demand (lista separada: deps libm), shim weak GNUC en generator.py+orquestador.syn (paridad M1 §3.1, rebuild generator.syn), bootstrap 3 etapas stage2==stage3 c2889554…c91d43; TestEjecucionReal migrado a exit code via MTO (H-R181-2: convención 1c1044c ratificada, la de 8f3f15b era aspiracional) — 5 GREEN/2 RED por deuda real; oráculo 5/5; quantum 8/8; deudas NUEVAS a filas: H-R181-1 toml/RAII runtime (R186), H-R181-3 lexer 'y' keyword (R184), H-R181-4 colisión stdlib en generador (R185); H-R181-5 cita fantasma corregida; lecciones: exes stale por ediciones post-compilación aunque sean comentarios, gate de lectura exige lecturas DEL DÍA (tras medianoche re-registrar), bash heredoc del commit cierra con )" ; antes: R180 ME r180_coincidir_nativo be5d447 COMPLETADO — H-R177-2 CERRADA: patrón literal numero + wildcard sobre primitivos con paridad S1↔nativo (M3 §3/M1 §3.1/M2 §2) — parser token_es_inicio_patron + emisor switch-sobre-valor por tipo C exacto int64_t/int/bool; test r11 alineado via TDD/MTO con OBL-M3-06; oráculo 4/4 273.75 s que detectó y cerró la heurística invertida del emisor (H-R180-3); lección H-R180-2: generator.syn es concatenado de generador/ — rebuild SIEMPRE antes de bootstrapear; H-R180-1 NUEVA (cuerpos-bloque del caso fallan en nativo también para ADT) → ME R183; antes: **2026-10-04** R179 ME r27_ctor_aridad 0faea8e COMPLETADO — H-R177-1 CERRADA: aridad del ctor de struct en el analizador nativo con paridad S1 — R1 total_campos poblado contando cadena NODO_PARAMETRO via slot [6] (M2 §2), R2 check de aridad restaurado en NODO_LLAMADA: struct no-función con 0<args≠campos → ERR_SEM_ARGUMENTOS_INVALIDOS rc=7 (M2 §8.2); oráculo 4/4 (auto-compilación 37747 nodos con check activo, probes `Punto(1,2)`→12, `Punto(1)`→rc7 paridad, `Punto()`→0); test r27 alineado via TDD/MTO con OBL-M2-05 + caso válido NUEVO; H-R179-1 lección: hijos del nodo plano viajan en slot [6] (accessor nodo_expr), NO en .hijo_izq — usar .hijo_izq contó 0 campos y el check rechazó la auto-compilación; antes: R178 ME check_cli 95b2374 COMPLETADO — `synapse check --no-emit` en dispatcher nativo + cli.py + binario synapse.exe: 3 fallos test_cli_check CERRADOS, oráculo 4/4, MTO OBL-M8-16; plan maestro de deudas docs/plan_maestro_deudas.md con cola R179-R182; antes: R177 ME nativa_rc5_familia 4ebd025 COMPLETADO — familia nativa rc=5/rc=0 de test_fase2_nativa_hm: 8 fallos → 1 (r27=H-R177-1); R1 canal en expresión, R2 constantes tipadas, R3 orden pool/fibras, R4 tipos por RHS Identificador, R5 constantes sin #define; oráculo 5/5, gates MTS 0 brechas; H-R177-2 NUEVO paridad de parser; antes: **2026-10-01** R176 re-baseline integración COMPLETADO — 1453✓/104✗/39skip, +6✓/−6✗ vs R171 = mejora; 0 regresiones de los 2 MEs de la sesión; 104 clasificados con parseo: 21 RED TDD EXACTOS, 27 GCC entorno = H-R176-1, 3 test_cli_check = H-R176-2 feature gap declarado; gates "alinea todo" SIN BRECHAS/DEUDA 0/0; antes: ME paridad_principal_syq 90eb18c COMPLETADO — 4 warps de paridad_syn_syq CERRADOS retirando los stubs de principal obsoletos de pipeline.py+puente; antes: ME puente_for_en_syq 1e1584b COMPLETADO — 3 bugs del camino Syquex reparados: for-en→SentenciaPara canónico, iterable en semántico range-for, cast len; test_result 5/5 GREEN por primera vez; antes: ME barrido_citas_v820 4a63327 COMPLETADO — DEUDA de alineación heredada en CERO: las 39 citas sin sección de la v8.2.0 barridas restaurando textualmente M7 §4.3/§6.1/§6.2/§6.4/§7.2/§8 + 3 re-anclajes §6→§6.2/§2.1; DEUDA.md = 0/0; suites 85/85; antes: ME m7_s73_restauracion 72d77f3 — H-R171-1 CERRADA con M7 §7.3 restaurada + permisos.syn re-anclada; R171 verificación suite integración 1447✓/110✗/39skip, 0 regresiones; antes: restauro_bucle_validacion b1ac1c2, validation_loop_fix 63c1731, transpiler_elif e0cbb35; D-R163-1 sigue pendiente de ratificación)

---

## 🚦 1. DASHBOARD ACTUAL```yaml
Frente H (2026-11-19): r272_docs_encoding COMPLETADO (b3720d3) — el encoding
                   documental se verifica por bytes: `verificar_manuales.py
                   --encoding --docs` rechaza BOM, U+FFFD, C1 y doble
                   codificacion en todo `docs/` (rc=0), y la auditoria canonica
                   y R205.md declaran con cabecera que la fuente de verdad es
                   `docs/manuales/`, conservando sus 1.275+ lineas. Oraculo
                   nuevo test_docs_encoding_r272.py 3/3; contrastar 2/2 PASS;
                   ME documental sin archivos de produccion (sin expediente).
                   Antes r273 (7cc1d91) cerro el instalador con GGUF de 873 MB:
                   r273_installer_modelo_grande COMPLETADO (7cc1d91) —
                   el instalador verifica el GGUF de 873 MB sin timeout falso:
                   sha256_update por bloques + transform con ventana rodante,
                   streaming con buffer de 1 MiB y cache de digest por
                   ruta+ tamano+mtime en ~/.synapse/cache/hash/. Medido: 10,3 s
                   -> 6,5 s en frio y 0,07 s con cache caliente;
                   tests/opensyn/test_installer.py (timeout 10 s) PASA sin
                   tocarlo; oraculo nuevo 17/17; S2==S3 49d7c51ac63e28a6.
                   Antes r270b (84f67ba/8e2c41f) cerro H-R252-5. Siguiente
                   del frente: r276_multiplataforma_release (P0); r274 y
                   r275 cerrados el 2026-11-20 (65a79c7, 251ddc4) y r275b
                   (aa83822) cerro H-R275-1 y H-R275-2: S2 ya emite
                   CadenaSegura al indexar texto y el sello del bootstrap
                   vuelve a certificar tras editar nucleo/principal.syn.
Fase roadmap:      POST-FASE 33 - DEUDA CERO. **2026-11-13 sesión:** R219
                   COMPLETADO (26e4cf8): ME r219_verificacion_aot - verificación
                   AOT con auto-refutación real (`synapse check --no-emit` y
                   hasta 5 casos límite compilados/ejecutados con timeout);
                   H-R219-1/H-R219-2 resueltos con `_syn_strcpy` en
                   `sha256_texto` y copia en `elemento_texto`; oráculo E2E nuevo
                   2/2 + estructural 13/13 = 15 passed, gates 0 brechas,
                   evidencia c0a201a1ecbe7d72. Antes R216 COMPLETADO (7adc440):
                   ME r216_tool_ejecutar - TOOL
                   ejecutar con allowlist (synapse check/build, pytest, git
                   status/diff), rechazo de rutas absolutas tras '=' en flags,
                   timeout de 5 s (rc 124, salida 32 KB),
                   Windows CreateProcessA y POSIX execvp sin shell; oráculo
                   nuevo 4/4, regresión escritura+permisos+patch 49/49,
                   control de alineación 24/24, evidencia db8058173bc4604a.
                   Antes R215 COMPLETADO (c1d051d): ME r215_tool_patch - TOOL
                   aplicar_patch con parser de diff unificado, sandbox y
                   aprobación ASK (alias a editar, MAX_HERRAMIENTAS=8 intacto);
                   oráculo nuevo 3/3, regresión escritura+permisos 46/46,
                   evidencia d815bb878cda3f41. Antes R218 COMPLETADO
                   (e2ec33f): ME r218_bootstrap_json — bootstrap nativo S2 con
                   `std/json.syn`/`std/texto.syn`, buffer de emisión de 4 MB,
                   inferencia nativa `OpBinaria`/llamadas/acceso a campo,
                   `generator.syn` regenerado y `fmt --check` GREEN; S2==S3 sha
                   950AA09B...A71B2A, 16/16 oráculos de auditoría, gates 0
                   brechas; evidencia 8cfce46f5d55e053. Antes R212
                   COMPLETADO (4ab0406): ME r212_memoria_cifrada —
                   `opensyn/memoria_persistente_cifrada.syn` reescrito sobre
                   XSalsa20-Poly1305/SHA-256 reales, tres capas, almacén
                   cifrado plano en `~/.opensyn/memoria.db` y estado explícito
                   `MemoriaCifrada`; retirado del baseline. Oráculo E2E nuevo
                   1/1, test estructural existente 14/14, gate Fase 32 2/2;
                   evidencia cc3cf959ff0b1a25. Antes R217
                   COMPLETADO (6497e80): ME r217_integracion_determinista —
                   `opensyn/pipeline_multiagente.syn` importa
                   `opensyn.explorer_det.syn` y `opensyn.architect_det.syn` y
                   retira las fases locales duplicadas; la fase Architect usa
                   `AnalisisImpacto` aplanado. Probe modular con ambos imports
                   OK; pipeline existente + E2E 16/16, architect existente + E2E
                   12/12, gate Fase 32 2/2, regresión combinada 114/114;
                   evidencia c5e70770a1514592. Antes R211 COMPLETADO (b3180ed):
                   ME r211_architect_det — Architect determinista compilable.
                   `opensyn/architect_det.syn` hace DFS invertido sobre
                   `GrafoProyecto`, contratos críticos por dependientes,
                   detección de ciclo por nodo y métricas de impacto;
                   `AnalisisImpacto` aplana las métricas por H-R207-1. Oráculo
                   E2E nuevo 1/1, architect existente 11/11, gate Fase 32 2/2,
                   regresión combinada 114/114; evidencia 6ac72a2f8744254a.
                   Antes R210 COMPLETADO (990aedb): ME
                   r210_explorer_det — Explorer determinista compilable.
                   `opensyn/explorer_det.syn` hace BFS sobre
                   `GrafoProyecto`/`NodoGrafo`/`AristaGrafo`, con
                   dependencias/dependientes, radio 0/1/2, deduplicación por
                   archivo y distancia entre nodos; sin `continuar` (S1) y con
                   `elemento_texto` para la indexación tipada de `Lista<texto>`.
                   Oráculo E2E nuevo 1/1, explorer existente 6/6, gate Fase 32
                   2/2, regresión combinada 102/102; evidencia 8c52618300038933.
                   Antes R209 COMPLETADO (3064d40): ME
                   r209_router_chat — router y chat compilables con extracción
                   de bloques, validación con `compilar_codigo`, selección de
                   modelo desde `~/.opensyn/config.toml` y stubs deterministas de
                   lifecycle. Oráculo E2E nuevo 1/1, gate Fase 32 2/2,
                   regresión 75/75; evidencia d0a46a4e11076ea6. Antes R208
                   COMPLETADO (95ea023): ME r208_run_manager — run manager
                   reanudable. `opensyn/run_manager.syn` compila y persiste
                   checkpoints (`_syn_escribir_archivo` 0=éxito), corrige
                   ownership con `_syn_strcpy`, reconstruye
                   `checkpoint_path`/`timestamp_inicio`, usa
                   `OPENSYN_RUNS_DIR` y genera `run_id` único con secuencia
                   estática. Helpers ASM locales (`ahora_ms`,
                   `entero_a_texto`, `concatenar_texto`) restaurados por tests
                   estructurales; `entero_a_texto` usa `pool_alloc`. Oráculo
                   E2E nuevo 1/1, runs reanudables 70/70, gate Fase 32 2/2;
                   evidencia 10cc67173f42e68a. Antes R207
                   COMPLETADO (a578e03): ME r207_pipeline_multiagente — pipeline
                   compilable y cableado E2E. `opensyn/pipeline_multiagente.syn`
                   usa imports canónicos, grafo real, fases Explorer/Architect
                   deterministas locales, Coder/Reviewer/Fixer con LLM real,
                   máximo 3 inferencias y validación final con
                   `validar_con_check`; `nucleo/grafo_conocimiento.syn` usa
                   `_json_a_texto` para evitar la colisión con `std.texto`.
                   Oráculo E2E nuevo 1/1, pipeline existente 15/15, grafo 1/1,
                   gate Fase 32 2/2; evidencia 15b96b3c8f8fe172. Antes R206
                   COMPLETADO (7f17dec): ME r206_validation_loop — bucle de
                   validación y corrección automática con compilador real.
                   `opensyn/validation_loop.syn` valida por rc con
                   `synapse check --no-emit`, parsea línea/columna/mensaje,
                   conserva último código/errores, ejecuta 3 intentos y separa
                   feedback humano; ownership corregido con
                   `_syn_strcpy`/`_syn_strlen`. Oráculo E2E nuevo 4/4,
                   regresión 85/85, gate Fase 32 2/2; evidencia
                   dc81f3f85c2e19f4. **2026-11-09 sesión:** R204
                   COMPLETADO (f018957): ME r204_tools_escritura — TOOL
                   escribir/editar en OpenSyn con sandbox de workspace y
                   aprobación explícita; `opensyn/herramientas.syn` nuevo
                   (`herramienta_escribir`/`herramienta_editar`,
                   `herr_ruta_permitida`); `principal.syn` despacha
                   `ruta :: contenido` y `ruta :: buscar :: reemplazo`,
                   normaliza la ruta absoluta antes de
                   `verificar_permiso_completo`, aliasa `escribir` a `editar`
                   y pide aprobación en pipe/consola/TUI; `permisos.syn` solo
                   corrige ownership (`_syn_strcpy`) para eliminar un doble
                   free preexistente (constantes y comportamiento intactos).
                   Gate de compilación Fase 32 con baseline de 10 módulos.
                   Oráculo E2E 3/3 + gate 2/2 + regresión 103/18; contraste
                   7 requisitos/2 oráculos, alineación 3 archivos,
                   verificar_alineacion 0 brechas; evidencia
                   24a7c2c76d9873d2. No se tocó nucleo/lsp_v3.syn (ajeno) ni
                   nucleo/embedded_libs.h. **2026-11-08 sesión:** R203
                   COMPLETADO (d865ab9): ME r203_update_nativo — `synapse
                   update` nativo (sin args, `--version <v>`, `--check`) con
                   consulta a GitHub Releases, descarga TLS vía curl,
                   checksum SHA-256, firma Ed25519, backup en
                   `~/.synapse/backup/` e instalación silenciosa; fallo
                   cerrado ante asset/checksum/firma inválidos. Fix ABI
                   `int64_t` en helpers C (un `int` devolvía 4294967295 por
                   -1), quoting robusto Windows (`cmd /S /C` cuando el
                   comando empieza por comilla) y override
                   `SYNAPSE_PUBLIC_KEY` (par efímero en tests, sin SKIP).
                   10 tests del oráculo + 33 de regresión; contraste 10/10,
                   alineación 4 archivos, verificar_alineacion 0 brechas;
                   evidencia 7d62c4c4b9752ec9. `nucleo/principal.syn` quedó en
                   1200 líneas exactas (D-9 si crece). No se tocó
                   nucleo/lsp_v3.syn (ajeno) ni nucleo/embedded_libs.h.
                   **2026-11-06 sesión:** R202
                   COMPLETADO (f1a4a02): ME r202_release_signing — release
                   firmado de punta a punta. distribuir.py firma cada artefacto
                   y MANIFEST.sha256 (.sig/.sha256/SBOM/SLSA); verificar_firma.py
                   acepta PEM/hex/raw y su CLI falla cerrado (fix: no .strip()
                   sobre firma raw de 64 bytes); workflow matrix 4 plataformas
                   firma y verifica antes de publicar solo en tags; instaladores
                   Linux/macOS exigen firma salvo SYNAPSE_SKIP_SIGNATURE=1;
                   release_keys/public.pem versionada, privada ignorada.
                   87 tests verdes; 19 artefactos/7 firmas SIGNATURE_VALID=YES;
                   contrastar 5/5, verificar_alineacion 0 brechas; evidencia
                   a48ecf5a77bedfc0. R201 COMPLETADO (c653fff): actualizador
                   real fail-closed con semver, SHA-256, backup/rollback y repo
                   canónico; 15 tests, evidencia a55d59bec59045c2. R200
                   COMPLETADO (f3b7268): OpenSyn doctor real, 4 tests y oráculo
                   13/13, evidencia e13f4308e5c35e65. Pendiente externo:
                   ED25519_PRIVATE_KEY en GitHub Actions, validación en runner
                   limpio y `synapse update` nativo. No se tocó
                   nucleo/lsp_v3.syn (ajeno) ni nucleo/embedded_libs.h.
                   **2026-11-05 sesión:** R199
                   COMPLETADO (a2d0ca3): ME r199_opensyn_install — OpenSyn
                   arranca llama-server sin Ollama en instalación limpia.
                   principal.syn: búsqueda de llama-server/.gguf, auto-arranque
                   con PowerShell `Start-Process -WindowStyle Hidden` (sin
                   `start /B`), readiness por /v1/models y builder incremental
                   `_syn_texto_builder_*` (fix del aliasing de `concat` en
                   comandos largos); .bat delega en bin/opensyn.exe; installer
                   descarga el servidor aunque reutilice GGUF del perfil.
                   E2E: instalador Inno compilado, instalación silenciosa
                   D:\OpenSynTest_Install rc=0, puerto 8088 LISTENING y
                   respuesta `OpenSyn> cerrar`; 8 tests verdes. Evidencia
                   r199 a86383cf07b5e14e. Incluye r198b3_fmt_lint con
                   expediente completado (10 archivos, evidencia
                   f6b961b78da460a1): citas literales, `tipo` válido y anclas
                   en sistema.c/.h, texto.c/.h, formatter/lint/principal,
                   runtime_bindings y opensyn/principal. Gates del hook:
                   verificar_alineacion 0 brechas, contrastar 2 planes OK,
                   MTO 55 OBL y lectura previa 11 archivos/4 registros.
                   Queda FUERA del commit `nucleo/lsp_v3.syn` (unstaged, sin
                   plan MTS que cubra M8 §1.1/1.4/2.3) y
                   `nucleo/embedded_libs.h` (generado). Lección: `contrastar`
                   toma solo la primera sección del `requisito:` combinado;
                   cada archivo necesita cita de una sección realmente listada
                   y `tipo: comportamiento|contrato` (no `implementacion`).
                   **2026-10-28 sesión:** R198b2
                   COMPLETADO (dd20276): ME r198b2_ancla — cierre
                   H-R198b1-2: ancla MTS `cumple Manual 2 §12` NUEVA en el
                   desugar REAL de NODO_PARA_EN(57)
                   (compilador/puente_canonico.py::_nodo_para_en, L614,
                   junto al `cumple Manual 3 §3 (H-R153-1)` preexistente),
                   según la dirección del Arquitecto: TDD RED→GREEN sobre
                   el archivo de producción (test inmutable NUNCA tocado);
                   comentario de documentación, cero diff en la emisión.
                   test_paridad_nodos.py 4/4 GREEN (el failed preexistente
                   verificado con stash en R198b1 ya no existe) + familia
                   del gate 19 passed. Gates: plan MTS
                   docs/plan_ME_r198b2_ancla.md con bloque estricto,
                   contrastar RC=0 (oráculo release en el hook),
                   expediente docs/alineacion/r198b2_ancla.md 0 brechas
                   (3 CUMPLE, evidencia 8881708525cba028),
                   verificar_alineacion SIN BRECHAS, MTO 55 OBL. Reporte
                   docs/reportes/R198b2.md
                   Cierre del barrido (0efd126 base): pytest tests/auditoria
                   COMPLETO sin timeout — 222 tests, 214 passed, 7 failed
                   deterministas en aislamiento (0 regresiones de R198b2,
                   paridad_nodos 4/4 bajo barrido completo). 4 deudas NUEVAS
                   a cola (cerrada en plan maestro): H-R198b2-1 exes stale
                   (stage2 vs coverage.syn; opensyn.exe vs principal.syn),
                   H-R198b2-2 fmt/lint de stage2 (rc fmt --check, timeout
                   generator.syn, lint Temp), H-R198b2-3 contrato-test
                   desalineado (io.syn `_resultado_` vs test `resultado` —
                   alinear test al manual SOLO con aprobación del
                   Arquitecto), H-R198b2-4 fixture de fecha literal del
                   oráculo R198b1 (resane rota al cambiar el día;
                   sellar .antes.json con fecha de HOY). Reporte
                   docs/reportes/R198b2_barrido.md
                   **2026-10-29 cierre ambiental (H-R198b2-1 CERRADA):**
                   regenerados synapse_stage2.exe + copia synapse.exe (el
                   test r3 solo refresca la copia si NO existe — copia
                   vieja 2026-10-11) + dist/bin/opensyn.exe → check_cli r3
                   + guard H-AUD-OP-2 2/2 GREEN. H-R198b2-2 confirmada como
                   COMPORTAMIENTO: los 3 de fmt/lint fallan igual con exes
                   frescos → ME de fmt/lint a cola (lección: regenerar la
                   COPIA del CLI también, no solo el stage2).
                   Antes (2026-10-27): R198b1 COMPLETADO (b657bb8): ME r198b1_resello — cierre
                   H-R198b-1: re-sello auto-sanante de `cambio_hash` en
                   auditoria/alineacion.py (cmd_verificar: helper
                   resellar_hash_expediente + predicado
                   _solo_brecha_hash_stale que NO enmascara otros errores
                   + re-verificación de una pasada in-proceso — converge
                   porque la huella cubre blobs de producción, nunca el
                   expediente); aviso no bloqueante de sello sin stage
                   (huella sobre blobs del INDEX, lección
                   R188/d948cab). Oráculo NUEVO
                   test_oraculos_r198b1_resello.py 4/4 (A1 helper +
                   idempotencia; A2 END-TO-END: expediente r198b con hash
                   anulado → --verificar rc=0 y expediente byte-a-byte
                   restaurado — el caso que antes exigía edición manual;
                   A3 no enmascara; A4 aviso sin stage). Regresión
                   familia del gate 18 passed; gates: contrastar RC=0,
                   verificacion_ME validada, verificar_alineacion SIN
                   BRECHAS. Deuda NUEVA a cola H-R198b1-2
                   test_paridad_nodos::test_emision_s1_cita_los_nodos_canonicos
                   FALLA PREEXISTENTE en HEAD (verificado con stash),
                   exige ancla MTS `cumple Manual 2 §12` en el desugar de
                   PARA_EN de compilador/puente_canonico.py — ME futuro
                   añade el comentario de cita (test inmutable) — CERRADA
                   en R198b2 (dd20276, ver entrada 2026-10-28). Reporte
                   docs/reportes/R198b1.md
                   Antes (2026-10-27): R198b COMPLETADO (f10401f): ME r198b_contratos — cierre
                   H-R196-3 con veredicto CONTRA la hipótesis: el emisor
                   de contratos NO estaba roto (emitía fielmente el AST,
                   M2 §5.1 en CADA retornar con _resultado_ del tipo REAL,
                   emit_declarations.py L781-816); las cláusulas del
                   std/opensyn estaban bajo semánticas no canónicas y se
                   corrigieron hacia el manual (precedente H-R196-1):
                   std/sistema.syn subcadena (1,2)→(1,1) fin EXCLUSIVO
                   (r196) en garantiza _validar_ruta_segura + patrón
                   relativo; principal.syn L213 alias bare `resultado`→
                   `_resultado_` (ruta_config_absoluta) y L1065
                   `longitud(_resultado_) >= 0` → `_resultado_ >= 0`
                   (pct_contexto, recorrido de validación M7 §4.2).
                   Oráculo NUEVO oraculo_r198b_contratos.py 3/3 (A1
                   compilación principal.syn rc=0, A2 sandbox contratos
                   5/5 antes 3✓/1✗/1E rc=0xC0000009, A3 regresión r198);
                   contratos/sandbox 44 passed + borrowing 17. Gates:
                   plan MTS contrastar RC=0; expediente r198b_contratos
                   0 brechas (3 CUMPLE, evidencia ca4229aa1e9364ab);
                   verificar_alineacion SIN BRECHAS; sello
                   r198b_contratos.antes.json (base 3aa5b6c). Hallazgo
                   NUEVO H-R198b-1 con resolución a la cola maestro:
                   CÍRCULO del re-sello de cambio_hash en cmd_verificar
                   (alineacion.py L920-957) — el mensaje pide re-ejecutar
                   --verificar para re-sellar pero el re-sello L945-952
                   solo corre tras pasar y el mismatch L455-463 retorna
                   1 ANTES; amplificador: cambio_hash lee blobs del INDEX
                   (`:{ruta}`), un --verificar SIN stage sella hash
                   fantasma (8b8b3688… con blobs vacíos) que el add
                   invalida (precedentes d948cab/lección R188):
                   EXPEDIENTE SIEMPRE sellado tras git add; ME futuro:
                   re-sello auto-sanante de una pasada (in-proceso,
                   oráculos incluidos). Reporte docs/reportes/R198b.md
                   Antes (2026-10-26): R198 COMPLETADO (18ee4ee): ME r198_cesion_struct — cierre
                   H-R197-1 (emisor liberaba el texto cedido a campo de
                   struct: slab reciclado → config.toml `ruta` corrupta):
                   S1 emit_declarations.py visitar_asignacion_campo + nativo
                   nodos_flujo.syn gen_visitar_asignacion_campo (unity
                   re-sellada con _rebuild_generator.py) marcan el ORIGEN
                   CONSUMIDO (move semantics M4 §3.3, paridad
                   ArgumentoTransferido H-R182c-1 extendida a cesión-campo;
                   M2 §5.1 el cleanup RAII respeta la cesión; M2 §12
                   contratos en el probe). Probe determinista
                   auditoria/probes/probe_cesion_struct.syn + oráculo NUEVO
                   oraculo_r198_cesion.py 3/3 (C sin _syn_texto_liberar(p) en
                   armado, salida íntegra rc=0); E2E real: config.toml `ruta`
                   ÍNTEGRA. Gates: plan MTS contrastar RC=0; expediente r198
                   0 brechas (evidencia e004e8e8e8645718, 5 CUMPLE);
                   verificar_alineacion SIN BRECHAS. Resolución asignada al
                   ME r198b (emisor de contratos, familia H-R196-3):
                   `garantiza` sobre retorno texto evalúa
                   `_resultado_`/`resultado` del pool tras el cleanup
                   (test_oraculos_config_ruta rc=0xC0000009 hoy vs
                   0xC0000374 ayer, PREEXISTENTE al bisect) + compilación S1
                   de opensyn/principal.syn falla (`longitud(resultado)` sin
                   renombrar + robo del `_resultado_` int64 de otra función —
                   resolver por TIPOS, no por nombre de variable).
                   Reporte docs/reportes/R198.md. Antes (2026-10-25): R197
                   COMPLETADO (ad4f5bd): ME r197_instalador_usuario — hallazgos
                   de EJECUTAR el instalador como usuario (rc=0 ≠ funciona):
                   wrapper _syn_hash_archivo(CadenaSegura) en runtime/core/modelo.c
                   (la nativa const char* leía longitud como puntero: hash
                   VACÍO), descarga TLS vía curl (-L -fsS --create-dirs),
                   externos -> entero (r194) + convención 0=éxito; E2E RC=0 con
                   hash verificado (gguf 873 MB) y config.toml/config_ollama.txt
                   generados. Gates: plan MTS contrastar RC=0; expediente r197
                   0 brechas (evidencia 0491b2530072b608); verificar_alineacion
                   SIN BRECHAS; familia instalador 17/17; oráculo 8/8.
                   Deudas NUEVAS a cola: H-R197-1 (emisor libera texto cedido a
                   campo de struct → config.ruta reciclada; repro determinista;
                   misma que los 2 fallos PREEXISTENTES de
                   test_oraculos_config_ruta rc=0xC0000374, herencia
                   confirmada con bisect-stash) y H-R197-3 (seleccionar_modelo
                   hardcodeado vs modelos.toml M9 §5.6, DESVIACION del
                   expediente). Reporte docs/reportes/R197.md. Antes (mandato
                   2026-10-18): cola del plan maestro CERRADA — R184 resuelta por r190 (78b8947:
                   debug CLI M8 §3.4, ayuda rc=0 sin sesión, navegación
                   mantiene rc≠0 contrato r150, tests con traza TRACE v1
                   real) + r191 (621051a: pgo rc de ley 42 en -O1/-O2;
                   checker S1 aplica M2 §9.3 — MISMATCH en retorno-&local y
                   consumo-con-préstamo-vivo, elisión §9.3 en retornar x,
                   ErrorCodes LIFETIME completos + plantillas 6 idiomas,
                   línea precisa §10.1 en LlamadaFuncion; federated al
                   literal canónico `nulo` M2 §4.3). Oráculos r190 3/3 +
                   r191 3/3; unit 514✓; lote 45+1✓; gates verdes ambos
                   (expedientes 63f5b931/94adcc427ab93c59). Barrido
                   integración completa (1600) TERMINADO (2h39m,
                   PYTEST_RC=1 con pipefail): **1547 passed / 34 skipped /
                   19 failed**; TRIAJE dual-tree (worktree 621051a vs
                   d8f03ac): TODOS los 19 PREEXISTENTES (deuda histórica,
                   NO regresión de r191): (A) infra 8 (axon/cache/opensyn
                   fixtures), (B) paridad S1 9 (fase2_hm/cobertura_d5/
                   binario_real/contracts/borrow_abort — mensajes heredados),
                   (C) borrowing_adv 2 — parser NO acepta `d: &mutable Dato`
                   ("Se esperaba RPAREN") → deuda del parser de params,
                   M2 §9.3. Cola NUEVA R192 en plan_maestro_deudas (grupos
                   A/B/C con resolución asignada). R192 COMPLETADO
                   (4e97f3f, 2026-10-20): contratos reactivados S1+nativo
                   con paridad (M2 §5.1/§5.2/§5.3 §12, macro assert_contrato,
                   _resultado_ tipado vía _G_fn_ret_tipo_c + delegación de
                   handle M6 §3.1), std barrida (40+ cláusulas canónicas,
                   Canal: es_valido/dominio), citas fabricadas "Manual 1
                   §165" corregidas a M2 §5.3 (M1 solo tiene §1–§9),
                   oráculos r192 (contracts_e2e + bootstrap S2==S3
                   780e2419384c), expediente 0 brechas a 17 archivos
                   (evidencia 6425a7aa2f59cf8d), contrastar RC=0, unit 514✓,
                   grupos B/C del barrido VERDE (112+15+8+1+7). R193
                   COMPLETADO (a78c57a, 2026-10-21): GRUPO A cerrado —
                   barrido r191 EN CERO (A+B+C). El frente de fixtures
                   destapó dos hallazgos de PRODUCCIÓN: H-R193-1 (enlace
                   cacheado _link_object sin paridad con el enlace normal:
                   sin módulos quantum/federated/IA ⇒ undefined
                   qc_aplicar_pauli_z; sin allow-multiple-definition ⇒
                   multiple definition _syn_qec_verificar_estado_logico
                   en TODO hit del enlace incremental; sin -static/env) y
                   H-R193-2 (key de caché de .o con base_flags crudo:
                   doble espacio desalineado entre caminos ⇒ 46 .o
                   recompilados en CADA pasada ~90 s). E2E: 2.ª pasada
                   0,9 s con [CACHE HIT] y 0 recompilas — cache.syn M1
                   §4 operativo. Oráculo r193 PASS (grupo A RC=0: 5+4+3+9);
                   expediente r193 0 brechas (evidencia 270133df57df7614,
                   anclas M1 §3.1/§4/§7.2), contrastar RC=0, unit 514✓.
                   Grupos B/C sin cambios (r192). NEXT: siguientes fases
                   del roadmap (cola del plan maestro disponible para
                   hallazgos NUEVOS).
                   Antes (2026-10-16):
                   ME r188_deuda_cero_1 COMPLETADO (9f6b1cd): H-R184-1
                   CERRADA en S1 — desugar `coincidir <canal> ->:` M5 §3.6
                   (flecha opcional, ExprRecibirCanal.modo_resultado,
                   tipo Resultado<elem,texto>, registrar_instancia_adt,
                   emit_control/emit_expressions codegen ADT especializado);
                   oráculo 4/4 (E2E ok=7/cerrado-2), foco 65✓, unit 514✓;
                   expediente 0 brechas re-sellado 2× (ancla ±3 + hash
                   stale tras git add).
                   Base anterior r188: deuda asserts/entorno medida en vivo:
                   test_debugger_timetravel SyntaxError de docstring
                   reparado + 3 asserts test_generator alineados al emisor
                   vigente (Lifetime Scope, mangle principal) → 49 passed;
                   restan 8 FAILED (listen/cli_run_debug/opensyn_cli/
                   debug_reverse) + cola baseline r183e; detalle en
                   docs/plan_maestro_deudas.md fila R184. Antes: ME
                   h_canon_let COMPLETADO (643b413):
                   H-canon-LET CERRADA — el serializador canónico pisaba la
                   llave discriminante 'tipo' del JSON con la anotación del
                   `let` (round-trip .syn.json corrupto): anotación →
                   'tipo_annot' (M2 §13, paridad ast_nodes.syn:83); 6 asserts
                   codegen al M2 §13 + 2 asserts débil<T> al runtime real
                   WeakRef (Manual 4 §4.2, autorización Arquitecto) + 1 aser-
                   ción @export al Lifetime Scope; f1d 8/8, vecinos 46✓;
                   gates MTS/expediente/lectura OK (evidencia ad34c2eb...).
                   Cola: plan maestro (H-R90-5, ME_27/29/30, ~46 asserts,
                   YAML CI; docs/plan_maestro_deudas.md).
                   Antes: ME r183d_flags_debug COMPLETADO (0528b7a):
                   cierre de los hallazgos UX de R182c: --version/--help
                   rc=0, prescan de flags --target/--release/--debug/
                   --safe/--output/-o (REAL-1 + REAL-4b cerrados),
                   fallback de salida `<archivo>.exe` nunca el stage2
                   (bootstrap protegido) y --debug degrada a -O0 -g en
                   toolchains sin libasan/libubsan (probe de link);
                   oráculo 11/11 + determinismo, S2==S3 sha c3231f34,
                   regression 793 passed, gates 0 brechas.
                   Antes: ME r182c_canal_vivir COMPLETADO (057d072):
                   H-R182c-1 CERRADA (pruebas usuario real): canales cedidos
                   a fibra/listener fueron destruidos por el cleanup del
                   scope contenedor (use-after-free, basura + segfault);
                   fix _canal_vars_cedidas con marcar en escuchar/lanzar;
                   oráculo e2e 42/100 rc=0; syquex 279✓, unit 514✓.
                   Hallazgos UX: synapse.exe --version/--help rc=2
                   (dispatcher nativo sin flags), --target wasm válido
                   solo tras subcomando build. Cola: R182+ feature gaps.
                   Antes: ME r182b_frontend_para_rango COMPLETADO (24d3912):
                   H-R182a-1 CERRADA (deuda 1F+9E test_concurrency/test_traductor
                   desde c2cd52e) — frontend Syquex segfaulteaba con `para` de
                   rango en .syq; causa raíz: 5 literales sintéticos del desugar
                   sin bits altos en sq_tokens_hi (span 64-bit reconstruido
                   inválido); regresión tests/syquex 279 passed / 1 skipped;
                   oráculo oraculo_r182b.py PASS; cola: R182+ feature gaps
                   (H-R90-5, ME_27/29/30), YAML CI release, ~46 asserts.
                   Antes: ME r184_r185_e2e COMPLETADO (e4e4022):
                   H-R181-3/H-R181-4/H-R186-1/H-R181-1/H-R188-1 CERRADAS
                   (lexer keyword+':' contextos + literales excluidos,
                   mangle _syn_usuario_ colisiones stdlib paridad 50,
                   _syn_texto_duplicar literales→RAII, préstamo de params
                   struct ownership, conftest rt_objs pre-colección);
                   oráculo 5/5; bootstrap S2==S3 cdcc5262…ac4600; cola:
                   R182 feature gaps, R183 cuerpos-bloque nativo.
                   Antes: ME restauro_bucle_validacion COMPLETADO (b1ac1c2):
                   deuda TestRequisitosManuales CERRADA — M7 §6.3 restaurada
                   textualmente (texto exacto pre-154a544, nota de procedencia
                   incluida) + cola truncada de §4.2 completada (pasos 9-11);
                   guarda 7/7, suites-guarda vecinos 67 passed 0 failed; índice
                   regenerado (1311 oraciones). Antes: ME validation_loop_fix COMPLETADO (63c1731):
                   deuda test_validation_loop_syn_exists CERRADA — aserción L217 de
                   test_opensyn_integration.py alineada al nombre vigente
                   validar_con_check (7824e5d/ME-4 renombró la función sin tocar el
                   test; autorización Arquitecto regla 5, Opción A). Antes: ME transpiler_elif COMPLETADO (e0cbb35): deuda
                   test_control_flow_pipeline CERRADA — el transpilador Python→Syquex
                   emitía sino_si (token inexistente en la gramática M2 §7.2; origen
                   R119 L60, justificada con cita fantasma Manual 7 §5.1) y ahora
                   emite "sino si" (M6 §6.2, forma canónica, paridad transpiler.syq);
                   aserción test_opensyn_integration.py:120 corregida con autorización
                   Arquitecto regla 5; DEUDA NUEVA: test_validation_loop_syn_exists
                   (nombre de función test vs código, preexistente, decisión
                   Arquitecto). Antes: las 3 deudas de FASE_33_CERTIFICACION §5
                   CERRADAS: ME fixture_syquex_timeout (ff6c54a, autorización
                   Arquitecto regla 5) — techo por-marker timeout(660) para el
                   fixture cuyo subprocess interno necesita ~500 s (el global 300 s
                   mataba la sesión pytest completa); 5/5 GREEN en 398.75 s
                   ME cli_lint_fmt COMPLETADO (12b342d): `synapse lint/fmt`
                   en el dispatcher Python (cli.py) → backend NATIVO (stage2,
                   módulos .syn lint/formatter); backing on-demand del bootstrap
                   (M1 §6, comando del job CI); raíz histórica del rc=0 falso
                   corregida (sys.exit(main())); oráculo 6/6
                   POST-FASE 33 — ME formatter_fix COMPLETADO (58ff1d1): cierre de H-33.5-3 —
                   dedupe lint→formatter (la normalizar_espacios duplicada de lint.syn
                   ensombrecida por first-wins del aplanador era la causa raíz), colapso
                   de espacios FUERA de literales, línea vacía preservada, nucleo 47/47
                   fmt --check rc=0 idempotente, oráculo 6/6, bootstrap S2==S3 nuevo
                   sello 6d579f9e…b1c
                   FASE 33.5 COMPLETADA — ME 33.5_certificacion (55a9950): certificación de la
                   Fase 33 — bootstrap S2==S3 byte-idéntico (sha256 36b82c4d…addf9c) sellado
                   en el job CI bootstrap (M9 §6.1), dispatcher nativo lint/fmt/test al
                   orden canónico de M8 §4.1, oráculo 5/5, FASE_33_CERTIFICACION.md; 0
                   regresiones (medición diferencial vs base)
                   FASE 33.4b COMPLETADA — ME 33.4b_genericos_para_mapa (dfdb1bd): genéricos de
                   usuario Caja(T) con monomorfización, para k en mapa (D-R163-1),
                   claves()/valores(); H-R153-3 CERRADA
                   FASE 33.4a COMPLETADA — ME 33.4a_paridad_indexado (5ff9235): paridad del
                   indexado de colecciones en S1+nativo; H-R153-3 cierre parcial
                   FASE 33.2 COMPLETADA — ME coverage_aristas (d0386f3): --coverage con
                   instrumentación de aristas en S1+nativo; H-R152-1 CERRADA
                   DEUDA H-CFG-4/H-CFG-5 RESUELTAS (4697132: ME reparacion_imports_ffi —
                   imports con fallback a la raíz del repo, FFI lista/mapa con handle
                   entero M6 §3.1 + firmas únicas; bootstrap S1 reparado — H-CFG-5b)
                   DEUDA H-EOF-3 RESUELTA (96e72f4: sandbox de std.sistema operativo —
                   separador de plataforma, borde de componente, normalizador con pila;
                   config del cwd relativa→absoluta decide el modo de OpenSyn)
                   DEUDA H-EOF-1 RESUELTA (8375ec6: API stdin_eof en runtime — EOF real ≠
                   línea vacía; OpenSyn cierra por EOF inmediato, contadores r155 de respaldo)
                   REPARACIÓN HALLAZGOS AUDITORÍA-OP COMPLETADA — H-AUD-OP-1 (830074a: chat/menú
                   cierran ante EOF), H-AUD-OP-2 (9a9170c: exe fresco + guard de frescura),
                   H-AUD-OP-3 (1f5f7e3: markers tdd/e2e registrados) — deuda restante H-EOF-3
                   (config relativa→absoluta) con resolución asignada
                   ME r153_s1_metodos_genericos COMPLETADO (d9e842c) — H-R152-4 CERRADA por Opción A: métodos/genéricos/for-en en S1+S2 y backend lint/fmt/test flipped a los módulos .syn
                   ME r151_linea_base COMPLETADO (5db1dab) + ME r152_bootstrap_link COMPLETADO (dbb9717) — H-R151-3 RESUELTA: bootstrap S1/S2 vuelve a ENLAZAR (Manual 1 §6)
                   FASE 32 COMPLETA — Agente de Codificación Avanzado + Memoria Persistente (5/5 ME)
                   FASE 31 COMPLETADA — Herramientas Nativas (ME-1..ME-5)
                   FASE 30-c ME_opensyn_best — ME-1..ME-6 TODOS COMPLETADOS
                   FASE 30-b HARDENING — OpenSyn TUI + IA local (R141/R142/R143) COMPLETADA
                   FASE 30 COMPLETADA — Instalación Unificada y Distribución Final
Estado:            Plan maestro de deudas EN CURSO (docs/plan_maestro_deudas.md):
                   ME check_cli COMPLETADO (95b2374, R178): `synapse check
                   --no-emit` — 3 fallos de test_cli_check CERRADOS (M8 §4.2/
                   §4.1/§4); modo_validar corta el pipeline tras el análisis
                   semántico; synapse.exe desplegable. Antes: ME nativa_rc5_familia COMPLETADO (4ebd025, R177): familia de fallos
                   nativos rc=5/rc=0 de test_fase2_nativa_hm — 8 fallos → 1
                   (r27 = H-R177-1, decisión del Arquitecto). R1 canal(...) en
                   expresión (parser_expr.syn, M5 §3.2); R2 constantes tipadas
                   no-texto (_G_native_consts_txt + rama _ot==30, M2 §2/§4.1);
                   R3 pool_destroy DESPUÉS de esperar fibras (_emit_main ×4,
                   M6 §2.2); R4 RHS Identificador hereda tipo (M2 §8.2);
                   R5 constantes de módulo enum/static const, no #define (M2 §2).
                   Oráculo 5/5 GREEN; bootstrap S1→S2 rc=0; unit 514✓; matriz 35✓;
                   gates MTS completos (contrastar PASA, huella 828a4be257954718,
                   verificar_alineacion SIN BRECHAS). H-R177-2 NUEVO: parser nativo
                   de coincidir sin literales/wildcard (S1 los acepta vía H-R90-6).
                   Deudas menores de flujo documentadas en verificacion_ME:
                   stage2 sin -o se sobreescribe, _X.c stale en ruta modular,
                   pipes ocultan rc (convenciones registradas).
                   Antes: R176 re-baseline integración COMPLETADO (verificación, sin commits de
                   producción): 1453✓/104✗/39skip sobre 1596 (2:12:18) vs R171
                   1447✓/110✗ → +6✓/−6✗ = MEJORA. Los 4 warps paridad NO
                   reaparecieron (90eb18c verificado en suite completa); loop_1M
                   no falló (4ª reconfirmación flaky). 0 regresiones: 21 RED TDD
                   IDÉNTICOS uno a uno, ninguna familia creció, 3 ambiguos FALLAN
                   aislados (link runtime completo, no tocan rutas .syq).
                   Clasificación: 21 RED TDD declarado EXACTOS + 10 YAML + 27 GCC
                   entorno (H-R176-1, ALTO: harness/link — ME candidato radio ~27)
                   + 8 compila .syn + 46 asserts + 4 flaky entorno + 3 lifetimes
                   + 3 cli_check feature gap DECLARADO (H-R176-2) + 1 wrapper.
                   Gates "alinea todo" (2ª mitad del mandato): verificar_alineacion
                   SIN BRECHAS, DEUDA.md 0/0, citas_muertas=0 — los 104 NO contienen
                   ninguna brecha de alineación (solo feature gaps declarados y
                   deudas de entorno). Antes: ME paridad_principal_syq COMPLETO (90eb18c): los 4 warps de
                   test_paridad_syn_syq CERRADOS — dos workarounds heredados de
                   ME-R90-8/8b inyectaban un stub `funcion principal()` cuando el
                   .syq no lo declara (pipeline.py tempfile en source H-R90-8b +
                   puente fallback en AST ME-R90-8); el pretexto "el runtime S1
                   filtra funciones sin principal" es FALSO con el frontend actual
                   (probe: el JSON conserva area sin principal). Ley M1 §3.1 (mismo
                   AST canónico, paridad F22) + M3 §3 L78 (principal opcional) +
                   main de biblioteca del generador (D-R150-4). paridad 6/6 PASSED;
                   E2E dual rc=7/rc=0; syquex+opensyn+r86+r92 405✓/3✗ (solo wasm
                   RED TDD); unit 514/514; matriz 35/35; bootstrap fresco; huella
                   907275bc6b04e287 (evidencia 907275bc6b04e287.json). Antes: ME
                   puente_for_en_syq COMPLETO (1e1584b): 3 bugs reales del camino .syq
                   reparados — (1) puente for-en produce el nodo canónico
                   SentenciaPara(variable, iterable, cuerpo) (antes desugaring a
                   Mientras con _paraind usada antes de declararse → "Variable '' no
                   declarada"); (2) semántico range-for mira iterable Y condicion (el
                   puente pone iterable, el parser S1 condicion); (3) builtin len con
                   cast (void*)(intptr_t) (gemelo longitud ya lo tenía). test_result
                   5/5 (operador ? GREEN POR PRIMERA VEZ), puente_canonico 12/12,
                   unit 514/514, syquex+opensyn 398✓/3✗ (solo wasm RED TDD Fase 25 —
                   un fallo MENOS que baseline R164), matriz 35/35, bootstrap S1→S2
                   fresco rc=0, huella ac3a132858571ecf (evidencia
                   auditoria/evidencia/ac3a132858571ecf.json). Mensaje del hook de
                   lectura con ruta vigente docs/gobernancia/mapa_manuales.md.
                   Antes: ME m7_s73_restauracion COMPLETO (72d77f3): H-R171-1 CERRADA —
                   M7 §7.3 restaurada textualmente (apéndice, nota 2026-10-01) +
                   permisos.syn L3 re-anclada a §7.3 (texto exacto fef314b, anclas
                   §1.1 preservadas, mapa actualizado); test_permisos 43/43 (el
                   oráculo R6 vuelve a resolver); suites-guarda 67/0; contrastar
                   PASA; alineación 0 brechas (huella 2fee9f2fa1cabff7). 3ª víctima
                   de la v8.2.0 reparada (tras §5.1/R119 y §6.3/b1ac1c2). ME
                   barrido_citas_v820 COMPLETO (4a63327): las 39 citas sin sección
                   BARRIDAS — M7 §4.3/§6.1/§6.2/§6.4/§7.2/§8 restauradas textuales
                   (36 citas auto-resolvieron) + 3 re-anclajes §6→§6.2 (chat.syn
                   L3/L54) y §6→§2.1 (ai_orchestrator.h L146); DEUDA.md = 0/0;
                   índice 304 secciones/1364 oraciones; suites 85/85; mapa saneado
                   (entrada stale §6.4 de chat.syn corregida).
                   R171: suite de integración completa 1447✓/110✗/39skip (2:16:06,
                   test_syquex_coverage incluido y 5/5 GREEN; 0 regresiones de la
                   sesión; 110 fallos = deuda heredada/entorno, clasificados en
                   R171). ME restauro_bucle_validacion COMPLETO (b1ac1c2): M7 §6.3
                   restaurada textualmente (los 5 requisitos del guarda vuelven a
                   existir en el manual: hasta 3 intentos vía §4.2 completada,
                   línea/columna/mensaje, prompt con error, feedback.jsonl, mensaje
                   de fallo definitivo vía §6.3); 3 referencias colgantes resuelven
                   (M7 L24/L627, M8 §5.1) y los 5 comentarios de producción `//
                   cumple Manual 7 §6.3` re-anclan a sección real; lección: tras
                   una revisión de manuales ejecutar los suites-guarda que clavan
                   texto. ME validation_loop_fix COMPLETO (63c1731): aserción L217
                   validar_codigo_con_check → validar_con_check (nombre vigente
                   usado por TODO el ecosistema: 3 llamadas internas + suite ME-4
                   51/51; ningún manual fija el nombre); test_opensyn_integration
                   18/18 (TestBucleValidacion 4/4); contrastar PASA con 2 oráculos
                   release; ME transpiler_elif COMPLETO (e0cbb35): transpiler.py L51/L197
                   emite "sino si" (antes sino_si — token inexistente en la gramática,
                   4 errores al compilar el .syn generado; OBL-M7-03 violado);
                   test_control_flow_pipeline PASSED por primera vez (deuda R166
                   CERRADA); aserción L120 corregida con autorización regla 5 (era
                   la única que codificaba la desviación y contradecía a
                   test_full_pipeline.py:230); contrastar PASA (test_full_pipeline
                   14/14 + test_transpile 3/3 en release); expediente huella
                   152a82c2ad565065; deuda NUEVA documentada:
                   test_validation_loop_syn_exists (espera validar_codigo_con_check,
                   el código define validar_con_check — preexistente, decisión
                   Arquitecto). ME fixture_syquex_timeout COMPLETO (ff6c54a): pytestmark timeout(660)
                   en test_syquex_coverage (aserciones byte-idénticas, tripwire global
                   300 s intacto); cuello de botella medido: subprocess interno ~500 s
                   (476 s suite con cov + 25 s benchmarks), coverage cuesta ~25%;
                   contrastar PASA con el propio fixture como oráculo (release).
                   ME cli_lint_fmt COMPLETO (12b342d): cli.py despacha lint/fmt al backend
                   nativo (sin reimplementar); _bootstrap_stage2_fresco() con el comando
                   del CI (rebuild solo si stale/stage1 ausente); rc propagado (sys.exit
                   (main()) — antes se descartaba: rc=0 falso universal); oráculo 6/6,
                   unit 514/514, nucleo 30/30, matriz 35/35, evidencia 07ba3f460c6d0bee;
                   test_control_flow_pipeline PREEXISTENTE (falla igual en base limpia).
                   ME formatter_fix COMPLETO (58ff1d1): H-33.5-3 CERRADA — lint.syn importa
                   formatter y delega (duplicados borrados), colapso fuera de literales
                   (estado en_literal), nucleo 47/47 formateado idempotente, oráculo
                   formatter_fix 6/6 + oráculo 33.5 5/5 (bootstrap revalidado), unit
                   514/514, nucleo 30/30, matriz 35/35, gates 0 brechas (evidencia
                   c365b2ea07a7bc8c). Fase 33.5 COMPLETA (55a9950): sello S2==S3 en job CI bootstrap (H-33.5-1
                   CERRADA); dispatcher lint/fmt/test acepta el orden canónico de M8 §4.1
                   (H-33.5-2 CERRADA); oráculo test_oraculos_33_5_certificacion.py 5/5
                   (bootstrap 3 etapas real, matriz extendida std/debug+std/modelo, dispatch
                   canónico, anti-fabricación); suites: unit 514/514, nucleo 30/30, matriz
                   35/35, syquex+opensyn 397✓/4✗ (idénticos en base), integration
                   1435✓/120✗ (114 idénticos en base + 1 flaky GREEN aislado); lint real
                   422 advertencias orquestador.syn; fmt viciado por H-33.5-3 (ME futuro);
                   evidencia 872565eea522073f.
                   Fase 33.4b COMPLETA (dfdb1bd): estructura Caja(T): parseada en ambas capas
                   (paréntesis M2 §2, param_generico), Caja(5) unifica T=entero (M2 §8.2) —
                   S1: _registrar_instancia_generica + typedefs monomorfizados + unificación T
                   en semántica (paridad D-2); nativo: gen_escanear_genericas 3 fases + guard
                   de typedefs planos; para k en mapa itera claves con m[k] (D-R163-1);
                   claves() encajona CadenaSegura* (mapa.c, ABI alineada a synapse_rt_types.h);
                   oráculo 6/6, unit 544/544, matriz 35/35, bootstrap S1→S2 verde; evidencia
                   5d27e18bcd289f21.
                   Fase 33.4a COMPLETA (5ff9235): indexado xs[i]/m[clave] emitido por S1 vía
                   runtime (_syn_lista_obtener/_syn_mapa_obtener, desencajonado escalares por
                   valor / structs-texto por dirección) y por el nativo (T_CORCH_IZQ/DER=75/76
                   sincronía D-9(e), lexer c==91/93, postfix NODO_INDICE(29) en r_post, puente
                   ExprIndice, emisor+tipo con trim de spans); oráculo 4/4, unit 514/514,
                   matriz 35/35; hallazgo: el ROADMAP asumía 'S1 ya emite vía r153' y era FALSO.
                   Fase 33.2 COMPLETA (d0386f3): nucleo/coverage.syn único (emisor cov_* +
                   reporte covrep_*/HTML), runtime/core/coverage.c/.h (buffer estático,
                   volcado JSON atexit), sondas _syn_cov OFF por defecto en S1 y nativo,
                   cli_test --coverage con JSON+HTML reales (Coverage: 66% en el probe);
                   oráculo 4/4, integration 6/6, unit 514/514; contrastar PASA;
                   expediente 34 anclas CUMPLE (evidencia b888fe497b9ae83c).
                   r153 (Opción A de H-R152-4, ratificada 2026-09-20): R1 builtins Lista/Mapa/
                   longitud delegando en runtime/core lista.c/mapa.c (ME f325 consumido);
                   R2 para-en paridad S1+nativo (T_EN, NODO_PARA_EN=57); R3 métodos postfijo
                   metodo:<tipo>:<nombre> (NODO_METODO=59); R4 cli_lint/fmt/test delegan en
                   lint/formatter/reports.syn importados; R6 RAII de retorno (temporal ANTES de
                   destructores, clase H-R146-1/H-R113); R5 bootstrap S1→S2 verde con módulos
                   importados. Oráculos r153 8/8; TDD módulos 3 GREEN; test_r3_param_adt GREEN;
                   matriz 35/35. Gates: contrastar PASA; verificar_alineacion SIN BRECHAS;
                   expediente r153 verificado (evidencia d5fb40c8d7530258; 40 CUMPLE +
                   3 DESVIACION ratificadas H-R153-NODE).
                   r151/r152: bootstrap restaurado (ver histórico de sesión 2026-09-20).
Commit fase:       b1ac1c2 (docs(manual): restaurar M7 §6.3 + cola §4.2 — guarda 7/7, autorización Arquitecto Opción A) sobre 63c1731 (test(opensyn): aserción L217 al nombre vigente validar_con_check — autorización regla 5 Opción A) sobre e0cbb35 (fix(transpiler): forma canónica "sino si" para elif — deuda test_control_flow_pipeline CERRADA; aserción L120 autorizada regla 5) sobre ff6c54a (test(integration): techo de tiempo 660 s para test_syquex_coverage — autorización Arquitecto regla 5) sobre 12b342d (feat(cli): `synapse lint/fmt` en el dispatcher Python — backend nativo + backing on-demand M1 §6) sobre 58ff1d1 (fix(formatter): cierre H-33.5-3 — dedupe lint→formatter + colapso fuera de literales + normalización fmt del nucleo) sobre 55a9950 (feat(33.5): certificación Fase 33 — bootstrap S2==S3 sellado en CI + dispatch canónico lint/fmt/test) sobre dfdb1bd (feat(33.4b): genéricos de usuario + para-en mapa en S1 y nativo — H-R153-3 CERRADA) sobre 5ff9235 (feat(33.4a): paridad del indexado de colecciones en S1 y nativo — H-R153-3) sobre d0386f3 (feat(coverage): --coverage con instrumentación de aristas en S1 y generador nativo — H-R152-1 CERRADA) sobre 4697132 (fix(compilador): imports fallback a raíz + FFI lista/mapa — H-CFG-4/H-CFG-5 RESUELTAS, bootstrap S1 reparado) sobre e780627 (docs manual2 §7.2, ME 33.1) sobre 96e72f4 (fix(sandbox): H-EOF-3) y 8375ec6 (feat(runtime): API de EOF stdin)
Próximo ME:        POST-FASE 33 — SIN deudas ejecutables de la certificación (las 3 de
                   FASE_33_CERTIFICACION §5 cerradas: formatter_fix 58ff1d1,
                   cli_lint_fmt 12b342d, fixture_syquex_timeout ff6c54a) y la deuda
                   test_control_flow_pipeline también CERRADA (transpiler_elif e0cbb35).
                   Deuda NUEVA documentada en R168: test_validation_loop_syn_exists
                   (nombre de función test vs código — requiere decisión del
                   Arquitecto). Leer ROADMAP con el Arquitecto para la siguiente
                   fase (termina en §33.5).
                   FASE 33 COMPLETA (33.1 e780627, 33.2 d0386f3, 33.4a 5ff9235, 33.4b dfdb1bd,
                   33.5 55a9950) — leer ROADMAP para la siguiente fase.                   ordenado del ROADMAP contradice M3 §3 L133) — RATIFICADA 2026-10-22
                   (el Arquitecto: "todo se ajusta a los manuales, incluyendo el
                   roadmap" → k=claves, forma implementada dfdb1bd, es la correcta),
                   H-CFG-2 (sandbox para lecturas builtin) — CERRADO en ME
                   r194_deuda_gobernanza (sandbox enraizado en emisores S1+nativo,
                   oráculo 4/4), H-R144-3 (cierre modelos.toml) — CERRADA 2026-10-22
                   (evidencia ETag 5/5), 3 SIN_CITA heredados de Fase 32 en
                   tests/opensyn — CERRADOS (OBL-M7-04/05/06 en MTO, auditor
                   rc=0); 33.3 (desviaciones R149 §5) — CERRADO (única desviación
                   vigente test_ai_explain, ya CERRADO en R183e); decisión NUEVA
                   D-R194-1 ratificada por el Arquitecto (allowlist suites-guarda
                   estructurales, 24 archivos, lista cerrada).
Próximo paso:      ME R181 — harness GCC (H-R176-1): reparar el comando gcc del
                   entorno de integración (rutas -I, embedded_libs.h, orden de
                   objetos, targets on-demand para los 21 RED TDD; ~27 fallos
                   de una vez). Luego R182+ feature gaps declarados (wasm F25,
                   RED TDD ME_27/29/30 D-5, H-R90-5) y NUEVO ME R183
                   coincidir_bloque_nativo (H-R180-1: cuerpos-bloque del caso
                   fallan en nativo TAMBIÉN para ADT — hallazgo de R180).
                   H-R177-2 CERRADA (R180 be5d447: patrón literal numero +
                   wildcard sobre primitivos con paridad S1↔nativo — parser
                   token_es_inicio_patron M3 §3, emisor switch-sobre-valor por
                   tipo C exacto espejo PRIMITIVOS de emit_control.py, S1
                   TokenID.NUMERO M1 §3.1, test r11 alineado via TDD/MTO con
                   OBL-M3-06; oráculo 4/4 detectó y cerró la heurística
                   invertida H-R180-3; lección H-R180-2: generator.syn es
                   concatenado de generador/ — rebuild SIEMPRE antes de
                   bootstrapear). H-R177-1 CERRADA (R179 0faea8e: código vigente
                   alineado a M2 §8.2 tras r153/H-R153-4b — test r27 alineado
                   via TDD/MTO, OBL-M2-05). H-R176-2 CERRADA (R178 95b2374,
                   synapse check --no-emit).
                   Continúa el mandato "repara todo" con el plan maestro
                   docs/plan_maestro_deudas.md; feature gaps: 3 RED
                   wasm extendido (Fase 25: i64/f64/imports/exports,
                   test_wasm_extended.py), ~21 RED TDD integration (ME_27/29/30,
                   D-5), H-R90-5 (métodos sobre locales en .syq); (4) nueva fase
                   del ROADMAP (termina en §33.5). Los 4 warps
                   paridad_syn_syq CERRADOS (90eb18c). H-R171-1 CERRADA (72d77f3). Barrido de las 39
                   citas sin sección REALIZADO (4a63327: DEUDA.md = 0/0). Deudas
                   CERRADAS esta sesión:
                   test_control_flow_pipeline (e0cbb35),
                   test_validation_loop_syn_exists (63c1731), TestRequisitosManuales
                   (b1ac1c2), test_permisos_cita_r6 (72d77f3). RATIFICACIONES/CIERRES
                   2026-10-22 (ME r194): D-R163-1 RATIFICADA (k=claves), H-CFG-2
                   CERRADO (sandbox emisores), H-R144-3 CERRADA (ETag 5/5),
                   3 SIN_CITA Fase 32 CERRADOS (OBL-M7-04/05/06), 33.3 CERRADO,
                   D-R194-1 (allowlist SNIFF_AMP) RATIFICADA;
                   R195_instalador CERRADA (2026-10-23, 53578a6): los 3 skips
                   de la familia instalador se cerraron ENTREGANDO el artefacto
                   exigido por cada test inmutable (sin tocar tests):
                   scripts/uninstall.py real (reversa install.sh + installer.syn,
                   --list/--dry-run/--yes, E2E en HOME temporal),
                   synapse_lsp.exe compilado en raíz con el pipeline real
                   (nucleo/lsp_v3.syn --release, 304 KB, artefacto local no
                   comiteado — regenerable con ese comando) e install.sh
                   delegador en raíz (M9 §7); familia 25 passed / 0 skipped
                   (rc=0).
Últimos commits:    3a0a0f7 (docs: post-commit R175 — reporte, bitácora y memoria; verificacion_ME sellada)
                    90eb18c (fix(syquex): retirar stubs de principal obsoletos — paridad .syn/.syq restaurada, 4 warps CERRADOS)
                    1e1584b (fix(syquex): 3 bugs del camino .syq — for-en SentenciaPara canónico, iterable en semántico, cast len)
                    4a63327 (fix(manual): barrido de las 39 citas sin sección — M7 §4.3/§6.1/§6.2/§6.4/§7.2/§8 restauradas + 3 re-anclajes; DEUDA.md = 0)
                    72d77f3 (fix(manual): restaurar M7 §7.3 + re-anclar permisos.syn — H-R171-1 CERRADA; autorización Opción A)
                    bf90262 (docs: post-commit R171 — verificación suite integración completa, 0 regresiones)
                    b1ac1c2 (docs(manual): restaurar M7 §6.3 textual + cola §4.2 — deuda TestRequisitosManuales CERRADA; autorización Opción A)
                    63c1731 (test(opensyn): aserción L217 al nombre vigente validar_con_check — deuda test_validation_loop_syn_exists CERRADA; autorización regla 5 Opción A)
                    e0cbb35 (fix(transpiler): forma canónica "sino si" para elif — deuda test_control_flow_pipeline CERRADA; aserción L120 autorizada regla 5)
                    ff6c54a (test(integration): techo de tiempo 660 s para test_syquex_coverage — el global de 300 s mataba el subprocess interno de ~500 s y abortaba la sesión pytest (autorización Arquitecto regla 5))
                    12b342d (feat(cli): `synapse lint/fmt` en el dispatcher Python — despacha al backend nativo (stage2) con backing on-demand del bootstrap (M1 §6))
                    58ff1d1 (fix(formatter): cierre H-33.5-3 — dedupe lint→formatter, colapso fuera de literales y normalización fmt del nucleo)
                    55a9950 (feat(33.5): certificación Fase 33 — bootstrap S2==S3 sellado en CI + dispatch canónico lint/fmt/test (M8 §4.1))
                    dfdb1bd (feat(33.4b): genéricos de usuario + para-en mapa en S1 y nativo — H-R153-3 CERRADA)
                    5ff9235 (feat(33.4a): paridad del indexado de colecciones en S1 y nativo — H-R153-3)
                    d0386f3 (feat(coverage): --coverage con instrumentación de aristas en S1 y generador nativo — H-R152-1 CERRADA)
                    4697132 (fix(compilador): imports con fallback a raíz + FFI lista/mapa con handle entero y firmas únicas — H-CFG-4/H-CFG-5 RESUELTAS; bootstrap S1 reparado H-CFG-5b)
                    e780627 (docs(manual2): tabla §7.2 corregida contra el nativo + filas NODO_PARA_EN=57/NODO_METODO=59 + oráculo de paridad 3-vías — ME 33.1)
                    96e72f4 (fix(sandbox): rutas relativas y sandbox de std.sistema operativos — H-EOF-3 RESUELTA; H-CFG-2 registrada: lecturas builtin sin sandbox)
                    8375ec6 (feat(runtime): API de EOF de stdin — stdin_eof distingue EOF de línea vacía, H-EOF-1 RESUELTA; cita fabricada io.c L58 re-anclada)
                    070a9be (docs: post-commit R155/R156/R157 — reportes, bitácora y memoria)
                    1f5f7e3 (test(config): registrar markers tdd y e2e en pytest.ini — H-AUD-OP-3, oráculo detectó además e2e sin registrar)
                    9a9170c (test(auditoria): oráculo de frescura y humo para dist/bin/opensyn.exe — H-AUD-OP-2, exe regenerado 23:22 con fix EOF)
                    830074a (fix(opensyn): cierre determinista del chat y menú ante EOF de stdin — H-AUD-OP-1, contadores eof_consecutivos/intentos_menu)
                    d9e842c (feat(r153): métodos, genéricos y for-en en S1+S2 — flip backend lint/fmt/test a los módulos .syn)
                    dbb9717 (fix(r152): restaurar el enlace del bootstrap S1 — R1 par F5-1, R2 backend lint/fmt/test)
                    5db1dab (test(r151): alinear línea base MTO/TDD — bootstrap on-demand, cita real M7 §2.2)
                    f36849c (fix(r150): cerrar hallazgos funcionales std↔runtime — matriz 35/35, CI, D-R150-9 ratificada)
                    8247564 (docs: post-commit R150 — reporte, bitácora y memoria)
                    d040500 (fix(r149): reparar hallazgos R149 — std/, runtime tiempo, fuga RAII, OpenSyn compilable, --check)
                    de7107c (feat(opensyn): Fase 32.2 — explorer_det + architect_det deterministas)
                    fa34825 (feat(nucleo): Fase 32.1 — grafo de conocimiento)
```

### ME r204_tools_escritura (2026-11-09, f018957)
- Hallazgo H-R204-1 (RESUELTO): doble free en `opensyn/permisos.syn` por pasar
  `texto` sin copia a funciones que consumen el parámetro (RAII); corrompía el
  pool TLS y producía contenido truncado/aliasado. Resolución: `_syn_strcpy`
  en los call sites; constantes y comportamiento intactos.
- Hallazgo H-R204-2 (RESUELTO): `strcpy_f` no existe para `main.py`; la copia
  canónica es `_syn_strcpy(var)` (`std/texto.syn`, `runtime/core/string_utils.c`).
- Lección: el sandbox se valida antes de la herramienta; `../malo.txt` se
  rechaza como denegación de sandbox (Manual 7 §7.3), no como error de escritura.
- Lección: helpers con retorno único a profundidad 0 liberan params/local de
  forma consistente; retornos anidados no.
- Plan maestro redactado en `docs/gobernancia/PLAN_MAESTRO_INDUSTRIAL.md`
  (2026-11-09, pendiente de ratificación del Arquitecto); siguiente ME
  propuesto: `r205_grafo_conocimiento`.

### ME r205_grafo_conocimiento (2026-11-10, b1e9959)
- Hallazgo H-R205-1 (RESUELTO): `g.hash_ast` quedaba corrupto tras construir
  un segundo grafo porque el duplicado del hash se calculaba en un local y el
  scope liberaba la memoria del pool. Resolución: calcular `calcular_hash_ast`
  inline en el constructor; el hash SHA-256 vive en malloc y permanece estable.
- Hallazgo H-R205-2 (RESUELTO): `nucleo/grafo_conocimiento.syn` tenía UTF-8
  doblemente codificado (secuencias U+00C2/U+00A7 y U+00C3/U+00B3 en lugar de
  `§` y vocales acentuadas); reparado a UTF-8 real y recompilado. Las citas
  `Manual 32` no son indexables por `indice_manual.py`
  (solo indexa `MANUAL N.md`); se anclaron las citas de producción a Manual 6
  §1.1 y Manual 2 §5.1/§7.3, manteniendo Manual 32 en plan/verificación.
- Lección: en S1 el ownership de `texto` exige duplicar en cada frontera;
  liberar un hash local después de duplicarlo puede dejar el duplicado en una
  ventana de reutilización del pool.
- Lección: el gate de lectura previa ve archivos ajenos sin commitear; se
  registró la lectura de `nucleo/lsp_v3.syn` (Manual 8 §1.7.4) sin modificar
  ni incluir ese archivo.
- Verificación: grafo 14/14, suite OpenSyn 123 passed/1 skipped, gate Fase 32
  2/2, `contrastar` 7 requisitos/1 oráculo, `alineacion` 1 archivo,
  `verificar_alineacion` 0 brechas; evidencia `b09dd7fb5f82ba7f`.

### ME r205b_lsp_v3 (2026-11-10, 5935a5d)
- Hallazgo H-R205b-1 (RESUELTO): `nucleo/lsp_v3.syn` tenía una `funcion
  longitud` duplicada y `cmp_texto` restaba textos. Resolución: eliminar el
  duplicado y usar `_syn_strcmp` en `cmp_texto`; `strstr_f`/`strlen_s` se
  reemplazan por `indice_de`/`_syn_strlen`.
- Hallazgo H-R205b-2 (RESUELTO): `enviar_respuesta` liberaba `header` y
  `respuesta` dos veces porque `escribir` consume su argumento; el pool se
  corrompía y sólo se procesaba el primer mensaje. Resolución: pasar
  `_syn_strcpy(header)` y `_syn_strcpy(respuesta)`.
- Hallazgo H-R205b-3 (RESUELTO): `shutdown` como notificación sin `id`
  rompía el contrato `id >= 0`. Resolución: contrato `id >= -1` y respuesta
  sólo si `id >= 0`.
- Autorización explícita del Arquitecto para reparar `nucleo/lsp_v3.syn`
  (trabajo ajeno) pese a la regla del plan maestro; se dejaron fuera
  `docs/gobernancia/GUIA_DE_GOBERNANZA.md` y los artefactos no rastreados.
- Lección: `longitud` libera su parámetro; para medir sin transferir ownership
  se usa `_syn_strlen`. `escribir` también consume; en cada frontera hay que
  duplicar con `_syn_strcpy`.
- Verificación: build OK, 13 tests LSP verdes, `contrastar` 3 requisitos/3
  oráculos, `alineacion` 1 archivo, `verificar_alineacion` 0 brechas;
  evidencia `c01c7e55ec8d56b9`.

### ME r208_run_manager (2026-11-10, 95ea023)
- `opensyn/run_manager.syn` compila y ejecuta E2E: checkpoints persistentes,
  reanudación desde la última subtarea completada, timeout absoluto de 300 s,
  fallo tras 3 intentos, límite de 20 subtareas y `run_id` único con secuencia
  estática. `OPENSYN_RUNS_DIR` aísla los runs en pruebas.
- Hallazgo H-R208-1 (RESUELTO): `_syn_escribir_archivo` devuelve `0` en éxito,
  pero el módulo comparaba contra `1`; todo checkpoint se reportaba como
  fallido. Resolución: `escribir_checkpoint_local` retorna `0/-1` y
  `guardar_checkpoint` comprueba `exito == 0`.
- Hallazgo H-R208-2 (RESUELTO): los parámetros `texto` se consumen en las
  fronteras; reutilizar `run_id`/`checkpoint_path`/`contenido` causaba doble
  free. Resolución: `_syn_strcpy` en cada llamada que conserva la cadena.
- Hallazgo H-R208-3 (RESUELTO): dos runs creados en el mismo milisegundo
  compartían `run_id`. Resolución: `siguiente_secuencia_run` con contador
  estático ASM; IDs `run_<ms>_<seq>`.
- Hallazgo H-R208-4 (RESUELTO): el expediente quedó doblemente codificado en
  UTF-8 por `Get-Content`/`Set-Content` de PowerShell 5.1 y las citas con
  acentos no resolvían. Resolución: reescribir el expediente como UTF-8 real y
  re-verificar (evidencia `10cc67173f42e68a`).
- Lección: los tests estructurales existentes exigen los símbolos ASM
  `clock_gettime`, `snprintf` y `memcpy`; se restauran helpers locales
  (`ahora_ms`, `entero_a_texto`, `concatenar_texto`) en lugar de editar tests.
  `entero_a_texto` usa `pool_alloc` para no devolver un buffer de stack.
- Verificación: build OK, oráculo E2E 1/1, runs reanudables 70/70, gate Fase 32
  2/2, `contrastar` 4 requisitos/1 oráculo, `alineacion` 1 archivo,
  `verificar_alineacion` 0 brechas; evidencia `10cc67173f42e68a`.

### ME r212_memoria_cifrada (2026-11-11, 4ab0406)
- `opensyn/memoria_persistente_cifrada.syn` (777 líneas) compila y ejecuta E2E:
  `PatronAprendido`, `MemoriaNegativa`, `EntradaCifrada`, `CapaMemoria` y
  `MemoriaCifrada`; cifrado real con
  `cluster_sesion_cifrar_buffer`/`cluster_sesion_descifrar_buffer`; KDF SHA-256
  iterado (20000 rondas) con sal de hardware; almacén cifrado plano
  línea-a-línea en `~/.opensyn/memoria.db`.
- Hallazgo H-R212-1 (RESUELTO parcial): Argon2id no existe en el runtime;
  `derivar_clave` usa SHA-256 iterado. Resolución: implementar Argon2id en un ME
  posterior; el módulo queda aislado tras `derivar_clave`.
- Hallazgo H-R212-2 (RESUELTO parcial): no hay API SQLite expuesta a Synapse;
  la capa Evolución usa almacén cifrado plano. Resolución: binding SQLite
  cifrado cuando el runtime lo exponga.
- Hallazgo H-R212-3 (RESUELTO): S1 no soporta globales mutables; la API usa
  `MemoriaCifrada` explícito y el llamador reasigna el estado devuelto.
- Hallazgo H-R212-4 (RESUELTO): el E2E destapó triple free en `tokenizar`;
  `tokens.agregar(minusculas(actual))` duplicaba la expresión en el constructor
  y `minusculas` (pura) libera su parámetro. Resolución:
  `let token = minusculas(_syn_strcpy(actual))` antes de `agregar`.
- Lección: el E2E de comportamiento detecta corrupciones de pool que `--check`
  y los tests estructurales no ven; `_syn_a_texto_decimal` usa `%g` (`0.9`, no
  `0.900000`); un driver de persistencia debe ser idempotente.
- Verificación: build OK, oráculo E2E 1/1, test estructural existente 14/14,
  gate Fase 32 2/2, `contrastar` 3 requisitos/2 oráculos, `alineacion` 1
  archivo, `verificar_alineacion` 0 brechas; evidencia `cc3cf959ff0b1a25`.

### ME r217_integracion_determinista (2026-11-11, 6497e80)
- `opensyn/pipeline_multiagente.syn` importa `opensyn.explorer_det.syn` y
  `opensyn.architect_det.syn`; retira las copias locales de `ArchivoRelevante`,
  `NodoAfectado`, `ContratoCritico`, `Ciclo`, `MetricasImpacto`,
  `explorar_contexto`, `analizar_impacto_completo` y `archivo_de_id`.
- La fase Architect consume `AnalisisImpacto` y copia sus métricas aplanadas
  (`metricas_total_afectados`, `metricas_profundidad_maxima`,
  `metricas_contratos_criticos`, `metricas_ciclos_potenciales`) a
  `ContextoPipeline`.
- Hallazgo H-R217-1 (RESUELTO): al importar `explorer_det` y `architect_det`
  juntos, `a_texto` colisiona (`std.texto.a_texto(entero)` vs
  `std.json.a_texto(NodoJson)`) y falla la compilación C, no el `--check`.
  Resolución: `architect_det` usa `entero_a_texto`.
- Deuda r217 de R207 (RESUELTA): Explorer/Architect deterministas ya se
  reutilizan en el pipeline; el cableado a un grafo persistido real sigue
  pendiente en `cargar_grafo_proyecto` (devuelve grafo vacío).
- Verificación: probe modular con ambos imports y enlace OK, pipeline existente
  + E2E 16/16, architect existente + E2E 12/12, gate Fase 32 2/2, regresión
  combinada 114/114, `contrastar` 3 requisitos/2 oráculos, `alineacion` 2
  archivos, `verificar_alineacion` 0 brechas; evidencia `c5e70770a1514592`.

### ME r215_tool_patch (2026-11-12, c1d051d)
- `opensyn/herramientas.syn`: `herramienta_aplicar_patch(ruta, diff, cwd)` y
  `herr_aplicar_diff` aplican diffs unificados en memoria; contexto/borrado
  estricto, hunks `@@`, adición, `\ No newline at end of file` y rechazo del
  parche completo ante cualquier desajuste. La ruta se valida con
  `herr_ruta_permitida` antes de leer o escribir.
- `opensyn/principal.syn`: `TOOL aplicar_patch <ruta> :: <diff>` con
  normalización de ruta a absoluta antes del sandbox; alias `aplicar_patch` →
  `editar` en la matriz de permisos (MAX_HERRAMIENTAS=8 intacto), aprobación ASK
  y denegación cerrada en stdin no interactivo. System Prompt actualizado.
- Oráculo nuevo `tests/integration/test_tool_patch.py` 3/3: parche aplicado,
  contexto inválido rechazado, archivo nuevo, marcador no-newline, escape `..`
  denegado, ASK deniega en pipe, aprobado aplica y modo ASK bloquea. Regresión
  `test_herramientas_escritura.py` + `test_permisos_opensyn.py` 46/46.
- Lección: validar el diff completo antes de escribir evita archivos a medias;
  el marcador `\ No newline` tras un borrado no debe quitar el salto de la línea
  anterior; aliasar a `editar` preserva el contrato inmutable de permisos.
- Verificación: `--check --no-emit` rc=0 en ambos módulos, `contrastar` 3
  requisitos/1 oráculo, `alineacion` 2 archivos, `verificar_alineacion` 0
  brechas; evidencia `d815bb878cda3f41`.

### ME r219_verificacion_aot (2026-11-13, 26e4cf8)
- `opensyn/verificacion_aot.syn`: validación del código generado con
  `synapse check --no-emit`, generación de hasta 5 casos límite, compilación y
  ejecución con timeouts, y resumen en `Verificacion`.
- H-R219-1 (RESUELTO): el wrapper generado de `sha256_texto` libera su
  argumento; `aot_nombre_base` le pasaba `caso.codigo_ejecucion` y el campo
  quedaba liberado, corrompiendo el driver del caso máximo. Fix:
  `sha256_texto(_syn_strcpy(caso.codigo_ejecucion))`.
- H-R219-2 (RESUELTO): `elemento_texto` devuelve copia para no liberar elementos
  de la lista; `aot_valor_default`/`aot_valor_caso` usan una variable
  `resultado` con un único `retornar`.
- Oráculo E2E nuevo `tests/integration/test_verificacion_aot_e2e.py` 2/2
  (válido 5 casos/0 fallos; inválido `CHECK=error` sin residuos) + suite
  estructural 13/13 = 15 passed.
- Lección: un campo de struct pasado a una función que libera su parámetro
  transfiere propiedad; copiar con `_syn_strcpy`. El E2E debe fijar `cwd` para
  que `CreateProcess` no resuelva un `synapse.exe` stale del repo.
- Verificación: `--check --no-emit` rc=0, `contrastar` 4 requisitos/2 oráculos,
  `alineacion` 1 archivo, `verificar_alineacion` 0 brechas; evidencia
  `c0a201a1ecbe7d72`.

### ME r216_tool_ejecutar (2026-11-12, 7adc440)
- `runtime/core/proceso.c/.h` (NUEVOS): `_syn_capturar_comando_timeout`
  devuelve `[RC]<rc>\n<salida>`, capa a 32 KB, usa `pool_alloc` y rc 124 en
  timeout. Windows `CreateProcessA`; POSIX `fork` + `execvp` con argv dividido
  por espacios, sin `system()` ni `sh -c`.
- `opensyn/herramientas.syn`: allowlist `synapse check`, `synapse build`,
  `pytest`, `git status`, `git diff`; rechazo de metacaracteres de shell, `..`,
  rutas absolutas (incluidas tras '=') y flags `--ext-diff`/`--textconv`/`--output`; helpers con
  contratos y `herramienta_ejecutar`.
- `opensyn/principal.syn`: despacho `TOOL ejecutar` en Code/Debug, alias
  `ejecutar` → `compilar` solo en la matriz (MAX_HERRAMIENTAS=8 intacto),
  prompt y ayuda actualizados.
- Oráculo nuevo `tests/integration/test_tool_ejecutar.py` 4/4: allowlist/
  inyección, modos ASK/Code, ejecución permitida y timeout con shim real;
  guarda de fuente sin `system`/`/bin/sh`/`execl`. Regresión patch+permisos+
  escritura 49/49 y control de alineación 24/24.
- Lección: el timeout debe terminar el hijo y cerrar el pipe; en Windows
  `TerminateProcess` no mata nietos; POSIX debe evitar `sh -c`; los comentarios
  finales cambian el `cambio_hash` y obligan a re-sellar el expediente.
- Verificación: `--check --no-emit` rc=0, `contrastar` 2 requisitos/1 oráculo,
  `alineacion` 4 archivos, `verificar_alineacion` 0 brechas; evidencia
  `db8058173bc4604a`.

### ME r218_bootstrap_json (2026-11-12, e2ec33f)
- `nucleo/principal.syn` incluye `std/json.syn` y `std/texto.syn` en el unity
  build nativo antes de `nucleo/actualizador.syn`; se mantiene en 1200 líneas
  (límite R13).
- Causa raíz H-R218-1 (RESUELTO): `gen_emitir_linea` truncaba en silencio al
  superar 1 MB; el C del compilador (1.072.939 bytes con CRLF) perdía `int
  main` y dejaba `return _rc;` fuera de función. Resolución: buffer de 4 MB en
  `emision_c.syn`, `nodos_flujo.syn`, `orquestador.syn` y
  `compilador/generator/generator.py`.
- H-R218-2 (RESUELTO): la inferencia nativa asumía `int64_t` en `OpBinaria`,
  llamadas y acceso a campo. Resolución: `_syn_nativo_expr_tipo_c` con paridad
  S1 (lógicos/comparación → `int`, `double` si algún lado, fallback por
  `_G_native_tipo_retorno`/`_G_native_campo_tipo`).
- `nucleo/generator.syn` se regeneró desde `nucleo/generador/*.syn` con
  `_rebuild_generator.py`; `fmt --check` GREEN y módulos reformateados.
- Lección: `generator.syn` es concatenado; los arreglos van en los submódulos y
  el bootstrap S2==S3 es el oráculo real. El truncamiento silencioso no produce
  diagnóstico; el buffer necesita margen.
- Verificación: S1/S2/S3 rc=0, S2==S3 SHA256
  `950AA09B8C3204E2A8FCC95102265FCB03AD5C7E2AC6E59997FAF6D94FA71B2A`,
  `fmt --check` correcto, 16/16 oráculos de auditoría, `contrastar` 2
  requisitos/1 oráculo, `alineacion` 9 archivos, `verificar_alineacion` 0
  brechas; evidencia `8cfce46f5d55e053`.

### ME r211_architect_det (2026-11-11, b3180ed)
- `opensyn/architect_det.syn` compila con `--check --no-emit` y ejecuta E2E:
  DFS invertido con dependientes directos/indirectos, contratos críticos,
  detección de ciclo por nodo y métricas de impacto sobre `GrafoProyecto`.
- Hallazgo H-R211-1 (RESUELTO): el codegen emite campos ADT anidados como
  puntero y el constructor con valor falla en el enlace del driver. Resolución:
  aplanar `MetricasImpacto` en campos enteros dentro de `AnalisisImpacto`;
  `MetricasImpacto` se conserva como tipo público. La deuda de codegen sigue en
  H-R207-1.
- Hallazgo H-R211-2 (RESUELTO): `NodoAfectado.tipo_relacion` se llenaba con el
  tipo de arista (`llamada`); debe describir la relación de impacto
  (`dependiente`). Resolución: valor fijo `dependiente` en
  `analizar_impacto_completo`.
- Deuda r217 (RESUELTA en 6497e80): `explorer_det` (r210) y `architect_det`
  (r211) ya se integran en `pipeline_multiagente`; las fases locales fueron
  retiradas.
- Verificación: build OK, oráculo E2E 1/1, architect existente 11/11, gate Fase
  32 2/2, regresión combinada 114/114, `contrastar` 3 requisitos/1 oráculo,
  `alineacion` 1 archivo, `verificar_alineacion` 0 brechas; evidencia
  `6ac72a2f8744254a`.

### ME r210_explorer_det (2026-11-11, 990aedb)
- `opensyn/explorer_det.syn` compila con `--check --no-emit` y ejecuta E2E:
  BFS por archivo sobre `GrafoProyecto`, dependencias/dependientes, radio 0/1/2,
  deduplicación por archivo y distancia entre IDs de nodo.
- Hallazgo H-R210-1 (RESUELTO): S1 no reconoce `continuar`. Resolución:
  condiciones anidadas/invertidas en los bucles.
- Hallazgo H-R210-2 (RESUELTO): la indexación de `Lista<texto>` infería `int`
  y comparaba texto con int. Resolución: `elemento_texto(Lista<texto>, entero)`
  con retorno `texto` y contrato.
- Hallazgo H-R210-3 (RESUELTO): `Manual 32` no existe como `MANUAL 32.md`; el
  archivo real es `MANUAL  FASE 32 AGENTE DE CODIFICACIÓN.md` (doble espacio).
  Resolución: el gate se ancla en Manual 6 §1.1 y Manual 2 §5.1; Manual 32
  §4.3/§4.6 queda como referencia funcional declarada.
- Hallazgo H-R210-4 (RESUELTO): el pre-commit exige Manual 7 para `opensyn/*`
  según `mapa_manuales.md`. Resolución: registrar también Manual 7 §2.3
  (extracción de contexto del AST/RAG) antes del commit.
- Deuda r217 (RESUELTA en 6497e80): `explorer_det` y `architect_det` ya se
  integran en `pipeline_multiagente`; las fases locales fueron retiradas.
- Verificación: build OK, oráculo E2E 1/1, explorer existente 6/6, gate Fase 32
  2/2, regresión combinada 102/102, `contrastar` 3 requisitos/1 oráculo,
  `alineacion` 1 archivo, `verificar_alineacion` 0 brechas; evidencia
  `8c52618300038933`.

### ME r209_router_chat (2026-11-10, 3064d40)
- `opensyn/router.syn` y `opensyn/chat.syn` compilan con `--check --no-emit`
  y ejecutan E2E: clasificación de tareas, modo, plan, file finder, parseo
  `linea:columna`, extracción de bloques en router/chat, validación de código
  vacío y selección de modelo desde `~/.opensyn/config.toml` con fallback.
- Hallazgo H-R209-1 (RESUELTO): el router usaba `cmp_texto`, `strstr_f` y
  `atoi_f` sin declararlos, y asignaba variables sin `let`. Resolución:
  wrappers deterministas sobre `std.texto`/externos y declaraciones `let`.
- Hallazgo H-R209-2 (RESUELTO): `ejecutar_lint`/`ejecutar_fmt` declaraban
  `texto` pero `ejecutar_comando` retorna `entero`. Resolución: tipo de retorno
  `entero`; no hay consumidores que esperen texto.
- Hallazgo H-R209-3 (RESUELTO): `prompt.datos` puede ser de solo lectura;
  escribir el truncado in situ fallaba. Resolución: reasignar con
  `subcadena(prompt, 0, max_chars)`.
- Hallazgo H-R209-4 (RESUELTO): `chat.syn` usaba sintaxis no soportada (`[]`,
  `intentar`, `para cada`, argumentos con nombre). Resolución: reescritura a
  `Lista<texto>()`, `para ... en`, `romper`/`siguiente`.
- Hallazgo H-R209-5 (RESUELTO): `leer_archivo` rechaza rutas fuera del cwd y
  `~/.opensyn/config.toml` vive en el perfil. Resolución: `_syn_leer_archivo`
  para la configuración.
- Hallazgo H-R209-6 (RESUELTO): `opensyn/orchestrator.h` declara la API de
  lifecycle pero no existe implementación C enlazable. Resolución: stubs
  locales deterministas; la integración real queda para el ME de orchestrator.
- Lección: los parámetros `texto` se consumen en las fronteras; si el llamador
  conserva la cadena debe pasar `_syn_strcpy`.
- Verificación: builds OK, oráculo E2E 1/1, gate Fase 32 2/2, regresión 75/75,
  `contrastar` 5 requisitos/1 oráculo, `alineacion` 2 archivos,
  `verificar_alineacion` 0 brechas; evidencia `d0a46a4e11076ea6`.

### ME r207_pipeline_multiagente (2026-11-10, a578e03)
- `opensyn/pipeline_multiagente.syn` compila y ejecuta E2E: imports
  `nucleo.grafo_conocimiento`/`opensyn.validation_loop`, estructuras reales del
  grafo, Explorer/Architect deterministas locales, prompts Coder/Reviewer/Fixer,
  `_syn_ollama_consultar` con overrides de host/puerto/modelo, máximo 3
  inferencias y validación final con `validar_con_check`.
- Hallazgo H-R207-1 (RESUELTO): el codegen emite campos struct anidados como
  puntero y el constructor compound-literal falla en C. Resolución: aplanar
  `MetricasImpacto` en `ContextoPipeline` y retornar `MetricasImpacto` (solo
  escalares); las listas de afectados/contratos/ciclos se usan localmente.
- Hallazgo H-R207-2 (RESUELTO): `std.texto.a_texto` colisiona con el conversor
  JSON del grafo. Resolución: `json_entero`/`json_decimal` usan `_json_a_texto`.
- Hallazgo H-R207-3 (RESUELTO): `_syn_ollama_consultar` ya está exportado por
  `validation_loop`; redeclararlo produce “Redefinición”.
- Deuda r217 (RESUELTA en 6497e80): `explorer_det` (r210, 990aedb) y
  `architect_det` (r211, b3180ed) ya se integran en el pipeline; las fases
  locales fueron retiradas. El codegen de structs anidados sigue pendiente
  (H-R207-1; r211 lo evitó aplanando las métricas).
- Verificación: build OK, oráculo E2E 1/1, pipeline existente 15/15, grafo 1/1,
  gate Fase 32 2/2, `contrastar` 4 requisitos/1 oráculo, `alineacion` 2 archivos,
  `verificar_alineacion` 0 brechas; evidencia `15b96b3c8f8fe172`.

### Cambios recientes esta sesión
| Commit | Descripción | Impacto |
|--------|-------------|---------|
| `b3720d3` | R272/ME r272_docs_encoding (P0): el encoding documental pasa a verificarse por bytes. `verificar_manuales.py --encoding --docs` recorre todo `docs/` y rechaza BOM, U+FFFD, controles C1 y doble codificacion (rc=0 sobre el arbol completo); la auditoria canonica y `docs/reportes/R205.md` llevan la cabecera `> Documento informativo. La fuente de verdad es `docs/manuales/`.` y conservan su contenido (>=1.275 lineas en la auditoria). No se reescribieron manuales de produccion ni se normalizaron documentos sanos. ME documental: sin archivos de produccion, sin expediente ni marcas `cumple`. Oraculo nuevo `tests/auditoria/test_docs_encoding_r272.py` 3/3; `contrastar --plan` 2/2 PASS; `verificar_alineacion` 0 brechas. Reporte: `docs/reportes/R272.md` |
| `7cc1d91` | R273/ME r273_installer_modelo_grande (P0 producto): `tests/opensyn/test_installer.py` fallaba por timeout (10 s) al verificar el GGUF local de 873 MB. Sonda con `_syn_ahora_ms` aislo el coste: **9.000 ms de 10.300 ms en `_syn_hash_archivo`** (hardware/config 0 ms). Tres causas: `sha256_update` copiaba byte a byte, `sha256_transform` sin ventana rodante y cero memoria del digest. Fix: bloques con `memcpy` + ventana de 16 palabras desenrollada (mismo digest FIPS 180-4; 126→138 MB/s), streaming con buffer de 1 MiB (antes 8 KB por `fread`), modulo NUEVO `runtime/core/hash_cache.c/.h` (cache por ruta+tamano+mtime en `~/.synapse/cache/hash/`, escritura atomica, opt-out `SYNAPSE_HASH_CACHE=0`, no cachea archivos con mtime < 5 s) y `opensyn/installer.syn` reporta `Verificacion SHA-256: N ms (M MB/s)` con aviso previo. Hallazgo colateral: `_syn_archivo_tamano` con `const char*` invocada desde Synapse repetia el ABI mismatch de R197 (devolvia -1) → wrapper `_syn_tamano_archivo(CadenaSegura)`. Medido: 10,3 s → 6,5 s frio y 0,07 s caliente; test preexistente PASA sin tocarlo (9,76 s con compilacion); oraculo nuevo 17/17; `contrastar` 3/3 PASS; `alineacion --verificar` 6 archivos (evidencia `e71dee4a8e127026`); `verificar_alineacion` 0 brechas; S2==S3 `49d7c51ac63e28a6`. Incidente: `os.replace` fallo con WinError 5 por un `synapse_stage1.exe` colgado (PID 6488). Reporte: `docs/reportes/R273.md` |
| `6497e80` | R217/ME r217_integracion_determinista: `opensyn/pipeline_multiagente.syn` importa `opensyn.explorer_det.syn` y `opensyn.architect_det.syn` y retira las estructuras/funciones deterministas locales; la fase Architect usa `AnalisisImpacto` aplanado. `architect_det` cambia `a_texto` por `entero_a_texto` para evitar la colisión con `std.json.a_texto` al importar ambos módulos (H-R217-1). Probe modular con ambos imports y enlace OK; pipeline existente + E2E 16/16, architect existente + E2E 12/12, gate Fase 32 2/2, regresión combinada 114/114; evidencia `c5e70770a1514592`; `contrastar` 3 requisitos/2 oráculos, `alineacion` 2 archivos, `verificar_alineacion` 0 brechas. Deuda r217 de R207 cerrada; queda pendiente cablear `cargar_grafo_proyecto` a un grafo persistido real. Reporte: `docs/reportes/R217.md` |
| R176 | Re-baseline suite integración COMPLETA tras los 2 MEs de la sesión (mandato "primera sugerencia + alinea todo"): 1596 tests → 1453✓/104✗/39skip (2:12:18) vs R171 1447✓/110✗ → **+6✓/−6✗ = MEJORA, no regresión**. Composición EXACTA de las 6 bajas: 4 warps paridad (cerrados por 90eb18c, 6/6 en suite) + 2 bajas netas familia GCC test_e2e_adv_10 (7→5, composición irrecuperable: R171 no individualizó y lastfailed sobrescrito). 0 regresiones certificadas: 21 RED TDD IDÉNTICOS uno a uno, ninguna familia creció, 3 ambiguos FALLAN aislados (link runtime completo, no tocan .syq). 104 clasificados con parseo de los 99 bloques de traceback: 21 RED TDD declarado EXACTOS, 10 YAML CI, 27 GCC entorno = **H-R176-1** (ALTO, ME candidato radio ~27), 8 compila .syn, 46 asserts, 4 flaky entorno, 3 lifetimes, 3 cli_check = **H-R176-2** feature gap declarado, 1 wrapper. Gates "alinea todo": SIN BRECHAS + DEUDA 0/0 — 0 brechas de alineación en los 104. Artefactos regenerados restaurados (suite regenera también test_cluster_handshake.c, fuera del patrón _*.c). Verificación pura: 0 producción/0 tests; reporte docs/reportes/R176.md |
| R179 | ME r27_ctor_aridad COMPLETADO (0faea8e): H-R177-1 CERRADA — aridad del ctor de struct en el analizador nativo con paridad S1. R1 (M2 §2): registrar_estructura puebla total_campos contando la cadena NODO_PARAMETRO via slot [6] canonico (patrón ADT de analizar_paso_estructuras); R2 (M2 §8.2): check de aridad restaurado en NODO_LLAMADA — struct no-función con 0<args≠campos → ERR_SEM_ARGUMENTOS_INVALIDOS rc=7, mensaje paridad S1. Oráculo NUEVO test_oraculos_r27_ctor_aridad.py 4/4 GREEN (144 s; auto-compilación 37747 nodos con check activo, cero falsos positivos; probes Punto(1,2)→12, Punto(1)→rc7 paridad, Punto()→0). Tests modificados AUTORIZADOS (regla 5/TDD/MTO): test_r27 de test_fase2_nativa_hm alineado de la forma pre-r153 deprecada a la ley vigente + test_r27_struct_ctor_aridad_invalida_rechazada NUEVO (3/3 con -k r27); OBL-M2-05 añadida al MTO (50 entradas OK). Gates MTS: contrastar PASA (4 requisitos, marca en UNA línea — el regex no cruza saltos), huella 1ff87d0097335768 (evidencia auditoria/evidencia/1ff87d0097335768.json), verificar_alineacion SIN BRECHAS, lectura previa OK. H-R179-1 cerrado: hijos del nodo plano viajan en slot [6] (nodo_expr), NO en .hijo_izq — el .hijo_izq contó 0 campos y el check rechazó la auto-compilación (stage2 rc=7); bootstrap la detectó. Bootstrap S1→S2 rc=0; unit 514✓; mb+nucleo+synapse 30✓; matriz 35✓. Reporte: docs/reportes/R179.md |
| R177 | ME nativa_rc5_familia COMPLETADO (4ebd025): familia de fallos nativos rc=5/rc=0 de test_fase2_nativa_hm reparada — 8 fallos → 1 (r27 = H-R177-1 para el Arquitecto). R1 canal(...) en EXPRESIÓN (parser_expr.syn, M5 §3.2; gcc rc=5 'entero' undeclared); R2 constantes tipadas no-texto (escaneo.syn _G_native_consts_txt + expr_eval.syn rama _ot==30: concat solo si el inicializador es texto, M2 §2/§4.1); R3 pool_destroy DESPUÉS de esperar fibras en _emit_main ×4 (M6 §2.2; antes segfault 0xC0000005 por args liberados; cita fabricada M6 §4.4→§2.2 corregida); R4 asignación a variable nueva con RHS Identificador hereda el tipo C (funciones.syn + nodos_flujo.syn, paridad S1 tipo_de_expr, M2 §8.2); R5 constantes de módulo S1 como enum/static const con guardas _SYN_CSTDECL_ y excepción ABI T_*/NODO_*/ERR_*/_ — el #define se expandía dentro de firmas que sombrean (M2 §2). Oráculo NUEVO test_oraculos_nativa_rc5_familia.py 5/5 GREEN; bootstrap S1→S2 rc=0; unit 514✓; mb+synapse+nucleo 30✓; matriz 35✓; fase2 familia 10✓/1✗. Gates MTS: contrastar PASA (5 requisitos, oráculo ejecutado release), huella 828a4be257954718, verificar_alineacion SIN BRECHAS. H-R177-2 NUEVO (paridad de parser: coincidir sin literales/wildcard en nativo). Tests: NINGUNO modificado. Reporte: docs/reportes/R177.md |
| `90eb18c` | R175/ME paridad_principal_syq (4 warps de paridad CERRADOS): retirados los 2 stubs de principal obsoletos — pipeline.py inyectaba `funcion principal()` en el source vía tempfile (H-R90-8b) y el puente lo añadía al AST como fallback (ME-R90-8); el pretexto "el runtime S1 filtra funciones sin principal" es FALSO con el frontend actual (probe). M1 §3.1 mismo AST canónico + M3 §3 L78 principal opcional + main de biblioteca D-R150-4. test_paridad_syn_syq 6/6 (antes 4✗); E2E dual rc=7/rc=0; 405✓/3✗ (solo wasm RED TDD); unit 514/514; matriz 35/35; huella 907275bc6b04e287. Tests sin modificar. Lecciones: un workaround sin test que demuestre su necesidad es deuda que degrada; probe del pretexto ANTES de tocar. Reporte: docs/reportes/R175.md |
| `1e1584b` | R174/ME puente_for_en_syq (primera reparación FUNCIONAL del camino .syq): 3 bugs reales — (1) puente_canonico._nodo_para_en producía SentenciaMientras con _paraind usada antes de declararse (errores espurios "Variable '' no declarada") → ahora nodo canónico SentenciaPara(variable, iterable, cuerpo) que visitar_para ya procesa (paridad .syn/.syq, M3 §3); (2) semantic_checker range-for miraba solo condicion (convención parser S1) y el puente pone iterable → variable tipada 'puntero'; ahora mira ambos; (3) builtin len sin cast (void*)(intptr_t) (gemelo longitud sí) → gcc -Wint-conversion. test_result 5/5 GREEN (operador ? por PRIMERA VEZ), unit 514/514, syquex+opensyn 398✓/3✗ (solo wasm RED TDD Fase 25, preexistente), matriz 35/35, bootstrap fresco, huella ac3a132858571ecf. Tests sin modificar. Lecciones: el camino .syq es ciudadano de segunda (el desugaring inventó una convención que nadie más esperaba); un test-spec RED es detector de bugs del compilador. Reporte: docs/reportes/R174.md |
| `75dc6cf` | R187/ME f14_mto_ci (2026-10-14): cierre del lote en vuelo — check de cuerpo-bloque tras `funcion:` en el PARSER (M2 §2 L56/L60, rc=1; `_validar_cuerpos` del lexer eliminado, M1 §3.1), release_matrix.yml GH Actions real + build.py S2==S3 + distribuir.py sellado (M9 §4/§6.2/§2.1/§6.3), fixtures canónicos M2 §13, paridad emisor embebido H-R181-3 (M2 §3), harnesses paridad RAIZ+stubs (M9 §6.2); oráculo executor 20/20+2/2, contrastar RC=0 en el hook, expediente 0 brechas (evidencia e1df969a904e3db5). Hallazgo H-R187-1 (preexistente): '(' abierto en firma malformada activa la continuación r153 y suprime NEWLINE/INDENT del resto del archivo. Lecciones: parsear_plan usa solo la PRIMERA sección del bloque requisito (el bloque que implementa cada archivo cita su sección en 1ª posición); cambio_hash stale tras editar producción → procedimiento d948cab; pre-commit con oráculos 2× → commit en background; gate de lectura con --archivos COMA-separado. Reporte: docs/reportes/R187.md |
| `4a63327` | R173/ME barrido_citas_v820 (cierre de la deuda de alineación heredada, AUTORIZACIÓN del Arquitecto Opción A): las 39 citas `cumple Manual` sin sección (heredadas de la v8.2.0/154a544, listadas en DEUDA.md del 2026-09-14) BARRIDAS — (1) M7 restaura textualmente las 6 secciones citadas (§4.3 en posición canónica, §6.1/§6.2/§6.4/§7.2/§8 como apéndices) → 36 citas AUTO-RESOLVIERON; (2) 3 citas al capítulo §6 re-ancladas a subsecciones (chat.syn L3/L54 → §6.2; ai_orchestrator.h L146 → §2.1, solo comentarios); (3) mapa saneado (chat.syn [§6.4] stale → [§6.2, §8]; nueva entrada ai_orchestrator.h); (4) DEUDA.md regenerado con --baseline: 0 citas muertas, 0 archivos sin mapa. citas_muertas_repo 39→0 por programa; índice 304/1364; suites 85/85; contrastar PASA (7 requisitos, 2 oráculos release); huella fe5ae9a7aa1147d7. Sin cambios de tests, sin cambios ejecutables. Lecciones: restaurar el manual es la vía de mayor radio de reparación (36/39 de golpe); el indexador registra `## N` como sección padre (citas de capítulo resuelven); el gate de lectura NO acepta MANUAL ENTERO sin sección (exige § explícita — "Manual 2" a secas es el no-op que cubre() cerró); el hook mensajea la ruta vieja docs/mapa_manuales.md (vigente: docs/gobernancia/mapa_manuales.md); los mapas del 2026-09-14 tenían entradas stale. Reporte: docs/reportes/R173.md |
| `72d77f3` | R172/ME m7_s73_restauracion (cierre de H-R171-1, AUTORIZACIÓN del Arquitecto Opción A): M7 §7.3 "Pruebas de Privacidad y Seguridad" restaurada TEXTUALMENTE del estado pre-154a544 (3 bullets: Cero telemetría, Modelos firmados SHA‑256, Sandboxing) como apéndice al final del manual + nota de restauración 2026-10-01; opensyn/permisos.syn L3 re-anclada al ancla ORIGINAL `cumple Manual 7 §7.3` (texto exacto de fef314b) preservando las anclas §1.1 del mapa (mapa_alineacion.md actualizado). Cadena de causa: fef314b citaba §7.3 existente → 154a544 eliminó el capítulo 7 → d040500/R149 re-ancló a §1.1 (correcto por gates; el test quedó atrás). test_permisos_opensyn 43/43 (antes 1✗ desde la v8.2.0); suites-guarda 67/0; índice 298 secciones/1315 oraciones; contrastar PASA (2 requisitos, oráculo release); huella 2fee9f2fa1cabff7. Sin cambios de tests (el test tenía razón — requisito literal de su docstring). Lecciones: los tests OBL-M7 de citas `cumple Manual X §Y` sobre producción (TestCitasCumpleManual) son OTRA familia de suites-guarda — barrer con grep tras cada revisión de manuales; el sello --leer mira el índice STAGED (stagear producción antes de --leer); la nota de restauración lleva la fecha real del ME (metadato de procedencia, no norma). Reporte: docs/reportes/R172.md |
| R171 | Verificación suite integración COMPLETA (petición "verifica suit integracion"): 1596 tests → 1447✓/110✗/39skip (2:16:06) — 0 fallos en la zona OpenSyn de los 3 MEs; normalizado vs baseline R164 (+7✓/−10✗, mejora); 110 fallos clasificados (21 RED TDD declarado ME_27/29/30, ~8 YAML CI release, ~7 GCC entorno, 4 warps paridad_syn_syq — frontend .syq añade principal() al AST, sin relación con elif; 1 flaky loop_1M reconfirmado PASA aislado; 1 CWD pollution; 1 exe instalado stale). H-R171-1 NUEVO: test_permisos_cita_r6 exige `cumple Manual 7 §7.3` — §7.3 existía pre-154a544 (L870) y fue eliminada: 3ª víctima de la truncación v8.2.0; candidatas: restauración textual (patrón restauro_bucle_validacion) o re-anclaje del test — decisión del Arquitecto. Sin cambios de producción/tests (verificación pura); reporte docs/reportes/R171.md |
| `b1ac1c2` | R170/ME restauro_bucle_validacion (cierre de la deuda TestRequisitosManuales, AUTORIZACIÓN del Arquitecto Opción A): la revisión de manuales v8.2.0 (154a544, 2026-09-13) había eliminado el capítulo 6 completo de MANUAL 7 y truncado §4.2 a media frase — el bucle de validación quedó a medias mudado (3 frases en M8 §5.1-§5.2, 2 sin hogar) con 3 referencias colgantes a la sección fantasma. Restauración TEXTUAL del estado pre-154a544: §6.3 completa (flujo 6 pasos + feedback humano + nota --check, con nota de procedencia) + pasos 9-11 de §4.2. TestRequisitosManuales 7/7 (antes 2/7); suites-guarda 67 passed 0 failed; índice regenerado (1311 oraciones, M7 §6.3 con 15 citables). Repara de golpe: 5 aserciones + 3 referencias + 5 comentarios de producción. Lecciones: el guarda anti-regresión de la spec FUNCIONÓ (detectó la degradación) pero nadie lo ejecutó desde el 13-09 — tras revisar manuales hay que correr los suites-guarda; dirección de la reparación según dónde viva la verdad: test→código (transpiler_elif, validation_loop_fix) vs manual→test (este ME) |
| `63c1731` | R169/ME validation_loop_fix (cierre de la deuda test_validation_loop_syn_exists documentada en R168, AUTORIZACIÓN EXPLÍCITA del Arquitecto regla 5/Opción A): la aserción L217 de test_opensyn_integration.py esperaba `funcion validar_codigo_con_check` — nombre abandonado cuando 7824e5d/ME-4 (2026-09-12) renombró la función a `validar_con_check` sin actualizar el test (creado coherente en 65b505e sobre e8d148a). Fix mínimo: 1 aserción + comentario justificativo. Evidencia: ningún manual nombra ninguna de las dos funciones; el nombre viejo solo vive en esa aserción; todo el ecosistema vivo usa el nuevo (3 llamadas internas + suite ME-4 51/51). Oráculos release: test_opensyn_integration 18/18 + test_ai_correction 51/51. HALLAZGO NUEVO: TestRequisitosManuales de test_bucle_validacion.py (5 FAILED preexistentes, ajenos) — el test (2026-08-28) exige 5 cadenas del contenido de "M7 §6.3" que la revisión de manuales v8.2.0 (154a544, 2026-09-13) retiró del MANUAL 7 (arqueología git log -S "hasta 3 intentos"): deuda manual↔test BIDIRECCIONAL (los tests de manuales también verifican que el manual contenga lo exigido). M7 §6.3 reconfirmada inexistente. Lecciones: el patrón "test viejo vs código nuevo" se resuelve alineando el test cuando la verdad vive en el código y ningún manual defiende el estado viejo; tras una revisión de manuales hay que barrer los tests que afirman contenido textual del manual |
| `e0cbb35` | R168/ME transpiler_elif (cierre de la deuda test_control_flow_pipeline de R166/R167): transpiler.py L51/L197 emitía el token `sino_si` — INEXISTENTE en la gramática (M2 §7.2: condicional_si solo define si/sino; alias T_SINO = sino/else/sinon/senao) — y el .syn generado no compilaba (4 errores; OBL-M7-03 "el .syq generado COMPILA" violado). Fix: emitir "sino si" (forma canónica, paridad con transpiler.syq L92 — el transpilador original). Origen arqueológico: R119 L60 "corrigió" la forma correcta a sino_si citando Manual 7 §5.1 — sección INEXISTENTE (M7 termina en §4; cita fantasma detectada hoy por el gate de secciones). Aserción test_opensyn_integration.py:120 corregida sino_si → "sino si" con AUTORIZACIÓN EXPLÍCITA del Arquitecto (regla 5): era la única que codificaba la desviación y contradecía a test_full_pipeline.py:230 (inmutable) — tests mutuamente incompatibles. Oráculos: test_control_flow_pipeline PASSED por PRIMERA VEZ + test_transpilar_condicional PASSED; regresión 87/1 con el fallo PREEXISTENTE y ajeno test_validation_loop_syn_exists (deuda NUEVA documentada). Gates: contrastar PASA (release), alineación 0 brechas (huella 152a82c2ad565065), MTO sin brechas, pre-commit verde. Lecciones: la cita debe ser oración INDEXADA (el prefijo "2. " de listas lo quita el indexador); el oraculo: del expediente es RUTA de archivo (no node ID); un comentario colecta UN `cumple Manual X §Y`; contrastar exige oráculo-archivo GREEN completo — el archivo de un test modificado no puede ser oráculo entero |
| `ff6c54a` | R167/ME fixture_syquex_timeout (última deuda de FASE_33_CERTIFICACION §5, AUTORIZACIÓN EXPLÍCITA del Arquitecto regla 5): cuello de botella MEDIDO — el fixture lanza UN subprocess interno (pytest de syquex+certs+fuzz+benchmarks con --cov=compilador, cacheado para 5 tests) que necesita ~500 s reales (476.54 s sin benchmarks + 25 s benchmarks; sin cov 394 s → coverage ~25%); el timeout GLOBAL pytest.ini 300 s lo mataba y ABORTABA la sesión pytest completa. Fix MÍNIMO: pytestmark = [integration, pytest.mark.timeout(660)] — techo 660 > 600 del subprocess (invariante exterior>interior); aserciones y umbrales M3 §3 BYTE-IDÉNTICOS; tripwire global intacto. 5/5 GREEN en 398.75 s; contrastar PASA (oráculo = el propio fixture en release); MTO sin brechas. Lecciones: el fixture NO era ineficiente — conflicto de techos de tiempo (exterior 300 < interior 600); el marker por-test es la vía canónica sin relajar el global; el flaky test_fibonacci_30 pasó aislado (reconfirmación R164); los 4 fallos syquex internos son preexistentes (el fixture mide cobertura, no éxito) |
| `12b342d` | R166/ME cli_lint_fmt (deuda #2 de FASE_33_CERTIFICACION §5): cli.py despacha `synapse lint/fmt` al backend NATIVO (stage2 del bootstrap, módulos .syn desde r153/Opción A) — sin reimplementar herramientas; orden canónico H-33.5-2 y antiguo aceptados; rc propagado (lint advertencias rc=1, fmt --check rc=1, errores rc=1). _bootstrap_stage2_fresco() (M1 §6): backing on-demand con el comando EXACTO del job CI, rebuild solo si stale o stage1 ausente (hook borra stage1, conserva stage2). RAÍZ HISTÓRICA: el punto de entrada descartaba el retorno de main() → rc=0 falso de CUALQUIER subcomando; ahora sys.exit(main()). Oráculo NUEVO 6/6 (E2E de python cli.py, anti-fabricación). Gates: evidencia 07ba3f460c6d0bee, contrastar PASA, unit 514/514, nucleo 30/30, matriz 35/35. test_control_flow_pipeline PREEXISTENTE (falla igual en base limpia con stash). Lecciones: la brecha era doble (no despachaba Y no propagaba rc); pop de stash en Windows puede fallar parcialmente por fixtures con Permission denied (verificar identidad con git rev-parse stash:N:ruta vs git hash-object antes de descartar); el validador de citas acepta filas de tabla como oraciones citables |
| `58ff1d1` | R165/ME formatter_fix (cierre de H-33.5-3, deuda prioridad 1 de FASE_33_CERTIFICACION §5): R1 (M3 §12.2) lint.syn importa formatter y fix_linea delega en formatear_linea — borrados normalizar_espacios (2 ramas) y recortar duplicados que el first-wins del aplanador (pipeline.py L523-539) ponía primero: CAUSA RAÍZ verificada con probes (H-FMT-1 del emisor RETIRADO). R2 (M1 §7.1) normalizar_espacios: colapso de espacios fuera de literales (estado en_literal respeta escapes y comillas), coma solo si queda contenido, UNA línea vacía preservada como separador. R3: oráculo NUEVO 6/6 GREEN (dedupe sin símbolos duplicados, repro --check rc=1→0, literales intactos byte a byte, lint --fix == fmt, bootstrap verde con rebuild on-demand si el hook borra stage1, nucleo 100% formateado). R4: normalización fmt de 47 módulos idempotente + reparación M2 §1.1 (ast_abi, frontend_nativo, funciones sin `#lang: es`) + anclas de norma y vínculo plan↔código colectable (M1 §7.1) en cabeceras. Bootstrap S2==S3 nuevo sello 6d579f9e…b1c. Gates: contrastar PASA, verificar_alineacion SIN BRECHAS, alineación 0 brechas (evidencia c365b2ea07a7bc8c), pre-commit verde con lecturas del día vinculadas 47/47. Lecciones: el pre-commit borra synapse_stage1.exe (patrón explícito) pero conserva stage2 → falso negativo de frescura "stage1 no existe" dentro del hook (guard añadido a _exe_fresco del oráculo); el gate de lectura previa exige registros DEL DÍA + vínculo explícito por archivo (--archivos lista CADA archivo, el sello --leer no lo sustituye); secciones padre sin oraciones indexadas (D-ALINEACION-F31) → anclar a la subsección (§1.1 cubre §1); la línea de vínculo plan↔código debe decir `cumple Manual X §Y` para ser colectada por contrastar.py; los oráculos con lista FIJA de fuentes vigiladas quedan stale ante ediciones fuera de la lista. Pendiente: lint/fmt en cli.py, timeout test_syquex_coverage; la norma de estilo real vive en MANUAL  FASE 31 (nombre propio, no citable como "Manual 31") |
| `55a9950` | R164/ME 33.5_certificacion (Fase 33.5 — certificación de la Fase 33): R1 job CI bootstrap con Etapa 2+3 y sha256 S2==S3 con fallo explícito (H-33.5-1 CERRADA, M9 §6.1); R2 dispatcher lint/fmt/test (principal.syn ~L1034-1060) clasifica flags --fix/--check/--junit/--json/--coverage y toma la ruta como primer arg no-flag — acepta el orden canónico de M8 §4.1 (flags ANTES de la ruta) y el antiguo (H-33.5-2 CERRADA); R3 oráculo NUEVO test_oraculos_33_5_certificacion.py 5/5 GREEN (bootstrap 3 etapas real, matriz extendida std/debug.syn para-en + std/modelo.syn indexado, dispatch canónico, anti-fabricación sha256); R4 suite completa medida con regresión diferencial vs base cdbfd86 (stash + rebuild stage1 desde fuente base) — 0 regresiones: unit 514/514, nucleo 30/30, matriz 35/35, syquex+opensyn 397✓/4✗ (idénticos en base), integration 1435✓/120✗ (114 idénticos en base + 1 flaky de timing GREEN aislado). Bootstrap determinista: mismo sha256 36b82c4d…addf9c en 3 regeneraciones. H-33.5-3 (formatter) y MEs futuros con resolución en docs/reportes/FASE_33_CERTIFICACION.md. Lecciones: test_syquex_coverage timeout 600>300 de pytest.ini aborta la sesión completa (--ignore + ME futuro para el fixture); regresión diferencial con stash+rebuild como metodología para certificar 0 regresiones sobre deuda roja; flaky de benchmark con umbral de tiempo falla bajo carga y pasa aislado; baile del cambio_hash (re-add tras --verificar muta el blob → blanquear + re-sellar + re-commitear, procedimiento d948cab); gate de lectura legacy exige M2 §1.1+§12 para nucleo/* además del §6.2 del mapa puntual |
| `dfdb1bd` | R163/ME 33.4b_genericos_para_mapa (Fase 33.4, H-R153-3 CERRADA): genéricos de usuario `estructura Caja(T):` con monomorfización + `para k en mapa` + métodos claves()/valores() en AMBAS capas. R1 (M2 §2): parser S1+nativo aceptan `( IDENTIFICADOR )` tras el nombre (param_generico; paréntesis, NO `<T>`), puente en puente_ast.syn. R2 (M2 §8.2): `Caja(5)` unifica T=entero — S1: _registrar_instancia_generica (alias primitivos, mangle Caja_entero, ctor compound literal, typedefs alfabéticos pre-bloque/modular, unificación T en semántica paridad D-2); nativo: gen_escanear_genericas 3 fases + guard de typedefs planos (recorrido.syn/orquestador.syn). R3 (M2 §4.3+M3 §3): rama Mapa< en _emitir_para_en ANTES de Lista — k=claves, valor vía m[k] (D-R163-1 PENDIENTE RATIFICACIÓN: el par ordenado del ROADMAP contradice M3 §3 L133 de UN identificador); claves() encajona CadenaSegura* (mapa.c paridad _encajonar_slot, H-R153-2) + _syn_lista_liberar RAII tras el cierre del for. R4: compound literal (Caja_entero){7LL}, ABI mapa.c alineada a synapse_rt_types.h (longitud/contiene → int). R5: módulo TDD en test_modulos_compilan.py; matriz 35/35; unit 544/544; bootstrap S1→S2 verde; probes E2E idénticos en ambas capas (p_full/p_gen2/p_mapa — antes segfault rc=139). Oráculo NUEVO 6/6 GREEN con anti-fabricación; contrastar PASA (5 requisitos R1-R5); evidencia 5d27e18bcd289f21. Lecciones: símbolos _G_native_* exigen TRES piezas (emisores + externs en _synapse_shared.h + definiciones en preámbulo principal de generator.py); extern dentro de un cuerpo .syn es scope de bloque C; alias de tipos normalizados en scan/resolve/hoisting; quirk R16 (asm con `}` + `{` interno → else-if huérfano, extender condición en la misma línea); unificación T faltante en semántica destapada por entero_a_texto(T) (log() variádico la ocultaba); cambio_hash stale → re-sello + re-commit (d948cab); --archivos usa COMA; M5 NO documenta Mapa (ley en M2 §4.3 + M3 §5.2) |
| `5ff9235` | R162/ME 33.4a_paridad_indexado (Fase 33.4, H-R153-3 cierre parcial): paridad del INDEXADO de colecciones en AMBAS capas + reparación del emisor S1 (el ROADMAP asumía 'S1 ya emite vía r153' y era FALSO — probe E2E: emitía `xs[0LL]` en C crudo → gcc 'subscripted value'). R1 S1: emit_expressions.py ExprIndice → _syn_lista_obtener/_syn_mapa_obtener con desencajonado (escalares por valor, structs/texto por dirección, patrón _emitir_para_en H-R153-2) + cast del handle en los 5 métodos de Mapa. R2-R3 nativo: T_CORCH_IZQ/DER=75/76 (sincronía D-9(e): tokens.syn, parser_constantes.syn, ast_nodos.h 134 constantes REGENERADO — es byte-exacto del script, no editar a mano; las citas viven en su cabecera fija), lexer c==91/93, postfix [idx] en r_post → NODO_INDICE(29). R4-R5: puente NODO_INDICE→ExprIndice (sin rama el nodo llegaba NULL y `let v = {0}` perdía el inicializador), emisor con desencajonado por tipo + trim de spans ('Mapa<texto, entero>' traía ' entero' sin mapear), tipo C del indexado en orquestador. R7: longitud(xs) ya existía en nativo (H-R153-14, r153) — NO se re-tocó. Oráculo NUEVO 4/4 GREEN (probes E2E ambas capas; anti-fabricación: sin indexado el cuerpo del C no llama al runtime); unit 514/514; matriz 35/35 + coverage 4/4; bootstrap stage1→stage2 verde; contrastar PASA (7 requisitos R1-R7); evidencia e72ce878c023a54b. Lecciones: toda NODO_* nueva exige 3 piezas (tokens/parser + puente + emisor); el hook regenera runtime_bindings.syq al tocar headers → la huella muta en el 1er intento (procedimiento d948cab); requisito §7.2+§7.3 exige AMBAS lecturas registradas + vinculación --archivos; bloques asm() en .syn una cadena por línea |
| `d0386f3` | R161/ME coverage_aristas (Fase 33.2, H-R152-1 CERRADA): --coverage con instrumentación de aristas en AMBAS capas. R1 runtime/core/coverage.c/.h NUEVOS — buffer estático de aristas (M5 §2.6), catálogo de ramas del emisor, volcado JSON atexit, OFF salvo SYNAPSE_COVERAGE=1. R2 S1: sondas _syn_cov(l,d) en emit_control/generator/context + --coverage en pipeline.py/cli.py (sin la bandera el C emitido es byte-idéntico, M1 §6). R3 nativo: nucleo/coverage.syn ÚNICO (emisor cov_* + reporte covrep_parsear/coverage_generar_html) + sondas en generador/{orquestador,recorrido,nodos_flujo}.syn + unity generator.syn regenerada. R4: cli_test formato 3 — SYNAPSE_COVERAGE=1 → compilar → ejecutar → covrep_parsear(<base>.coverage.json) → HTML `Coverage: 66%` + aristas no ejecutadas. Oráculo NUEVO test_oraculos_coverage.py 4/4 (E2E real: 3 ramas, 2 cubiertas, sino listada; sin --coverage el C no lleva sondas; MTO --solo-mto); integration 6/6; unit 514/514; contrastar PASA; 0 brechas; expediente 34 anclas (evidencia b888fe497b9ae83c). Lecciones: retorno CadenaSegura con buffer estático (no de stack — concat pisa el stack antes del memcpy), el reset no borra la ruta externa fijada por generar_etapa, offsets del parser JSON (+20/+11), exes stage1/stage2 stale tras editar nucleo/*.syn, citas del expediente LITERALES (bullets sin guion no se indexan; M9 §6.1 lleva prefijo □), gate de lectura exige sección explícita por archivo |
| `4697132` | R160/ME reparacion_imports_ffi (H-CFG-4/H-CFG-5 RESUELTAS): R1 imports — resolvedor_axon.py convención de paquete + fallback a la RAÍZ del repo (E-603 según carpeta del fuente) y pipeline.py resuelve imports encadenados contra el DIRECTORIO del módulo importado + precedencia del principal del USUARIO (M1 §3.1). R2 FFI — prototipos canónicos ÚNICOS (fin conflicting-types test_puente_ffi), casts (void*)(intptr_t)(h)/(intptr_t)crear() en 3 bordes del emisor y variables Lista<T>/Mapa<K,V> como intptr_t; H-CFG-5b: la regresión destapó que void* + asignación (intptr_t) ROMPÍA el bootstrap S1 (M1 §6) — reparado alineando el emisor al manual. R3 MTO — 10 citas muertas re-ancladas (M7 §4.2, M9 §5.x/§2.x/§4.1); deuda MTO 30→29 GREEN sin citar (oráculo nuevo cita OBL-M1-02). Oráculo NUEVO 6/6 sin skips; puente_ffi 12/12; unit 514/514; contrastar PASA; expediente 10 anclas CUMPLE (evidencia a14b5fb6f7623963). Lección: auditar_calidad_tests full-scan NUNCA como oráculo directo de plan — envoltorio --solo-mto en el oráculo del ME |
| `96e72f4` | R159/ME config_ruta_absoluta (H-EOF-3 RESUELTA): sandbox de std.sistema operativo — `_syn_normalizar_ruta` con separador de plataforma (H-EOF-3a: antes '/' vs cwd '\\' = sandbox teatro), `_syn_ruta_en_directorio` con borde de componente (H-EOF-3b), normalizador REESCRITO con pila de componentes (H-CFG-1: antes X/../Y → XY); std/sistema.syn resuelve relativa→absoluta + contratos M2 §5.1; principal.syn `ruta_config_absoluta()` en leer/guardar config; test_tiempo reparado (synapse_rt_memory.o, H-CFG-3, 15 errores de link preexistentes). H-CFG-2 REGISTRADA (lecturas builtin sin sandbox — Arquitecto). Oráculo 5/5 sin skips |
| `1f5f7e3` | R157/ME marker_tdd (H-AUD-OP-3): markers `tdd` y `e2e` registrados en pytest.ini; oráculo de colección limpia (0 PytestUnknownMarkWarning en 3085 tests, `-m tdd` operativa 144). H-TDD-1: `e2e` sin registrado detectado por el oráculo y resuelto en el mismo commit |
| `9a9170c` | R156/ME opensyn_exe_fresco (H-AUD-OP-2): dist/bin/opensyn.exe regenerado con pipeline real main.py (23:22, con fix EOF); guard OBL-EXE-R2 permanente: mtime(exe) > último commit de principal.syn; smoke dual-modo rc==0. dist/bin/ untracked → artefacto no commiteable |
| `8375ec6` | R158/ME eof_runtime_api (H-EOF-1 RESUELTA): runtime/core/io.c marca flag de EOF en sus 3 puntos y expone _syn_stdin_eof() (M5 §2.6); binding stdin_eof() con garantiza (M2 §5.1); OpenSyn cierra por EOF real (contadores r155 de respaldo); mapa con entradas explícitas io.c/std-io.syn; oráculo 5/5 + regresión r155 GREEN; H-EOF-RT-1: cita fabricada preexistente "Manual 7 §8" re-anclada a M7 §1.1 |
| `830074a` | R155/ME eof_cierre_chat (H-AUD-OP-1): chat modo línea y menú de bienvenida cierran ante EOF (3 lecturas vacías → rc=0 / Modo Oráculo por defecto); oráculo E2E GREEN (compila con main.py y ejecuta con stdin cerrado); H-EOF-1 (io.c colapsa EOF/vacío) y H-EOF-3 (config relativa al cwd rechazada; fallbacks PF disparan modo antes del menú) = deudas con resolución |
| `d9e842c` | R154/ME r153_s1_metodos_genericos: métodos, genéricos y for-en en S1+S2 — flip del backend lint/fmt/test a los módulos .syn (Opción A de H-R152-4) — R1 builtins Lista/Mapa/longitud (lista.c/mapa.c, encajonado por dirección, Manual 2 §4.3); R2 para-en S1+nativo (NODO_PARA_EN=57, Manual 3 §3); R3 métodos postfijo metodo:<tipo>:<nombre> (NODO_METODO=59); R4 principal.syn importa lint/formatter/reports (Manual 8 §4.1); R6 RAII de retorno (M2 §9.1); R5 bootstrap S1→S2 verde. H-R153-NODE ratificada (tabla M2 §7.2 por actualizar — Arquitecto). Oráculos 8/8, TDD módulos 3, matriz 35/35, expediente verificado (evidencia d5fb40c8d7530258) |
| `dbb9717` | R153/ME r152_bootstrap_link: bootstrap S1 restaurado (H-R151-3, Manual 1 §6) — R1: par F5-1 emitido en _emit_cabecera_comun (paridad con bloque 'modulo'); R2: subcomandos lint/fmt/test con backend real cli_lint/cli_fmt/cli_test (contratos Manual 2 §5.1; C embebido por H-R152-4), 5 externs fantasma eliminados; junit/json reales (Manual 9 §6.2); --coverage honesto rc=1 (H-R152-1). S1/S2 rc=0 con comando CI; test_r3_param_adt GREEN (TDD); oráculo r152 8/8; matriz 35/35; expediente verificado |
| `5db1dab` | R152/ME r151_linea_base: 4 fallos de línea base alineados con MTO/TDD (solo tests) — puente_canonico 54/57 traducidos (R1/R2), S1 on-demand (R3, destapó H-R151-3), cita fabricada "M7 §7.2" eliminada + skip honesto + benchmark real /v1/chat/completions (R4, H-R151-1); oráculo r151 3 GREEN (anti-fabricación) |
| `d9c498a` | F30-b: chat OpenSyn real (Ollama) + consola UTF-8 + LSP multi-mensaje + instalador 8.1.0 revisado | opensyn/principal.syn chat interactivo; runtime/core/ollama.c nuevo; io.c/string_utils.c UTF-8 y stdin pipes; lsp_v3.syn dispatch tolerante a espacios; synapse.iss sin [Run] roto, model=qwen-coder, PATH sin duplicados, Excludes; vsix repack. LSP 36/36, instalador 11/11, 0 brechas |
| `de901bb` | ME_30_T8: Docs/Packaging | README.md con instrucciones completas, 5 tests GREEN |
| `f3e5ad3` | ME_30_T7: Auto-actualización | auto_actualizar.py con verificar_version, 5 tests GREEN |
| `5c22529` | ME_30_T6: Tests de smoke | test_smoke.py con verificación de sintaxis, 5 tests GREEN |
| `b1390ba` | ME_30_T5: Verificación Ed25519 | verificar_firma.py con Ed25519, 5 tests GREEN |
| `72f60bd` | ME_30_T4: Instalador macOS | create_dmg.sh con opciones de componentes, 6 tests GREEN |
| `e5e9b58` | ME_30_T3: Instalador Linux | install.sh con detección de distribución, 6 tests GREEN |
| `5775c5a` | ME_30_T2: Instalador Windows | synapse.iss con componentes, 6 tests GREEN |
| `b9aa55f` | ME_30_T1: Estructura instaladores | Directorios instaladores/{windows,linux,macos,common}, 5 tests GREEN |
| `d64a07e` | fix(ci): normalizar line-endings + limpiar artefactos | CRLF→LF en 87 archivos, `// cumple Manual`→`# cumple Manual`, 2 stray files borrados, release_matrix.yml Create Release step |
| `fa3c548` | feat(installer): generar instalador Windows Manual 9 §2.5 | synapse.iss → instaladores/windows/, install.ps1, 3 CI workflows + 3 tests actualizados, valid_installer.py + AUDIT_EXITOSA, 48 tests pass |
| `609e9a4` | fix: modular S1 build + CI fix + register std lectures | Replaced broken GCC step with `python main.py --output` modular build; registered readings for std/concurrencia (Manual 5 §3.4), std/sync (Manual 5 §5.1), std/wasm (Manual 1 §5.3); cleaned merge conflict markers from lecturas.jsonl; dist/bin/synapse.exe generated (timestamp 2/9/2026 18:59:44) |
| `6dd0139` | docs(release): actualizar memoria y auditoría post-cleanup | Documentación post-commit cleanup |
| `d001d74` | fix(auditoria): reparar gate de citas `cumple Manual` (§ opcional) + tests MTS | ME-Q1: CUMPLE_RE acepta § opcional → citas_archivo valida 552/588 citas (antes 34/588); test_citas_archivo VERDE. ME-Q2: tests/test_citas_formato.py. ME-Q3: MTO OBL-M2-02 §12→§5 (Manual 2 §5=contratos). Plan MTS docs/plan_ME_reparacion_control_calidad.md (contrastar --plan OK, 0 brechas). |
| `ce0e291` | R113: chat OpenSyn estilo OpenCode/Freebuff sin corrupción de cadenas + UTF-8 consola + instalador 8.1.0 | HALLAZGO R113: el generador S1 libera parámetros texto al retornar desde bloques anidados (verificado en C generado) → helpers con alias destruían la lista de modelos del chat (use-after-free). Fix: fix_borrowing en pipeline.py aplicado a módulos C de dir_base (no solo nucleo/); helpers single-pass + copias strcpy_f; chat /modelos /model< n> /model<nombre> /ayuda /skills /tdd /revisar /plan con auto-detección y persistencia del modelo real (qwen-coder→qwen-coder:latest); io.c escribir_linea CP65001 (mojibake consola real); ollama.c _syn_ollama_modelos; synapse.iss wizard pregunta PRIMERO conectar a Ollama existente (Sí omite descargas). Verificado E2E contra Ollama real + pipes. Reporte R139. 0 brechas. |
| `e4d09c0` | R140/ME_agente_opensyn: OpenSyn AGENTE (herramientas TOOL + contexto repo real) + UI estilo OpenCode/Freebuff + cliente Ollama robusto | HALLAZGO R140: `_ollama_leer_respuesta` leía con recv bloqueante SIN timeout → Ollama colgado congelaba el chat en "Tu>" en silencio (150 s+ sin salida). Fix ollama.c: SO_RCVTIMEO 2 s + plazo absoluto 300 s + corte temprano por Content-Length + errores distinguidos (red/plazo/corte). Además: System Prompt con contexto estático (reglas Synapse .syn + Syquex .syq/@export + AGENTS.md + carpetas raíz + git); bucle agente [TOOL] listar/leer/git (sistema.c _syn_listar_directorio/_syn_capturar_comando, solo lectura); banner ASCII retro + prompt ❯ ANSI solo consola real (io.c _syn_es_consola/_syn_ansi); estado "[*] Consultando a <modelo>…" antes de cada llamada. E2E Ollama REAL: responde con la primera línea real de AGENTS.md, stderr 0 bytes, banner 1 sola vez. MTS completo (plan R1 §1.1/R2 §2.3/R3 §8, 2 oráculos E2E, verificacion_ME). Reporte R140. 0 brechas. |
| `a13332b` | R141/R142: OpenSyn TUI pantalla completa (banner de PÍXELES "OpenSyn", panel+caja de entrada con ❯, streaming NDJSON _syn_ollama_stream_*, menús modales / y /model con flechas, fallback pipe OPENSN_TUI_TEST=1) + historial persistente ~/.opensyn/history.jsonl (FIFO 1000, ↑↓) + autocompletado Tab (comandos / y rutas, doble Tab = menú). Vendor deps/agent-skills v0.6.8 MIT (pin d2c37ef, base de std/agent_skills.syn para /tdd /revisar /plan /skills). Instalador: SHA256 de llama-server/modelos (update_hashes.ps1 sin duplicaciones). Oráculos historial/autocomplete GREEN, E2E pipes limpia (rc=0, stderr 0), pytest 38 passed. Reportes R141/R142. |
| `db4ccf9` | R144/R144b: test instalador como usuario real — 3 bloqueantes corregidos en synapse.iss/update_hashes.ps1: (1) faltaban fuentes/headers de enlace en bin\ → compilador instalado no compilaba; (2) hash de modelos placeholder + hash ZIP-vs-exe de llama-server + URL 1B 401 + curl sin --fail → descarga IA imposible; (3) extracción copiaba solo el launcher sin sus 50 DLLs → motor IA no arrancaba. E2E v6b: compilación OK, IA local sirviendo completions, oráculos instalados en verde, PATH sin duplicados. Reporte R144. |
| `bdb615c` | R145: terminar WIP cliente OpenAI-compatible + banner figlet | ollama.c: streaming /v1/chat/completions con system/user ([USUARIO]), errores HTTP ≥400 propagados, cortes [DONE]/finish_reason, prefijo SSE data:, bloque DEBUG con ruta local hardcodeada eliminado, fix OOB 1 byte en escape, truncado system a últimos 3500 bytes (lección R144c) en ambas rutas; principal.syn: banner figlet (decisión Arquitecto; oráculo banner RED → H-R145-1); .syn.json regenerado (R35). Oráculos historial/autocomplete/GGUF GREEN, alineación 0 brechas. |
| `df8ff5f` | R146: prueba interactiva VS Code + instalación completa — principal.syn: filtrar_listado() excluye artefactos de build (prefijo _, .c.o/.o/.syn.json/.exe) del listado inyectado al modelo; TOOL listar y contexto estático devuelven UNA línea compacta acotada a 2400 chars (H-R146-1: el modelo 1.3B repetía el listado en bucle y el contexto cambiaba en cada build). lsp_v3.syn: synapse/aiExplain implementado (Manual 8 §2.3; antes -32601 y el comando de VS Code quedaba colgado), registrado en MODULOS_D9.md (1256 L, regla 13). Oracle banner: prompt natural ("nombra 3" confundía al modelo, determinista con temp 0). Instalador 8.1.0 reinstalado TYPE=full con binarios byte-idénticos (sha256). Oráculos banner GREEN x2 (~90 s)/autocomplete/GGUF GREEN, LSP 33 passed, alineación 0 brechas. |
| `7d2edbc` | R143/ME_opensyn_ia_gguf: motor GGUF local endurecido — vocab desde el array real tokenizer.ggml.tokens (antes solo escalar → 0 con GGUFs reales → rechazo), cache de posición O(n) para arrays, límites contra tamano_mmap, cache perezoso F32 (F16/Q4_0/Q4_1/Q5_0/Q5_1/Q8_0 exactos), dims GGUF ne[0]=contigua (w_k OOB corregido), top_p qsort O(vs log vs). Oráculo E2E determinista NUEVO GREEN: GGUF sintético (vocab 11, merges, token_embd Q8_0) → driver .syn compilado con S1 → carga+ingesta 5 tokens+generación "abababababababab" (temp=0)+cierre limpio. H-GGUF-2 INVARIANTE: output.weight debe tener n_vocab filas (LM head itera vocab del tokenizer). Reporte R143. |

### Deudas / Hallazgos críticos activos

- **H-CFG-4 (RESUELTO, 4697132 — ME reparacion_imports_ffi):** la resolución de imports
  fallaba (E-603) cuando el fuente vivía fuera de la raíz (probes en $TEMP, tests/):
  `importar opensyn` solo buscaba en dir_base. Cierre: resolvedor_axon.py añade
  convención de PAQUETE (<base>/<mod>/principal.syn) y fallback de búsqueda a la RAÍZ
  del repo; pipeline.py resuelve imports ENCADENADOS contra el directorio del MÓDULO
  importado (no del fuente raíz) y descarta el principal IMPORTADO cuando el propio
  archivo define el suyo (Manual 1 §3.1). Repro exacto cubierto por el oráculo del ME.
- **H-CFG-5 (RESUELTO, 4697132 — ME reparacion_imports_ffi):** las FFI de colecciones
  declaradas `externo funcion _syn_lista_*` duplicaban los prototipos canónicos del
  header compartido con tipos incompatibles (handle entero Synapse vs void* C) →
  conflicting-types en test_puente_ffi. Cierre (Manual 6 §3.1 + M2 §4.1): entran a
  _C_FUNCTIONS_NEED_DATOS (sin duplicación), casts explícitos (void*)(intptr_t)(h) /
  (intptr_t)crear() en los 3 bordes del emisor y prototipos únicos en generator.py.
- **H-CFG-5b (RESUELTO en el mismo ME, 4697132):** hallado por la regresión unit —
  la mitad R2 del plan dejaba el modelo de tipos a medias: traducir_tipo_c declaraba
  variables Lista<T>/Mapa<K,V> como void* mientras los creadores emitían (intptr_t) →
  `void* x = (intptr_t)_syn_lista_crear()` ROMPÍA el bootstrap S1 (Regla de hierro
  M1 §6, test_r3_param_adt_s1 RED). Cierre: las variables de colección se declaran
  intptr_t (mismo ancho que void* en x86-64) y el for-en castea su temporal
  (void*)(intptr_t)(...) — alineado al manual, sin relajar el oráculo (lección TDD).
- **Lección R160 (gobernanza de oráculos, verificada):** un plan MTS jamás debe citar
  `auditoria/auditar_calidad_tests.py` (escaneo completo) como oráculo directo: su modo
  full-scan reporta SIN_CITA fatales de deuda preexistente fuera de alcance (hoy 3 en
  tests/opensyn/test_{memoria_cifrada,pipeline_multiagente,verificacion_aot}.py de
  Fase 32, requieren ratificación del Arquitecto) y contrastar.py no acepta argumentos
  ni tolera fallos no atribuibles. Forma canónica del repo: envoltorio
  `--solo-mto` dentro del oráculo test_*.py del ME (patrón test_oraculos_<ME>.py).
- **H-CONTROL-1 (RESUELTO en working tree, ME-control_solido):** el job CI `auditoria` usaba `steps.base.outputs.ref` SIN definir el paso `id: base` → base vacía → `git diff "" HEAD` → 0 brechas FALSAS: el gate de bitácora más fuerte del servidor estaba muerto (fallo abierto). Fix: paso `id: base` propio + fallo por exit code (pipefail). Además `nonnull_base` degrada base vacía a HEAD~1 en verificar_alineacion/contrastar.
- **H-CONTROL-2 (RESUELTO en working tree):** NINGUNA capa ejecutaba los oráculos MTS: CI pasaba `--sin-oraculos` a alineacion.py y el hook solo los corría con ALINEACION_ORACULOS=1 (jamás establecida). Fix: CI sin `--sin-oraculos`; hook los corre por defecto (opt-out=0); contrastar.py EJECUTA cada oráculo del plan (pytest release: SKIP/vacío/fallo = FAIL; scripts: exigen marca OK/PASS/SIN BRECHAS). Oráculo nuevo: tests/auditoria/test_gate_mts_oraculos.py (15 GREEN, OBL-MCTRL-01..04).
- **H-CONTROL-3 (RESUELTO en working tree):** el MTO validaba solo formato. Fix: `auditar_calidad_tests.py --solo-mto` (pre-commit + CI) valida OBL con Manual § real; SIN_OBL fatal en modo incremental; detección SNIFF ampliada (SNIFF_AMP, fatal con --estricto-sniff). DEUDA VISIBLE: MTO cita 10 secciones renumeradas inexistentes (Manual 7 §6.3/§7, Manual 8 §6.3, Manual 9 §9) y 30 GREEN sin test citador — requieren ratificación del Arquitecto (regla 5).
- **H-CONTROL-4 (RESUELTO en working tree):** vínculo plan↔código laxo, sello no bloqueante, evidencia desanclada, .syq fuera del alcance, D-9 sin C/opensyn, hook borraba archivos rastreados por patrón, base CI vacía, parser de bitácora hardcodeaba 2026. Fix: vínculo ESTRICTO multi-plan (--plan repetible; hook/CI contrastan TODOS los planes juntos); cambio_hash mismatch BLOQUEA; sello con frescura + --exigir-sello; evidencia CI comiteada exigida (evidencia_ci_ok); .syq en PROD_EXTS/CI; D-9 escanea opensyn/syquex/runtime-core y MODULOS_D9 acepta .c (11 módulos registrados); limpieza del hook SOLO no-rastreados; bitácora con fecha AAAA-MM-DD. Detalle: docs/plan_ME_control_solido.md + docs/verificacion_ME_control_solido.md + docs/GOBERNANZA_BRANCH_PROTECTION.md.
- **H-TEST-FIX-1 (RESUELTO, fix_test_seccion):** tests/test_auditoria_alineacion.py::test_seccion_es_de_manual fallaba porque la cadena de prueba no contenía el carácter §. Fix: agregar § faltante a "cumple Manual 2 §3 en el codigo". Plan MTS docs/plan_ME_test_seccion_fix.md.
- **H-CFG-2 (REGISTRADO, 96e72f4 — requiere ratificación del Arquitecto):**
  `leer_archivo`/`existe_archivo` son BUILTINS del S1 Python
  (compilador/semantic_scope.py:53-56, decisión ratificada H-R153-2 citando
  Manual 2 §4.3) que delegan DIRECTO en `_syn_leer_archivo` SIN sandbox;
  `escribir_archivo`/`eliminar_archivo` sí lo pasan → la LECTURA fuera del cwd
  no está protegida en el pipeline Python. Resolución asignada: ME futuro de
  hardening (quitar del builtin o enraizar el sandbox en el runtime); los tests
  no se tocan (regla 5).
- **H-CFG-1 (RESUELTO, 96e72f4):** el normalizador retrocedía el componente
  equivocado al resolver '..' cuando el carácter previo era el separador recién
  emitido (X/../Y → XY, '..' podía sobrevivir literal); reescrito con pila de
  componentes ('.' descarta, '..' desapila, '..' sobre raíz relativa se conserva
  para que el sandbox lo rechace). Detectado por el debug E2E del propio ME.
- **H-CFG-3 (RESUELTO, 96e72f4 — infraestructura de tests):** `test_tiempo`
  enlazaba "tiempo.o" sin "synapse_rt_memory.o" (tiempo.c usa pool_alloc) → 15
  errores de link PREEXISTENTES (verificados con baseline git stash); reparado
  en harness tests/conftest.py (la especificación C no se tocó).
- **D-ALINEACION-F31 (RATIFICADO, 469780a):** secciones Manual 6 §5, Manual 5 §2, Manual 1 §1, Manual 1 §5 no tienen oraciones indexadas en .indice.json (el índice solo indexa subsecciones 5.1/5.3, 2.1, 1.1). El código CUMPLE las secciones del manual pero el gate de alineación no puede verificar citas literales sin oraciones en el índice. Decisión: marcar como DESVIACION en expediente f31_deficiencias.md con nota justificativa. Resolución: re-indexar manuales para incluir secciones padre o aceptar deuda.
- **H-F29-T5b (RESUELTO):** bug RAII preexistente en `runtime/core/sistema.c:24 concat()` con CadenaSegura retornada por FFI — usaba `malloc()` pero liberada con `pool_free()`. Fix commit `478f047`: cambiado a `pool_alloc()`. Mismo bug corregido en `_syn_sha256()`/`_syn_sha256_archivo()` (axon.c:37,63) y `_syn_home()` (modelo.c:781 — usaba `strdup()` que internamente llama `malloc`).
- **test_binding_typescript:** GREEN (ME_29_T2 completado) — bindings TypeScript implementados en opensyn/bindings_generator.py.
- **test_gestion_modelos:** GREEN (ME_29_T3_mod completado) — test modificado para verificar funcionalidad implementada en installer.syn.
  - **test_latencia_meta:** RED esperado — requiere llama-server activo en :8088 (benchmark real).
- **H-CS1 (REGISTRADO):** Config `core.autocrlf=true` (global) conflictuaba con `.gitattributes` (`* text=auto eol=lf`), causando CRLF en working tree en Windows. Fix: `git config --local core.autocrlf false` (commit `d64a07e`). Los archivos `.syn` en working tree quedan con LF.
- **H-CS2 (REGISTRADO):** 2 artefactos accidentales de release v8.1.0-industrial: (1) filename `"e create v8.1.0-industrial --draftgh release create..."` = output de `less` paginador capturado; (2) `tests/unit/tokens.syn` = formato YAML no-Synapse no referenciado. Borrados en commit `d64a07e`.
- **H-F30b-1 (RESUELTO, d9c498a):** el `[Run]` del instalador ejecutaba `synapse.exe {app}\opensyn\installer.syn`, que SOLO COMPILA (nunca ejecuta) y fallaba en silencio (~240 ms, sin GCC). Eliminado: la configuración de OpenSyn la hace el wizard [Code] `DownloadAIComponents` (Manual 9 §5.2-5.3) y `opensyn.exe` lee la config instalada. Desviación documentada.
- **H-F30b-2 (RESUELTO, d9c498a):** el wizard escribía `model=<nombre GGUF>` (ej. deepseek-coder-1.3b-Q4_K_M.gguf) en `config_ollama.txt` al conectar con Ollama existente — nombre inválido como tag de Ollama. Ahora escribe `model=qwen-coder` (el modelo que anuncia el diálogo).
- **H-F30b-3 (RESUELTO, d9c498a):** reinstalaciones repetidas anexaban `{app}\bin` al PATH una y otra vez (se observaron 9-10 entradas duplicadas apuntando a carpetas inexistentes en esta máquina). Fix: Checks `NotSynapseInUserPath`/`NotSynapseInMachinePath` en [Registry]; en esta máquina se limpiaron manualmente las entradas fantasma (User+Machine).
- **H-F30b-4 (RESUELTO, d9c498a):** la consola Windows mostraba mojibake (┬┐/├®) porque el runtime no alineaba la consola a UTF-8. Fix: `SetConsoleOutputCP(65001)`/`SetConsoleCP(65001)` SOLO cuando stdout/stdin es consola real (GetConsoleMode OK); los pipes del LSP quedan intactos (Manual 8 §1.2).
- **H-LSP-1 (RESUELTO, d9c498a):** el dispatch del LSP (WIP) extraía `method` asumiendo JSON compacto (`"method":"x"`, como VS Code); `json.dumps` de Python emite `"method": "x"` con espacios → `method_name` vacío → ningún request respondía (test_lsp_multimsg/workspace RED). Fix: extracción tolerante a espacios. Los tests pasaban antes solo porque apuntaban al binario viejo `nucleo/lsp_test.exe`.
- **H-R113 (REGISTRADO, ce0e291 — deuda de compilador):** el generador S1 del pipeline modular libera los parámetros `CadenaSegura` de una función cuando un `retornar` ocurre dentro de un bloque anidado (si/mientras, depth≥1) — `_syn_texto_liberar(param)` antes del return — y también en varios retornos de nivel raíz. Consecuencia: una función .syn que recibe `texto` NO es de solo lectura por defecto; CONSUME la cadena del llamador (use-after-free silencioso sobre el pool). Manual 2 §11 prescribe borrowing; hoy se resuelve con el post-proceso `fix_borrowing` (whitelist read-only) + regla empírica para helpers .syn: single-pass, retornos solo en depth 0, y el llamador pasa copias `strcpy_f` de cadenas vivas. No se corrige el generador (fuera de alcance); registrar como deuda para el compilador S1.
- **H-R140 (REGISTRADO, e4d09c0 — cliente HTTP sin plazo):** `_ollama_leer_respuesta` (runtime/core/ollama.c) usaba `recv()` bloqueante sin timeout ni plazo absoluto: si Ollama aceptaba la conexión y se colgaba (llama-server caído a mitad de generación, doble instancia, carga lenta del modelo), opensyn quedaba congelado en "Tu>" en silencio indefinido. Fix: `SO_RCVTIMEO` 2 s + plazo absoluto de 300 s por request (carga en frío + generación) + corte temprano cuando `Content-Length` queda satisfecho; código de resultado que distingue error de red (-1), plazo agotado (-2) y corte a mitad de cuerpo (-3), traducido por `_syn_ollama_consultar` a un mensaje claro. Lección: todo cliente de red del runtime debe tener plazo absoluto + timeout de grano fino; el chat imprime "[*] Consultando a <modelo>…" antes de cada llamada bloqueante para que la carga del modelo sea visible.
- **ME-agente-herramientas (CALIDAD, pendiente opcional):** con qwen-coder el modelo a veces responde directamente (con el contexto ya inyectado) en lugar de pedir [TOOL] — aceptable porque la inyección estática cubre la mayoría de preguntas del repo; refuerzo con few-shot de [TOOL] en el System Prompt queda como mejora opcional de prompts.
- **H-R144-2 (REGISTRADO, db4ccf9):** VRAM/RAM/CPU detectan -1 en contexto elevado del instalador → modo silencioso elige siempre el 1B (conservador); ME futuro: logging de detección + fallback.
- **H-R144-3 (RESUELTA/VERIFICADA 2026-10-22, ME r194_deuda_gobernanza):** el catálogo
  `opensyn/modelos.toml` fue limpiado ya en el árbol (URLs/SHA256 reales, 0 placeholders).
  Cierre con EVIDENCIA fresca: los 5 SHA256 del toml verificados HOY contra el
  `X-Linked-ETag` (LFS oid real) de HuggingFace vía curl -sIL → 5/5 coincidencia byte a
  byte (04cebb6f…118, c3866cb9…6d17, f4222b2c…dd857, b889f38e…243ce, 26e7ece4…cecee).
  Ratificado por el Arquitecto en sesión 2026-10-22 ("el catálogo debe ser real, nada
  de placeholder").
- **H-R144-5 (REGISTRADO, db4ccf9):** upgrade silencioso con GGUF existente salta la provisión de llama-server (bloque `if not UseExisting`); caso borde tras crash sin modelo ni server (ME futuro).
- **H-R144-4 (DOCUMENTADO):** MSYS Git Bash manglea `/FLAG` de instaladores silenciosos (usar .cmd literal o MSYS2_ARG_CONV_EXCL); el diálogo de idioma aparece en VERYSILENT sin /LANG (Inno, 2 [Languages]).
- **H-R144-6 (RESUELTO, sesión 2026-09-08):** prompt enviado al modelo LLM contiene bytes basura (16 bytes de prefijo no ASCII) que corrompen el system prompt, causando que el modelo no responda correctamente. Causa raíz: `visitar_asignacion` en `compilador/generator/emit_declarations.py` generaba `_syn_texto_liberar(var)` ANTES de evaluar la expresión RHS — use-after-free para `sys = concat(sys, ctx)` que liberaba `sys` antes de que `concat` leyera su valor. Fix: evaluar en variable temporal única (`_syn_tmp_{var}_{counter}`) ANTES de liberar. Elimina trabajo previo de skip de 16 bytes en `ollama.c` (ya no necesario). Lección: RAII con reasignación requiere evaluar RHS primero; el compilador debe generar código defensivo incluso cuando el usuario viola semántica de borrowing.
- **Lección R144:** la validación del instalador debe incluir instalación+compilación+ejecución E2E (los tests de estructura del .iss no ven bloqueantes de runtime); los defines de hash con placeholder "TODO_..." no fallan el build — fallan el usuario final; el hash debe calcularse sobre el MISMO objeto que se verifica (exe extraído, no zip).
- **Lección R144c:** optimizar system prompt para modelos pequeños (1.3B) es crítico — el contexto completo de OpenSyn (~8KB) excede la ventana de 2048 tokens de deepseek-1.3b; truncar a últimos 3500 bytes preserva el mensaje del usuario al final del prompt.
- **H-GGUF-2 (INVARIANTE REGISTRADO, 7d2edbc):** `_syn_modelo_evaluar_token` dimensiona logits con `mc->vocab_size` (tokens del tokenizer) pero el LM head itera `output.weight` con stride n_embd — si output.weight tiene menos filas que el vocab del tokenizer la lectura sale del mmap (logits corruptos → generación vacía). Con GGUFs reales tokenizer==output por diseño, así que no se manifiesta en producción; INVARIANTE: output.weight debe tener n_vocab filas. Detectado por el oráculo sintético (vocab 11 vs output 8).
- **H-GGUF-1 / H-HIST-1 / H-HIST-2 (RESUELTOS, a13332b y 7d2edbc):** merges BPE exigen la pieza resultado en el vocab (resolución por texto exacto); " salir" con espacios se recorta antes de filtrar; Tab/flechas en modo pipe Windows con semántica idéntica a POSIX. Detalle en verificacion_ME_opensyn_ia_gguf.md y verificacion_ME_opensyn_historial_autocomplete.md.
- **Entorno de esta máquina (nota operativa):** Ollama NO instalado — los oráculos de contenido (banner chequeo 2, agente) requieren Ollama vivo con modelo descargado; en esta máquina pasan los chequeos que no dependen de él (banner ASCII, historial, autocomplete, GGUF sintético, pytest 38). Los print con ↑↓/❯ requieren PYTHONIOENCODING=utf-8 en consola cp1252 (patrón conocido).

- **H-R145-1 (CERRADO, 4a7e77d):** el Arquitecto autorizó modificar el oráculo banner en sesión 2026-09-10: chequeo 1 actualizado al banner figlet y marcas del chequeo 2 ampliadas a entradas reales de la raíz (el modelo responde con porciones variables del listado real vía TOOL listar). GREEN verificado con llama-server real (deepseek-coder-1.3b en :11434).
- **H-R145-2 (CERRADO, 4a7e77d):** obsoleto — llama-server SÍ está disponible en esta máquina (:11434, GGUF deepseek-coder-1.3b); el chequeo 2 del oráculo banner pasa con backend real.
- **H-R145-3 (RESUELTO, 4a7e77d):** el parser SSE de ollama.c tratab "finish_reason":null — presente en TODOS los chunks de streaming OpenAI — como fin de stream → el chat se quedaba en "Consultando…" sin respuesta. Fix `_oll_linea_json`: extraer content PRIMERO (el chunk final de llama.cpp trae content + finish_reason:"stop" en la misma línea) y marcar done solo si finish_reason tiene valor entre comillas; "done":true (Ollama) y data: [DONE] intactos.
- **H-R145-4 (RESUELTO, 4a7e77d):** GGUF sin chat template (deepseek-coder-1.3b vía llama-server) genera el template ChatML como TEXTO (<|im_end|>, <|im_start|>system...) en bucle hasta agotar max_tokens (~87 s por consulta). Fix: stop sequences ["<|im_end|>","<|im_start|>","<|EOT|>"] en el body de ambas rutas (stream y no-stream). Consulta real: 87 s → ~5 s.
- **H-R145-5 (REGISTRADO, 4a7e77d — resolución asignada):** el oráculo historial tiene timeout fijo de 60 s por ejecución de subprocess; con backend real cada prompt enviado ES una llamada al modelo (su test 3 envía 3 prompts = 105 s). Funcionalidad validada manualmente con timeout largo (3 entradas exactas en history.jsonl + navegación ↑↑ = "dos", rc=0). ME futuro: subir timeout del oráculo o acortar sus prompts (requiere aprobación del Arquitecto).
- **Lección R145:** (1) el cache `~/.synapse/cache/runtime_obj/*.o` puede enmascarar ediciones de runtime/core/*.c — invalidar el .o y recompilar tras editar (patrón "exe stale"); (2) los WIP heredados pueden contener decisiones NO ratificadas (banner) que revierten planes completados — contrastar contra el plan/la bitácora antes de continuar; (3) el smoke de opensyn reescribe config_ollama.txt (auto-persistencia R139) — restaurarlo antes de commitear.

- **Lección R145b (E2E contra servidor real):** (1) en streaming OpenAI, "finish_reason":null aparece en TODOS los chunks — jamás usarlo como terminador sin verificar el valor; (2) los GGUF sin chat template reproducen el template como texto (ChatML <|im_end|>) → enviar stop sequences siempre (patrón cliente robusto); (3) los oráculos E2E de chat con timeout fijo (60 s) quedan obsoletos cuando el chat FUNCIONA: cada prompt es una llamada real al modelo — diseñar oráculos con prompts que no disparen consultas o con timeout proporcional.
- **H-R146-1 (RESUELTO, df8ff5f):** el contexto inyectado al modelo no era determinista — el listado de la raíz incluía artefactos de build que cambian en cada compilación (_*.c/_*.o/synapse_bootstrap.exe generados por S1 en la raíz) y el modelo 1.3B repetía el listado multilinea en bucle agotando max_tokens (las respuestas variaban según la basura del momento). Fix: filtrar_listado() en principal.syn excluye artefactos por convención del repo (prefijo _, .c.o/.o/.syn.json/.exe) y comprime a UNA línea acotada a 2400 chars, aplicado a TOOL listar y al contexto estático. Respuestas deterministas y con contenido real verificado x2.
- **Lección R146 (producto instalado = producto validado):** (1) al corregir binarios, reconstruir el instalador y reinstalar de inmediato — y verificar sha256 de lo instalado contra lo validado — para que la prueba interactiva del usuario ejerza el mismo binario que pasaron los oráculos; (2) los prompts de los oráculos no deben contener números literales ("nombra 3"): un modelo pequeño los copy-pastea como respuesta literal (determinista con temperature:0); (3) los artefactos que el propio build genera en la raíz contaminan cualquier listado inyectado a un agente — filtrar por convención, no limpiar a mano.

### Hallazgos de la auditoría de operatividad OpenSyn (2026-09-25, AUDITORIA-OP-OPENSYN)

- **H-AUD-OP-1 (RESUELTO, 830074a):** el chat en modo oráculo NO
  termina ante EOF de stdin: si el pipe se cierra sin enviar "salir",
  `chat_tui` (opensyn/principal.syn) re-imprime "Tu>" en bucle infinito. Evidencia:
  `echo "status" | timeout 12 dist/bin/opensyn.exe` → rc=124 y log de 21 MB
  (~210.000 prompts). Los oráculos no lo detectan porque siempre envían "salir".
  Cierre (ME eof_cierre_chat, R155): contadores en capa aplicación — `eof_consecutivos`
  en el bucle de chat modo línea y `intentos_menu` en el menú de bienvenida;
  3 lecturas vacías = EOF → cierre limpio rc=0 / Modo Oráculo por defecto. Oráculo
  E2E permanente (stdin cerrado sin "salir" → rc==0 exigido). Refinamiento final
  con la API de EOF del runtime: ver H-EOF-1 (RESUELTO, 8375ec6). Deuda derivada
  restante: H-EOF-3 (abajo).
- **H-EOF-1 (RESUELTO, 8375ec6):** causa raíz runtime de H-AUD-OP-1:
  `_syn_leer_linea()` (runtime/core/io.c) colapsaba EOF y línea vacía en
  {longitud=0} — indistinguibles en capa aplicación. Cierre (ME eof_runtime_api,
  R158): flag `_syn_stdin_eof_flag` marcado en los 3 puntos EOF de io.c (consola
  fgets NULL, pipe ReadFile sin datos al inicio, POSIX fgets NULL) + API
  `_syn_stdin_eof()` thread-safe (M5 §2.6); binding `stdin_eof()` con garantiza
  (M2 §5.1); OpenSyn consulta stdin_eof en chat modo línea y menú — EOF real
  cierra de inmediato, contadores r155 de respaldo. Mapa de alineación con
  entradas explícitas runtime/core/io.c → M5 §2.6 y std/io.syn → M2 §5.1.
  H-EOF-RT-1: cita fabricada preexistente en io.c L58 ("Manual 7 §8") re-anclada
  a M7 §1.1.
- **H-EOF-3 (RESUELTA, 96e72f4 — ME config_ruta_absoluta):** la lectura de config
  RELATIVA al cwd NO funcionaba: `_validar_ruta_segura` rechazaba TODAS las rutas
  (relativas por longitud; absolutas por separador '/' vs '\' del cwd crudo —
  sandbox teatro, todo consumidor real vivía en bypass asm). Cierre en 3 capas:
  runtime (separador de plataforma H-EOF-3a + comparador con borde de componente
  H-EOF-3b + normalizador con pila de componentes H-CFG-1), std/sistema.syn
  (resolución relativa→absoluta ANTES de normalizar + contratos M2 §5.1),
  principal.syn (ruta_config_absoluta en leer/guardar). Oráculo 5/5 sin skips;
  el E2E del menú (inmutable) mantiene su skip por dato de instalación PF (la
  demostración del fix vive en OBL-CFG-R3).
- **H-AUD-OP-2 (RESUELTO, 9a9170c):** `dist/bin/opensyn.exe` (17-sep 21:11) era STALE —
  anterior a la última edición de `opensyn/principal.syn` (17-sep 22:19, fix
  H-R149-WIP). Cierre (ME opensyn_exe_fresco, R156): exe regenerado con el pipeline
  real main.py (23:22, incluye fix EOF) + guard permanente de frescura
  (mtime(exe) > último commit del fuente, OBL-EXE-R2). Nota: dist/bin/ es untracked
  → el guard protege el artefacto local; sincronizarlo en CI queda a diseño de
  release. Deuda menor CERRADA (2026-09-26): dist/bin/synapse_lsp.exe regenerado
  con main.py nucleo/lsp_v3.syn (post-R159) + smoke JSON-RPC initialize GREEN +
  suite LSP 33 passed/2 skipped (skips preexistentes por backend).
- **H-AUD-OP-3 (RESUELTO, 1f5f7e3):** marker `@pytest.mark.tdd` sin registrar en
  `pytest.ini` → 8 PytestUnknownMarkWarning en tests/opensyn. Cambio de CONFIG de
  tests (no de tests, regla 5 intacta): `tdd:` añadido a markers; el oráculo de
  colección limpia detectó además `e2e` sin registrar (H-TDD-1) → registrados ambos,
  0 PytestUnknownMarkWarning en la suite (oráculo permanente OBL-TDD-R1/R2).
- **H-R144-3 (CERRADA, ratificada por el Arquitecto 2026-10-22, ME r194):** `opensyn/modelos.toml` tiene URLs
  HuggingFace LFS reales + SHA-256 reales, 0 placeholders; los 5 SHA256 re-verificados 2026-10-22 contra
  X-Linked-ETag (5/5 coinciden). Cierre ejecutado (ver fila H-R144-3 RESUELTA arriba).
- Verificado sano: pytest tests/opensyn 122 passed/1 skipped; oráculos
  historial/autocomplete/banner/ia_gguf GREEN (agente RED por entorno, sin backend IA);
  LSP responde initialize JSON-RPC; 13 comandos TUI presentes; sandbox M7 §1.1 activo.
  Informe completo: docs/auditorias/AUDITORIA_OPENSYN_OPERATIVIDAD.md (fila en
  bitácora canónica: AUDITORIA-OP-OPENSYN).

### Decisiones y hallazgos del ME r153_s1_metodos_genericos (2026-09-25)

- **H-R153-NODE (RATIFICADO, sesión 2026-09-25):** el Manual 2 §7.2 (tabla
  "Constantes de Tipo de Nodo") solo llega hasta `NODO_DELEGAR=55`; los nodos
  nuevos `NODO_PARA_EN=57` y `NODO_METODO=59` (R2/R3) NO existen en la tabla
  canónica. Regla 3 (no inventar): no se fabricaron filas de manual. Decisión:
  los valores 57/59 se emitieron sin colisión con la tabla vigente (verificado
  grep en parser_constantes.syn), se implementaron end-to-end en AMBAS capas
  (S1 pipeline Python + nativa compilándose a sí misma) y quedan ratificados
  como extensión con DESVIACION declarada en el expediente r153
  (docs/alineacion/r153_s1_metodos_genericos.md); la actualización de la tabla
  §7.2 del Manual 2 es tarea del Arquitecto (los manuales son ley, no se
  auto-editan).

### Archivos de interés rápido
- `auditoria/registrar_lectura.py` — Gate de lectura previa (obligatorio antes de commit)
- `auditoria/verificar_alineacion.py` — 0 brechas antes de commitear
- `auditoria/auditar_calidad_tests.py` — Valida tests no sean "sniff"
- `scripts/enable_branch_protection.ps1` — Aplica/revisa branch protection en GitHub
- `.github/CODEOWNERS` — Revisión humana obligatoria

---

### Decisiones y hallazgos del ME r149_reparacion (2026-09-17)

- **H-R149-WIP (RESUELTO en working tree, sesión 2026-09-17):** el WIP del ME
  introdujo `var ultimo_tipo_tarea: entero = 0` a nivel de módulo en
  `opensyn/principal.syn` alegando "patrón de memoria_persistente_cifrada.syn".
  Verificado: (1) `var` NO existe en la gramática (Manual 2 §2 L134 solo define
  `let`; parser.py:148) y el compilador lo rechaza; (2) Synapse nativo no define
  globales mutables (semantic_checker.py:341-343 — `variable` es keyword de
  SyQuex, Manual 3 §3); (3) `let` a nivel de módulo SÍ emite el global en el C
  MONOLÍTICO pero NO en el MODULAR (queda como local sombra dentro de
  `_principal_impl` — sondeado con probe en $TEMP); (4) el "patrón de
  referencia" `memoria_persistente_cifrada.syn` usa `var` en fuente pero ni
  siquiera compila aislado (header `#lang`). Fix definitivo: sin estado global —
  `tui_agente()` retorna la clasificación (0..4), `tui_comando()` la recibe por
  parámetro (mismo nombre → lectores /next sin tocar) y el estado es `let`
  local en `chat_tui()` y `modo_oraculo()`. Exe fresco relinkado. Lección:
  verificar que el patrón citado en un comentario realmente compila antes de
  copiarlo; los comentarios de WIP no son evidencia.
- **H-R149-2 (RESUELTO en working tree):** la autodetección de expedientes en
  `alineacion.py --verificar` (sin `--me`, la que corre el hook) matchea por
  INTERSECCIÓN de archivos y recorre `docs/alineacion/*.md` alfabéticamente:
  expedientes históricos (ME-7, f31_*, f32_*) con anclas PENDIENTES y hash
  vacío interceptaban cambios nuevos que tocaban los mismos archivos (ej.
  `opensyn/principal.syn` está en ME-7 y en r149) → el gate validaba contra un
  expediente muerto y bloqueaba. Fix: expedientes históricos archivados en
  `docs/alineacion/archivo/` (el glob de autodetección no es recursivo); el
  expediente activo r149_reparacion queda en la raíz. Los tests no dependen de
  ellos (test_alineacion_control.py usa fixture ME-T).
- **H-R149-EXP (RESUELTO en working tree):** el expediente
  `docs/alineacion/f32_4b_cita_principal.md` era un borrador no verificable:
  duplicaba anclas de `r149_reparacion.md` sobre el MISMO cambio_hash
  (94c9b9fff045f0e2) con solo 1 de 12 archivos → "el expediente no tiene bloque
  para: …". Además usaba clave `citation:` (el validador lee `cita:`) y apuntaba
  a Manual 3 §12.1 que NO existe (Manual 3 termina en §12 sin subsecciones; la
  cita literal vive en §12, línea 458). Consolidado: expediente borrado, su plan
  apunta a r149_reparacion.md.
- **D-R149-1 (RATIFICADA, con expresa aprobación del Arquitecto en sesión):** los
  comentarios `// cumple Manual` DEBEN citar secciones que existan en el índice
  de manuales (`docs/manuales/.indice.json`); NO pueden usarse secciones
  "ilustrativas" ni "mentoras" (ej. `Manual 3 §12.1: CLI debe aceptar -o` o
  `Manual 7 §8: capa de IA`). El requisito literal que el código implementa
  (texto no indexado como prosa) queda registrado en el PLAN MTS y en el
  EXPEDIENTE (bloque DESVIACION con `decision: D-R149-1`); el comentario en el
  código se ancla a la sección REAL más próxima que especifica ese archivo.
  Origen: 21 citas muertas heredadas en archivos del cambio; 14 re-ancladas a
  secciones reales (cli.py/synapse_rt.c/tiempo.h→M1 §3.2, M8 §4.1, M4 §2,
  M5 §2.6; opensyn/principal.syn→M7 §2.1/§2.3; permisos.syn→M7 §1.1), 7
  declaradas en expediente.
- **D-R149-2 (RATIFICADA, con expresa aprobación del Arquitecto en sesión):**
  `docs/gobernancia/mapa_alineacion.md` entraba `opensyn/permisos.syn` a
  `Manual 7 §7.3`, sección que NO existe en Manual 7 (que termina en §4.2).
  Corregido el mapa a `Manual 7 §1.1` (asistente IA local: permisos mínimos,
  cero telemetría, sin nube), que es la sección que realmente especifica el
  sandbox de rutas del agente. Origen: DEUDA de alineación 2026-09-14.
- **Nota técnica D-R149-3:** el formato del expediente de alineación permite
  `decision: D-xxx` solo en bloques DESVIACION (alineacion.py:605-611); en
  CUMPLE solo hay evidencia+oráculo. Los archivos sin prosa citable (cabeceras
  nuevas) se anclan a la sección real que especifica el área.

## 💡 2. ERRORES RECURRENTES (patrones a evitar)

0. **Anti-cuelgue que corre tras progreso exitoso (R183)**
   - ❌ Un `token_avanzar(est)` de anti-cuelgue al final del bucle de casos que corre SIEMPRE, incluso tras parsear un caso con éxito → se come el DESINDENTAR/patrón real y corrompe la pila de niveles (rc=1/rc=8 según shape)
   - ✅ El anti-cuelgue SOLO corre si la iteración NO produjo progreso (flag `caso_parseado`); tras un caso completo el cursor ya está en el token real siguiente
   - Regla general: un guard anti-cuelgue de bucle parseador debe condicionarse a "no hubo progreso esta iteración", nunca correr tras un parseo exitoso

1. **Encoding UTF-8 en `subprocess.run`** en Windows
   - ❌ `subprocess.run([...], text=True)` → usa `cp1252` por defecto → `UnicodeDecodeError`
   - ✅ Siempre: `subprocess.run([...], text=True, encoding="utf-8", errors="replace")`
   - Archivos afectados: `auditoria/verificar_alineacion.py` (fix en commit 553fde1)

2. **ABI mismatch CadenaSegura**
   - ❌ Añadir campos a `CadenaSegura` (struct en C) → desborda 16 bytes de `synapse_rt_types.h`
   - ✅ Solo 16 bytes exactos (`Manual 2 §4.1`): `{char* datos; int longitud; int capacidad;}`
   - Solución para C functions que retornan malloc'd: `pool_alloc` + `pool_free`

3. **GitHub API version obsoleta**
   - ❌ Usar default o `2022-04-21` → error 400 "Problems parsing JSON"
   - ✅ Siempre header `X-GitHub-Api-Version: 2022-11-28`

4. **Ruleset API — `integration_owner` como string**
   - ❌ `"integration_owner": "synapse"` → 422
   - ✅ `"integration_owner": ["GitHub Actions"]` (array) o omitir

5. **Ruleset API — `ref_name` pattern**
   - ❌ `"include": ["main"]` → 422 "Invalid target patterns"
   - ✅ `"include": ["refs/heads/main"]`

6. **PowerShell `git add && git commit`**
   - ❌ `&&` no funciona en PS 5.1 (error parser)
   - ✅ Usar `;` o ejecutar comandos por separado

7. **PowerShell `Out-File -Encoding utf8`**
   - ❌ Agrega BOM que rompe `gh api --input`
   - ✅ Usar `-Encoding ascii` o `[System.IO.File]::WriteAllText()`

8. **`git diff` puede devolver `None` en hooks**
   - ❌ `diff.splitlines()` → `AttributeError: 'NoneType'`
   - ✅ Siempre `diff = out.stdout or ""`

9. **Escaping de `%` en asm() dentro de .syn**
   - ❌ El emisor Python pasa `%` VERBATIM al C (no hace sustitución) → usar `%%s` produce literal "%%s" en pantalla
   - ✅ Usar `%s`/`%d` simple (convención de principal.syn:91); `%%` solo si el asm pasa por la ruta nativa gen_emitir_linea (synapse_unity.c:7719 duplica)
   - Doble validación: el C generado (_principal.c) debe compilar; un error de escaping en UN asm mata el link completo (H-R151-3: 12 símbolos "undefined" que SÍ estaban definidos)

10. **Sintaxis NO compilable por el pipeline Python S1 (H-R152-4)**
   - ❌ `obj.metodo(...)` (postfijo . seguido de llamada no se parsea), `para x en ...`, `Lista<T>()` como constructor, `es ok/es err`, `valor_ok()` (inexistente)
   - ✅ Desenvolver Resultado<T,E> con `coincidir ... ok(x) => ... err(m) => ...`; contratos con acceso a campo (`ruta.longitud > 0`) — el orquestador NATIVO no emite definición ni extern de `longitud()`
   - nucleo/lint.syn, formatter.syn y reports.syn usan esa sintaxis → NO importarlos al bootstrap (referencia canónica); backend real = C embebido en principal.syn (cli_lint/cli_fmt/cli_test)

11. **`system()` de cmd.exe se come las comillas extremas**
   - ❌ `system("\"ruta con espacios.exe\"")` → cmd interpreta `"ruta` como comando → rc=1 con "no se reconoce"
   - ✅ Duplicar comillas exteriores: `"\"\"exe\"\""` (workaround documentado de cmd /c)

---

## 📚 3. LECCIONES CLAVE

### Arquitectura / Diseño
- **D-F22-A:** Frontends Syquex → Synapse (no .syq hasta completar fase)
- **R10:** `pool_alloc` registra punteros fuera-del-pool en `_g_extra_ptrs[]` → `pool_free` solo libera punteros registrados → literales estáticos = no-op
- **Regla D-2:** Escanear TDOS los parámetros (retorno + params) para ADT en nativo
- **Regla H-R90-8b:** Inyectar `principal` en .syq source físico ANTES del runtime S1

### Build / Bootstrap
- **S2==S3 byte-idéntico** (criterio de aceptación por fase)
- **Timeout builds ≥ 900s** (`python main.py` toma 2-5 min)
- **Verificar timestamp del exe** después de build (no asumir por log)
- **`nucleo/generator.syn` es UNITY regenerado** → `_rebuild_generator.py` después de editar `nucleo/generador/`
- **R152 (lección H-R151-3):** un fallo de COMPILACIÓN en un solo módulo del link modular (= _principal.c no compiló por un error de escaping) produce docenas de "undefined reference" ENGAÑOSAS a símbolos que sí existen; diagnosticar el PRIMER error de compilación antes de perseguir los undefined del linker
- **R152:** el link modular usa el venv tdm64 gcc10 (rc=0 en compilación C != válido para AVisar errores de la ruta unity); los fallos del unity generan [FALLBACK] silencioso → SIEMPRE grep 'error:' del log y verificar el exe con `ls -la`

### Codificación / Patrones
- **Parámetros de salida:** funciones C no pueden devolver `CadenaSegura` por valor → usar buffers por puntero
- **Escapado en `.syn`:** `\\n` (2 BS) → `\n` en C emitido; `\\\\n` (4 BS) para arrays C embebidos
- **Lexema real en tokens:** todo token debe conservar el lexema del buffer fuente (patrón `lexer_push_token_punt`)
- **Pre-scans AST:** deben cubrir TODOS los attrs recursivos (`'derecho'`/`'izquierdo'`)
- **Stubs con structs:** emitir SOLO cuando ADT instanciado en el programa

### TDD / Tests
- **Test nace del MANUAL, no del código** → si el test falla, corregir el CÓDIGO (no el test)
- **Sin `pytest.skip`** → el test debe FALLAR si código no implementado
- **`pytest --collect-only -q` = 0 errores** ANTES de cada commit
- **Baseline `git stash`** antes de modificar (confirmar fallas preexistentes)
- **Leer manual antes de tocar tests** → registrar lectura en `auditoria/registrar_lectura.py`

### Seguridad (FFI / RAI)
- **RAII sobre literales estáticos → 0xC0000374 (heap corruption)** → fix `pool_free` registry
- **CadenaSegura: 16 bytes exactos** → no usar `es_externo` (causaba ABI mismatch)
- **Nonce CSPRNG:** `randombytes()` C API, no `rand()` (Manual 6 §5.3)
- **Serialización:** validar ESTRUCTURA 0x08 rechazada sin esquema

---

## 📜 4. HISTÓRICO DETALLADO (F1–F27)

> 📄 **Snapshot completo con historia de fases, fixes y decisiones arquitectónicas.**
> Ver: `docs/bitacoras/HISTORICO_F17_F27.md` (contenido preservado de la estructura legacy).

**Fase completa:** F23 — Syquex auto-alojado (parche de bootstrap S1→S2→S3)
**Fase completa:** F26 — Herramientas (S1 bootstrap toolchain)
**Fase completa:** F27 — Herramientas de Desarrollo (LSP, VS Code, Debugger)
**Fase completa:** F32 — Agente de Codificación Avanzado y Memoria Persistente

| Fase | Estado | Commit | Tests | Reporte |
|------|--------|--------|-------|---------|
| F11 | ✅ | fb5b75c | — | FASE_11.md |
| F12 | ✅ | ce1f846 | 417/417 | R79/R80 |
| F13 | ✅ | ce1f846 | 233/233 | R79 |
| F14 | PARCIAL | — | 95/95 | — |
| F15 | ✅ | 633ed03 | 164/164 | R82 |
| F16 | ✅ | — | — | R42 |
| F17 | ✅ | 4e0ab7f | — | FASE_17.md |
| F18 | ✅ | 1f278d8 | — | — |
| F19 | ✅ | a7ec2af | 24/24 | R78/R83/R84 |
| F20 | ✅ | — | 7/7 | — |
| F21 | PARCIAL | — | — | RAII completa, destructor maps F23 |
| F22 | ✅ | — | — | D-F22-A aplicado |
| F23 | ✅ | — | — | Syquex auto-alojado |
| F26 | ✅ | — | — | Toolchain S1 |
| F27 | ✅ (52/52) | 1aa62ba | 52/52 | — |
| F32 | ✅ (72/72) | 20ba43f | 72/72 | — |

### Decisiones clave históricas
- **D-F22-A (2026-08-10):** Frontends Syquex → Synapse (no .syq hasta completar fase). Justificado por Manual 1 §4 (auto-alojado) + paradoja de bootstrap.
- **R7 (2026-08-10):** Parser nativo pasada 3 declara parámetros en scope → elimina 653 falsos positivos "variable no declarada".
- **R10 (2026-08-10):** RAII sobre literales estáticos — fix en `runtime/core/memory.c` con `_g_extra_ptrs[]`.
- **R11 (2026-08-10):** Exhaustividad `coincidir` nativa → switch sobre `.tag` + hoisting D-2 para ADT en parámetros.
- **R13 (2026-08-11):** Tipos ADT anidados → parseo balanceado `<...>` (consumir solo `>` de nivel 0).

---

## 📋 5. CHECKLIST DE VERIFICACIÓN (antes de commitear)

1. ✅ `python auditoria/verificar_alineacion.py` → 0 brechas
2. ✅ `python auditoria/registrar_lectura.py --pendientes` → nada pendiente (registrar lecturas si modifica productivo)
3. ✅ `python -m pytest <tests-afectados> -v` → todos pass
4. ✅ `git diff --cached --name-only` → solo paths explícitos (no `.exe`/artefactos)
5. ✅ Trailing whitespace: `grep -r ' $'` en archivos modificados
6. ✅ Hook pre-commit: limpieza artefactos + higiene + alineación + lectura previa
7. ✅ Si agregaste `docs/plan_ME_*.md`: `python auditoria/contrastar.py --plan docs/plan_ME_<id>.md` → 0 brechas

> 📄 Para historia completa, decisiones y debugging detallado: `docs/bitacoras/HISTORICO_F17_F27.md`

### H-INST-1 (2026-09-08): Inno Setup installer download pages frozen
- **Síntoma:** `DownloadPage` showed "Descargando..." but progress bar never moved; download was invisible
- **Causa raíz:** `DownloadFile()` used `Exec(... ewWaitUntilTerminated)` which blocked the UI thread entirely. Even though DownloadPage was added at `wpInstalling`, the UI never repainted during download.
- **Fix:** Changed `DownloadFile()` to use `Exec(... ewNoWait)` with `Sleep(1000)` polling loop + `WizardForm.Repaint`. Moved `DownloadPage` from `wpReady` to `wpInstalling` so it appears during actual installation phase.
- **Compilación:** `ISCC.exe` exitoso — `Synapse-8.1.0-industrial-Windows-x64.exe` generado
- **Resolución:** Fix aplicado, usuario debe probar con reinstalación limpia

### H-TEST-REPAIR (2026-09-14): Reparación de tests bajo MTO/TDD — 9 bugs reales de producción
- **Regla aplicada:** MTO/TDD — el test es el oráculo; se corrige CÓDIGO, jamás tests (regla 5).
- **Bugs corregidos (producción):**
  1. `sino si` no compilaba (parser Python y espejo .syn se comían el `sino`) → desugar a `si` anidado (paridad `_P_si` C): `compilador/parser_control.py`, `nucleo/parser_sentencias.syn`
  2. Frontend Syquex sin enlazar: blob `importar` llamaba `sq_arena_alloc` inexistente → usa `sbuf/str_pos` de SqLexerBuffers (1 MiB), disponible en TODO contexto lexer+parser (antes usaba trad_arena que no existe en el combinado de test_parser): `syquex/parser.syn`
  3. `para i en 0..10` (rango, Manual 3 §L133) sin soporte frontend → `sq_para_desugar` reutiliza el desugar C-style + contratos requiere/garantiza (Manual 2 §12): `syquex/parser.syn`
  4. `intentar:` (forma bloque) se parseaba como forma funcional → el `:` inmediato ahora fuerza bloque: `syquex/parser.syn` (sintaxis del dialecto: `y` no `&&`)
  5. `escuchar c:` consumía `:` dos veces → removido el token_esperar duplicado: `syquex/parser.syn`
  6. `canal <- valor` generaba `0;` (envío NUNCA emitido en ruta .syq) → SentenciaExpr despacha sentencias de canal envueltas: `compilador/generator/generator.py`
  7. `texto` no puede viajar por canal como void* → par runtime `canal_enviar_texto`/`canal_recibir_texto` (CadenaSegura por valor + liberación heap emisor): `runtime/core/concurrency.c`, `synapse_rt_types.h`, emisores
  8. `extern void _listener_N` faltante (pre-scan no recursaba en cuerpos) → `_contar_escuchar_emision` recorre funciones: `compilador/generator/generator.py`
  9. Send `<-` parseaba su RHS con unario (envío anidado en suma → C inválido) → el envío consume la expresión completa y retorna: `syquex/expr.syn`
- **Enlaces rotos en conftest (build, no tests):** `test_math/texto/tiempo/web` no enlazaban sus `.o` del runtime (math.o/texto.o/tiempo.o/web.o). ADVERTENCIA: `test_tiempo/test_web` pasaban por EXES STALE (fuente Sep 1 > exe Aug 26) — trampa documentada en AGENTS.md; al reconstruir fallaban → enlace real corregido.
- **Resultado:** tests/syquex 273 passed (antes 252), 6 failed restantes = 2 contradicciones de FÁBRICA (regla 5 → Arquitecto):
  (a) `test_result.py` 3 tests exigen compilar INTENTO/PARA_EN por el puente vs `tests/unit/test_puente_canonico.py::test_no_soportados_fallan_rapido` exige fail-fast (decisión 93e1ee5: handlers generaban C silenciosamente incorrecto — PARA_EN→while(0), LISTA_LIT→NULL). AMBOS inmutables → decisión del Arquitecto: o implementar backend de NODO_INTENTO/ PARA_EN, o modificar test_result.
  (b) `test_wasm_extended.py` 3 tests exigen el WAT en stdout vs el C nunca lo imprime (solo buffer interno + archivo .wat temporal que borra). Roto desde el commit de creación 45cfcd7 (test C y test Python nacieron incompatibles).
- **Otros fallos verificados preexistentes a HEAD (no míos):** `test_r3_param_adt` (D-2 documentada, ROJO TDD deliberado), `test_seccion_es_de_manual` (roto por construcción propia, documentado).
- **Gates:** verificar_alineacion SIN BRECHAS (D-9: syquex/parser.syn registrado en MODULOS_D9.md); lectura file-binding OK (24 registros); MTO rc=0; MTS multi-plan rc=0.
- **Lección:** exe stale = verde falso (confirmado empíricamente 2 veces en esta ronda); el verificador anti-stale de build_syquex_frontend.py funciona, el patrón `if os.path.exists(BIN_ABS): return BIN_ABS` en fixtures NO verifica mtime.

---

## 🚦 1. DASHBOARD — Actualización de sesión 2026-09-16

**Exploración FFI y arquitectura del AST:**

- Fase 32 completada (F32.1-F32.4). Próximo ME: Fase 32.5+ (puente FFI lista/mapa).
- **Fase 32 completada** (F32.1-F32.5, 72 tests GREEN):
  - **F32.1 Grafo de Conocimiento** (fa34825): `nucleo/grafo_conocimiento.syn` (471 líneas, 22 funciones, 13 tests)
  - **F32.2 Explorer + Architect Det.** (de7107c): `opensyn/explorer_det.syn` (BFS, `ArchivoRelevante`, 6 tests) + `opensyn/architect_det.syn` (DFS invertido + Tarjan, `AnalisisImpacto`, 11 tests)
  - **F32.3 Memoria Persistente Cifrada** (e0493bf): `opensyn/memoria_persistente_cifrada.syn` (XSalsa20-Poly1305 + Argon2id, 14 tests)
  - **F32.4 Pipeline Multi-Agente** (f3dab3f): `opensyn/pipeline_multiagente.syn` (5 fases, 5 modos, 15 tests)
  - **F32.5 Verificación AOT** (20ba43f): `opensyn/verificacion_aot.syn` (auto-refutación, timeouts, 13 tests)
  - Todos con plan MTS, expediente de alineación, lecturas registradas.
- `nucleo/grafo_conocimiento.syn` registrado en `docs/gobernancia/mapa_alineacion.md`
  → Manual 6 §1.1, Manual 2 §5.1.
- SemNodo struct confirmado en `nucleo/analizador_semantico.syn:74` + `nucleo/ast_abi.syn`;
  NODO_* constants provienen de `importar parser_constantes` (Manual 2 §7.2 = ILUSTRATIVO).
- Patrón FFI lista/mapa: `entero` handle, NO `lista`/`mapa` tipo. Ver detalle en
  `docs/fases/f32_exploracion_ffi.md`.

**Archivo de referencia:** `docs/fases/f32_exploracion_ffi.md` (bitácora completa de la exploración).

## 🚦 1. DASHBOARD — Actualización de sesión 2026-09-17

**Fase 32 COMPLETADA — Agente de Codificación Avanzado y Memoria Persistente:**

- Fase 32 completa (F32.1-F32.5). 72 tests GREEN, 5 expedientes, 5 planes MTS.
- Próximo: definir Fase 33 del roadmap.

## 🚦 1. DASHBOARD — Actualización de sesión 2026-09-18

**ME r150_funcional EN CURSO — estado de oráculos y gates (WIP sin commit):**

- Plan: `docs/plan_ME_r150_funcional.md` (12 bloques: M1 llvm/wasm a _RT_FUENTES,
  M2 cluster worker_*, M3a-d CLI honesto, M4 construir eliminado (D-R150-2),
  M6 versión única desde VERSION, M7 raw string, M13 .gitignore, M14 pytest-timeout,
  M15 std/testing.verificar + oráculo matriz de compilación).
- WIP (12 archivos): cli.py, pipeline.py, compilador/generator/generator.py,
  runtime/core/cluster.{c,h}, std/testing.syn, scripts/verificar_e2e.py,
  .gitignore, requirements.txt, ROADMAP.md + NUEVOS: plan, tests/auditoria/test_oraculos_r150.py.
- ORÁCULOS R150 (sesión 2026-09-18, ronda 2): test_oraculos_r150.py **14/14 GREEN**.
  - M2 RESUELTO: el probe C ahora enlaza la FRONTERA CANÓNICA del S1 (_RT_FUENTES:
    synapse_rt + runtime/core/*.c + motores nucleo + tweetnacl + sqlite3 + cuánticos +
    federated + IA, pipeline.py:828-850) — el harness anterior enlazaba solo
    cluster.c+synapse_rt.c y el link reventaba con pool_alloc/sha256_*/crypto_*.
    Lección: un probe que enlaza menos que el S1 no mide la frontera real.
  - M3d RESUELTO (2 bugs reales en cli.py): (1) `_debug_cargar_traza` construía la
    lista `eventos` pero nunca la incluía en `meta` → KeyError 'eventos' (D-R150-5);
    (2) `--reverse` con semántica off-by-one: el cursor apunta al SIGUIENTE evento
    de --step, retroceder debe mostrar _dbg_pos-2 (D-R150-6).
  - M4 RESUELTO: `axon_build.exe` eliminado también de los comentarios de cli.py.
  - MATRIZ (sesión 2026-09-18, ronda 3): **31/35**. math/mem RESUELTOS con D-R150-8:
    los prototipos hardcodeados `Tensor crear_tensor(int,int)`/`Tensor reserva(int)`
    en generator.py:893/emit_tensors.py contradecían las definiciones int64_t
    emitidas desde std.math/std.mem (entero→int64_t desde 86e89db) → "conflicting
    types" en _synapse_shared.h. Fix: int64_t en prototipos y emisores; el ancho
    64-bit de entero está en Manual 2 §4.1 ("Alias de int64_t") — ancla real, sin
    desviación. Regresión: 633 passed/4 failed línea base EXACTA.
  - MATRIZ (sesión 2026-09-18, ronda 4): **35/35 GREEN — ME CERRADO**. Los 4 fallos
    restantes resueltos con D-R150-9/D-R150-10:
    (a) parseo: Manual 2 §2 L56 hace `[ "->" tipo ]` OPCIONAL en declaracion_funcion;
        el parser lo exigía → retorno ausente normaliza a 'nulo' en
        _parsear_def_funcion y _parsear_externo_funcion (+ UnboundLocalError de
        tok_retorno en DeclaracionExterna corregido);
    (b) casts `(Decimal)x`: no existen en la gramática; la coerción entero→decimal
        en FFI es implícita (verificada por bisección, caso F) → eliminados de
        symbolic_exec se_crear_entero;
    (c) TVar ambiguo en quantum_err_corr: CAUSA RAÍZ = tipos capitalizados
        (Entero/Decimal/Puntero/Cadena/Booleano) no son aliases de Manual 2 §4.1;
        el generador los acepta pero el checker unifica TVar frescos por ocurrencia
        (bisección: C3 capitalizado RED, canónico GREEN) → los 4 std normalizados a
        los canónicos en minúsculas;
    (d) agent_skills definía `principal` → colisión con el entry point del programa
        importador → renombrado a demostrar_agent_skills() (los std son bibliotecas,
        el patrón `principal() -> nulo` es solo de programa, M2 §13) + contrato
        requiere (M2 §12, gate global).
    Regresión final: 633 passed/4 failed = línea base EXACTA (0 regresiones).
- Notas D-R150 (ronda 4): (9) los tipos capitalizados NO son aliases del manual:
  los std y el runtime usan SOLO los canónicos §4.1 — el checker no los unifica y
  produce TVar ambiguos; (10) una biblioteca std jamás define `principal`; (11) las
  citas `cumple Manual` a secciones inexistentes (M7 §6 no existe) se re-anclan o se
  documentan como D-R149-1 — el gate las trata como citas muertas bloqueantes.
- GATES (ronda 2): `verificar_alineacion.py` **SIN BRECHAS**; `alineacion.py --verificar
  --me r150_funcional` **OK** (6 archivos, citas textuales verificadas, oráculo ejecutado,
  evidencia auditoria/evidencia/f82eddaa76c1b58f.json); lecturas previas registradas
  (3 registros: M1 §3.1 ×3, M5 §8.1 ×2, M2 §2 ×1); mapa_alineacion gana
  std/testing.syn → Manual 2 §2 (el requisito real del wrapper verificar es la
  gramática, no M7 §2.3); `contrastar.py --plan` resuelve los 12 requisitos y ejecuta
  los oráculos: el del ME pasa, la matriz sigue RED por diseño hasta cerrar los 6
  hallazgos std↔runtime.
- Notas D-R150: (5) meta['eventos'] debe viajar con la traza parseada; (6) semántica
  de cursor del debugger documentada en cli.py; (7) el oráculo matriz vive en SU
  propio archivo (job CI aparte) para que el oráculo del expediente sea ejecutable
  en verde mientras la matriz expone hallazgos; (8) los prototipos de builtin en
  generator.py y los emisores de emit_tensors.py deben mantener paridad de tipos
  con el C emitido (entero=int64_t, Manual 2 §4.1) — el compilador y sus protos
  son UNA sola frontera de tipos.
- GOBERNANZA RESUELTA (sesión 2026-09-19, decisión del Arquitecto "alinea todo a lo
  que indican los manuales"): (1) el oráculo matriz quedó integrado en
  .github/workflows/ci-tests.yml como job aparte `matriz-compilacion` (ubuntu,
  gcc, 90 min) y los jobs test/bootstrap lo excluyen con --ignore (D-R150-7); (2)
  D-R150-9 RATIFICADA: Manual 2 §4.1 es la línea canónica — los tipos capitalizados
  NO son aliases y los std se normalizan a §4.1; el parser NO acepta capitalizados.
  Además el plan ganó los bloques M16/M17 (rondas 3-4) con citas M2 §2/§4.1 y el
  gate MTS fase 4b contrastar.py pasa con 14 requisitos y 2 oráculos ejecutados en
  release (docs/verificacion_ME_r150_funcional.md creado).

<!-- H-R192-4 (2026-10-20): el pre-commit (paso “Limpiando artefactos de build") BORRA binarios no rastreados del source tree — synapse_stage*.exe NO se versionan (correcto); tras cualquier commit, restaurar la cadena con `.venv/Scripts/python.exe build.py` (rc=0, S2==S3). La evidencia del hook (auditoria/evidencia/<hash>.json) se REGENERA determinista (lista sorted); commitear la regenerada y el próximo hook no producirá diff. -->

<!-- H-R193-3 (r193, 2026-10-21) Lección de fixtures/infra: un meta-test de
auditoría cuyo cuerpo termina en `return bool` y comparte un contador global
PASS/FAIL tiene aserciones FALLIDAS fillas de pago: pytest ignora el valor de
retorno (PytestReturnNotNoneWarning), el check queda impago en el contador y
el SIGUIENTE test lo cobra (el assert FAIL==0 vivía solo en el último test).
Cobrar la cuenta POR TEST (fixture autouse de reset + assert propio) vuelve
legible cuál check falla. Compañera H-R193-4: cuando un mismo comando de
enlace se arma en DOS caminos del pipeline, la paridad debe ser COMPLETA
(módulos, flags del ld Y base_flags) antes de subir cualquier piececita
suelta; y las keys de caché que comparan strings deben canonizar espacios
(' '.join(s.split())) — el doble espacio con flags vacíos vaciaba el HIT del
runtime (46 .o recompilados ~90 s por pasada). -->
| 2026-11-20 | **r274_gates_independientes** | P0 · CERRADO (corregido) | Cita fabricada de M9 §6.2 sustituida por citas literales; --mutar ya no toca el árbol; oráculo cableado en CI | Manual 9 §6.1, §6.2; Manual 1 §7.4 | contrastar 4/4 PASS; H-R274-1 resuelto (firmas Ed25519 verificadas) | docs/reportes/R274.md | 65a79c7, 8fbd0ce | 

| 2026-11-20 | **r275_opensyn_e2e_bench** | P0 · CERRADO | E2E real con llama-server+GGUF, benchmark medido, sandbox y privacidad de red; runner como oráculo único | Manual 7 §7.2, §7.3, §8; Manual 9 §5.5 | contrastar 4/4 PASS con oráculos ejecutados; E2E 4/4; H-R275-1 abierto | docs/reportes/R275.md | 251ddc4 | 
