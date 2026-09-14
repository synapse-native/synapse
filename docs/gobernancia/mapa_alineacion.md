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
  "opensyn/router.syn": ["Manual 7 §2.4", "Manual 7 §4.2"],
  "opensyn/principal.syn": ["Manual 7 §2.1", "Manual 7 §4.2"],
  "opensyn/installer.syn": ["Manual 7 §2.5", "Manual 9 §5.2", "Manual 9 §5.3", "Manual 9 §5.4"],
  "opensyn/chat.syn": ["Manual 7 §6.4"],
  "opensyn/validation_loop.syn": ["Manual 7 §6.3"],
  "opensyn/permisos.syn": ["Manual 7 §7.3"],
  "opensyn/run_manager.syn": ["Manual 7 §4.3"],
  "opensyn/planificador.syn": ["Manual 7 §2.1"],
  "nucleo/lsp.syn": ["Manual 8 §1"],
  "nucleo/lsp_v3.syn": ["Manual 8 §1"],
  "nucleo/parser.syn": ["Manual 2 §2"],
  "nucleo/lexer.syn": ["Manual 2 §3"],
  "nucleo/analizador_semantico.syn": ["Manual 2 §8"],
  "nucleo/puente_ast.syn": ["Manual 2 §7"],
  "nucleo/parser_constantes.syn": ["Manual 2 §7"],
  "nucleo/verificador_formal.syn": ["Manual 2 §5"],
  "nucleo/lifetimes.syn": ["Manual 4 §4"],
  "syquex/lexer.syn": ["Manual 3 §1"],
  "syquex/parser.syn": ["Manual 3 §3"],
  "syquex/traductor.syn": ["Manual 6 §1"],
  "runtime/core/memory.c": ["Manual 4 §2"],
  "runtime/core/concurrency.c": ["Manual 5 §2"],
  "runtime/core/ollama.c": ["Manual 7 §2.2"],
  "runtime/core/tui.c": ["Manual 5 §1"],
  "runtime/core/lsp.c": ["Manual 8 §1"],
  "instaladores/windows/synapse.iss": ["Manual 9 §2.5"],
  "nucleo/lint.syn": ["Manual 3 §12"],
  "axon/axon_rt.c": ["Manual 8 §4.3", "Manual 6 §5"],
  "runtime/core/axon.c": ["Manual 8 §4.3", "Manual 6 §5"],
  "runtime/core/sistema.c": ["Manual 2 §9.1", "Manual 5 §1"]
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
