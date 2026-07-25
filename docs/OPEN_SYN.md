# Especificación Técnica: OpenSyn — Migrador Automático Python → Synapse

**Versión:** 1.0.0  
**Fecha:** 24 Julio 2026  
**Estado:** Especificación Técnica — v3.0 Roadmap  
**Autor:** Arquitecto Principal, Synapse/OpenSyn  
**Versión Base:** Synapse v2.2.2 (núcleo estable)

---

## 1. Visión General

### 1.1 Propósito
OpenSyn es el **migrador automático Python → Synapse** que convierte código Python válido a código Synapse idiomático, seguro y optimizado, eliminando la dependencia de Python en proyectos que migran a Synapse.

### 1.2 Objetivos
- **Migración automática**: `.py` → `.syn` con un solo clic (LSP) o CLI (`synapse migrate archivo.py`)
- **Seguridad por defecto**: Tipado estático obligatorio, ownership único, sin `null`
- **Optimización nativa**: Aprovecha SIMD, canales tipados, contratos lógicos
- **Reversibilidad**: Round-trip `.py` → `.syn` → `.py` (lossless para subconjunto soportado)

### 1.3 Alcance
- **Entrada**: Python 3.10+ (subconjunto tipado: `typing`, type hints obligatorios)
- **Salida**: Synapse v2.2.2+ (`.syn` + `.syn.json` AST canónico)
- **Integración**: LSP `synapse/migrateFile` + CLI `synapse migrate` + Code Action VS Code

---

## 2. Arquitectura del Migrador

```
┌─────────────────────────────────────────────────────────────────┐
│                        OPEN SYN PIPELINE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  INPUT (.py) ──▶ py_parser (ast) ──▶ type_inference ──▶        │
│       │              │                    │                     │
│       ▼              ▼                    ▼                     │
│  .syn.json ◄── ast_mapper ◄── type_inference ◄── mapper        │
│       │                                                           │
│       ▼                                                           │
│   .syn (pretty-print) ──▶ LSP CodeAction / CLI                   │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Módulos Principales

| Módulo | Archivo | Responsabilidad |
|--------|---------|-----------------|
| **py_parser** | `synapse_lsp/open_syn/py_parser.py` | Parseo Python `ast` → AST Universal Canónico (`.syn.json`) |
| **type_inference** | `synapse_lsp/open_syn/type_inference.py` | Inferencia de tipos dinámicos → tipado estricto Synapse |
| **ast_mapper** | `synapse_lsp/open_syn/ast_mapper.py` | Mapeo AST Universal → AST Synapse (`.syn.json`) |
| **pretty_printer** | `synapse_lsp/open_syn/pretty_printer.py` | `.syn.json` → `.syn` (pretty-print con estilo canónico) |
| **lsp_endpoint** | `synapse_lsp/server.py` | Endpoint LSP `synapse/migrateFile` + CodeAction `synapse.migrateFile` |
| **cli_migrate** | `main.py` | CLI `synapse migrate archivo.py` |

---

## 3. Especificación del AST Universal Canónico (`.syn.json`)

### 3.1 Formato Canónico
El AST Universal Canónico (`.syn.json`) es la **representación intermedia única** entre Python y Synapse.

```json
{
  "version": "1.0",
  "language": "synapse",
  "source_language": "python",
  "source_file": "ejemplo.py",
  "ast": {
    "type": "Programa",
    "sentencias": [
      {
        "tipo": "DeclaracionFuncion",
        "nombre": "saludar",
        "parametros": [
          {"nombre": "nombre", "tipo": "texto"}
        ],
        "tipo_retorno": "nulo",
        "cuerpo": [
          {
            "tipo": "Expresion",
            "expresion": {
              "tipo": "LlamadaFuncion",
              "nombre": "escribir_linea",
              "argumentos": [
                {"tipo": "Concatenacion", "izquierda": "Hola, ", "derecha": "nombre"}
              }
            }
          }
        }
      }
    ]
  },
  "metadata": {
    "source_hash": "sha256:...",
    "migration_timestamp": "2026-07-24T10:00:00Z",
    "open_syn_version": "1.0.0"
  }
}
```

### 3.2 Mapeo de Nodos AST (Python → Universal → Synapse)

| Python AST (`ast` module) | Universal Canónico (`.syn.json`) | Synapse AST (`.syn`) |
|---------------------------|----------------------------------|----------------------|
| `ast.Module` | `Programa` | `Programa` |
| `ast.FunctionDef` | `DeclaracionFuncion` | `DeclaracionFuncion` |
| `ast.AsyncFunctionDef` | `DeclaracionFuncion` (async=true) | `DeclaracionFuncion` (async) |
| `ast.ClassDef` | `DefinicionEstructura` | `DefinicionEstructura` |
| `ast.If` | `SentenciaSi` | `SentenciaSi` |
| `ast.While` | `SentenciaMientras` | `SentenciaMientras` |
| `ast.For` | `SentenciaPara` | `SentenciaPara` |
| `ast.Return` | `SentenciaRetornar` | `SentenciaRetornar` |
| `ast.Assign` | `AsignacionVariable` | `AsignacionVariable` |
| `ast.AnnAssign` | `DeclaracionVariable` (con tipo) | `DeclaracionVariable` |
| `ast.AugAssign` | `AsignacionCompuesta` | `AsignacionCompuesta` |
| `ast.Expr` (call) | `LlamadaFuncion` | `LlamadaFuncion` |
| `ast.Call` | `LlamadaFuncion` | `LlamadaFuncion` |
| `ast.BinOp` | `OpBinaria` | `OpBinaria` |
| `ast.UnaryOp` | `OpUnaria` | `OpUnaria` |
| `ast.Compare` | `OpComparacion` | `OpComparacion` |
| `ast.BoolOp` | `OpLogica` | `OpLogica` |
| `ast.Constant` | `Literal*` | `Literal*` |
| `ast.Name` | `Identificador` | `Identificador` |
| `ast.Attribute` | `AccesoCampo` | `AccesoCampo` |
| `ast.Subscript` | `Indice` | `Indice` |
| `ast.List` / `ast.Tuple` | `ExprTensor` | `ExprTensor` |
| `ast.Dict` | `ExprDiccionario` | `ExprDiccionario` |
| `ast.Raise` | `SentenciaLanzar` | `SentenciaLanzar` |
| `ast.Try` | `SentenciaRecuperar` | `SentenciaRecuperar` |
| `ast.With` | `SentenciaEscuchar` (canal) | `SentenciaEscuchar` |
| `ast.Import` / `ast.ImportFrom` | `SentenciaImportar` | `SentenciaImportar` |
| `ast.AsyncWith` | `SentenciaEscuchar` (async) | `SentenciaEscuchar` (async) |
| `ast.Await` | `ExpresionAwait` | `ExpresionAwait` |

---

## 4. Inferencia de Tipos Estrictos (Type Inference)

### 4.1 Reglas de Inferencia

| Python Type Hint | Synapse Type | Notas |
|------------------|--------------|-------|
| `int` | `entero` | `int64_t` |
| `float` | `decimal` | `double` |
| `bool` | `booleano` | `bool` |
| `str` | `texto` | `CadenaSegura` (longitud, no null-terminated) |
| `bytes` | `bytes` | `uint8_t[]` + longitud |
| `None` | `nulo` | `void` |
| `List[T]` | `Canal<T>` / `Lista<T>` | Según uso |
| `Dict[K, V]` | `Diccionario<K, V>` | Hash map nativo |
| `Optional[T]` | `Opcion<T>` | `tag + union` |
| `Union[T, E]` | `Resultado<T, E>` | `tag + union` |
| `Callable[..., R]` | `funcion(...) -> R` | Función de primera clase |
| `Iterable[T]` | `Iterador<T>` | Canales o iteradores |
| `AsyncIterable[T]` | `Canal<T>` | Streaming nativo |
| `Callable[[A, B], R]` | `funcion(A, B) -> R` | Firma completa |

### 4.2 Reglas de Inferencia Estricta

1. **Variables sin anotación** → Error de compilación con sugerencia:
   ```python
   # Python
   x = 42
   # Error OpenSyn:
   # error: Variable 'x' sin anotación de tipo.
   # Sugerencia: x: entero = 42
   ```

2. **Variables con `Any`** → Requiere anotación explícita:
   ```python
   from typing import Any
   x: Any = 42
   # Error OpenSyn:
   # error: Tipo 'Any' no permitido. Use tipo explícito.
   ```

3. **Variables con inferencia exitosa** → Genera declaración con tipo:
   ```python
   # Python
   x: int = 42
   # Synapse
   x: entero = 42
   ```

3. **Funciones sin anotaciones** → Error en firma:
   ```python
   def sumar(a, b):
       return a + b
   # Error OpenSyn:
   # error: Función 'sumar' sin anotaciones de tipo.
   # Sugerencia: funcion sumar(a: entero, b: entero) -> entero:
   ```

### 4.3 Inferencia Contextual (Flow-Sensitive)

```python
# Python
def procesar(items: list[str]) -> int:
    total = 0
    for item in items:
        total += len(item)
    return total

# OpenSyn infiere:
# - items: Lista<texto> (por type hint)
# - total: entero (inicializado a 0, operado con +)
# - item: texto (iteración sobre Lista<texto>)
# - len(item): entero (builtin)
# - total += ...: entero + entero = entero
# - return total: entero (coincide con -> int)
```

---

## 5. Pipeline de Migración (RAG Local)

### 5.1 Contexto Inyectado (RAG Local)

Cuando el LSP recibe `synapse/migrateFile`, inyecta contexto:

```json
{
  "source_file": "modulo.py",
  "ast_universal": {...},
  "rag_context": {
    "imports_resueltos": ["std.io", "std.concurrencia"],
    "tipos_inferidos": {"x": "entero", "items": "Lista<texto>"},
    "contratos_sugeridos": [
      {"funcion": "procesar", "requiere": "items.longitud > 0", "garantiza": "_resultado_ >= 0"}
    ],
    "patrones_optimizacion": ["SIMD vectorizable en bucle for línea 15"]
  }
}
```

### 5.2 Pipeline RAG Quirúrgico (Reutiliza `synapse_rag`)

```
Entrada (.py) ──▶ py_parser ──▶ AST Universal
                              │
                              ▼
                        type_inference ──▶ AST Universal Tipado
                              │
                              ▼
                        ast_mapper ──▶ AST Synapse (.syn.json)
                              │
                              ▼
                        pretty_printer ──▶ Código Synapse (.syn)
                              │
                              ▼
                    LSP CodeAction / CLI Output
```

---

## 6. Endpoint LSP: `synapse/migrateFile`

### 6.1 Request (LSP)

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "synapse/migrateFile",
  "params": {
    "uri": "file:///workspace/modulo.py",
    "options": {
      "infer_types": true,
      "add_contracts": true,
      "optimize_simd": true,
      "output_format": "syn"  // o "syn.json"
    }
  }
}
```

### 6.2 Response (LSP)

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "migrated_code": "#lang: es\nimportar std.io\n\nfuncion saludar(nombre: texto) -> nulo:\n    requiere:\n        nombre.longitud > 0\n    garantiza:\n        _resultado_ == nulo\n    escribir_linea(\"Hola, \" + nombre)\n\nfuncion principal() -> entero:\n    saludar(\"Mundo\")\n    retornar 0\n",
  "ast_json": "{...}",
  "diagnostics": [],
  "warnings": [
    "Variable 'x' en línea 12 inferida como 'entero'. Considere añadir anotación explícita."
  ]
}
```

---

## 7. CLI: `synapse migrate`

### 7.1 Uso

```bash
# Migrar un archivo
synapse migrate modulo.py

# Migrar directorio completo
synapse migrate src/ --output src_syn/

# Con opciones
synapse migrate app.py --output app.syn --add-contracts --optimize-simd
```

### 7.2 Salida

```bash
$ synapse migrate modulo.py
[OpenSyn] Leyendo modulo.py...
[OpenSyn] Parseando AST Python (ast.parse)...
[OpenSyn] Inferencia de tipos: 12 variables, 3 funciones
[OpenSyn] Mapeo AST: 47 nodos → Synapse AST
[OpenSyn] Generando modulo.syn...
✅ Migrado: modulo.py → modulo.syn (47 nodos, 0 errores, 2 warnings)

Warnings:
  - Línea 12: Variable 'x' inferida como 'entero'. Considere anotación explícita.
```

---

## 8. Code Action VS Code: `synapse.migrateFile`

### 8.1 `package.json` Contribution

```json
{
  "contributes": {
    "codeActions": [
      {
        "command": "synapse.migrateFile",
        "title": "Migrar a Synapse",
        "kind": "refactor.rewrite"
      }
    ],
    "menus": {
      "editor/context": [
        {
          "when": "resourceExtname == .py",
          "command": "synapse.migrateFile",
          "group": "refactor"
        }
      ]
    }
  }
}
```

### 8.2 Flujo en VS Code

1. Usuario abre `modulo.py`
2. Click derecho → **Refactorizar → Migrar a Synapse**
3. VS Code muestra **Diff interactivo** (`.py` original ↔ `.syn` generado)
4. Usuario acepta → Se crea `modulo.syn` al lado de `modulo.py`
5. Se registra en `axon.toml` si hay dependencias

---

## 9. Round-Trip: Synapse → Python

### 9.1 Subconjunto Soportado (Lossless)

| Synapse | Python | Notas |
|---------|--------|-------|
| `entero` | `int` | ✅ |
| `decimal` | `float` | ✅ |
| `booleano` | `bool` | ✅ |
| `texto` | `str` | ✅ |
| `Resultado<T, E>` | `Union[T, E]` | ✅ (requires `typing.Union`) |
| `Opcion<T>` | `Optional[T]` | ✅ |
| `Canal<T>` | `asyncio.Queue[T]` | Aproximado |
| `funcion` | `def` / `async def` | ✅ |
| `estructura` | `dataclass` / `class` | ✅ |
| `canal<T>` | `asyncio.Queue` | Parcial |
| `lanzar` / `escuchar` | `asyncio.create_task` / `await queue.get()` | Parcial |

### 9.2 Limitaciones Conocidas

| Synapse Feature | Python Equivalent | Estado |
|-----------------|-------------------|--------|
| `requiere`/`garantiza` | `assert` + decoradores | Parcial (runtime only) |
| `inseguro` / punteros | `ctypes` / `memoryview` | No soportado |
| `asm()` | `ctypes` / inline assembly | No soportado |
| `std.simd` | `numpy` / `numba` | Aproximado |
| Contratos en tiempo de compilación | `pydantic` / `beartype` | Parcial (runtime) |

---

## 10. Configuración (`axon.toml` / `open_syn.toml`)

```toml
[open_syn]
# Inferencia de tipos
strict_mode = true           # Requiere anotaciones en todo
infer_loops = true           # Infiere tipos en bucles
infer_loops = true           # Infiere tipos en bucles
infer_calls = true           # Infiere tipos en llamadas

# Contratos
add_contracts = true         # Genera requiere/garantiza básicos
infer_preconditions = true   # Infiere precondiciones de uso
infer_postconditions = true  # Infiere postcondiciones de retorno

# Optimizaciones
optimize_simd = true         # Detecta bucles vectorizables
dead_code_elimination = true # Elimina código muerto detectado

# Salida
output_format = "syn"        # "syn" | "syn.json" | "both"
preserve_comments = true     # Preserva comentarios Python
format_style = "canonical"   # Estilo canónico Synapse
```

---

## 11. Tests de Validación (E2E)

| Test | Descripción | Estado |
|------|-------------|--------|
| `test_migrate_simple.py` | `def f(x: int) -> int: return x + 1` | 🚀 Planificado |
| `test_migrate_typing.py` | `Optional`, `Union`, `List`, `Dict` | 🚀 Planificado |
| `test_migrate_classes.py` | `dataclass`, herencia, métodos | 🚀 Planificado |
| `test_migrate_async.py` | `async def`, `await`, `asyncio` | 🚀 Planificado |
| `test_migrate_generics.py` | `TypeVar`, `Generic[T]` | 🚀 Planificado |
| `test_migrate_contracts.py` | `requiere`/`garantiza` inferidos | 🚀 Planificado |
| `test_roundtrip.py` | `.py` → `.syn` → `.py` (subconjunto) | 🚀 Planificado |
| `test_migrate_performance.py` | Benchmark 1000 archivos | 🚀 Planificado |
| `test_lsp_migrate.py` | LSP `synapse/migrateFile` + CodeAction | 🚀 Planificado |

---

## 12. Estructura de Archivos del Proyecto

```
synapse_lsp/
├── open_syn/
│   ├── __init__.py
│   ├── py_parser.py          # ast.parse → AST Universal
│   ├── type_inference.py     # Inferencia tipos estricta
│   ├── ast_mapper.py         # Universal AST → Synapse AST
│   ├── pretty_printer.py     # .syn.json → .syn (pretty)
│   ├── config.py             # Config open_syn.toml
│   └── validators.py         # Validación round-trip
├── server.py                 # LSP server + endpoints
├── llm_bridge.py             # (existente) Ollama bridge
└── open_syn.py               # Entry point: migrate_file()

compilador/
├── open_syn/
│   ├── py_parser.py          # (shared) o wrapper
│   ├── type_inference.py     # (shared)
│   ├── ast_mapper.py         # (shared)
│   └── cli_migrate.py        # CLI entry point

main.py                       # Entry point: `synapse migrate` command
```

---

## 13. Criterios de Aceptación (Definition of Done)

| Criterio | Métrica | Objetivo |
|----------|---------|----------|
| **Cobertura AST** | % nodos Python mapeados | ≥ 95% (core Python) |
| **Inferencia tipos** | % variables inferidas sin anotación | ≥ 90% |
| **Contratos generados** | % funciones con `requiere`/`garantiza` | ≥ 80% |
| **Round-trip fidelity** | `.py` → `.syn` → `.py` semánticamente equivalente | ≥ 95% (subconjunto) |
| **Tiempo migración** | 1000 archivos | < 30 segundos |
| **LSP latency** | `synapse/migrateFile` latency | < 500ms |
| **Tests E2E** | Suite completa | 100% pass |

---

## 14. Dependencias y Riesgos

| Dependencia | Versión | Riesgo | Mitigación |
|-------------|---------|--------|------------|
| `ast` (stdlib) | 3.10+ | Bajo | Stdlib estable |
| `typing` (stdlib) | 3.10+ | Bajo | Stdlib estable |
| `synapse_lsp` (interno) | v2.2.2+ | Medio | Tests E2E |
| `tweetnacl` (Ed25519) | 20200518 | Bajo | Dominio público |
| `toml` (stdlib 3.11+) | 3.11+ | Medio | Fallback `tomli` |

---

## 15. Referencias

- [Documento Maestro de Ingeniería](./DOCUMENTO_MAESTRO_DE_INGENIERIA.md)
- [Especificación Arquitectónica v2.2.2](./ARCH_ESPECIFICACION.md)
- [LSP Nativo v2.2.2](./LSP_NATIVO.md)
- [Especificación Axon v2.2.2](./AXON_SPEC.md)
- [Manual Lenguaje v2.2.2](./MANUAL_LENGUAJE.md)
- [AST Canónico `.syn.json`](../tests/fixtures/valid/*.syn.json)
- [Python `ast` module docs](https://docs.python.org/3/library/ast.html)

---

## 16. Historial de Cambios

| Versión | Fecha | Autor | Cambios |
|---------|-------|-------|---------|
| 1.0.0 | 24 Jul 2026 | Arquitecto Principal | Especificación inicial v3.0 Roadmap M2 |

---

**Fin de la Especificación Técnica OpenSyn v1.0.0**  
*Documento vivo — actualizar con cada iteración de implementación*