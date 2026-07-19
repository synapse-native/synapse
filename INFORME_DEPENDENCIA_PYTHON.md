# INFORME DE DEPENDENCIA PYTHON — Synapse Compiler v2.0

## Resumen Ejecutivo

**Cero dependencias externas (no estándar).** Todo el compilador (`compilador/` + `main.py`) se sostiene exclusivamente sobre la biblioteca estándar de Python y módulos propios del proyecto. Esto hace que el bootstrapping sea inmediatamente viable.

---

## 1. MAPEO DE IMPORTS

### 1.1 Dependencias Internas (propias del proyecto)

| Módulo Importado | Dónde se usa | Archivos fuente |
|---|---|---|
| `exceptions` | `main.py`, `lexer.py` | `exceptions.py` |
| `compilador.ast_nodes` | Todos los módulos del compilador + `main.py` | `compilador/ast_nodes.py` |
| `compilador.lexer` | `main.py`, `parser.py` | `compilador/lexer.py` |
| `compilador.parser` | `main.py` | `compilador/parser.py` |
| `compilador.generator` | `main.py`, `analizador_semantico.py` | `compilador/generator.py` |
| `compilador.diagnostics` | `main.py`, `parser.py`, `analizador_semantico.py` | `compilador/diagnostics.py` |
| `compilador.analizador_semantico` | `main.py` | `compilador/analizador_semantico.py` |
| `compilador.resolvedor_axon` | `main.py` | `compilador/resolvedor_axon.py` |
| `compilador.symbol_table` | `analizador_semantico.py` | `compilador/symbol_table.py` |

### 1.2 Dependencias Estándar de Python

| Módulo Std | Dónde se importa | Líneas |
|---|---|---|
| `os` | `main.py:1`, `resolvedor_axon.py:1` | E/S archivos, manipulación de rutas |
| `sys` | `main.py:2`, `diagnostics.py:2` | Salida estándar, salida del proceso |
| `json` | `main.py:3` | Serialización canónica del AST |
| `argparse` | `main.py:4` | CLI del compilador |
| `typing` (List, Optional, Dict, Tuple, Any, Set) | `main.py`, `ast_nodes.py`, `lexer.py`, `parser.py`, `diagnostics.py`, `generator.py`, `analizador_semantico.py`, `symbol_table.py`, `resolvedor_axon.py` | Anotaciones de tipos (sintáctico, no pesa en runtime) |
| `enum` (Enum, auto) | `ast_nodes.py`, `diagnostics.py`, `symbol_table.py` | Enumeraciones (`TokenID`, `ErrorCodes`, `Propiedad`) |
| `dataclasses` (dataclass, field) | `ast_nodes.py`, `symbol_table.py` | AST nodes y símbolos |
| `re` | `analizador_semantico.py:316` | Pattern matching en `NodoCoincidir` |

### 1.3 Dependencias Externas (no estándar)

**Ninguna.** No hay imports a librerías de terceros en `compilador/` ni en `main.py`.

---

## 2. EVALUACIÓN DE IMPACTO

| Módulo Std | Función | Impacto | Dificultad de reemplazo |
|---|---|---|---|
| `os` | Rutas de archivos, `os.path.exists`, `os.path.join`, `os.path.normpath` | **Bajo** — reemplazable con llamadas al sistema operativo desde C (GetFileAttributes, PathCombine) o con una biblioteca Synapse `std.fs` |
| `sys` | `sys.stderr`, `sys.exit` | **Bajo** — `fprintf(stderr, ...)` y `exit()` en C son equivalentes directos |
| `json` | AST canónico ↔ dict de Python (`json.dumps` / `json.loads`) | **Medio** — requiere un serializador/parser JSON en Synapse o C. Alternativa: formato canónico binario (CBOR/flatbuffers). Ya existe un plan de migración a canónico nativo. |
| `argparse` | CLI (`--tokens`, `--lang`, `--lsp`, `--dump-ast`, `construir`) | **Medio** — parsing manual de `argv` en C es tedioso pero trivial. Ya hay entry point nativo (`axon_build.exe`). |
| `typing` | Anotaciones de tipos | **Despreciable** — solo decorativo en Python. En Synapse/C no aplica. Cero esfuerzo de migración. |
| `enum` | Enumeraciones `TokenID`, `ErrorCodes`, `Propiedad` | **Bajo** — reemplazable por `#define` o `enum` en C. Directo. |
| `dataclasses` | Definiciones de AST (`@dataclass`) | **Bajo** — reemplazable por `struct` en C. Cada nodo AST se traduce directamente a una struct de C. |
| `re` | `re.match()` en `NodoCoincidir` | **Bajo** — patrón simple `(\w+)\((\w+)\)`. Reemplazable por escaneo manual de caracteres. |

### Evaluación por módulo del compilador

| Módulo | Dependencias Std | Dependencias Internas | Criticidad para auto-hospedaje |
|---|---|---|---|
| `ast_nodes.py` | `enum`, `dataclasses`, `typing` | Ninguna | **Raíz del AST.** Debe migrarse primero. |
| `symbol_table.py` | `dataclasses`, `enum`, `typing` | `ast_nodes` | Baja — tabla de símbolos simple. |
| `lexer.py` | `typing` | `ast_nodes`, `exceptions` | **Crítico** — entrada del pipeline. Sin dependencias externas. |
| `diagnostics.py` | `sys`, `enum`, `typing` | `ast_nodes` | **Crítico** — reporte de errores. `sys.stderr` fácil de reemplazar. |
| `parser.py` | `typing` | `ast_nodes`, `lexer`, `diagnostics` | **Crítico** — corazón sintáctico. Sin dependencias externas. |
| `generator.py` | `typing` | `ast_nodes` | **Crítico** — generación de código C. Sin dependencias externas. |
| `analizador_semantico.py` | `typing`, `re` | `ast_nodes`, `diagnostics`, `symbol_table`, `generator` | **Crítico** — análisis semántico. `re` es mínimo. |
| `resolvedor_axon.py` | `os`, `typing` | Ninguna | **Bajo** — gestor de dependencias. `os` fácil de reemplazar. |
| `main.py` | `os`, `sys`, `json`, `argparse`, `typing` | Todos los anteriores | **Orquestador.** `json` y `argparse` son los dos únicos módulos con reemplazo no trivial. |

---

## 3. PROPUESTA DE MIGRACIÓN (Orden de Reescritura a C/Synapse)

### Fase A — Núcleo sin dependencias externas (se puede auto-compilar inmediatamente)

| Orden | Módulo | Justificación |
|---|---|---|
| 1 | `exceptions.py` → `SynapseError` como struct/typedef en C | Dependencia de `lexer` y `main`. Mínimo esfuerzo. |
| 2 | `ast_nodes.py` → structs en C (equivalente a las ya generadas) | Base de todo el AST. Ya existe en el generador C. |
| 3 | `symbol_table.py` → struct + funciones en C | Depende solo de `ast_nodes`. Sencillo. |
| 4 | `lexer.py` → Synapse/C | Sin dependencias externas. Ya existe un `tokenizar()` C generado. |
| 5 | `diagnostics.py` → Synapse/C | `sys.stderr` → `fprintf`. `enum` → `#define`/`enum`. |
| 6 | `parser.py` → Synapse/C | Sin dependencias externas. Ya existe `parsear()` C generado. |
| 7 | `generator.py` → Synapse/C | Ya genera C. Meta-circular: la versión Synapse se compila a C. |
| 8 | `analizador_semantico.py` → Synapse/C | `re` se reemplaza con búsqueda manual de subcadenas. |
| 9 | `resolvedor_axon.py` → Synapse/C | `os.path` → `stat`/`GetFileAttributes`. |

### Fase B — Dependencias estándar con reemplazo nativo

| Orden | Módulo | Justificación |
|---|---|---|
| 10 | `main.py` → `principal.syn` | Orquestador. Requiere que todos los módulos previos estén listos. `argparse` se reemplaza por parseo manual de `_argc`/`_argv` (builtins ya existentes). |
| 11 | Reemplazo de `json` | Formato canónico. Pendiente de implementar serializador/deserializador en Synapse o C. Alternativa inmediata: invocar minijson desde C. |

### Fase C — Auto-hospedaje completo

| Paso | Acción |
|---|---|
| 12 | Compilar el compilador escrito en Synapse usando el compilador actual (Python) |
| 13 | Usar el binario resultante para compilar el compilador escrito en Synapse a sí mismo (bootstrap) |
| 14 | Descartar el compilador Python — el compilador Synapse se auto-compila |

---

## Conclusión

El compilador ya tiene **cero dependencias externas Python**. Los únicos módulos estándar que requiere un reemplazo no trivial son `json` (serialización canónica) y `argparse` (CLI). Ambos tienen alternativas viables: el entry point `axon_build.exe` ya salta `argparse`, y el formato canónico puede emitirse directamente como structs en C sin pasar por JSON.
