# API de Referencia: AST Canónico (.syn.json) v5.0

**Versión:** 5.0.0
**Fecha:** 26 Julio 2026
**Estado:** LIBERACIÓN — Generado a partir del compilador Synapse v5.0

---

## 1. INTRODUCCIÓN

El **AST Canónico** (`.syn.json`) es la representación intermedia universal del ecosistema Synapse. Es el formato utilizado para:

- **Serialización del compilador** (`main.py` genera `.syn.json`)
- **Migración Python→Synapse** (OpenSyn produce `.syn.json` intermedio)
- **Depuración Time-Travel** (snapshots de AST en trazas)
- **Análisis LSP** (diagnóstico, hover, completado)
- **RAG quirúrgico** (contexto para LLM local)

### 1.1 Formato

```json
{
  "version": "5.0",
  "language": "synapse",
  "ast": {
    "tipo": "Programa",
    "sentencias": [...]
  }
}
```

### 1.2 Versiones

| Versión | Fecha | Cambios |
|---------|-------|---------|
| 5.0 | 2026-07-26 | Compatibilidad con todas las fases M8-M11 |
| 2.0 | 2026-07-24 | Estabilización del formato canónico |
| 1.0 | 2026-07-22 | Versión inicial |

---

## 2. NODOS DEL AST

### 2.1 Programa

Nodo raíz que contiene todas las declaraciones del archivo fuente.

```json
{
  "tipo": "Programa",
  "sentencias": [ ... ]
}
```

**Campos:**
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `tipo` | `string` | `"Programa"` |
| `sentencias` | `array` | Lista de nodos de declaración |

---

### 2.2 DefinicionFuncion

Declaración de una función.

```json
{
  "tipo": "DefinicionFuncion",
  "nombre": "sumar",
  "parametros": [
    {"nombre": "a", "tipo": "entero"},
    {"nombre": "b", "tipo": "entero"}
  ],
  "tipo_retorno": "entero",
  "requiere": [...],
  "garantiza": [...],
  "cuerpo": [...]
}
```

**Campos:**
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `tipo` | `string` | `"DefinicionFuncion"` |
| `nombre` | `string` | Nombre de la función |
| `parametros` | `array` | Lista de parámetros |
| `tipo_retorno` | `string` | Tipo de retorno (vacío si no especificado) |
| `requiere` | `array` | Precondiciones (nodos de expresión) |
| `garantiza` | `array` | Postcondiciones (nodos de expresión) |
| `cuerpo` | `array` | Cuerpo de la función (nodos de sentencia) |

---

### 2.3 DefinicionEstructura

Declaración de una estructura/tipo compuesto.

```json
{
  "tipo": "DefinicionEstructura",
  "nombre": "Punto",
  "campos": [
    {"nombre": "x", "tipo": "decimal"},
    {"nombre": "y", "tipo": "decimal"}
  ]
}
```

**Campos:**
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `tipo` | `string` | `"DefinicionEstructura"` |
| `nombre` | `string` | Nombre de la estructura |
| `campos` | `array` | Lista de campos (`{nombre, tipo}`) |

---

### 2.4 StmtConstante

Declaración de una constante en tiempo de compilación.

```json
{
  "tipo": "StmtConstante",
  "nombre": "PI",
  "tipo": "decimal",
  "valor": { "tipo": "LiteralDecimal", "valor": 3.14159 }
}
```

**Campos:**
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `tipo` | `string` | `"StmtConstante"` |
| `nombre` | `string` | Nombre de la constante |
| `tipo` | `string` | Tipo inferido o explícito |
| `valor` | `object` | Nodo de expresión con el valor |

---

### 2.5 DeclaracionExterna

Declaración de una función externa (C FFI).

```json
{
  "tipo": "DeclaracionExterna",
  "nombre": "printf",
  "parametros": [
    {"nombre": "formato", "tipo": "&texto"}
  ],
  "tipo_retorno": "entero"
}
```

**Campos:**
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `tipo` | `string` | `"DeclaracionExterna"` |
| `nombre` | `string` | Nombre de la función externa |
| `parametros` | `array` | Lista de parámetros |
| `tipo_retorno` | `string` | Tipo de retorno |

---

## 3. SENTENCIAS

### 3.1 SentenciaSi

Condicional if/elif/else.

```json
{
  "tipo": "SentenciaSi",
  "condicion": { "tipo": "OpBinaria", ... },
  "cuerpo": [...],
  "cuerpo_sino": null
}
```

**Campos:**
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `tipo` | `string` | `"SentenciaSi"` |
| `condicion` | `object` | Nodo de expresión de condición |
| `cuerpo` | `array` | Cuerpo del if (lista de nodos) |
| `cuerpo_sino` | `array|null` | Cuerpo del else (null si no hay) |

### 3.2 SentenciaMientras

Bucle while.

```json
{
  "tipo": "SentenciaMientras",
  "condicion": { "tipo": "OpBinaria", ... },
  "cuerpo": [...]
}
```

### 3.3 SentenciaPara

Bucle for.

```json
{
  "tipo": "SentenciaPara",
  "variable": "i",
  "inicio": { "tipo": "LiteralNumero", "valor": 0 },
  "fin": { "tipo": "LiteralNumero", "valor": 10 },
  "cuerpo": [...]
}
```

### 3.4 SentenciaRetornar

Sentencia de retorno.

```json
{
  "tipo": "SentenciaRetornar",
  "expr": { "tipo": "Identificador", "nombre": "resultado" },
  "es_transferencia": false
}
```

**Campos:**
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `tipo` | `string` | `"SentenciaRetornar"` |
| `expr` | `object|null` | Expresión a retornar (null si retorno vacío) |
| `es_transferencia` | `boolean` | Si es transferencia de ownership (`->`) |

### 3.5 SentenciaLanzar

Lanzar un hilo/concurrencia.

```json
{
  "tipo": "SentenciaLanzar",
  "llamada": { "tipo": "LlamadaFuncion", ... }
}
```

### 3.6 SentenciaRecuperar

Try/except (recuperación de errores).

```json
{
  "tipo": "SentenciaRecuperar",
  "accion_critica": [...],
  "plan_b": [...]
}
```

### 3.7 SentenciaEscuchar

Listener/receiver de canal.

```json
{
  "tipo": "SentenciaEscuchar",
  "canal": { "tipo": "Identificador", "nombre": "canal" },
  "respuesta": [...]
}
```

### 3.8 SentenciaRomper

```json
{ "tipo": "SentenciaRomper" }
```

### 3.9 SentenciaSiguiente

```json
{ "tipo": "SentenciaSiguiente" }
```

### 3.10 DeclaracionVariable

```json
{
  "tipo": "DeclaracionVariable",
  "nombre": "x",
  "tipo": "entero",
  "expresion": { "tipo": "LiteralNumero", "valor": 42 }
}
```

### 3.11 AsignacionVariable

```json
{
  "tipo": "AsignacionVariable",
  "nombre": "x",
  "expresion": { "tipo": "OpBinaria", ... }
}
```

### 3.12 NodoCoincidir

```json
{
  "tipo": "NodoCoincidir",
  "expresion": { "tipo": "Identificador", "nombre": "valor" },
  "casos": [
    {
      "tipo": "NodoCaso",
      "patron": "0",
      "tipo_extraido": "",
      "cuerpo": [...]
    },
    {
      "tipo": "NodoCaso",
      "patron": "_",
      "cuerpo": [...]
    }
  ]
}
```

### 3.13 SentenciaImportar

```json
{
  "tipo": "SentenciaImportar",
  "ruta": "std.io"
}
```

### 3.14 BloqueInseguro

```json
{
  "tipo": "BloqueInseguro",
  "cuerpo": [...]
}
```

### 3.15 ImportarC

```json
{
  "tipo": "ImportarC",
  "ruta": "stdio.h",
  "es_sistema": true
}
```

### 3.16 SentenciaEnviarCanal

```json
{
  "tipo": "SentenciaEnviarCanal",
  "canal": { "tipo": "Identificador", "nombre": "canal" },
  "valor": { "tipo": "LiteralNumero", "valor": 42 }
}
```

### 3.17 AsignacionCampo

```json
{
  "tipo": "AsignacionCampo",
  "objeto": { "tipo": "Identificador", "nombre": "p" },
  "nombre_campo": "x",
  "expresion": { "tipo": "LiteralDecimal", "valor": 1.0 }
}
```

---

## 4. EXPRESIONES

### 4.1 Identificador

```json
{
  "tipo": "Identificador",
  "nombre": "variable"
}
```

### 4.2 LiteralNumero

```json
{
  "tipo": "LiteralNumero",
  "valor": 42
}
```

### 4.3 LiteralDecimal

```json
{
  "tipo": "LiteralDecimal",
  "valor": 3.14
}
```

### 4.4 LiteralCadena

```json
{
  "tipo": "LiteralCadena",
  "valor": "Hola, mundo"
}
```

### 4.5 LiteralBooleano

```json
{
  "tipo": "LiteralBooleano",
  "valor": true
}
```

### 4.6 OpBinaria

```json
{
  "tipo": "OpBinaria",
  "izquierdo": { "tipo": "Identificador", "nombre": "a" },
  "operador": "+",
  "derecho": { "tipo": "Identificador", "nombre": "b" }
}
```

**Operadores soportados:** `+`, `-`, `*`, `/`, `%`, `==`, `!=`, `<`, `>`, `<=`, `>=`, `&&`, `||`, `y`, `o`

### 4.7 OpUnaria

```json
{
  "tipo": "OpUnaria",
  "operador": "-",
  "expr": { "tipo": "Identificador", "nombre": "x" }
}
```

**Operadores soportados:** `-`, `!`, `no`

### 4.8 LlamadaFuncion

```json
{
  "tipo": "LlamadaFuncion",
  "nombre": "sumar",
  "argumentos": [
    { "tipo": "LiteralNumero", "valor": 1 },
    { "tipo": "LiteralNumero", "valor": 2 }
  ]
}
```

### 4.9 ExprAccesoCampo

```json
{
  "tipo": "ExprAccesoCampo",
  "objeto": { "tipo": "Identificador", "nombre": "punto" },
  "nombre_campo": "x"
}
```

### 4.10 ExprIndice

```json
{
  "tipo": "ExprIndice",
  "expr": { "tipo": "Identificador", "nombre": "lista" },
  "indice": { "tipo": "LiteralNumero", "valor": 0 }
}
```

### 4.11 ExprTensor

```json
{
  "tipo": "ExprTensor",
  "filas": 3,
  "columnas": 3
}
```

### 4.12 ExprCrearCanal

```json
{
  "tipo": "ExprCrearCanal",
  "tipo_contenido": "entero",
  "capacidad": { "tipo": "LiteralNumero", "valor": 10 }
}
```

### 4.13 ExprRecibirCanal

```json
{
  "tipo": "ExprRecibirCanal",
  "canal": { "tipo": "Identificador", "nombre": "canal" }
}
```

### 4.14 ExprDereferencia

```json
{
  "tipo": "ExprDereferencia",
  "expr": { "tipo": "Identificador", "nombre": "ptr" }
}
```

### 4.15 ExprObtenerDireccion

```json
{
  "tipo": "ExprObtenerDireccion",
  "expr": { "tipo": "Identificador", "nombre": "x" }
}
```

### 4.16 ExprAsm

```json
{
  "tipo": "ExprAsm",
  "instruccion": "mov eax, 1"
}
```

### 4.17 ArgumentoTransferido

```json
{
  "tipo": "ArgumentoTransferido",
  "expr": { "tipo": "Identificador", "nombre": "datos" }
}
```

---

## 5. CONTRATOS (REQUIERE / GARANTIZA)

Las cláusulas `requiere` y `garantiza` se almacenan como listas de nodos de expresión.

```json
{
  "tipo": "DefinicionFuncion",
  "nombre": "dividir",
  "requiere": [
    {
      "tipo": "OpBinaria",
      "izquierdo": { "tipo": "Identificador", "nombre": "b" },
      "operador": "!=",
      "derecho": { "tipo": "LiteralNumero", "valor": 0 }
    }
  ],
  "garantiza": [
    {
      "tipo": "OpBinaria",
      "izquierdo": { "tipo": "Identificador", "nombre": "_resultado_" },
      "operador": ">=",
      "derecho": { "tipo": "LiteralNumero", "valor": 0 }
    }
  ]
}
```

**Variable especial:** `_resultado_` se refiere al valor de retorno en postcondiciones.

---

## 6. TOKENS

Cada token en el flujo de tokens tiene la siguiente estructura:

```json
{
  "tipo": "TokenID",
  "valor": "identificador_o_literal",
  "linea": 10,
  "columna": 5
}
```

### 6.1 Tipos de Token

| Token | Descripción |
|-------|-------------|
| `IF` | `si` |
| `ELSE` | `sino` |
| `FUNCTION` | `funcion` |
| `RETURN` | `retornar` |
| `SPAWN` | `lanzar` |
| `RECOVER` | `recuperar` |
| `LISTEN` | `escuchar` |
| `WHILE` | `mientras` |
| `IMPORT` | `importar` |
| `STRUCT` | `estructura` |
| `BREAK` | `romper` |
| `CONTINUE` | `siguiente` |
| `IDENTIFIER` | Identificador |
| `NUMBER` | Número entero |
| `FLOAT` | Número decimal |
| `STRING` | Cadena de texto |
| `TRUE` / `FALSE` | Booleanos |
| `AND` / `OR` / `NOT` | Operadores lógicos |
| `MATCH` | `coincidir` |
| `REQUIERE` | `requiere` (contrato) |
| `GARANTIZA` | `garantiza` (contrato) |
| `CANAL` | `canal` |
| `CONSTANTE` | `constante` |
| `PARA` | `para` (bucle for) |
| `ASM` | `asm()` |
| `INSEGURO` | `inseguro` (bloque unsafe) |
| `EXTERNO` | `externo` |
| `IMPORTAR_C` | `importar_c` |
| `EOF` | Fin de archivo |

---

## 7. EJEMPLO COMPLETO

**Código Synapse:**
```synapse
#lang: es
importar std.io

estructura Punto:
    x: decimal
    y: decimal

funcion distancia(origen: Punto, destino: Punto) -> decimal:
    requiere:
        origen.x >= 0
    garantiza:
        _resultado_ >= 0
    let dx = destino.x - origen.x
    let dy = destino.y - origen.y
    retornar raiz_cuadrada(dx * dx + dy * dy)
```

**AST Canónico Generado:**
```json
{
  "version": "5.0",
  "language": "synapse",
  "ast": {
    "tipo": "Programa",
    "sentencias": [
      {
        "tipo": "SentenciaImportar",
        "ruta": "std.io"
      },
      {
        "tipo": "DefinicionEstructura",
        "nombre": "Punto",
        "campos": [
          {"nombre": "x", "tipo": "decimal"},
          {"nombre": "y", "tipo": "decimal"}
        ]
      },
      {
        "tipo": "DefinicionFuncion",
        "nombre": "distancia",
        "parametros": [
          {"nombre": "origen", "tipo": "Punto"},
          {"nombre": "destino", "tipo": "Punto"}
        ],
        "tipo_retorno": "decimal",
        "requiere": [
          {
            "tipo": "OpBinaria",
            "izquierdo": {
              "tipo": "ExprAccesoCampo",
              "objeto": {"tipo": "Identificador", "nombre": "origen"},
              "nombre_campo": "x"
            },
            "operador": ">=",
            "derecho": {"tipo": "LiteralNumero", "valor": 0}
          }
        ],
        "garantiza": [
          {
            "tipo": "OpBinaria",
            "izquierdo": {"tipo": "Identificador", "nombre": "_resultado_"},
            "operador": ">=",
            "derecho": {"tipo": "LiteralNumero", "valor": 0}
          }
        ],
        "cuerpo": [
          {
            "tipo": "DeclaracionVariable",
            "nombre": "dx",
            "tipo": "decimal",
            "expresion": {
              "tipo": "OpBinaria",
              "izquierdo": {
                "tipo": "ExprAccesoCampo",
                "objeto": {"tipo": "Identificador", "nombre": "destino"},
                "nombre_campo": "x"
              },
              "operador": "-",
              "derecho": {
                "tipo": "ExprAccesoCampo",
                "objeto": {"tipo": "Identificador", "nombre": "origen"},
                "nombre_campo": "x"
              }
            }
          },
          {
            "tipo": "DeclaracionVariable",
            "nombre": "dy",
            "tipo": "decimal",
            "expresion": {
              "tipo": "OpBinaria",
              "izquierdo": {
                "tipo": "ExprAccesoCampo",
                "objeto": {"tipo": "Identificador", "nombre": "destino"},
                "nombre_campo": "y"
              },
              "operador": "-",
              "derecho": {
                "tipo": "ExprAccesoCampo",
                "objeto": {"tipo": "Identificador", "nombre": "origen"},
                "nombre_campo": "y"
              }
            }
          },
          {
            "tipo": "SentenciaRetornar",
            "expr": {
              "tipo": "LlamadaFuncion",
              "nombre": "raiz_cuadrada",
              "argumentos": [
                {
                  "tipo": "OpBinaria",
                  "izquierdo": {
                    "tipo": "OpBinaria",
                    "izquierdo": {"tipo": "Identificador", "nombre": "dx"},
                    "operador": "*",
                    "derecho": {"tipo": "Identificador", "nombre": "dx"}
                  },
                  "operador": "+",
                  "derecho": {
                    "tipo": "OpBinaria",
                    "izquierdo": {"tipo": "Identificador", "nombre": "dy"},
                    "operador": "*",
                    "derecho": {"tipo": "Identificador", "nombre": "dy"}
                  }
                }
              ]
            },
            "es_transferencia": false
          }
        ]
      }
    ]
  }
}
```

---

## 8. REFERENCIAS

| Documento | Descripción |
|-----------|-------------|
| `compilador/ast_nodes.py` | Definiciones de nodos AST en Python |
| `nucleo/ast_nodes.syn` | Definiciones de nodos AST en Synapse nativo |
| `compilador/canonical.py` | Serialización/deserialización del formato canónico |
| `tests/fixtures/valid/*.syn.json` | Ejemplos de AST canónico |
| `docs/especificacion_opensyn.md` | Especificación de OpenSyn (usa AST canónico) |

---

## 9. HISTORIAL DE CAMBIOS

| Versión | Fecha | Cambios |
|---------|-------|---------|
| 5.0 | 26 Jul 2026 | Referencia completa de todos los nodos del AST canónico con ejemplos. |

---

**Fin de la Referencia del AST Canónico v5.0**
