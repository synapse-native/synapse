# Synapse: Especificación Arquitectónica del Compilador v2.2.0

> **Documento:** `ARCH_ESPECIFICACION.md`
> **Versión:** 2.2.0 — PRODUCTION-READY
> **Última actualización:** 24 Julio 2026

---

## 1. Visión General del Pipeline

El compilador de Synapse opera en **5 etapas estrictamente lineales**. Ninguna etapa puede omitirse. Cada etapa recibe la salida de la anterior y produce la entrada de la siguiente.

```
                    ┌─────────────┐
  fuente.syn ──────▶│   LEXER     │───▶ tokens[]
                    └─────────────┘
                           │
                    ┌──────▼────────┐
                    │    PARSER     │───▶ AST (linked-list)
                    └───────────────┘
                           │
                    ┌──────▼────────────┐
                    │  ANALIZADOR SEM.  │───▶ SemNodo[] + tabla símbolos
                    └───────────────────┘
                           │
                    ┌──────▼──────────┐
                    │  GENERADOR C    │───▶ código C (synapse_unity.c)
                    └─────────────────┘
                           │
                    ┌──────▼──────┐
                    │  GCC/CLANG  │───▶ binario .exe / ELF
                    └─────────────┘
```

### 1.1 Pipeline Nativa (auto-hospedada)

La pipeline nativa se implementa en `nucleo/principal.syn` como `generar_etapa()`:

1. **`tokenizar()`** — `nucleo/lexer.syn`: fuente → tokens con IDs `T_*`
2. **`parsear()`** — `nucleo/parser.syn`: tokens → AST linked-list (`Nodo*`)
3. **`_f8_flatten()`** — Aplana linked-list a `SemNodo[]` (flat array)
4. **`analizar()`** — `nucleo/analizador_semantico.syn`: validación semántica
5. **`generar()`** — `nucleo/generator.syn`: AST validado → código C
6. **`system("gcc ...")`** — compilación C a binario nativo

### 1.2 Pipeline Python (referencia)

La pipeline Python (`main.py + compilador/`) se usa como referencia para bootstrap:

```
python main.py -o salida.exe nucleo/principal.syn
  → lexer.py → parser.py → analizador_semantico.py → generator.py → GCC
```

### 1.3 Modularización v2.2.0 (Fases A-F)

En v2.2.0, el punto de entrada monolítico `main.py` (656 líneas) fue desacoplado en submódulos limpios:

- **`main.py`** (10 líneas): Lanzador minimalista que delega a `cli.py`
- **`cli.py`** (110 líneas): Manejo de argumentos con `argparse` y ruteo de comandos
- **`pipeline.py`** (317 líneas): Orquestación del pipeline de compilación

Esta modularización mejora la mantenibilidad y separa responsabilidades:
- CLI: Argumentos, comandos (`construir`, LSP), flags (`--tokens`, `--dump-ast`)
- Pipeline: Lectura, análisis léxico, parseo, análisis semántico, generación C, compilación nativa

---

## 2. Árbol de Sintaxis Abstracta (AST)

### 2.1 Nodos del AST

El AST se define en `nucleo/ast_nodes.syn` como una unión discriminada (`Nodo`) con
un campo `tipo` entero (constantes `NODO_*`).

```c
// Tipos de nodo (constantes compartidas entre parser.syn, generator.syn y analizador.syn)
enum {
    NODO_PROGRAMA        = 1,
    NODO_FUNCION         = 2,
    NODO_SI              = 3,
    NODO_MIENTRAS        = 4,
    NODO_RETORNAR        = 5,
    NODO_ASIGNACION      = 6,
    NODO_EXPRESION       = 7,
    NODO_LLAMADA         = 8,
    NODO_IDENTIFICADOR   = 9,
    NODO_LITERAL_NUMERO  = 10,
    NODO_LITERAL_CADENA  = 11,
    NODO_OPERACION       = 12,
    NODO_ESTRUCTURA      = 13,
    NODO_CAMPO           = 14,
    NODO_IMPORTAR        = 15,
    NODO_LANZAR          = 16,
    NODO_RECUPERAR       = 17,
    NODO_ESCUCHAR        = 18,
    NODO_EXTERNO         = 19,
    NODO_CONSTANTE       = 20,
    NODO_ASM             = 21,
    NODO_CANAL           = 22,
    NODO_CONTRATO        = 46,
    NODO_PARA            = 45,
    // ...
};
```

### 2.2 AST Aplanado (SemNodo[])

Para el análisis semántico, el AST linked-list se aplana a un array `SemNodo[]`:

```c
#define F8_MAX_NODOS 65536
#define F8_MAX_SYMS  16384

typedef struct {
    int tipo_nodo;              // NODO_FUNCION, NODO_SI, etc.
    int linea, columna;
    union {
        struct { /* función */ char nombre[64]; int num_params; };
        struct { /* si */       Nodo* condicion; };
        struct { /* asignación */ char var_nombre[64]; };
        // ...
    };
} SemNodo;
```

### 2.3 Unity Build (Multi-archivo)

La pipeline nativa compila 6 archivos `.syn` en un solo binario:

```
tokens.syn → lexer.syn → parser.syn → analizador_semantico.syn → generator.syn → principal.syn
```

Cada archivo produce un AST que se fusiona en `_merged` (linked-list global)
antes de F8 + analizar + generar.

---

## 3. Lexer (`nucleo/lexer.syn`)

### 3.1 Especificación Léxica

- **Codificación:** UTF-8 estricto
- **Indentación:** Off-side rule (inyección de tokens INDENT/DEDENT)
- **Tabuladores:** Prohibidos (error léxico fatal)
- **Comentarios:** `//` línea, `/* */` bloque
- **Directiva obligatoria:** `#lang: es` (o `en`, `fr`, `pt`) en primera línea

### 3.2 Tokens Principales

| Token ID | Categoría | Ejemplos |
|----------|-----------|----------|
| `T_FIN` (0) | EOF | — |
| `T_IDENTIFICADOR` (1) | Nombres | `foo`, `bar`, `mi_variable` |
| `T_NUMERO` (2) | Enteros | `42`, `0`, `-1` |
| `T_DECIMAL` (3) | Flotantes | `3.14`, `-0.5` |
| `T_CADENA` (4) | Strings | `"hola"`, `"ruta\\n"` |
| `T_FUNCION` (5) | Keywords | `funcion` / `function` |
| `T_RETORNAR` (6) | Keywords | `retornar` / `return` |
| `T_SI` (7) | Keywords | `si` / `if` |
| `T_MIENTRAS` (8) | Keywords | `mientras` / `while` |
| ... | ... | ... |
| `T_CANAL` (52) | Keywords | `canal` / `channel` |
| `T_ASM` (53) | Inline | `asm` |

---

## 4. Parser (`nucleo/parser.syn`)

- **Algoritmo:** Descenso recursivo puro
- **Sensible a indentación:** usa tokens INDENT/DEDENT del lexer
- **Contratos:** `requiere`/`garantiza` → almacenados como `NODO_CONTRATO`
- **Canales:** `canal<T>(cap)`, `<-` (enviar), `->` (recibir), `lanzar`/`escuchar`

### 4.1 Métodos de Parseo Clave

| Función | Propósito |
|---------|-----------|
| `parsear_programa()` | Punto de entrada: sentencias raíz |
| `parsear_funcion()` | Firma + parámetros + contratos + cuerpo |
| `parsear_bloque()` | Cuerpo indentado (INDENT...DEDENT) |
| `parsear_sentencia()` | Enrutador por tipo de sentencia |
| `parsear_expresion()` | Recursivo por precedencia (lógicos → relacionales → aritméticos → unarios) |
| `parsear_crear_canal()` | `canal<T>(capacidad)` |
| `parsear_enviar_canal()` | `canal <- valor` |
| `parsear_recibir_canal()` | `canal ->` |

---

## 5. Analizador Semántico (`nucleo/analizador_semantico.syn`)

### 5.1 Fases de Análisis

```c
void analizar(AnalizadorSemanticoEst* est) {
    // Fase 1: Registrar estructuras globales
    for (int i = 0; i < est->total_nodos; i++)
        if (est->nodos[i].tipo_nodo == NODO_ESTRUCTURA)
            _sem_registrar_struct(est, &est->nodos[i]);

    // Fase 2: Registrar funciones y sus parámetros
    for (int i = 0; i < est->total_nodos; i++)
        if (est->nodos[i].tipo_nodo == NODO_FUNCION)
            _sem_registrar_funcion(est, &est->nodos[i]);

    // Fase 3: Analizar cuerpos de función (scopes locales)
    for (int i = 0; i < est->total_nodos; i++)
        if (est->nodos[i].tipo_nodo == NODO_FUNCION)
            _sem_analizar_cuerpo(est, &est->nodos[i]);
}
```

### 5.2 Validaciones Principales

| Validación | Código de Error | Descripción |
|-----------|-----------------|-------------|
| Variable no declarada | `ERR_SEM_VAR_NO_DECLARADA` | Uso de ID sin declaración previa |
| Tipo incompatible | `ERR_SEM_TIPO_INCOMPATIBLE` | Operación entre tipos incompatibles |
| Función no definida | `ERR_SEM_FUNC_NO_DEFINIDA` | Llamada a función sin definición |
| Redefinición | `ERR_SEM_REDEFINICION` | Misma variable/función en mismo scope |
| Uso después de move | `ERR_SEM_USE_AFTER_MOVE` | Variable transferida usada de nuevo |

---

## 6. Generador C (`nucleo/generator.syn`)

### 6.1 Generación de Código

El generador traduce nodos AST validados a C estándar (C11/C17).

| Nodo AST | C generado |
|----------|-----------|
| `NODO_FUNCION` | `int nombre(Tipo param) { ... }` |
| `NODO_SI` | `if (cond) { ... } else { ... }` |
| `NODO_MIENTRAS` | `while (cond) { ... }` |
| `NODO_ASIGNACION` | `Tipo var = expr;` |
| `NODO_LLAMADA` | `funcion(args)` |
| `NODO_CONTRATO` | `assert(precond); ... assert(postcond);` |
| `NODO_CANAL` | `canal_crear(sizeof(T), cap)` |
| `NODO_ASM` | `asm("...")` (escapado para C) |
| `NODO_LANZAR` | `synapse_lanzar_hilo(funcion, args)` |

### 6.2 Escape de Cadenas

Los bloques `asm()` requieren escape doble para C:

```c
// Synapse:   asm("printf(\"Hola\\n\");")
// C emitido: asm("printf(\"Hola\\n\");");
//            ↘ mediante gen_escribir_cadena_escapada()
```

### 6.3 Struct Constructores

Tipos definidos por el usuario (structs) se inicializan con `{0}`:

```c
// Synapse:   p = Punto{x: 1, y: 2}
// C emitido: struct Punto p = {1, 2};
```

---

## 7. Runtime Nativo (`synapse_rt.c` + `axon_rt.c`)

### 7.1 Componentes del Runtime

| Componente | Archivo | Tamaño | Propósito |
|-----------|---------|--------|-----------|
| Runtime base | `synapse_rt.c` | 98KB .o | Canales, SIMD, red, JSON, TOML, SHA-256, GGUF |
| Axon | `axon_rt.c` | 133KB .o | HTTP download, TAR, Ed25519, SemVer, axon.lock, TOML parser |
| Criptografía | `tweetnacl.c` | 35KB .o | Ed25519 firmas digitales |

### 7.2 Gestión de Memoria

- **Sin GC:** Ownership único con RAII
- **MemoryWatchdog:** `SYNAPSE_DEBUG_MEM` activa contadores de alloc/free
- **Canal buffers:** Ring buffer protegido por mutex + condition variables

---

## 8. Compilación Multiplataforma

### 8.1 Detección de Compilador

```python
if sys.platform == "darwin":
    compiler = "clang"
    platform_flags = "-Wl,-dead_strip"
else:
    compiler = "gcc"
    platform_flags = "-fno-ident -Wl,--gc-sections"
    if sys.platform == "win32":
        platform_flags += " -Wl,--no-insert-timestamp -Wl,--stack,8388608"
    else:
        platform_flags += " -Wl,--stack,8388608"
```

### 8.2 Flags de Enlace

| Plataforma | Flags |
|-----------|-------|
| Windows | `-lpthread -lm -lws2_32` |
| Linux | `-lpthread -lm` |
| macOS | `-lpthread -lm` |

---

## 9. Sistema de Importación

### 9.1 Sysroot (`std.*`)

```python
importar std.io          → std/io.syn
importar std.concurrencia → std/concurrencia.syn o std/concurrencia/principal.syn
```

### 9.2 Axon (paquetes externos)

```python
importar mi-lib          → axon_modules/mi-lib/principal.syn
```

### 9.3 Unity Build Deduplication

El compilador elimina definiciones duplicadas cuando múltiples módulos
comparten el mismo tipo o función (por nombre).

---

## 10. Fuzzing y Seguridad

### 10.1 Fuzzing Destructivo (F11)

Motor de fuzzing con 7 estrategias de generación:

| Estrategia | Peso | Descripción |
|-----------|------|-------------|
| Sintaxis válida | 10% | Programas Synapse válidos mínimos |
| Semi-válido | 20% | Con errores comunes |
| Aleatorio | 25% | Caracteres imprimibles + control |
| Cadenas malformadas | 20% | Comillas sin cerrar, keywords sueltos |
| Indentación rota | 10% | 3/5/7 espacios |
| Unicode corrupto | 10% | Zero-width, BOM, combining accents |
| Binario simulado | 5% | Bytes crudos no UTF-8 |

**Resultados:** 500+ iteraciones, 0 crashes, 0 errores no controlados.

### 10.2 Concurrencia (F10)

- **10,000 hilos simultáneos** (5,000 productores + 5,000 consumidores)
- **0 deadlocks, 0 data races, 0 bytes perdidos** (MemoryWatchdog)
- **Throughput:** ~8,083 msg/seg en canal de capacidad 1,000

---

## 11. Estados de Compilación

| Componente | Archivos | Estado |
|-----------|----------|--------|
| Lexer Python | `compilador/lexer.py` | ✅ Estable |
| Parser Python | `compilador/parser.py` | ✅ Estable |
| Generador Python | `compilador/generator/` | ✅ Estable |
| Lexer nativo | `nucleo/lexer.syn` | ✅ Funcional |
| Parser nativo | `nucleo/parser.syn` | ✅ Funcional |
| Analizador semántico nativo | `nucleo/analizador_semantico.syn` | ✅ Funcional |
| Generador nativo | `nucleo/generator.syn` | ✅ Funcional |
| Pipeline nativa | `nucleo/principal.syn` | ✅ Funcional |
| LSP nativo | `nucleo/lsp.syn` | ✅ 5/5 tests |
| Runtime C | `synapse_rt.c` | ✅ 0 errores GCC |
| Axon | `axon_rt.c` | ✅ 19/19 E2E |
| Criptografía | `tweetnacl.c` | ✅ Ed25519 |
| Tests totales | — | ✅ 283 passed, 2 skipped |
