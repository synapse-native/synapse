// Documento informativo; la ley es docs/manuales/
# EVALUACIÓN DE AVANCE — 2026-11-08

> Informe de evaluación del avance, no un reporte de ME. Base:
> `release/v8.1.0-industrial`, HEAD `d58c059`. No se modificó código de
> producción para producirlo. Los porcentajes son estimaciones de rúbrica, no
> una métrica absoluta; la evidencia que los sostiene está en la sección 5.

## 1. Resumen ejecutivo

| Lente | Estimación | Lectura |
|---|---:|---|
| Ecosistema Synapse (compilador + runtime + distribución + OpenSyn + madurez) | **~61%** | Núcleo fuerte; producto agéntico a medio construir. |
| OpenSyn como producto (TUI + loop + modelo + tools + integración) | **~42%** | Funciona para chat/lectura; no para edición autónoma. |
| Paridad agéntica con opencode/Codebuff | **~27%** | Le faltan las capacidades que definen a un agente de coding. |

Diferenciadores reales: inferencia local sin telemetría, bucle de validación
con el compilador real, distribución firmada con `synapse update`, instalador y
perfil de hardware. La brecha no es de "ciencia": es de integración, tools de
escritura/ejecución y calidad de los módulos de Fase 32.

## 2. Rúbrica usada

Se definió "industrial" como: un usuario externo puede usarlo sin asistencia
del equipo, con tests que prueban comportamiento (no solo texto fuente),
integración real en el binario, documentación y distribución reproducible.

| Capa | Peso | Nota | Aporte |
|---|---:|---:|---:|
| Compilador + runtime + stdlib | 30% | 85% | 25.5 |
| Distribución/instalación/update/firma/CI | 10% | 80% | 8.0 |
| Gobernanza, pruebas, documentación | 10% | 90% | 9.0 |
| OpenSyn (TUI + loop + tools + modelo) | 25% | 42% | 10.5 |
| Integración LSP/IDE/CLI y ecosistema | 10% | 20% | 2.0 |
| Madurez industrial (uso real, rendimiento, multiplataforma) | 15% | 40% | 6.0 |
| **Total ponderado** | **100%** |  | **61.0%** |

## 3. OpenSyn frente a opencode/Codebuff

| Capacidad | OpenSyn | opencode/Codebuff |
|---|---|---|
| Leer/explorar repositorio | Sí (`TOOL listar`, `TOOL leer`, `TOOL git`) | Sí (`read/grep/glob`) |
| Editar/escribir/aplicar patch | **No** | Sí |
| Ejecutar shell/tests/build con aprobación | **No** | Sí |
| Bucle autónomo editar → compilar → corregir | Parcial, solo sobre código generado (`std.oraculo`) | Sí |
| Índice semántico/AST en el loop vivo | **No integrado** | Sí |
| LSP: diagnósticos y acciones IA | **No** (`aiExplain/aiComplete/aiFix/aiStatus` en TDD) | Sí |
| Multi-proveedor/cloud | No (local-only, decisión de producto) | Sí |
| Sesiones/reanudar/undo/share | Parcial (historial/fork; `run_manager` no compila) | Sí |
| Subagentes/paralelo | Archivo existe, **no compila** | Sí |
| MCP/plugins | No (fuera de alcance Fase 32) | Sí |
| Permisos/sandbox | Sí, razonable | Sí, más maduro |
| TUI | Sí, funcional | Sí, más pulida |
| Instalación/update firmado | Sí, reciente y probado | Sí |
| Privacidad local + validación con compilador | **Diferenciador** | No equivalente |

## 4. Qué está realmente terminado

- `synapse update` nativo (R203): descarga, SHA-256, firma Ed25519, backup,
  instalación y fallo cerrado. 10 tests del oráculo + 33 de regresión.
- Distribución firmada (R202): release con `.sig`, `.sha256`, SBOM y SLSA.
- Actualizador Python fail-closed (R201) y `OpenSyn doctor` (R200).
- Instalación limpia de OpenSyn con `llama-server` (R199), probada con
  instalador Inno real.
- Motor GGUF local: E2E sintético determinista verde (carga, vocab real,
  ingesta, generación y cierre limpio).
- Núcleo del compilador y bootstrap S1→S2 con gates de determinismo.

## 5. Evidencia de la brecha

### 5.1 Tests de OpenSyn

Barrido de `tests/opensyn`, bindings/transpiler, modos, integración y pipeline
RAG: **414 passed, 6 skipped** (420 recolectados).

Los 6 skips no son cosméticos:

- `tests/integration/test_ai_commands_opensyn.py`: `synapse/aiExplain`,
  `aiComplete`, `aiFix`, `aiStatus` marcados "no implementado aún (TDD)".
- `tests/opensyn/test_inference.py`: benchmark de latencia requiere
  `llama-server` en `:8088` (no disponible en el árbol de desarrollo).

### 5.2 Módulos avanzados que no compilan

Verificado con `python main.py <archivo> --check --no-emit`:

| Archivo | Resultado |
|---|---|
| `opensyn/principal.syn` | OK |
| `opensyn/permisos.syn` | OK |
| `nucleo/grafo_conocimiento.syn` | 135 errores |
| `opensyn/validation_loop.syn` | 3 errores semánticos |
| `opensyn/explorer_det.syn` | 31 errores |
| `opensyn/architect_det.syn` | 61 errores |
| `opensyn/pipeline_multiagente.syn` | error léxico de indentación |
| `opensyn/memoria_persistente_cifrada.syn` | cadena sin cerrar |
| `opensyn/verificacion_aot.syn` | 131 errores |
| `opensyn/run_manager.syn` | tipo `texto` vs `int` |
| `opensyn/router.syn` | 27 errores |

Además, `pipeline_multiagente.syn` importa `opensyn.grafo_conocimiento`, que
**no existe**; el grafo real está en `nucleo/grafo_conocimiento.syn` y tampoco
compila. Muchos tests de Fase 32 son inspección de texto fuente, por lo que un
"verde" no prueba comportamiento.

### 5.3 Ejecutor de herramientas

`opensyn/principal.syn:1054` solo implementa `listar`, `leer` y
`git status|log`. La tabla de modos anuncia `plan`, `editar` y `compilar`
(`opensyn/principal.syn:883`), pero no hay rama de ejecución para ellos. La
matriz de permisos marca `editar` como `ASK` (`opensyn/permisos.syn:66`), pero
al no existir la herramienta, la confirmación nunca se usa.

### 5.4 Integración CLI y runtime

- `synapse opensyn <subcomando>` (Manual 8 §4.1) no está despachado por el
  binario nativo; existe un `opensyn.exe` separado.
- `opensyn doctor` falla en este árbol: `[FAIL] llama-server.exe no
  encontrado` en `dist/opensyn/ia`. El modelo GGUF sí está
  (`deepseek-coder-1.3b-Q4_K_M.gguf`, 873 MB) y la configuración está en modo
  oráculo.
- No hay puertos `11434` (Ollama) ni `8088` (llama-server) activos, así que el
  E2E de chat real no es verificable en esta máquina. El E2E GGUF sintético sí
  pasa.

## 6. Distancia y prioridades

Para que OpenSyn sea usable en tareas reales de coding faltan, en orden:

1. **Tools de escritura**: `escribir`, `editar`, `aplicar_patch` y `ejecutar`
   (shell/tests/build) con confirmación y sandbox.
2. **Reparar e integrar Fase 32**: hacer compilar `grafo_conocimiento`,
   `validation_loop`, `pipeline_multiagente`, `run_manager` y los detectores;
   corregir el import del grafo; cablearlos en `principal.syn`; agregar un gate
   de compilación para todo `.syn` de producción.
3. **LSP IA**: implementar `aiExplain/Complete/Fix/Status` y quitar los skips.
4. **Sesiones/UX**: reanudar, undo/revert y `synapse opensyn` como subcomando.
5. **Calidad**: E2E con `llama-server` real, benchmark de latencia y tests de
   comportamiento en lugar de inspección de fuentes.

La recomendación es 1 + 2 antes que LSP o multiagente: sin edición y shell,
OpenSyn no puede competir con opencode aunque el resto esté perfecto; sin
reparar Fase 32, el 42% está inflado por código que no compila.

## 7. Limitaciones del informe

- Los porcentajes son una estimación ponderada; cambiar los pesos cambia el
  número. La evidencia y la lista de brechas son verificables.
- No se ejecutó un benchmark contra opencode/Codebuff; la comparación es de
  capacidades, no de latencia ni calidad de código.
- No se validó el chat con un modelo real por falta de `llama-server` en el
  árbol de desarrollo.
- Algunos tests de Fase 32 son de inspección de fuente; se contaron como
  "existentes", no como "funcionales".

*Fin del informe de evaluación — 2026-11-08.*
