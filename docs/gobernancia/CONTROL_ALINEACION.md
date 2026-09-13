# CONTROL DE ALINEACIÓN — de "registro de lectura" a "prueba de alineación"

> Reemplaza el control declarativo (`auditoria/lecturas.jsonl`) como gate de
> carga. Regla que mecaniza: *los manuales son ley; el código desviado se
> corrige hacia el manual, o la desviación se registra con decisión ratificada.*

## 1. Por qué fallaba el control anterior (diagnóstico)

| Síntoma observado | Causa raíz |
|---|---|
| Agentes que no leían las secciones | El gate solo verificaba un **registro**; el resumen (`--puntos`) pasaba con cualquier frase de ≥60 caracteres |
| Lectura no ligada al cambio | El campo `--archivos` se escribía y **nunca** se verificaba; la cobertura era global por (manual, sección) |
| Gate satisfecho para siempre | El modo CI usaba **todas** las lecturas históricas (478 registros): una sola lectura de Manual 7 §1.1 cubría los 7 archivos `opensyn/*` |
| Desviaciones sin evaluar | `contrastar.py` solo corría si el `plan_ME` estaba *staged*; sin plan, "gate MTS no aplica". `verificacion_ME_*` era opcional |
| Manual desincronizado del código | `docs/**` está exento del gate: el manual podía reescribirse sin revalidar las citas del código (caso real: `MANUAL 7.md` 933→637 líneas dejó 71 citas sin sección) |
| El gate generaba desviaciones | `d64a07e` renombró en masa `// cumple Manual` → `# cumple Manual` "por consistencia": el grep mandaba, no el manual (Manual 2 §1.3) |

## 2. Arquitectura

Tres piezas, un motor (`auditoria/alineacion.py`), dos puertas (pre-commit y CI).

1. **Índice de la ley** — `auditoria/indice_manual.py` → `docs/manuales/.indice.json`
   Secciones + **oraciones normativas** con id estable (`sha1` del texto
   normalizado). Permite citar y detectar cuándo la ley cambia.
2. **Expediente del cambio** — `docs/alineacion/<ME>.md`
   Por archivo de producción, anclas con `manual`, `seccion`, `cita` (textual),
   `tipo`, `estado`, `evidencia` (archivo:línea), `oraculo`.
3. **Evidencia** — `auditoria/evidencia/<cambio_hash>.json`
   Huella del cambio + resultado de los oráculos ejecutados. Es lo que el CI
   exige en HEAD (un commit con `--no-verify` no la tiene → no mergea).

## 3. Flujo de trabajo (antes / después)

```bash
# ANTES de codificar (lectura dirigida, segundos)
python auditoria/alineacion.py --leer --me ME-7 --archivos opensyn/router.syn
#   imprime las oraciones normativas literales de las secciones exigidas
#   y deja el sello .git/alineacion/ME-7.antes.json

# El expediente (una vez por ME)
python auditoria/alineacion.py --nuevo --me ME-7     # scaffold con citas reales
# se completa: cita, tipo, estado, evidencia, oraculo

# DESPUÉS de codificar (bloqueante)
python auditoria/alineacion.py --verificar --me ME-7
python auditoria/alineacion.py --verificar --desde <base> --ci   # gate de servidor
```

El desvío se **corrige o se registra**: `estado: DESVIACION` exige
`correccion:` que toque líneas reales del diff, o `decision: D-xxx` ratificada.

## 4. Qué verifica (y qué agujero cierra)

1. El expediente cubre **exactamente** los archivos de producción del cambio.
2. Cada archivo cubre los requisitos de su sección puntual (`mapa_alineacion.md`,
   patrón más específico gana).
3. **La cita existe literalmente** en esa sección del manual vigente
   (anti-fabricación real: no se puede pasar sin abrir el manual).
4. `CUMPLE` exige el comentario `cumple Manual X §Y` en ±3 líneas de la
   `evidencia` declarada (no hay CUMPLE de palabra).
5. `DESVIACION` sin corrección en el diff ni decisión ratificada **bloquea**.
6. Los oráculos **se ejecutan** (modo release); `SKIP`, `xfail`, "no tests ran"
   y rc≠0 no son evidencia.
7. El `tipo` fija la evidencia mínima: `contrato` → unitario; `comportamiento`
   → oráculo E2E; `seguridad` → aserción negativa; `rendimiento` → umbral.
8. Si el cambio **toca los manuales**, se revalidan todas las citas vivas del
   repo: las de los archivos del cambio deben quedar declaradas.
9. La deuda heredada se congela en `docs/alineacion/DEUDA.md` y no bloquea;
   solo bloquea lo que el cambio toca (**no empeorar**).

## 5. Activación

| Fase | Estado | Cómo |
|---|---|---|
| A | Gate instalado en **warn** (informa, no bloquea) | por defecto en `scripts/githooks/pre-commit` |
| B | Gate **bloqueante local** | `ALINEACION_MODO=block` (y `ALINEACION_ORACULOS=1` para correr oráculos en el hook) |
| C | Gate **bloqueante en CI** | job `alineacion` de `ci-tests.yml` con `--desde <base> --ci` |

## 6. Honestidad de diseño (límites conocidos)

- **El sello de lectura es local** (`.git/alineacion/`): prueba que la lectura
  precedió al código en la máquina del agente. El CI no puede verlo; el CI
  verifica el *resultado* (expediente + evidencia atados a la huella del cambio).
- **No hay juez LLM**: el motor es determinista y auditable (grep-chequeable).
  Verifica que lo afirmado existe en el manual y en el código; no interpreta
  prosa.
- **Una huella por cambio**: el flujo asume un ME = un commit (práctica actual
  del repo). Un PR con varios commits exige el expediente del diff `base...HEAD`.
- Los gates previos (`lecturas.jsonl`, `contrastar.py`) quedan como bitácora y
  no se eliminan: sus tests son inmutables. El gate de carga es este.
