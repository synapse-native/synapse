# Plan ME-r204 — Herramientas de escritura y gate de compilación Fase 32

Contexto: la evaluación del 2026-11-08 dejó dos brechas prioritarias: (1) el
agente OpenSyn solo puede leer (`listar`/`leer`/`git`) aunque la tabla de modos
anuncia `editar`; (2) los módulos de Fase 32 no compilan y no hay gate que lo
detecte. Este ME implementa `TOOL escribir` y `TOOL editar` con sandbox y
confirmación, y agrega un gate de compilación con baseline y trinquete para los
módulos de Fase 32.

Autorización: el Arquitecto pidió explícitamente estas dos capacidades en la
sesión 2026-11-08. El manual no describe la herramienta de escritura con detalle;
se implementa como extensión del rol "equivalente a OpenCode/Copilot" de
Manual 7 §1.1, con el sandbox de Manual 7 §7.3. `aplicar_patch` y la ejecución
de shell quedan fuera de este ME (requieren parser de parches y allowlist de
comandos); se registrarán para r205.

## Ley citada (MTS: requisito / texto / implementacion / oraculo)

requisito: Manual 7 §1.1 (rol de OpenSyn)
texto: "OpenSyn es el **asistente de inteligencia artificial local** del ecosistema Synapse."
implementacion: `opensyn/herramientas.syn` implementa `herramienta_escribir(ruta, contenido, cwd)` con contrato y escritura confinada; `opensyn/principal.syn` despacha `TOOL escribir <ruta> :: <contenido>` en modo CODE.
oraculo: tests/integration/test_herramientas_escritura.py

requisito: Manual 7 §1.1 (rol de OpenSyn)
texto: "OpenSyn es el **asistente de inteligencia artificial local** del ecosistema Synapse."
implementacion: `opensyn/herramientas.syn` implementa `herramienta_editar(ruta, buscar, reemplazar, cwd)`: exige que `buscar` aparezca exactamente una vez y reescribe el archivo; `opensyn/principal.syn` despacha `TOOL editar <ruta> :: <buscar> :: <reemplazar>`.
oraculo: tests/integration/test_herramientas_escritura.py

requisito: Manual 7 §7.3 (sandbox)
texto: "**Sandboxing:** El servidor de inferencia se ejecuta con permisos mínimos."
implementacion: `opensyn/herramientas.syn` rechaza rutas vacías, con `..`, con unidad (`:`), con `~` o fuera del workspace normalizado; la escritura usa `escribir_archivo` de `std.sistema`, que valida contra el cwd. `opensyn/principal.syn` normaliza cwd y ruta antes de `verificar_permiso_completo`.
oraculo: tests/integration/test_herramientas_escritura.py

requisito: Manual 7 §7.3 (sandbox)
texto: "**Sandboxing:** El servidor de inferencia se ejecuta con permisos mínimos."
implementacion: `opensyn/principal.syn::ejecutar_tool_con_aprobacion` pide confirmación interactiva para `editar`/`escribir` (nivel ASK); en stdin no interactivo (pipe) deniega con `[TOOL_ERROR]` y no escribe nada.
oraculo: tests/integration/test_herramientas_escritura.py

requisito: Manual 7 §2.3 (inyección de contexto/prompt)
texto: "OpenSyn **no** necesita un modelo fine‑tuneado."
implementacion: `AGENTE_SYS_BASE` y el prompt del agente en streaming describen el formato `TOOL escribir/editar` y la regla de confirmación; `herramientas_permitidas(MODO_CODE)` mantiene su contrato inmutable (anuncia `editar`, no `escribir`) y `escribir` se aliasa a `editar` en la verificación de permisos.
oraculo: tests/integration/test_herramientas_escritura.py

requisito: Manual 9 §6.2 (validación en CI/CD)
texto: "La suite de tests completa en cada target."
implementacion: `tests/integration/test_compilacion_fase32.py` compila con `main.py --check --no-emit` cada `.syn` de producción de `opensyn/` más `nucleo/grafo_conocimiento.syn`; falla si un módulo fuera del baseline no compila o si un módulo del baseline ya compila (trinquete). El baseline vive en `tests/fixtures/compilacion_baseline.txt`.
oraculo: tests/integration/test_compilacion_fase32.py

requisito: Manual 2 §5.1 (contratos)
texto: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
implementacion: toda función pública nueva de `opensyn/herramientas.syn` y de `opensyn/principal.syn` declara `requiere`/`garantiza` booleanos; cada archivo de producción modificado lleva `// cumple Manual 7 §...`.
oraculo: tests/integration/test_herramientas_escritura.py

## Archivos previstos

Producción:

- `opensyn/herramientas.syn` (nuevo): escritura/edición + sandbox + helpers.
- `opensyn/principal.syn`: despacho de `escribir`/`editar`, aprobación,
  actualización de `herramientas_permitidas` y del prompt.
- `docs/gobernancia/mapa_alineacion.md`: entradas de `opensyn/herramientas.syn`
  y ampliación de `opensyn/principal.syn`.

Tests (nuevos, no se modifica ningún test existente):

- `tests/integration/test_herramientas_escritura.py`: E2E con driver `.syn`
  compilado por `main.py`; escribe, edita, rechaza ambigüedad y path traversal.
- `tests/integration/test_compilacion_fase32.py`: gate de compilación con
  baseline/trinquete.
- `tests/fixtures/compilacion_baseline.txt`: lista de módulos actualmente rotos
  (deuda visible; el trinquete obliga a quitarlos cuando se reparen).

## Oráculos y criterios de aceptación

- `pytest tests/integration/test_herramientas_escritura.py -v` → todo GREEN.
- `pytest tests/integration/test_compilacion_fase32.py -v` → GREEN con el
  baseline actual; si se toca un módulo del baseline y sigue roto, el test
  informa el error exacto; si se repara, exige quitarlo del baseline.
- Regresión: `pytest tests/integration/test_permisos_opensyn.py
  tests/integration/test_opensyn_integration.py -v` → sin regresiones.
- `python main.py opensyn/principal.syn --check --no-emit` → rc=0.
- `python auditoria/contrastar.py --plan docs/plan_ME_r204_tools_escritura.md`
  → RC=0.
- `python auditoria/verificar_alineacion.py` → 0 brechas.
- `python auditoria/alineacion.py --verificar --me r204_tools_escritura` → 0
  brechas y evidencia en `auditoria/evidencia/`.

## Riesgos

- La sintaxis de Synapse no soporta parámetros por defecto ni retorno múltiple;
  el parseo de `ruta :: contenido` se hace con `indice_de`/`subcadena` y
  `herr_desescapar_saltos` para `\n`.
- `std.texto.reemplazar` reemplaza todas las ocurrencias; la herramienta exige
  ocurrencia única antes de llamarlo para evitar ediciones ambiguas.
- El modelo 1.3B puede pedir `TOOL escribir` con rutas o formatos raros: el
  ejecutor falla cerrado y devuelve `[TOOL_ERROR]` sin tocar el disco.
- `tests/integration/test_permisos_opensyn.py` fija `MAX_HERRAMIENTAS = 8`; por
  eso `escribir` se aliasa a `editar` en la verificación de permisos y no se
  cambian las constantes ni la matriz de `opensyn/permisos.syn`. Durante el E2E
  se detectó un doble free preexistente en `permisos.syn` (parámetros `texto`
  pasados sin `_syn_strcpy` a funciones usuario); se corrigió únicamente la
  ownership de esos call sites, sin alterar comportamiento ni contratos.
- El gate de compilación no "arregla" los módulos rotos; los hace visibles y
  impide que la deuda crezca. La reparación de cada módulo es un ME posterior.

## Fuera de alcance

- `aplicar_patch` (parser de diff unificado).
- `TOOL ejecutar` (shell/tests/build con allowlist y timeout).
- `compilar` como herramienta del agente.
- Reparación de los 10 módulos de Fase 32 (solo se congelan en el baseline).
- LSP `aiExplain/aiComplete/aiFix/aiStatus`.
