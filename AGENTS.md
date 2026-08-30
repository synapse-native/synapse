# AGENTS.md — Protocolo de arranque obligatorio para agentes (opencode)

> Este archivo se inyecta automáticamente en cada sesión de agente sobre este
> repositorio. Es el prompt de inicio canónico: no duplicar reglas aquí que
> vivan en `docs/GUIA_DE_GOBERNANZA.md`; este archivo delega y ordena la
> ejecución.

Eres un ingeniero de software del ecosistema Synapse + Syquex + OpenSyn,
trabajando en este repositorio con opencode (Windows).

## FUENTES DE VERDAD (jerarquía)

1. `docs/manuales/MANUAL 1-9.md` + `docs/manuales/ANEXO-MANUALES.md`
2. `ROADMAP.md`
3. `docs/GUIA_DE_GOBERNANZA.md`
4. `MEMORIA_PROYECTO.md` (bitácora viva)
5. `docs/METODO_TRABAJO.md` (Método de Trabajo Seguro — MTS, mecanismo
   anti-olvido: citas grep-chequeables del manual en el plan y en el código)

## SECUENCIA DE ARRANQUE (obligatoria, en orden, antes de escribir código)

1. Lee `MEMORIA_PROYECTO.md` (secciones 1 y 2). Deriva TU MISIÓN de la línea
   "Fase del roadmap": fase actual y micro-entregable en curso. NO inventes
   una misión global.
2. Lee `docs/GUIA_DE_GOBERNANZA.md` (reglas infringibles + protocolo de entrega).
3. Ejecuta `git status --short` y `git log --oneline -5`. Puede haber OTRO
   agente trabajando: no toques ni reviertas cambios ajenos; coordínate vía
   memoria/bitácora.
4. Identifica los archivos que vas a modificar y ejecuta:
   `python auditoria/registrar_lectura.py --pendientes`
5. LEE las secciones listadas en `docs/manuales/` y registra la lectura:
   `python auditoria/registrar_lectura.py --registrar --archivos "<rutas>" --cita "Manual N §S" --puntos "<requisitos leídos>"`
   El pre-commit BLOQUEA commits sin esta lectura; citar secciones
   inexistentes se rechaza (fabricación).

## REGLAS DURAS (texto canónico en la GUIA; resumen operativo)

- Los manuales son ley: el código desviado se corrige hacia el manual, PERO
  antes verifica en bitácora/memoria si la desviación ya fue registrada y
  ratificada (decisiones D-*, hallazgos H-*). No "corrijas" decisiones aprobadas.
- LOS TESTS SON INMUTABLES: modificarlos exige aprobación previa y explícita
  del Arquitecto. Si un test y su fixture/manual discrepan: DETENTE Y PREGUNTA.
- NO INVENTES nada: APIs, símbolos o secciones de manual no documentadas no existen.
- Cero deuda sin seguimiento (resolver o registrar con resolución asignada);
  código muerto se elimina; módulos >1200 líneas requieren registro D-9.
- Contratos requiere/garantiza en TODA función pública nueva (Manual 2 §12).
- Método de Trabajo Seguro (MTS, `docs/METODO_TRABAJO.md`): el plan de cada ME
  cita el requisito literal del manual (`requisito:`/`texto:`/`implementacion:`/
  `oraculo:`) y TODO archivo de producción modificado lleva un comentario
  `// cumple Manual X §Y` (grep-chequeable). El gate `auditoria/contrastar.py`
  es OBLIGATORIO (fase 4b) antes de integrar cuando hay `docs/plan_ME_<id>.md`.
- Prohibido: `--no-verify`, force-push, saltarte fases del roadmap.
- Si no puedes cumplir algo o hay ambigüedad real: DETENTE Y PREGUNTA al Arquitecto.

## CICLO POR MICRO-ENTREGABLE

1. Plan breve citando Manual X, Sección Y (qué requisito implementa cada cambio).
   Si usas MTS (`docs/METODO_TRABAJO.md`), el plan `docs/plan_ME_<id>.md` usa el
   bloque estricto `requisito:`/`texto:`/`implementacion:`/`oraculo:`.
2. Codifica. Valida mentalmente contra las reglas de sintaxis de Synapse. Cada
   archivo de producción modificado lleva `// cumple Manual X §Y`.
3. Prueba y verifica:
   - `.venv\Scripts\python.exe main.py <archivo.syn>` — compila a `.exe`; ejecútalo.
   - `.venv\Scripts\python.exe -m pytest <ruta-de-tests> -v` — suite afectada + regresión.
   - `.venv\Scripts\python.exe auditoria\verificar_alineacion.py` — 0 brechas, obligatorio.
3b. Gate MTS (fase 4b, obligatorio si hay `docs/plan_ME_<id>.md`):
   `python auditoria/contrastar.py --plan docs/plan_ME_<id>.md` — resuelve
   cualquier brecha antes de integrar.
4. Entrega el REPORTE DE MICRO-ENTREGABLE (formato exacto en GUIA_DE_GOBERNANZA).
5. Commitea (hook automático: limpieza + verificador + gate de lectura + header ABI).
6. Documenta DESPUÉS del commit con el hash real: fila en
   `docs/AUDITORIA_ALINEACION_MANUALES.md` + reporte en `docs/reportes/R<N>.md`
   + actualiza `MEMORIA_PROYECTO.md` (fase en curso, hallazgos con resolución,
   lecciones).

## CONTEXTO OPERATIVO

- Intérprete: `.venv\Scripts\python.exe`. Compilador S1: `python main.py <fuente.syn>`.
- Los builds tardan >30 s: usa timeouts largos y verifica que el exe sea NUEVO
  (timestamp); un exe stale parece éxito y no lo es.
- Revisa `logs/` para patrones de error conocidos antes de depurar desde cero.
- La memoria es tu cuaderno de bitácora: actualízala SIEMPRE al cerrar una
  tarea; no dependas de la ventana de chat.

## INSTRUCCIÓN FINAL

Tu primera acción de esta sesión es el paso 1 de la secuencia de arranque.
Reporta en una línea (fase, ME en curso, tu tarea) antes de proponer
cualquier cambio de código.
