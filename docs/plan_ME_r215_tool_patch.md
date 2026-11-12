# Plan ME r215_tool_patch - TOOL aplicar_patch con sandbox y aprobacion

FASE: POST-FASE 33 - PLAN MAESTRO INDUSTRIAL (Frente B)
ID: r215_tool_patch
ESTADO: implementacion
ORIGEN: el plan maestro industrial (Frente B, ola 1) exige `aplicar_patch` como
tool de OpenSyn con sandbox y aprobacion; la evaluacion 2026-11-08 §6.1 lo
declara brecha de producto.

## 1. Resumen del micro-entregable

Implementar `TOOL aplicar_patch <ruta> :: <diff>` en el agente OpenSyn. El diff
es un unificado (`@@ -a,b +c,d @@`) que se aplica en memoria, se valida contra
el contenido real y solo se escribe si todas las lineas de contexto/borrado
coinciden. La ruta se confina al workspace y la operacion pasa por la matriz de
permisos como `editar` (nivel ASK), por lo que exige aprobacion explicita.

### Requisito R1 - Sandbox y aprobacion de la escritura

requisito: Manual 7 §7.3
texto: "**Sandboxing:** El servidor de inferencia se ejecuta con permisos mínimos."
implementacion: `herramienta_aplicar_patch` valida la ruta con
`herr_ruta_permitida` antes de leer o escribir; el despacho de
`ejecutar_tool_aprobado` aliasa `aplicar_patch` a `editar` en la matriz de
permisos (MAX_HERRAMIENTAS = 8, contrato inmutable) y normaliza la ruta a
absoluta antes de `verificar_permiso_completo`, igual que `escribir`/`editar`.
Sin aprobacion (`aprobado == 0`) la respuesta es `[TOOL_ASK]`; en stdin no
interactivo se deniega cerrado.
oraculo: tests/integration/test_tool_patch.py

### Requisito R2 - Tool de parche del asistente local

requisito: Manual 7 §1.1
texto: "OpenSyn es el **asistente de inteligencia artificial local** del ecosistema Synapse. Es el equivalente a un «Copilot» o «OpenCode»"
implementacion: `opensyn/herramientas.syn` agrega
`herramienta_aplicar_patch(ruta, diff, cwd)` con un aplicador de diff unificado
determinista (`herr_aplicar_diff`) que soporta hunks `@@`, contexto, borrado,
adicion y marcador `\ No newline at end of file`; rechaza contexto no aplicable,
hunks desordenados y diffs sin hunks sin tocar el archivo. El System Prompt del
agente documenta la nueva tool y `principal.syn` la despacha.
oraculo: tests/integration/test_tool_patch.py

### Requisito R3 - Contratos en funciones publicas nuevas

requisito: Manual 2 §5.1
texto: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
implementacion: `herramienta_aplicar_patch` y los helpers publicos nuevos
declaran `requiere`/`garantiza` booleanos; no se agregan funciones publicas sin
contrato.
oraculo: tests/integration/test_tool_patch.py

## 2. Archivos a modificar

- `opensyn/herramientas.syn` - `herramienta_aplicar_patch` + aplicador de diff.
- `opensyn/principal.syn` - despacho `TOOL aplicar_patch`, alias de permisos,
  normalizacion de ruta y prompt del agente.
- `tests/integration/test_tool_patch.py` - oraculo de comportamiento NUEVO.
- `docs/alineacion/r215_tool_patch.md` - expediente.
- `docs/reportes/R215.md` - reporte.

## 3. Cita del manual (grep-chequeable)

```c
// cumple Manual 7 §7.3: la ruta del parche se confina al workspace y la escritura exige aprobacion
// cumple Manual 7 §1.1: tool aplicar_patch del asistente local equivalente a OpenCode/Copilot
// cumple Manual 2 §5.1: requiere/garantiza booleanos en las funciones publicas nuevas
```

## 4. Verificacion

- `.venv\Scripts\python.exe main.py opensyn/herramientas.syn --check --no-emit` - rc=0
- `.venv\Scripts\python.exe main.py opensyn/principal.syn --check --no-emit` - rc=0
- `.venv\Scripts\python.exe -m pytest tests/integration/test_tool_patch.py -v` - verde
- `.venv\Scripts\python.exe -m pytest tests/integration/test_herramientas_escritura.py tests/integration/test_permisos_opensyn.py -v` - regresion verde
- `.venv\Scripts\python.exe auditoria\verificar_alineacion.py` - 0 brechas
- `.venv\Scripts\python.exe auditoria\contrastar.py --plan docs/plan_ME_r215_tool_patch.md` - verde
- `.venv\Scripts\python.exe auditoria\alineacion.py --verificar --me r215_tool_patch` - sin brechas
