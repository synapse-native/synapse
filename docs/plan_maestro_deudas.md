# PLAN MAESTRO DE DEUDAS — mandato "repara todas las deudas, nunca deuda nueva o antigua"

**Fecha:** 2026-10-03 · **Base:** 4ebd025 (R177) · **Autoridad:** Arquitecto —
"estas autorizado a tomar las decisiones siempre que sigas las reglas".
**Regla de dirección del Arquitecto (sesión 2026-10-03):** los tests SOLO se
modifican para ALINEARLOS al manual. Si el código está alineado y el test no,
se modifica el test aplicando TDD (RED→GREEN) y verificando con MTO.
Todo ME sigue el ciclo MTS completo (plan → leer → codificar → oráculo →
gates → commit → docs post-commit) y cita Manual X §Y en cada archivo tocado.

## Cola de MEs (prioridad por radio/costo, actualizable)

- **R198b1/ME r198b1_resello (CERRADA 2026-10-27, commit b657bb8):**
  cierre H-R198b-1 — re-sello auto-sanante de `cambio_hash` en
  `auditoria/alineacion.py`: `cmd_verificar` era un círculo (el re-sello
  solo corría tras pasar y el mismatch retornaba antes; el mensaje pedía
  re-ejecutar lo que no podía sanar). Fix: helper
  `resellar_hash_expediente(me, ch)` + predicado `_solo_brecha_hash_stale`
  (no enmascara otros errores) + re-verificación de una pasada in-proceso
  (converge: la huella cubre blobs de producción, nunca el expediente);
  aviso no bloqueante de sello sin stage (huella sobre blobs del INDEX,
  lección R188/d948cab). Oráculo tests/auditoria/test_oraculos_r198b1_resello.py
  4/4 (A2 END-TO-END: expediente con hash anulado → rc=0 y expediente
  byte-a-byte restaurado — el caso que antes exigía edición manual).
  Gates: contrastar RC=0, verificacion_ME validada, verificar_alineacion
  SIN BRECHAS. **Deuda NUEVA a cola:** H-R198b1-2 (test inmutable
  tests/auditoria/test_paridad_nodos.py::test_emision_s1_cita_los_nodos_canonicos
  FALLA PREEXISTENTE en HEAD — verificado por aislamiento con stash —,
  exige la ancla MTS `cumple Manual 2 §12` en el desugar de PARA_EN de
  `compilador/puente_canonico.py`; ME futuro: añadir el comentario de cita
  al archivo de producción, sin tocar el test).
- **R198b/ME r198b_contratos (CERRADA 2026-10-27, commit f10401f):**
  cierre H-R196-3 — veredicto CONTRA la hipótesis de R198: el emisor de
  contratos NO estaba roto (emitía fielmente el AST, M2 §5.1 en CADA
  `retornar` con `_resultado_` del tipo REAL, emit_declarations.py
  L781-816); las cláusulas de std/opensyn estaban bajo semánticas no
  canónicas y se corrigieron hacia el manual (precedente H-R196-1):
  std/sistema.syn subcadena (1,2)→(1,1) fin EXCLUSIVO (r196) en
  `garantiza` de `_validar_ruta_segura` + patrón de resolución relativa;
  opensyn/principal.syn L213 alias bare `resultado`→`_resultado_`
  (ruta_config_absoluta; la compilación S1 fallaba con robo del
  `_resultado_` int64 de otra función) y L1065 `longitud(_resultado_)
  >= 0`→`_resultado_ >= 0` (pct_contexto — el C inventado NO compilaba;
  cláusula del recorrido de validación M7 §4.2). Oráculo NUEVO
  auditoria/oraculos/oraculo_r198b_contratos.py 3/3 (compilación
  principal.syn rc=0; sandbox contratos 5/5 antes 3✓/1✗/1E
  rc=0xC0000009; regresión r198 3/3); contratos/sandbox 44 passed +
  borrowing 17. Gates: plan MTS contrastar RC=0; expediente r198b_contratos
  0 brechas (3 CUMPLE, evidencia ca4229aa1e9364ab); sello
  r198b_contratos.antes.json (base 3aa5b6c). Reporte
  docs/reportes/R198b.md. Hallazgo NUEVO H-R198b-1 (círculo del re-sello;
  CERRADA por r198b1, arriba).
- **R198/ME r198_cesion_struct (CERRADA 2026-10-26, commit 18ee4ee):**
  cierre H-R197-1 — cesión de `texto` a campo de struct transfiere la
  propiedad al CAMPO y el ORIGEN queda CONSUMIDO (move semantics M4 §3.3,
  paridad H-R182c-1 extendida de args a asignación-campo; M2 §5.1 el cleanup
  RAII del scope respeta la cesión; M2 §12 contratos en el probe nuevo).
  Emisores S1 (emit_declarations.py visitar_asignacion_campo) y nativo
  (nodos_flujo.syn gen_visitar_asignacion_campo + unity regenerada con
  _rebuild_generator.py). Probe determinista auditoria/probes/
  probe_cesion_struct.syn (C sin `_syn_texto_liberar(p)` en armado, salida
  íntegra rc=0) + oráculo auditando/oraculos/oraculo_r198_cesion.py 3/3; E2E
  real del instalador: config.toml `ruta` íntegra.
  Gates: plan MTS docs/plan_ME_r198_cesion_struct.md contrastar RC=0,
  expediente docs/alineacion/r198_cesion_struct.md 0 brechas (evidencia
  e004e8e8e8645718, 5 CUMPLE), verificar_alineacion SIN BRECHAS. Reporte:
  docs/reportes/R198.md. Resoluciones ACTUALIZADAS: la deuda fija H-R196-3
  (emisor de contratos con `garantiza` sobre el valor de retorno texto:
  probe rc=0xC0000009 hoy vs 0xC0000374 ayer, misma cláusula) queda con
  resolución asignada al **ME r198b** junto al hallazgo nuevo de la misma
  familia (compilación S1 de opensyn/principal.syn falla: `garantiza:
  longitud(resultado)` sin renombrar a `_resultado_` + robo del
  `_resultado_` int64 de otra función — el emisor de contratos debe resolver
  el símbolo del valor de retorno por TIPOS, no por nombre de variable).
  *Nota de alcance:* el plan de r197 contemplaba "bootstrap 3 etapas" para
  esta familia; el fix del emisor S1 NO requiere bootstrap (S1 Python es el
  compilador de producción); la paridad nativa quedó cubierta por el módulo
  + rebuild de la unity — bootstrap integral queda pendiente del ME de
  bootstrap dedicado.
- **R197/ME r197_instalador_usuario (CERRADA 2026-10-25, commit ad4f5bd):**
  hallazgos de EJECUTAR el instalador como usuario real (rc=0 ≠ funciona):
  (R1) wrapper `_syn_hash_archivo(CadenaSegura)` en runtime/core/modelo.c —
  la nativa `const char*` de axon.c leía `longitud` como puntero y el hash
  salía VACÍO ("checksum incorrecto" con el archivo CORRECTO); E2E real RC=0
  con hash verificado (gguf 873 MB).
  (R2) descarga TLS vía curl del sistema (`curl -L -fsS --create-dirs`) —
  `_syn_descargar` es HTTP/1.0 plano sin TLS/redirects (HF 30x HTML).
  (R3) externos `-> entero` (int64_t, r194; el TU del instalador no compilaba)
  + convención 0=éxito en escribir_config.
  Gates: expediente r197 0 brechas (evidencia 0491b2530072b608), plan MTS
  contrastar RC=0, verificar_alineacion SIN BRECHAS, familia instalador 17/17,
  oráculo 8/8. Reporte: docs/reportes/R197.md.
  **Deuda NUEVA a cola:** H-R197-1 (REPRO DETERMINISTA: el emisor libera el
  parámetro `texto` cedido a un campo de struct al retornar — H-R182c-1
  extendida a structs — y el slab TLS reciclado corrompe el campo →
  config.toml `ruta` prefix reciclado; fix: emisor + self-host + rebuild +
  bootstrap 3 etapas, ME propio; provoca también los 2 fallos PREEXISTENTES
  de test_oraculos_config_ruta — rc=0xC0000374 heap corruption en el
  contrato garantiza del probe, bisect con stash OK) y H-R197-3
  (seleccionar_modelo hardcodeado; §7.2.5 exige leer modelos.toml M9 §5.6;
  DESVIACION en expediente con correccion anclada al diff installer.syn:10-11;
  ME propio con binding TOML).
- **R196/ME r196_deuda_contrato_y_cobertura (CERRADA 2026-10-23, commit d022ad8):**
  los 2 fallos DETERMINISTAS del barrido r195 cerrados (los 5 del grupo A
  pasaban aislados — infra del barrido):
  (R1/H-R196-1, decisión Arquitecto ratificada "corregir contrato al manual")
  `requiere: longitud(subcadena) > 0` retirado de contiene/indice_de en
  std/texto.syn (4 sitios; M8 §1.7.3 declara bindings SIN precondición; el
  barrido r192 la añadió sin mandato). Runtime E2E ya lo manejaba
  (contiene("hola","")→1, indice_de→0). Cierra
  test_string_utils::test_contiene_subcadena_vacia (13/13).
  (R2) cobertura 44.719%→51.228% (≥45%) con tests NUEVOS
  tests/syquex/test_sandbox_cover_r196.py (probes .syn por el pipeline:
  sandbox H-CFG-2 dentro/fuera + builtins de texto); cierra
  test_syquex_coverage::test_cobertura_total_minima (verificado aislado rc=0).
  Gates: expediente sellado (hash del index), contrastar RC=0 (2× en hook),
  verificar_alineacion SIN BRECHAS, oráculo r196 4/4.
  **Deuda NUEVA a cola:** H-R196-2 (std/texto.syn con 12 funciones duplicadas
  en 2 bloques; dedupe ME futuro) y H-R196-3 (frontend Syquex SEGFAULT
  0xC0000005 compilando .syq con Resultado/err/ok/abrir/atrapar — 10 fallos
  del medidor de coverage: test_result×5 + test_concurrency×5, fuera del
  barrido de integración; repro aislado; familia de H-R182b; ME futuro de
  bisección).
  Reporte: docs/reportes/R196.md.
- **R195/ME r195_instalador (CERRADA 2026-10-23, commit 53578a6):** mandato del
  Arquitecto ("deja el instalador completamente funcional y operativo") — los 3
  skips declarados de la familia instalador se cerraron ENTREGANDO el artefacto
  que cada test INMUTABLE exige (sin tocar tests):
  (R1/M9 §4.1) scripts/uninstall.py NUEVO — reversa de install.sh
  (/opt/synapse + symlink + log) e installer.syn (~/.opensyn);
  --list/--dry-run/--yes; E2E probado en HOME temporal rc=0; skip TDD de
  test_uninstall.py:28 CERRADO.
  (R2/M9 §2.5) synapse_lsp.exe REAL compilado en raíz con el pipeline del
  proyecto (nucleo/lsp_v3.syn --release, 304 KB); el skip de
  test_install_windows.py:33 CERRADO (artefacto local regenerable, no comiteado).
  (R3/M9 §7) install.sh delegador NUEVO en raíz (exec a
  instaladores/linux/install.sh); el skip de test_install_linux.py:25 CERRADO.
  Suite familia instalador: 25 passed / 0 skipped / 0 failed (rc=0).
  Gates: contrastar RC=0, verificar_alineacion SIN BRECHAS, sin cambios de
  producción (gate de lectura no aplica).
  Reporte: docs/reportes/R195.md.
- **R194/ME debt_gobernanza (CERRADA 2026-10-22, commit aade9dc):**
  mandato explícito del Arquitecto ("eligencia el agujero de seguridad; catálogo real,
  nada de placeholder; completa las citas; no se deja deuda") → 6 frentes en un ME:
  (R1) H-CFG-2 CERRADO — sandbox `_syn_ruta_validar` (runtime/core/sistema.c,
  composición `_syn_normalizar_ruta`+`_syn_ruta_en_directorio` H-EOF-3a/b,
  contención del cwd) enraizado en AMBOS emisores: builtin `leer_archivo`/
  `existe_archivo` SIN import pasan por el validador antes del runtime
  (emit_expressions.py + orquestador.syn enraizado al sandbox, separador
  `_syn_leer_archivo(_syn_ruta_validar(arg))`); externs añadidos a ambos
  preámbulos con firma `int64_t` alineada a std/sistema.syn (evita conflicting
  types en TU compartidos — hallazgo del bootstrap); oráculo NUEVO
  tests/auditoria/test_oraculos_r194_sandbox.py 4/4 (E2E pipeline real:
  lectura dentro OK, evasión fuera RECHAZADA sin crash, paridad nativa).
  (R2) H-R144-3 CERRADA con evidencia: 5/5 SHA256 de modelos.toml verificadas
  2026-10-22 contra X-Linked-ETag (LFS) de HuggingFace.
  (R3) MTO saneado de citas fantasma y GREEN sin citador; 3 SIN_CITA heredados
  de Fase 32 CERRADOS (OBL-M7-04/05/06 añadidas, auditar rc=0).
  (R4) Full-scan auditor: 0 SIN_CITA, 0 SNIFF, 0 SIN_OBL.
  (R5) D-R163-1 RATIFICADA (Arquitecto: "todo se ajusta a los manuales, incluyendo
  el roadmap" → k=claves vigente dfdb1bd) y 33.3 (R149 §5) CERRADO — única
  desviación vigente test_ai_explain ya cerrada en R183e.
  (R6) D-R194-1 RATIFICADA por el Arquitecto (sesión 2026-10-22): las suites-guarda
  estructurales ya commiteadas (24 archivos, 113 aserciones) son VÁLIDAS; lista
  cerrada FAMILIA_ESTRUCTURAL_RATIFICADA en auditar_calidad_tests.py (D-R194-1);
  los archivos NUEVOS/MODIFICADOS fuera de ella faten con --estricto-sniff;
  el RESUMEN muestra el conteo exento (nunca oculto).
  Bootstrap S1/S2/S3 con el fix sellado (S2==S3 verificado por build.py).
  Gestión de deuda restante: el barrido integración r191 quedó en CERO
  (grupos A+B+C cerrados en r193/r192); deuda nueva que aparezca en el
  barrido del día se tria con la misma cola.
- **R192/ME deuda_barrido_r191 (CERRADA 2026-10-20, commit 4e97f3f):** 19 fallos del barrido
  completo de integración (1600 tests, post-commit d8f03ac, PYTEST_RC\=1,
  2h39m), TRIADOS con worktree dual (HEAD 621051a vs working tree): TODOS
  PREEXISTENTES (NO regresión de r191):
  (A) infra 8: test_axon_e2e 3 (test_axon_lock: AssertionError del lock),
  test_gen_helper, test_path_traversal_binary; test_cache_audit 1
  (test_axon_lock_existente); test_opensyn_cli 3 (has_chat_mode /
  principal_syn_exists / wrapper_exists); test_cache_adv_10 1
  (test_segunda_compilacion_mas_rapida).
  (B) paridad nativa S1 9: test_fase2_nativa_hm 2 (r17 orden instancia↔struct,
  r18 match binding); test_cobertura_d5 2 (codegen_s1 extenso/principal);
  test_binario_real_10 2 (suma, escribir_linea); test_contracts_e2e 2
  (garantiza_pasa, requiere_pasa_en_runtime); test_e2e_borrow_abort 1.
  (C) borrow checker 2: test_borrowing_adv_10 test_borrow_conflicto_detectado
  + test_borrow_mutual_exclusivo — el parser NO acepta `d: &mutable Dato`
  ("Se esperaba RPAREN") por lo que el conflicto `&mut` doble nunca llega al
  checker; deuda del parser de params (M2 §9.3).
  Resolución asignada: barrido grupo C en el próximo ME de lifetimes (r192);
  grupos A/B en ME de fixtures/infra. Reporte de triaje: fila del día en
  AUDITORIA_ALINEACION_MANUALES.
  **CIERRE DEL GRUPO A (2026-10-21, a78c57a, ME r193_fixtures_infra):** los 8
  fallos de infra CERRADOS con dos hallazgos de producción descubiertos por
  ese frente (H-R193-1/H-R193-2): el enlace cacheado `_link_object` faltaba
  de paridad respecto del enlace normal (módulos quantum/federated/IA,
  `-Wl,--allow-multiple-definition` por el dup de quantum_err_corr.o,
  `-static` win32 + SYNAPSE_GCC_FLAGS) y la key de caché de los .o comparaba
  `base_flags` crudo (doble espacio desalineado entre caminos ⇒ 46 .o recompilados
  en cada pasada ~90 s). E2E: 2.ª pasada 0,9 s con [CACHE HIT] y 0
  recompilas — cache.syn (M1 §4) operativo. Oráculo r193 PASS (grupo A
  completo RC=0); unit 514 ✓; expediente 0 brechas (270133df57df7614);
  contrastar RC=0. Reporte: docs/reportes/R193.md. BARRIDO r191 EN CERO
  (A+B+C).
  **CIERRE (2026-10-20, 4e97f3f):** grupos B (paridad nativa S1: fase2_hm
  112✓, cobertura_d5 15✓, binario_real 8✓, contracts_e2e 9✓ rc de ley
  1c1044c, borrow_abort 1✓) y C (borrowing_adv_10 7✓ — la sintaxis vigente
  es `&mut` M4 §4.2; la forma retirada `&mutable` Foster se alineó al manual).
  Nemotecnia de la deuda: los fallos eran asserts desalineados a
  convenciones ratificadas + contratos invalidados por el emisor roto
  ME-27_T3, no bugs del compilador. Contratos reactivados S1+nativo con
  paridad (M2 §5.1/§5.3 §12); std barrida (M2 §5.1 §12 + M3 §12).
  Reporte: docs/reportes/R192.md.
  78b8947/621051a):** deuda de asserts/features medida en vivo tras el fix
  canónico (H-canon-LET RESUELTA en 643b413 + R183e). Primer lote de 5
  archivos:
  11 FAILED → 3 reparados (test_generator 3 asserts alineados al emisor
  vigente: Lifetime Scope `= 42LL; + return _ret_`, mangle
  `_principal_impl` H-R181-4, acceso puntero `= ptr->a;`) y 1 archivo
  con SyntaxError de docstring reparado (test_debugger_timetravel →
  colección bloqueada desde baseline previo) → 49 passed.
  CIERRE (2026-10-18): los 4 RED de test_cli_run_debug cerrados en r190
  (debug CLI alineado a M8 §3.4 con traza real; ayuda rc=0 sin sesión;
  navegación mantiene rc≠0 contrato r150) y el lote declarado del baseline
  (pgo 2 / lifetimes 2 / federated 5) cerrado en r191: aserción pgo al
  rc de ley 1c1044c, checker S1 aplica M2 §9.3 (MISMATCH de
  retorno-&local y de consumo-con-préstamo-vivo; enum+plantillas 6 idiomas,
  línea precisa §10.1), federated al literal canónico `nulo` (M2 §4.3).
  Oráculos r190 3/3 y r191 3/3; unit 514✓; lote 45+1✓.
  ACTUALIZACIÓN R183e (misma sesión, medido): test_listen 4/4 RESUELTOS
  — los tests usaban sintaxis `valor => ...` dentro de `escuchar` que
  NO está en el manual; alineados a la forma canónica M5 §4.2
  (`mensaje = ch ->` + bloque, all rc=0 por probe antes de editar);
  con ello ya solo quedan 4 FAILED: test_cli_run_debug (4 — feature
  gap del dispatcher: `synapse debug --help/step/reverse/snapshots`
  rc=1, ME_27/29/30 del roadmap; M8 §5.2). HALLAZGO H-R184-1 (NUEVA,
  con resolución asignada el ME R184): el parser S1 no acepta la forma
  canónica `coincidir ch ->:` del M5 §3.6 ("se esperaba COLON, se
  encontró ARROW") — el pattern ok(v) => / err(_) alineado al §3.6
  queda bloqueado en S1 (S2/nativo por verificar). Más cola declarada
  del baseline r183e (84 entradas pre-fix, clasificadas/assert por
  revisar): parser_ext (5, hoy GREEN), axon_e2e (3),
  federated/pgo/lifetimes/borrowing (2 c/u). Reglas del lote: asserts
  nuevos corresponden al modelo del emisor vigente Lifetime
  Scope/WeakRef con decisiones ratificadas; los errores de entorno se
  documentan como feature gap, no se debilitan aserciones.
- **R187/ME f14_mto_ci (COMPLETADO, 2026-10-14, 75dc6cf):** cierre del lote
  en vuelo de la sesión anterior (recuperación, no deuda del maestro):
  F1.4 check de cuerpo-bloque tras `funcion:` en el PARSER (M2 §2 L56/L60,
  rc=1; `_validar_cuerpos` del lexer eliminado, M1 §3.1), release_matrix.yml
  real + build.py S2==S3 + distribuir.py sellado (M9), fixtures canónicos
  (M2 §13), paridad emisor embebido (H-R181-3), harnesses A2.3/A3.1.
  Deuda/testigo asignado a ME futuro: H-R187-1 (preexistente: '(' sin
  cerrar en firma malformada activa la continuación multilínea r153 y
  suprime NEWLINE/INDENT/DEDENT del resto del archivo — ruido de cascada,
  decisión del Arquitecto). Reporte: docs/reportes/R187.md.

### ME R178 — check_cli (H-R176-2) — `synapse check` en cli.py
requisito: Manual 8 §4 (+ subfase 26.1 del ROADMAP: flag `--check`/`--no-emit`
para validación rápida usada por el LSP/OpenSyn).
texto: el test test_cli_check (3 fallos) declara en su propio mensaje
"Binario synapse no encontrado — implementar CLI (M8 §4)" — feature gap
DECLARADO. El dispatcher Python no implementa `check` (valida sintaxis +
semántica sin generar código).
implementacion: cli.py despacha `check` al backend (validación sin emitir
binario, paridad con `--check`/`--no-emit` existente en pipeline.py/ principal.syn
según lo que el test exija); oráculo E2E tests/auditoria/test_oraculos_check_cli.py.
impacto: cierra 3 fallos de integración.
estado: COMPLETADO (R178 95b2374 — H-R176-2 cerrada, oráculo 4/4, OBL-M8-16)

### ME R179 — h_r177_1 test_r27: alinear test↔manual↔código (aridad de ctor)
requisito: Manual 2 (declaracion_estructura / instanciación: constructor con
argumentos por campo). Ley: Manual 2 L67 define el ctor posicional.
Decisión autorizada: el CÓDIGO vigente (H-R153-4b ratificada en r153: se RELAJÓ
el check de aridad aceptando ctor posicional con 1 arg por campo, paridad
S1↔nativo) está ALINEADO al Manual 2 (la gramática del ctor posicional existe
en el manual y S1+nativo la implementan de forma paritaria). El test
test_r27_struct_ctor_con_argumentos_rechazado espera el comportamiento PRE-r153
(rechazo rc=7) que ya NO es la ley vigente.
implementacion (TDD/MTO con autorización de dirección del Arquitecto):
invertir la aserción del test a la semántica ACEPTADA por el manual (o
reemplazarla por el caso que sí se rechaza según M2) — RED primero: el test
nuevo falla contra el código actual solo si el código desviara al manual;
GREEN con el código alineado vigente. Verificación MTO del requisito.
impacto: cierra r27 (último fallo de la familia nativa rc=5/rc=0 → familia en CERO).
estado: COMPLETADO (R179 0faea8e — H-R177-1 cerrada, oráculo 4/4, OBL-M2-05)

### ME R180 — coincidir_nativo (H-R177-2): paridad de parser nativo
requisito: Manual 2 §2 — el patrón de `coincidir` según M2 L123-127 es
IDENTIFICADOR/tag/var o "_" (wildcard). S1 además acepta literales (H-R90-6).
Decisión autorizada: implementar en el parser NATIVO el wildcard `_` y los
literales de primitivos que S1 ya acepta (paridad M1 §3.1: mismo AST canónico;
el manual define patron ::= ... | "_" para wildcard, los literales extienden
H-R90-6 vigente en S1).
implementacion: nucleo/parser_sentencias.syn (patrón: token_es_inicio_patron =
token_es_nombre OR T_NUMERO — el wildcard `_` ya lexea como T_IDENTIFICADOR),
emisor NodoCoincidir nativo con case C para literales/wildcard → default
(gen_visitar_coincidir: switch sobre VALOR si dígito en patrones o tipo C
exacto int64_t/int/bool — espejo PRIMITIVOS de emit_control.py; ruta ADT
.tag byte-idéntica), S1 _parsear_coincidir acepta TokenID.NUMERO; puente de
patrones intacto (el patrón sigue siendo un span de texto).
oráculo E2E: coincidir con literal y wildcard compila y corre en nativo.
impacto: paridad total de coincidir S1↔nativo (para patrones numero/wildcard;
residuales: patrón cadena — C no soporta case string, falla igual en ambas
tuberías — y forma de BLOQUE en nativo → ME R183).
estado: COMPLETADO (R180 be5d447 — H-R177-2 cerrada, oráculo 4/4 273.75 s,
OBL-M3-06; H-R180-3 lección TDD: heurística invertida detectada por el
oráculo r4 y corregida a tipo C exacto; H-R180-2 lección de cadena:
rebuild generator.syn SIEMPRE tras editar generador/ y antes de bootstrapear)

### ME R181 — harness_gcc (H-R176-1): entorno de integración
requisito: Manual 9 §6.2 (entorno de CI reproducible: los tests del repo no
pueden depender de exes/objetos inexistentes ni de rutas de include rotas).
Diagnóstico previo (R176): embedded_libs.h no resuelto desde tests/, link del
runtime completo con --allow-multiple-definition, 21 RED TDD exigen artefactos
que nadie construye.
implementacion: reparar el comando gcc del harness (rutas -I, orden de objetos,
targets on-demand para los artefactos que los RED exigen — construcción real,
no stubs). Los tests NO se tocan (no es su deuda).
impacto: ~27 fallos de una vez + habilita medir los RED TDD de verdad.
estado: COMPLETADO (R181 9657482 — H-R176-1 cerrada: CPATH raíz + quantum .o on-demand + shim weak GNUC S1/nativo; oráculo 5/5; quantum 8/8; TestEjecucionReal migrado a exit code via MTO; bootstrap 3 etapas stage2==stage3 c2889554…c91d43; deudas NO-harness halladas en el camino a filas R184/R185/R186)

### ME R184 — lexer_y_keyword (H-R181-3, hallado en R181)
requisito: Manual 2 §2/§3 — la gramática de parámetros acepta IDENTIFICADOR; el
lexer debe clasificar `y` como AND SOLO en posición de operador (o el parser
debe reconocer `y` como nombre de parámetro). Ley: identifiers suelen ir en L21
del lexer (y=keyword AND).
hallazgo: `crear_punto(x: entero, y: entero)` no se parsea porque `y` es
keyword AND del lexer S1 (lexer.py L21, ruta keywords L630-650) — el test
test_programa_estructura_ejecuta (TestEjecucionReal, aserción MTO rc==55) queda
RED por esta deuda, no por su aserción.
implementacion: análisis de contexto del lexer (operador binario vs posición de
nombre: tras `:` o `,` es identificador) o reorden de tabla de keywords; TDD
con el checksum de estructura como GREEN.
impacto: cierra el RED de estructura; desbloquea programas con `y` como
nombre.
estado: COMPLETADO (R184 e4e4022 — regla keyword+':' degrada a identificador con exclusiones sino/requiere/garantiza/inseguro/recuperar y literales verdadero/falso/nulo nunca son nombres (H-R184-1a); fallback primario AND/OR/NOT→Identificador; paridad S1 lexer.py L652 ↔ nativo lexer.syn L529 + parser_expressions.py L184 ↔ parser_expr.syn L624; oráculo r2/r3)

### ME R185 — stdlib_colision_generador (H-R181-4, hallado en R181)
requisito: Manual 2 §9.1/§12 — el C generado debe ser válido; los nombres de
funciones de usuario no pueden colisionar con la stdlib cuyo header se incluye
incondicionalmente.
hallazgo: una función usuario `abs(x: entero)` genera `int64_t abs(int64_t);`
en conflicto con `int abs(int)` de stdlib.h (incluida incondicionalmente) →
gcc error "conflicting types for 'abs'"; afecta a min/max/exit/cualquier
nombre stdlib.
implementacion: prefijado de símbolos usuario (paridad con el mangle de
monomorfos) o no-emisión de prototipos innecesarios cuando la función es local
al modulo; TDD con test_programa_si_sino_ejecuta (aserción MTO rc==5) como
GREEN.
impacto: cierra el RED de si_sino; elimina una clase entera de colisiones.
estado: COMPLETADO (R185 e4e4022 — _COLISIONES_STDLIB 50 nombres en context.py + tabla _resv en orquestador.syn en paridad exacta (oráculo r4); firma/prototipo/llamada emiten _syn_usuario_<n>; externas FFI sin mangle (M6 §3.1); definición _G_native_funcdefs añadida a ambos preámbulos del generador Python — sin ella el unity del compilador no enlazaba)

### ME R186 — toml_raii_runtime (H-R181-1, hallado en R181)
requisito: Manual 5 §5 (toml del runtime) + Manual 2 §9.1 — el test
test_toml_compile_and_run exige compilar, Y ejecutar la escritura/lectura toml
RAII.
hallazgo: tras R181 el test COMPILA Y ENLAZA (CPATH + shim weak) pero el exe
falla en runtime (salida vacía / segfault 0xC0000005 con toolchain canónico):
deuda funcional RAII/toml del path standalone (probe de R181).
implementacion: diagnóstico del segfault (determinar si es del código toml
embebido o del runtime RAII en el path standalone de la suite), reparación y
paridad S1↔nativo.
impacto: cierra el último RED de la familia que era de enlace-ahora-runtime
toml.
estado: COMPLETADO (R184-R186 e4e4022 — causa raíz doble: H-R188-1 params struct ownership liberados en el callee (→ préstamo, M4 §3.3) y H-R181-1 literales estáticos pasados a RAII texto (→ _syn_texto_duplicar al pool); conftest rt_objs pre-colección (H-R186-1); test_toml_raii 2/2 + oráculo r5 FIN RAII OK)

### ME R188 — doble_free_params_struct (H-R188-1, hallado y CERRADO en R184)
requisito: Manual 4 §3.3 — la propiedad solo se transfiere con move explícito;
el default es préstamo; Manual 4 §5.2 — cleanup y liveness en el ámbito del
llamador.
hallazgo: emit_declarations.py registraba TODOS los parámetros con destructor
en el scope del callee → pop_scope liberaba el NodoToml/NodoJson del LLAMADOR
en la 1ª llamada → handle colgante → use-after-free + doble free (0xC0000374)
en la 2ª/3ª llamada (diagnosticado con bisect toml_dbg+stub: doble [LIBERAR
tipo=1] del mismo handle).
implementacion: _es_destructor_ownership (context.py L574) distingue dtors de
ownership (NodoToml/NodoJson → PRÉSTAMO, no se consumen en el callee) de
_syn_texto_liberar (pool del callee, seguro porque el llamador DUPLICA los
literales — H-R181-1).
impacto: test_toml_raii 2/2 GREEN; sin fila de trabajo pendiente.
estado: COMPLETADO (2026-10-07 en R184 e4e4022)

### ME R182a — wasm backend F25 funcional — **COMPLETADO 0c74d80 (2026-10-09)**
requisito: Manual 1 §3.2 — "Traduce el AST validado a código intermedio: C
(C99/C11), LLVM IR o WAT (WASM)."; Manual 8 §4.2 — `--target native|wasm|llvm`.
hallazgo: los "3 RED del plan" ya estaban verdes (test_wasm_extended 9/9, el C es
autocontenido); el fallo REAL era el criterio F25 "genera WASM válido": el WAT
emitía call a funciones no definidas sin import, sin locals, sin drop, y wat2wasm
(locae en emsdk, fuera de PATH) rechazaba todo módulo.
implementacion: wat_generator (imports automáticos env con firma inferida
determinista, locals recursivos, drop en sentencia, export principal/main,
result omitido para nulo, default inalcanzable con result, imports antes de toda
definición); pipeline (búsqueda wat2wasm en emsdk lokal).
oráculo: tests/auditoria/test_oraculos_r182a_wasm_valido.py 4/4 (wat2wasm rc=0,
magic 0asm, export entrada, imports-primero, determinismo byte a byte).
estado: **COMPLETADO** (2026-10-09, commit 0c74d80) — evidencia
auditoria/evidencia/b88df2bbbc5ea917.json; 514 unit, 16 wat_gen, 18 wasm/spa.

### ME R182b — cierre deuda pre-existente test_traductor/test_concurrency
- Hallazgo H-R182a-1 CERRADO (2026-10-10, commit 24d3912): causa raíz = bits
  altos del puntero sin escribir en los 5 literales sintéticos del desugar de
  `para` (syquex/parser.syn); el emisor JSON reconstruía una dirección inválida
  → segfault. Regresión tests/syquex 279 passed / 1 skipped.
- oráculo: auditoria/oraculos/oraculo_r182b.py PASS; evidencia
  auditoria/evidencia/37994ff3735a2c44.json; reporte docs/reportes/R182b.md.
- estado: **COMPLETADO**.

### ME R182+ — feature gaps (cola, una por ME con TDD)
- H-R90-5 (métodos sobre locales en .syq).
- ME_27/29/30 (~21 RED TDD: aiComplete/aiExplain/aiFix, federated, quantum
  build, build/release) — R181 (harness) COMPLETADO: ya medibles.
- YAML de CI release (10): signing/SLSA — infraestructura, requiere secretos →
  documentar como deuda de infra con resolución asignada si no es local.
- ~46 asserts residuales por familia (axon, borrowing, debug CLI, escuchar,
  serialización embebida, lexer rc/modulo, salida_metal.c) tras R181.
estado: PENDIENTE

### ME r188a — deuda_cero_1 (H-R184-1): receive-modo-resultado S1 — **COMPLETADO 9f6b1cd (2026-10-16)**
requisito: Manual 5 §3.6 — forma canónica `coincidir <canal> ->:` (flecha del
receive OPCIONAL ante el ':' del bloque).
hallazgo H-R184-1: el parser S1 rechazaba la forma canónica ("se esperaba COLON,
se encontró ARROW"); el desugar sería trivial (el receive-es-sujeto
Result҉ADO<elem,texto>).
implementacion: flecha opcional en parser_control.py; ExprRecibirCanal
.modo_resultado (ast_nodes); semantic_types tipo Resultado<elem,texto>;
context.registrar_instancia_adt (tipo invisible para el pre-scan D-2);
emit_control sujeto/typedef/compound + emit_expressions canal_recibir(&_ce0)
con ADT especializado (_ce0: bool). Paridad de ENTRADA nativa:
nucleo/parser_sentencias.syn + lexer.syn (fft: TokenID.ARROW opcional).
oráculo: tests/auditoria/test_oraculos_r188_deuda_cero_1.py 4/4 (E2E ok=7/
cerrado-2, histórica sin regresión, firma multilínea).
estado: COMPLETADO (9f6b1cd, evidencia 2afa8c33ad689160 + a2bbf48...
impacto: lee.

### ME r188b — receive_resultado_nativo (H-R188-2): codegen nativo del receive-resultado — **COMPLETADO 2202cce (2026-10-17)**
requisito: Manual 5 §3.6 (M1 §3.1: mismo semantismo en ambos pipelines).
hallazgo: el stage1 NATIVO ACEPTA la sintaxis `coincidir c ->:` (rc=0,
grays compartida) pero su codegen/semantico trata el sujeto como
struct ADT/puntero → C roto (probe nativo rc=5, log capturado).
implementacion: semántica nativa del receive-modo-resultado (expr_eval o
equivalente: tipo Resultado<elem,texto>) + gen_visitar_coincidir (recorrido.syn/
generador: recibir + construir ADT especializado + case .tag) hasta probe
nativo rc=0 con paridad S1 (misma salida de las dos ramas).
oráculo: coincidir-canal con flecha compila y ejecuta en NATIVO (ok/err);
expediente/probes según MTS.
impacto: cierra la brecha nativa de §3.6 (después del r188a S1).
estado: **COMPLETADO** (2202cce, 2026-10-17) — causa raíz: el sujeto tras la
flecha llegaba al codegen como identificador/puntero sin envoltura de receive.
R1: parser_sentencias.syn re-wrapea el sujeto como NODO_RECIBIR_CANAL;
monomorfizacion.syn R24 (ADT builtin Resultado/Opcion + ctors ok/err,
paridad context.py S1) + gen_emitir_str_typedef_instancia (M2 §12);
nodos_flujo.syn sujeto → instancia + typedef + flag _G_co_modo_resultado;
expr_eval.syn statement-expression `canal_recibir(...&_ce0)` con ADT
especializado; orquestador/generator_constants/generator.py global único
(H-R151-3). Hoistos H-r188b-1/2/3 cerrados (typedef dentro del bloque, temp
única, global compartido). Oráculo test_oraculos_r188b.py 3/3; bootstrap
S2==S3 2534e776…; regresión 15/15; unit 514✓; expediente 0 brechas
(c661ce1d660ed5b4); contrastar RC=0; verificar_alineacion SIN BRECHAS.
Reporte: docs/reportes/R189.md

## Reglas transversales del plan
1. Cada ME: plan citando Manual X §Y → `alineacion.py --leer --me <id>` →
   codificar con `// cumple Manual X §Y` → oráculo E2E → unit/regresión →
   expediente + contrastar + verificar_alineacion → commit → docs post-commit.
2. Tests: solo para alinearlos al manual (dirección test→código o código→test
   según dónde viva la verdad, con TDD RED→GREEN y MTO). NUNCA relajar un test
   que codifica el manual vigente.
3. Deuda hallada en el camino: se repara o se registra con resolución asignada
   (cero deuda sin seguimiento). Deuda antigua del mismo archivo/área: misma
   oportunidad de reparación (mandato "no importa de quién es").
4. Antes de commitear: artefactos regenerados por suites → `git checkout --`.
5. Prohibido --no-verify; los 7 gates del pre-commit mandan.

### ME R183 — coincidir_bloque_nativo (H-R180-1, hallazgo de R180) — **COMPLETADO 70ca347 (2026-10-08)**
requisito: Manual 3 §3 L140 — `caso ::= patron "=>" ( sentencia | NEWLINE
INDENT bloque DEDENT )`: la segunda alternativa (cuerpo en bloque) ES ley
(y S1 la implementa: r5_ref compila y corre `tres/hola/4`).
hallazgo: el pipeline NATIVO falla con `Error Fatal Generador: Nodo tipo
[DefinicionFuncion] no reconocido` para CUALQUIER coincidir con cuerpos-bloque,
INCLUSO patrones ADT pre-existentes (bisección R180: sin coincidir pasa;
una-línea pasa; bloque-literal y bloque-ADT fallan igual) — el problema está
en la construcción del AST del caso con cuerpo-bloque o en el walk del
generador nativo, no en los literales.
implementacion: rastrear parsear_coincidir nativo (parser_sentencias.syn: rama
NEWLINE-INDENT del cuerpo del caso) y el walk del generador (recorrido.syn /
nodos_flujo.syn) hasta la divergencia; TDD con probe bloque-ADT (bisect_d de
/tmp/probe_lf) como RED.
oráculo: bloque-ADT y bloque-literal compilan rc=0 y ejecutan en nativo con
paridad S1.
impacto: cierra la segunda forma del caso en nativo (paridad total M3 §3).
estado: **COMPLETADO** (2026-10-08, commit 70ca347) — causa raíz: el anti-cuelgue
R11 del bucle de casos en parsear_coincidir corría también tras un caso parseado
con éxito y consumía el DESINDENTAR que cierra el bloque de casos (b4: el bucle
externo se comía el cierre del cuerpo de la función → `funcion principal`
expuesto como def anidada → rc=1 "DefinicionFuncion no reconocido") o el patrón
numérico del caso siguiente (b1/exotic: rc=8). Fix: flag `caso_parseado` — el
anti-cuelgue solo corre si la iteración no produjo caso. Oráculo NUEVO
test_oraculos_r183_coincidir_bloques.py 7/7 (RED 5/2 confirmado); bootstrap
S2==S3 d8493487…397a944; expediente r183.md huella 19d51d2bf8e46079;
verificar_alineacion SIN BRECHAS; contrastar PASA; MTO OBL-M3-07; unit 510/510;
r180 4/4; r11 5/5. Reporte: docs/reportes/R183.md
