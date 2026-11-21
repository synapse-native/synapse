# MAPA DE ALINEACIÓN — requisito puntual por archivo de producción

Fuente máquina del gate `auditoria/alineacion.py`. Cada archivo de producción
declara **qué sección del manual lo especifica** (sección puntual, no "Manual
7" entero). El gate exige, para el cambio en curso, un **ancla por requisito**
en `docs/alineacion/<ME>.md` con la **cita textual literal** de esa sección.

- Semántica: gana el **patrón más específico** que coincida (fnmatch: más
  caracteres literales, menos comodines). El motor es independiente del orden.
- Un archivo sin entrada aquí cae al mapa legacy
  (`docs/gobernancia/mapa_manuales.md`) para no quedar sin requisito; `--baseline`
  lista los que no están en ninguno.
- Si una sección de este mapa no existe en el manual vigente, el gate lo
  reporta como `mapa desactualizado` y **no** deja pasar el cambio: o se
  corrige el mapa, o el manual perdió una sección que el código necesita.
- Al agregar un área nueva de producción, agregá su entrada aquí.

```json
{
  "opensyn/router.syn": ["Manual 7 §2.4", "Manual 7 §4.2", "Manual 7 §4.3"],
  "opensyn/principal.syn": ["Manual 7 §2.1", "Manual 7 §2.3", "Manual 7 §4.2", "Manual 7 §7.3"],
  "opensyn/herramientas.syn": ["Manual 7 §1.1", "Manual 7 §2.3", "Manual 7 §7.3", "Manual 2 §5.1"],
  "opensyn/installer.syn": ["Manual 7 §2.5", "Manual 9 §5.2", "Manual 9 §5.3", "Manual 9 §5.4"],
  "opensyn/chat.syn": ["Manual 7 §6.2", "Manual 7 §8"],
  "opensyn/validation_loop.syn": ["Manual 7 §6.3"],
  "opensyn/permisos.syn": ["Manual 7 §1.1", "Manual 7 §7.3"],
  "nucleo/ai_orchestrator.h": ["Manual 7 §2.1"],
  "opensyn/generate_runtime_bindings.py": ["Manual 6 §3.1"],
  "opensyn/run_manager.syn": ["Manual 7 §4.3"],
  "opensyn/planificador.syn": ["Manual 7 §2.1"],
  "opensyn/explorer_det.syn": ["Manual 6 §1.1"],
  "opensyn/architect_det.syn": ["Manual 6 §1.1"],
  "opensyn/memoria_persistente_cifrada.syn": ["Manual 6 §1.1"],
  "opensyn/pipeline_multiagente.syn": ["Manual 6 §1.1"],
  "opensyn/verificacion_aot.syn": ["Manual 6 §1.1", "Manual 7 §4.2", "Manual 7 §6.3", "Manual 2 §5.1"],
  "nucleo/grafo_conocimiento.syn": ["Manual 6 §1.1", "Manual 2 §5.1"],
  "nucleo/puente_ffi_lista_mapa.syn": ["Manual 6 §3.1", "Manual 6 §3.2", "Manual 2 §5"],
   "nucleo/lsp.syn": ["Manual 8 §1"],
   "nucleo/lsp_v3.syn": ["Manual 8 §1.1"],
   "nucleo/parser.syn": ["Manual 2 §2"],
   "nucleo/principal.syn": ["Manual 9 §6.2", "Manual 8 §4.2", "Manual 8 §4.1"],
  "nucleo/actualizador.syn": ["Manual 9 §3.1", "Manual 9 §3.2", "Manual 2 §5.1"],
  "nucleo/lexer.syn": ["Manual 2 §1.1", "Manual 2 §1.2", "Manual 2 §3", "Manual 8 §4.1"],
  "nucleo/analizador_semantico.syn": ["Manual 2 §4.2", "Manual 2 §8.1"],
  "nucleo/puente_ast.syn": ["Manual 2 §7"],
  "nucleo/parser_constantes.syn": ["Manual 2 §7"],
  "nucleo/verificador_formal.syn": ["Manual 2 §5"],
  "nucleo/lifetimes.syn": ["Manual 4 §4"],
  "syquex/lexer.syn": ["Manual 3 §1"],
  "syquex/parser.syn": ["Manual 3 §3", "Manual 1 §1.1", "Manual 1 §5.1"],
  "syquex/traductor.syn": ["Manual 6 §1"],
  "runtime/core/memory.c": ["Manual 4 §2"],
  "runtime/core/io.c": ["Manual 5 §2.6"],
  "runtime/core/modelo.c": ["Manual 9 §5.3"],
  "runtime/core/hash_cache.c": ["Manual 9 §5.3"],
  "runtime/core/hash_cache.h": ["Manual 9 §5.3"],
  "runtime/core/cripto.c": ["Manual 9 §5.3"],
  "std/sistema.syn": ["Manual 2 §5.1"],
  "runtime/core/ollama.c": ["Manual 7 §2.2"],
  "runtime/core/tui.c": ["Manual 5 §1"],
  "runtime/core/lsp.c": ["Manual 8 §1"],
  "instaladores/common/auto_actualizar.py": ["Manual 9 §3.2", "Manual 9 §4.1", "Manual 1 §3.1"],
  "instaladores/common/verificar_firma.py": ["Manual 9 §6.3", "Manual 9 §4.1"],
  "instaladores/windows/synapse.iss": ["Manual 9 §2.5", "Manual 9 §6.1"],
  "instaladores/linux/install.sh": ["Manual 9 §2.4", "Manual 9 §6.1"],
  "instaladores/windows/empaquetar_toolchain.py": ["Manual 9 §2.5", "Manual 9 §7"],
  "instaladores/windows/scripts/install.ps1": ["Manual 9 §2.5"],
  "scripts/verificar_release_limpio.py": ["Manual 9 §6.1", "Manual 9 §6.3", "Manual 9 §2.4", "Manual 9 §2.5"],
  "build.py": ["Manual 9 §6.2", "Manual 9 §2.3", "Manual 1 §6"],
  "distribuir.py": ["Manual 9 §6.3", "Manual 9 §2.1", "Manual 9 §6.1"],
  ".github/workflows/release_matrix.yml": ["Manual 9 §4", "Manual 9 §6.1", "Manual 9 §6.2", "Manual 9 §6.3"],
  "vscode-synapse/extension.js": ["Manual 8 §2.3"],
  "vscode-synapse/package.json": ["Manual 8 §2.3"],
  "axon/axon_rt.c": ["Manual 8 §4.3", "Manual 6 §5.1"],
  "axon/axon_rt.h": ["Manual 6 §5.1"],
  "runtime/core/axon.c": ["Manual 8 §4.3", "Manual 6 §5.1", "Manual 9 §5.3"],
  "runtime/core/axon.h": ["Manual 2 §1.2"],
  "runtime/core/concurrency.c": ["Manual 5 §2.1", "Manual 2 §1.2"],
  "runtime/core/debug.c": ["Manual 2 §1.2"],
  "runtime/core/actualizador.c": ["Manual 9 §3.1", "Manual 9 §3.2"],
  "runtime/core/actualizador.h": ["Manual 9 §3.1", "Manual 9 §3.2"],
  "runtime/core/sistema.c": ["Manual 2 §9.1", "Manual 5 §1", "Manual 7 §7.3"],
  "runtime/core/proceso.c": ["Manual 7 §7.3", "Manual 2 §9.1"],
  "runtime/core/proceso.h": ["Manual 7 §7.3"],
  "runtime/core/texto.c": ["Manual 6 §3.1"],
  "runtime/core/texto.h": ["Manual 6 §3.1"],
  "runtime/core/lista.c": ["Manual 6 §3.1"],
  "runtime/core/ast_nodos.h": ["Manual 2 §7.2", "Manual 2 §7.3"],
  "runtime/core/mapa.c": ["Manual 6 §3.1"],
  "compilador/generator/emit_declarations.py": ["Manual 2 §1.3", "Manual 2 §5.1"],
  "compilador/generator/emit_contracts.py": ["Manual 2 §5.1", "Manual 2 §5.3"],
  "std/io.syn": ["Manual 2 §12", "Manual 2 §5.1"],
  "std/json.syn": ["Manual 2 §5.1"],
  "std/os.syn": ["Manual 2 §5.1"],
  "std/sistema.syn": ["Manual 2 §5.1"],
  "std/texto.syn": ["Manual 2 §5.1"],
  "nucleo/coverage.syn": ["Manual 2 §5.1"],
  "nucleo/lint.syn": ["Manual 3 §12", "Manual 2 §5.1", "Manual 6 §3.1", "Manual 9 §6.2"],
  "nucleo/formatter.syn": ["Manual 3 §12", "Manual 2 §5.1", "Manual 6 §3.1"],
  "nucleo/reports.syn": ["Manual 3 §12", "Manual 2 §5.1"],
  "nucleo/parser_base.syn": ["Manual 2 §5.1"],
  "nucleo/generador/expr_eval.syn": ["Manual 6 §3.1", "Manual 2 §5.1"],
  "nucleo/generador/emision_c.syn": ["Manual 2 §5.1"],
  "nucleo/generador/funciones.syn": ["Manual 2 §5.1"],
  "nucleo/generador/monomorfizacion.syn": ["Manual 2 §5.1"],
  "nucleo/generador/nodos_flujo.syn": ["Manual 2 §5.1"],
  "nucleo/generador/orquestador.syn": ["Manual 2 §5.1"],
  "nucleo/generator.syn": ["Manual 2 §8.2"],
  "compilador/generator/emit_expressions.py": ["Manual 2 §12", "Manual 6 §3.1", "Manual 5 §3.6"],
  "compilador/generator/emit_control.py": ["Manual 3 §3", "Manual 1 §6", "Manual 5 §3.6"],
  "compilador/generator/context.py": ["Manual 6 §3.1", "Manual 2 §4.1", "Manual 2 §4.2"],
  "pipeline.py": ["Manual 1 §3.1"],
  "compilador/resolvedor_axon.py": ["Manual 1 §3.1"],
  "compilador/generator/generator.py": ["Manual 2 §5.1"],
  "compilador/generator/emit_tensors.py": ["Manual 2 §4.1"],
  "compilador/parser_declarations.py": ["Manual 2 §2"],
  "std/agent_skills.syn": ["Manual 2 §4.1"],
  "std/atp_engine.syn": ["Manual 2 §4.1"],
  "std/quantum_err_corr.syn": ["Manual 2 §4.1"],
  "std/symbolic_exec.syn": ["Manual 2 §4.1"],
  "compilador/parser_control.py": ["Manual 2 §1.3", "Manual 5 §3.6"],
  "nucleo/parser_sentencias.syn": ["Manual 2 §1.3", "Manual 5 §3.6"],
  "compilador/puente_canonico.py": ["Manual 3 §11.1", "Manual 6 §5.1"],
  "compilador/canonical.py": ["Manual 2 §13"],
  "compilador/ast_nodes.py": ["Manual 5 §3.6"],
  "compilador/semantic_types.py": ["Manual 5 §3.6"],
  "compilador/lexer.py": ["Manual 2 §2", "Manual 8 §4.1"],
  "nucleo/lexer.syn": ["Manual 2 §1.1", "Manual 2 §1.2", "Manual 2 §3", "Manual 8 §4.1"],
  "synapse_rt_types.h": ["Manual 2 §4.1"],
  "syquex/expr.syn": ["Manual 3 §3"],
  "lib/runtime_bindings.syq": ["Manual 6 §3.1"],
  "std/testing.syn": ["Manual 2 §2"]
}
```

## Protocolo del agente (4 pasos)

1. **Leer (antes):** `python auditoria/alineacion.py --leer --me <ME>` —
   imprime las oraciones normativas literales de las secciones exigidas y deja
   el sello de lectura previa.
2. **Expediente:** `python auditoria/alineacion.py --nuevo --me <ME>` y
   completar cada ancla (`cita`, `tipo`, `estado`, `evidencia`, `oraculo`).
3. **Corregir:** lo que la cita del manual no se cumple en el código se
   corrige; si no se puede, se declara `DESVIACION` con `correccion:` (que
   toque el diff) o `decision: D-xxx` ratificada por el Arquitecto.
4. **Verificar (después):** `python auditoria/alineacion.py --verificar --me <ME>`
   — valida citas, anclas, oráculos (se ejecutan en modo release) y escribe
   `auditoria/evidencia/<cambio_hash>.json`.

Detalle del rediseño en `docs/gobernancia/CONTROL_ALINEACION.md`.
