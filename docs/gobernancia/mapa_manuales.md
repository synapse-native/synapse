# MAPA DE MANUALES — lectura obligatoria por área de código

Regla 1 de gobernanza: antes de codificar, leer la sección del manual que
especifica el trabajo. Este mapa define QUÉ secciones exige el gate mecánico
(`auditoria/registrar_lectura.py --verificar`, invocado por el pre-commit).

## Protocolo del agente (obligatorio)

1. Identifica los archivos de producción que vas a tocar.
2. Ejecuta `python auditoria/registrar_lectura.py --pendientes` para listar
   las secciones exigidas por el mapa.
3. LEE esas secciones y registra la lectura ANTES de entregar:

   ```
   python auditoria/registrar_lectura.py --registrar ^
     --archivos "syquex/traductor.syn,syquex/parser.syn" ^
     --cita "Manual 6 §1.3; Manual 3 §11.2" ^
     --puntos "resumen de 3-6 requisitos extraídos de la sección"
   ```

4. El hook de pre-commit bloquea el commit si hay archivos productivos
   modificados sin lectura registrada EL MISMO DÍA, o si la cita citada no
   existe realmente en `docs/manuales/`.

## Método de Trabajo Seguro (MTS) — `docs/METODO_TRABAJO.md`

El MTS es el mecanismo anti-olvido que garantiza que lo leído en el manual se
aplica en el código. Está integrado en el arranque de `AGENTS.md` (FUENTES DE
VERDAD #5, REGLAS DURAS y fase 4b del CICLO) y en el gate de auditoría.

- **Plan:** `docs/plan_ME_<id>.md` con un bloque por requisito:
  `requisito:` / `texto:` / `implementacion:` / `oraculo:` (ruta al test).
- **Código:** TODO archivo de producción modificado debe llevar un comentario
  grep-chequeable anclado a la construcción real, p. ej.
  `// cumple Manual 8 §1.2: leer Content-Length y validar tope máximo`.
- **Gate (fase 4b, obligatorio si el commit incluye un `docs/plan_ME_*.md`):**
  el pre-commit ejecuta `python auditoria/contrastar.py --plan <plan>` y
  bloquea si: (1) algún `requisito:` carece de `oraculo:` existente; (2) algún
  archivo de producción *staged* no contiene `cumple Manual X §Y`; (3)
  `verificar_alineacion.py` reporta brechas; (4) falta `CUMPLE`/`NO CUMPLE` en
  `docs/verificacion_ME_<id>.md`.

El mapeo de abajo ya exige la sección del manual a leer por área de producción
(p. ej. `*.c`/`*.h`/`*.py` → `Manual 1`); el comentario `cumple Manual X §Y`
debe citar esa misma sección para satisfacer el gate MTS.

## Formato del mapa

El bloque JSON de abajo es la fuente máquina (la parsea el registrador).
Semántica: **primera entrada cuyo patrón coincida gana** (fnmatch; orden =
específico primero, genérico al final). Las citas admiten varias secciones
separadas por coma/espacio (`Manual 3 §11.1 §11.2`). Una cita sin `§N`
(obligación de leer el manual completo) es válida pero solo para áreas sin
sección única clara — preferir siempre la sección puntual.

Al incorporar un área nueva de producción, AÑADE su entrada aquí; el gate
fallará con instrucción explícita si un archivo modificado no está mapeado.

```json
{
  "syquex/traductor.syn": ["Manual 6 §1.3", "Manual 3 §11"],
  "syquex/parser.syn": ["Manual 3 §3"],
  "syquex/expr.syn": ["Manual 3 §3"],
  "syquex/lexer.syn": ["Manual 3 §1", "Manual 3 §4"],
  "syquex/analizador_alcance.syq": ["Manual 3 §5", "Manual 4"],
  "syquex/*": ["Manual 3"],
  "nucleo/lsp.syn": ["Manual 8 §1"],
  "nucleo/ast_abi.syn": ["Manual 6 §1"],
  "nucleo/parser_constantes.syn": ["Manual 2 §7"],
  "nucleo/puente_ast.syn": ["Manual 2 §7"],
  "nucleo/nodos_flujo.syn": ["Manual 2 §2"],
  "nucleo/lifetimes.syn": ["Manual 4 §4"],
  "nucleo/verificador_formal.syn": ["Manual 2 §12"],
  "nucleo/lexer.syn": ["Manual 2 §3"],
  "nucleo/lexer_keywords.syn": ["Manual 2 §3"],
  "nucleo/parser.syn": ["Manual 2 §2"],
  "nucleo/analizador_semantico.syn": ["Manual 2 §8", "Manual 2 §10"],
  "nucleo/generador/*": ["Manual 2"],
  "nucleo/llvm_backend.syn": ["Manual 1"],
  "nucleo/wasm_backend.syn": ["Manual 1"],
  "runtime/core/debug.c": ["Manual 9 §1"],
  "runtime/core/quantum_runtime.h": ["Manual 9 §6"],
  "runtime/core/memory.c": ["Manual 4"],
  "runtime/core/concurrency.c": ["Manual 5"],
  "runtime/core/axon.c": ["Manual 6 §5"],
  "runtime/core/cache.c": ["Manual 5 §11"],
  "runtime/*": ["Manual 5"],
  "axon/*": ["Manual 6 §5"],
  "std/cluster*": ["Manual 5 §6"],
  "std/ai*": ["Manual 7"],
  "std/quantum*": ["Manual 9 §6"],
  "std/*": ["Manual 2"],
  "lib/*": ["Manual 3 §12"],
  "opensyn/*": ["Manual 7"],
  "compilador/*": ["Manual 1"],
  "librerias/*": ["Manual 1"],
  "nucleo/*": ["Manual 2"],
  "test_*.syn": ["Manual 1 §3.1"],
  "*.c": ["Manual 1"],
  "*.h": ["Manual 1"],
  "*.py": ["Manual 1"]
}
```

## Exclusiones (sin exigencia de lectura)

Tests (`tests/**`), documentación (`docs/**`, `*.md` raíz), auditoría,
scripts de soporte (`scripts/**`, `auditoria/**`), fixtures, benchmarks,
ejemplos y artefactos de IDE. Además, **cualquier archivo cuyo nombre empiece
con `_`** se considera artefacto/instrumentación temporal (convención regla
12: harnesses `_tmp_*`, probes) y queda exento. La razón: la lectura
obligatoria protege el CÓDIGO DE PRODUCCIÓN contra desviaciones de
especificación; los tests son derivados del comportamiento especificado (y su
modificación ya está gobernada por la regla 5 con aprobación del Arquitecto).
