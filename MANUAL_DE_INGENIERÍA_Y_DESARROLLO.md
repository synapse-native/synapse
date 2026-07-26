# MANUAL DE INGENIERÍA Y DESARROLLO DE SYNAPSE (v5.0) — UNIFICADO

**Documento Oficial de Arquitectura, Especificación de Compilador e Implementación**  
*Clasificación: Ingeniería / Uso Interno — Núcleo de Desarrollo*  
*Versión: 5.0 — Unificación de Especificaciones (Base a Revolución Cognitiva)*  

---

## ÍNDICE

1. [Introducción y Alcance de la Ingeniería](#1-introducción-y-alcance-de-la-ingeniería)  
2. [Estructura del Repositorio y Workspace Layout](#2-estructura-del-repositorio-y-workspace-layout)  
3. [Especificación Léxica](#3-especificación-léxica-lexersyn)  
4. [Especificación Sintáctica y Parser](#4-especificación-sintáctica-y-parser-parsersyn)  
5. [El AST Canónico](#5-el-ast-canónico-ast_nodessyn)  
6. [Analizador Semántico y Sistema de Tipos](#6-analizador-semántico-y-sistema-de-tipos-analizador_semanticosyn)  
7. [El Pacto: Seguridad de Memoria](#7-el-pacto-seguridad-de-memoria-ownership--borrowing)  
8. [Concurrencia Aislada y Diseño por Contrato](#8-concurrencia-aislada-y-diseño-por-contrato)  
9. [Generador de Código C y Optimizaciones](#9-generador-de-código-c-y-optimizaciones-generatorsyn)  
10. [Compilación Incremental y Caché Determinista](#10-compilación-incremental-y-caché-determinista)  
11. [Depuración Asistida por IA (Time-Travel Debugging)](#11-depuración-asistida-por-ia-time-travel-debugging)  
12. [Grafos de Dependencias y Análisis de Impacto](#12-grafos-de-dependencias-y-análisis-de-impacto)  
13. [Sandbox de Ejecución para IA](#13-sandbox-de-ejecución-para-ia)  
14. [Axon Hub Descentralizado](#14-axon-hub-descentralizado)  
15. [Ecosistema de IA Local y LSP — Arquitectura Desacoplada](#15-ecosistema-de-ia-local-y-lsp--arquitectura-desacoplada)  
16. [Gestor de Paquetes Inmutable (Axon)](#16-gestor-de-paquetes-inmutable-axon)  
17. [Especificación de la Biblioteca Estándar](#17-especificación-de-la-biblioteca-estándar-std)  
18. [Pruebas, Fuzzing y Aseguramiento de Calidad](#18-pruebas-fuzzing-y-aseguramiento-de-calidad)  
19. [Proceso de Bootstrap y Auto-Hospedaje](#19-proceso-de-bootstrap-y-auto-hospedaje-self-hosting)  
20. [Guías de Contribución y Reglas de Ingeniería](#20-guías-de-contribución-y-reglas-de-ingeniería)  
21. [Arquitectura del Toolchain y CLI](#21-arquitectura-del-toolchain-y-cli-synapse-cli)  
22. [Interoperabilidad y FFI](#22-interoperabilidad-y-ffi-foreign-function-interface)  
23. [Taxonomía de Errores del Compilador](#23-taxonomía-de-errores-del-compilador)  
24. [Seguridad — Vectores de Ataque y Mitigaciones](#24-seguridad--vectores-de-ataque-y-mitigaciones)  
25. [Anexos: Diagramas, Checklists y Casos de Prueba](#25-anexos-diagramas-checklists-y-casos-de-prueba)  
26. [Firma y Certificación Técnica](#26-firma-y-certificación-técnica)

---

## 1. INTRODUCCIÓN Y ALCANCE DE LA INGENIERÍA

Este manual constituye la especificación técnica fundamental para el diseño, desarrollo, mantenimiento y evolución del ecosistema **Synapse**. Su propósito es servir como referencia inequívoca para cualquier ingeniero que se incorpore al proyecto, estableciendo las estructuras de datos, los algoritmos de compilación, las reglas semánticas y los protocolos de integración del runtime, abarcando desde el núcleo base hasta las capacidades cognitivas de la versión 5.0.

### 1.1. Principios Rectores ("El Pacto")

El desarrollo de Synapse no tolera ambigüedades. Cada módulo está subordinado a los siguientes principios innegociables:

| Principio | Descripción |
| :--- | :--- |
| **Tipado Estricto Inferido** | Variables con tipo deducido en tiempo de compilación, sin ambigüedades. |
| **Zero-GC** | Gestión de memoria determinista sin recolector de basura (Ownership & Borrowing). |
| **Tipado Algebraico de Errores** | `Resultado<T,E>` y `Opcion<T>` con coincidencia exhaustiva obligatoria. |
| **Rendimiento Nativo** | Compilación a C nativo con backend GCC/Clang y optimización agresiva. |
| **Soberanía del Usuario** | Cero telemetría, cero conexiones en red ocultas, ejecución local y privada. |
| **Compilación Incremental** | Caché determinista para tiempos de compilación 10-50x más rápidos. |
| **Depuración Asistida por IA** | Análisis de trazas con OpenSyn para explicar errores (Time-Travel). |
| **Sandbox para IA** | Ejecución segura de código generado con recursos limitados. |
| **Cadena de Suministro Descentralizada** | Axon Hub con verificación distribuida y firmas múltiples. |

### 1.2. Filosofía de Evolución

Synapse evoluciona mediante una estrategia de tres fases complementarias, todas ellas consolidadas en el presente manual:

- **Fase M (Adopción Masiva):** Romper la fricción de entrada, garantizar la cadena de suministro y demostrar superioridad de rendimiento frente a CPython.
- **Fase v4.0 (Supremacía de Ingeniería):** Superar los límites de rendimiento de GCC, descentralizar la ejecución en red y alcanzar verificación matemática formal en subconjuntos seguros.
- **Fase v5.0 (Revolución Cognitiva):** Compilación incremental, depuración con IA, sandbox para IA, grafos de dependencias y Axon Hub descentralizado.

---

## 2. ESTRUCTURA DEL REPOSITORIO Y WORKSPACE LAYOUT

El repositorio está organizado de forma modular para desacoplar el compilador autocontenido, el runtime, el gestor de paquetes, el demonio LSP y el servicio de IA (OpenSyn).

```text
/synapse
│
├── .github/                      # Pipelines de CI/CD (Matriz multi-arquitectura y firmas Ed25519)
│
├── nucleo/                       # Código fuente del compilador
│   ├── lexer.syn                 # Tokenizador e inyector de indentación
│   ├── parser.syn                # Parser de descenso recursivo puro
│   ├── analizador_semantico.syn  # Motor de tipado y verificación de Ownership (3 pasadas)
│   ├── generator.syn             # Emisor de código C optimizado (-O2, PGO, LTO)
│   ├── generator_pgo.syn         # Emisión con instrumentación PGO
│   ├── verificador_formal.syn    # Módulo --safe para subconjunto verificable
│   ├── wasm_backend.syn          # Generador de código para WebAssembly
│   ├── cache.syn                 # Sistema de caché para compilación incremental
│   ├── grafo_dependencias.syn    # Análisis de dependencias e impacto
│   └── sandbox.c                 # Sandbox de ejecución con seccomp y límites
│
├── opensyn/                      # Servicio de IA desacoplado
│   ├── orchestrator.c            # Gestor de ciclo de vida del motor de inferencia
│   ├── llama_client.c            # Cliente HTTP nativo para llama.cpp
│   ├── rag_pipeline.c            # Pipeline RAG quirúrgico
│   ├── synapse_embeddings.c      # Generación local de embeddings
│   ├── router.syn                # Enrutador determinista basado en AST
│   ├── trace_analyzer.syn        # Análisis de trazas para depuración asistida por IA
│   ├── router_config.yaml        # Configuración de reglas de enrutamiento
│   └── sandbox_config.yaml       # Configuración del sandbox
│
├── std/                          # Biblioteca estándar
│   ├── net.syn                   # std::net (HTTP / TCP nativo)
│   ├── json.syn                  # std::json (Serialización acelerada por SIMD)
│   ├── concurrencia.syn          # std::concurrencia (Canales tipados Canal<T>)
│   ├── cluster.syn               # std::cluster (Canales remotos distribuidos)
│   ├── telemetry.syn             # std::telemetry (Logs estructurados y OpenTelemetry)
│   ├── debug.syn                 # std::debug (Depuración con Time-Travel y IA)
│   └── sandbox.syn               # std::sandbox (Interfaz para ejecución aislada)
│
├── axon/                         # Gestor de paquetes
│   ├── axon_rt.c                 # Runtime de Axon (Verificación Ed25519, manejo TAR)
│   ├── axon_hub.c                # Cliente para el registro descentralizado de paquetes
│   ├── axon_ipfs.c               # Integración con IPFS para almacenamiento descentralizado
│   └── axon.toml                 # Especificación de metadatos de paquetes
│
├── bridge/                       # Puentes de interoperabilidad empresarial
│   ├── python_bridge/            # Generador de módulos nativos para Python
│   ├── java_bridge/              # Bindings JNI para Java
│   └── typescript_bindings/      # Generador automático de .d.ts para TypeScript
│
├── lsp/                          # Demonio del Protocolo de Servidor de Lenguaje
│   ├── synapse_lsp.syn           # Implementación nativa del LSP (JSON-RPC 2.0 sobre stdio)
│   └── lsp_handlers.syn          # Manejo de diagnósticos, autocompletado y refactorización
│
├── vscode-synapse/               # Extensión oficial para VS Code
│   └── src/                      # Interfaz TypeScript para el demonio synapse_lsp
│
├── tests/                        # Suite de pruebas
│   ├── unit/                     # 350+ pruebas unitarias
│   ├── integration/              # 30+ pruebas de integración end-to-end
│   ├── fuzzing/                  # 1000+ entradas sintácticamente corruptas
│   │   ├── fuzz_engine.py
│   │   └── fuzz_cases.json
│   ├── security/                 # Pruebas de seguridad específicas
│   ├── benchmarks/               # Pruebas comparativas abiertas vs Python/Java/C++
│   └── sandbox/                  # Pruebas del sandbox de ejecución
│
├── docs/                         # Documentación técnica
│   └── manual_ingenieria_v5.0.md # Este documento
│
└── cache/                        # Directorio de caché de compilación (~/.synapse/cache/)
    └── (archivos .cache generados automáticamente)
```

---

## 3. ESPECIFICACIÓN LÉXICA (`lexer.syn`)

El analizador léxico transforma el flujo de caracteres de un archivo `.syn` en un flujo estructurado de tokens, controlando estrictamente la indentación por bloques y validando la cabecera del idioma.

### 3.1. Requisitos de Cabecera y Codificación

Todo archivo fuente válido **debe** comenzar obligatoriamente en la línea 1 con la directiva de idioma:

```synapse
#lang: es
```

Cualquier archivo que omita esta directiva es rechazado de inmediato con el código de error `ERR_LEX_MISSING_LANG`.

### 3.2. Gestión de Indentación (Control de Bloques)

Synapse prohíbe el uso de llaves `{ }` para delimitar bloques. El alcance sintáctico se determina mediante un sistema de pila de indentación (`IndentStack`):

1. Se contabilizan exclusivamente los espacios al inicio de línea (múltiplos estrictos de 4 espacios). Los tabuladores (`\t`) están prohibidos y generan `ERR_LEX_TAB_DETECTED`.
2. Si el nivel de indentación actual es mayor que el nivel en la cima de la pila, se emite `T_INDENT` y se hace `push`.
3. Si el nivel es menor, se emiten tantos `T_DEDENT` como cierres de bloque sean necesarios.

### 3.3. Tabla de Tokens Canónicos

| Token | Descripción | Ejemplo |
| :--- | :--- | :--- |
| `T_LANG_DIRECTIVE` | Directiva de idioma | `#lang:` |
| `T_IDENT` | Identificadores | `variable`, `miFuncion` |
| `T_KEYWORD` | Palabras reservadas | `let`, `fn`, `coincidir`, `ok`, `err`, `lanzar` |
| `T_COLON` | Apertura obligatoria de bloque | `:` |
| `T_INDENT` | Inicio de bloque indentado | (4 espacios) |
| `T_DEDENT` | Fin de bloque | (retroceso de indentación) |
| `T_NEWLINE` | Fin de línea significativo | `\n` |

---

## 4. ESPECIFICACIÓN SINTÁCTICA Y PARSER (`parser.syn`)

El parser implementa un algoritmo de **descenso recursivo puro** sin retroceso, optimizado para garantizar un tiempo de compilación lineal $\mathcal{O}(n)$.

### 4.1. Gramática Formal (EBNF)

```ebnf
Programa       ::= LangDirective { Declaracion }
LangDirective  ::= "#lang:" Identificador Newline

Declaracion    ::= FuncionDef | EstructuraDef | ConstDef | TipoDef | ExportDef

ExportDef      ::= "@export(" TipoExport ")" FuncionDef | EstructuraDef
TipoExport     ::= "python" | "java" | "typescript" | "wasm"

FuncionDef     ::= "fn" Identificador "(" [ Parametros ] ")" [ "->" Tipo ]
                   [ Contratos ] ":" Newline Indent Bloque Dedent

Contratos      ::= [ "requiere" Expr ] [ "garantiza" Expr ]
                  | "puro"                           (* Función pura verificable *)

Parametros     ::= Identificador ":" Tipo { "," Identificador ":" Tipo }

Bloque         ::= { Sentencia Newline }

Sentencia      ::= Asignacion | Retorno | Condicional | Coincidencia
                  | LanzarHilo | Expresion | DebugTrace

DebugTrace     ::= "trace" Expresion

Coincidencia   ::= "coincidir" Expresion ":" Newline
                   Indent { PatronCaso } Dedent

PatronCaso     ::= Patron "=>" ( Sentencia | Newline Indent Bloque Dedent )

EstructuraDef  ::= "estructura" Identificador [ "<" ParametrosTipo ">" ] ":" Newline Indent
                   { Campo } Dedent

TipoDef        ::= "tipo" Identificador "=" TipoAlgebraico

TipoAlgebraico ::= "Resultado" "<" Tipo "," Tipo ">"
                  | "Opcion" "<" Tipo ">"
                  | "enum" "{" { Identificador [ "(" Tipo ")" ] } "}"
```

### 4.2. Prevención de Ambigüedades

El parser evalúa expresiones mediante funciones de precedencia escalonadas:

| Nivel | Operadores | Asociatividad |
| :--- | :--- | :--- |
| 1 | Asignación | Derecha |
| 2 | `||` | Izquierda |
| 3 | `&&` | Izquierda |
| 4 | `==`, `!=` | Izquierda |
| 5 | `<`, `>`, `<=`, `>=` | Izquierda |
| 6 | `+`, `-` | Izquierda |
| 7 | `*`, `/`, `%` | Izquierda |
| 8 | `!`, `-` (unario) | Derecha |
| 9 | `()` (llamada), `.` (acceso) | Izquierda |

---

## 5. EL AST CANÓNICO (`ast_nodes.syn`)

El Árbol de Sintaxis Abstracta se serializa internamente en estructuras fuertemente tipadas, convertibles a formato `.syn.json` para herramientas de migración y análisis estático.

### 5.1. Definición de Nodos Fundamentales

```synapse
tipo NodoTipo = enum {
    NODO_PROGRAMA,
    NODO_FUNCION,
    NODO_FUNCION_PURA,        (* Verificable formalmente --safe *)
    NODO_ASIGNACION,
    NODO_COINCIDENCIA,
    NODO_ESTRUCTURA,
    NODO_TIPO_ALGEBRAICO,
    NODO_BUCLE,
    NODO_CONDICIONAL,
    NODO_RETORNO,
    NODO_LLAMADA,
    NODO_VARIABLE,
    NODO_LITERAL_ENTERO,
    NODO_LITERAL_FLOTANTE,
    NODO_LITERAL_STRING,
    NODO_LITERAL_BOOLEANO,
    NODO_OPERACION_BINARIA,
    NODO_OPERACION_UNARIA,
    NODO_TRACE,               (* Nodo de depuración: trace expr *)
    NODO_LLAMADA_WASM,        (* Marcador para compilación a WebAssembly *)
    NODO_EXPORTACION_PYTHON,  (* Marcador para generación de bindings Python *)
    NODO_EXPORTACION_JAVA,    (* Marcador para generación de bindings Java *)
    NODO_EXPORTACION_TS,      (* Marcador para generación de bindings TypeScript *)
    NODO_EXPORTACION_WASM     (* Marcador para exportación WASM *)
}

estructura NodoFuncion:
    nombre: String
    parametros: Lista<Parametro>
    tipo_retorno: Tipo
    es_pura: Booleano
    contratos: Contratos
    cuerpo: Bloque
    metadatos: Metadatos
    hash_ast: String          (* SHA-256 del AST para caché *)

estructura Contratos:
    requiere: Opcion<Expr>
    garantiza: Opcion<Expr>
    invariantes: Lista<Expr>

estructura Parametro:
    nombre: String
    tipo: Tipo
    es_referencia: Booleano   (* true para &T *)
    es_mutable: Booleano      (* true para &mut T *)

estructura NodoTrace:
    expresion: NodoExpresion
    metadatos: Metadatos

estructura ExportDef:
    tipo: TipoExport          (* python, java, typescript, wasm *)
    funcion: Opcion<NodoFuncion>
    estructura: Opcion<NodoEstructura>
```

### 5.2. Metadatos de Origen

Cada nodo incluye metadatos de trazabilidad:

```synapse
estructura Metadatos:
    archivo: String
    linea: Entero
    columna: Entero
    hash_segmento: String     (* SHA-256 del fragmento para auditoría *)
```

---

## 6. ANALIZADOR SEMÁNTICO Y SISTEMA DE TIPOS (`analizador_semantico.syn`)

El analizador semántico es el auditor central de **El Pacto**. Opera en tres pasadas secuenciales:

### 6.1. Ejecución en Tres Fases (Three-Pass Analysis)

| Pasada | Función | Validaciones |
| :--- | :--- | :--- |
| **Pasada 1** | Estructuras y Tipos Globales | Registra definiciones de estructuras, tipos algebraicos y constantes en la tabla de símbolos |
| **Pasada 2** | Firmas de Funciones | Valida tipos de parámetros, retorno y contratos lógicos (`requiere`/`garantiza`) |
| **Pasada 3** | Cuerpos y Ownership | Analiza bloques internos, verifica Use-After-Move y valida coincidencias exhaustivas |

### 6.2. Tipado Estricto e Inferencia

Synapse no utiliza tipado dinámico. Las variables declaradas mediante `let` reciben un tipo estricto deducido por inferencia estática unidireccional:

```synapse
let x = 42           (* Tipo inferido: Entero *)
let y = x + 3.14     (* ERROR: ERR_SEM_TYPE_AMBIGUOUS *)
let z: Flotante = 42.0  (* Correcto: tipo explícito *)
```

#### 6.2.1. Algoritmo de Inferencia de Tipos (Hindley-Milner Restringido)

Synapse implementa un algoritmo de inferencia de tipos basado en **Hindley-Milner con restricciones de unicidad** (para ownership).

**Estructuras de Datos:**

```synapse
tipo Tipo = enum {
    TVar(String),           // Variable de tipo: 'a, 'b, etc.
    TConst(String),         // Tipo concreto: Entero, Flotante, Booleano, String
    TAp(Tipo, Tipo),        // Aplicación: Lista(Entero), Resultado(String, Error)
    TFun(Tipo, Tipo),       // Función: Entero -> String
    TRef(Tipo),             // Referencia: &Entero
    TRefMut(Tipo),          // Referencia mutable: &mut Entero
    TError                  // Tipo de error (para propagación)
}

tipo Substitución = Mapa<String, Tipo>
tipo Ecuación = (Tipo, Tipo)
```

**Algoritmo de Unificación:**

```
función unificar(t1: Tipo, t2: Tipo, subst: Substitución) -> Resultado<Substitución, Error>:
    t1 = aplicar_subst(subst, t1)
    t2 = aplicar_subst(subst, t2)

    coincidir (t1, t2):
        (TVar(a), TVar(b)) si a == b => ok(subst)
        (TVar(a), _) si a no está en t2 => ok(subst + {a -> t2})
        (_, TVar(a)) si a no está en t1 => ok(subst + {a -> t1})
        (TConst(a), TConst(b)) si a == b => ok(subst)
        (TAp(a1, b1), TAp(a2, b2)) =>
            subst1 = unificar(a1, a2, subst)
            subst2 = unificar(b1, b2, subst1)
            ok(subst2)
        (TFun(a1, b1), TFun(a2, b2)) =>
            subst1 = unificar(a1, a2, subst)
            subst2 = unificar(b1, b2, subst1)
            ok(subst2)
        (TRef(a), TRef(b)) => unificar(a, b, subst)
        (TRefMut(a), TRefMut(b)) => unificar(a, b, subst)
        (TRef(a), TRefMut(b)) => err("ERR_SEM_TYPE_MISMATCH: no se puede convertir &mut a &")
        _ => err("ERR_SEM_TYPE_UNIFICATION_FAILED")
```

**Manejo de Ambigüedades:**

| Escenario | Comportamiento | Código de Error |
| :--- | :--- | :--- |
| `let x = 42` | ✅ OK: `x: Entero` | - |
| `let x = 42.0` | ✅ OK: `x: Flotante` | - |
| `let x = 42 + 3.14` | ❌ AMBIGUO | `ERR_SEM_TYPE_AMBIGUOUS` |
| `let x: Flotante = 42` | ✅ OK: Conversión explícita | - |
| `let x = []` | ❌ AMBIGUO | `ERR_SEM_TYPE_AMBIGUOUS` |
| `let x: Lista<Entero> = []` | ✅ OK | - |

**Recuperación de Errores:** El compilador registra el error, propaga `TError` y continúa para reportar múltiples fallos.

### 6.3. Tipos Algebraicos de Datos (ADTs)

```synapse
tipo Resultado<T, E> = ok(T) | err(E)
tipo Opcion<T> = algun(T) | ninguno
```

**Regla Semántica:** Uso de `coincidir` obligatorio para estos tipos.  
`ERR_SEM_EXHAUSTIVE_MATCH_REQUIRED` si falta algún caso.

---

## 7. EL PACTO: SEGURIDAD DE MEMORIA (OWNERSHIP & BORROWING)

Synapse prescinde de GC y prohíbe `malloc`/`free` manual en código de usuario.

### 7.1. Reglas de Posesión (Ownership)

| Regla | Descripción |
| :--- | :--- |
| **Posesión Única** | Cada recurso tiene un único propietario. |
| **Liberación Determinista** | RAII estático: liberación al salir del ámbito. |
| **Semántica de Movimiento** | Asignación o paso por valor transfiere la posesión. |
| **Use-After-Move** | Detección en tiempo de compilación → `ERR_MEM_USE_AFTER_MOVE`. |

### 7.2. Préstamo (Borrowing)

```synapse
fn procesar(datos: &[Entero]) -> Entero:
    (* Referencia prestada, solo lectura *)
```

| Tipo de Préstamo | Mutabilidad | Duración |
| :--- | :--- | :--- |
| `&T` | Solo lectura | Lifetime del préstamo |
| `&mut T` | Lectura/Escritura | Exclusivo |

### 7.3. Regla de Oro

> "Una variable solo puede ser movida una vez. Después de un movimiento, no puede ser utilizada a menos que sea reasignada."

### 7.4. Análisis de Lifetimes (Vidas Útiles)

**Representación:**

```synapse
tipo Lifetime = enum {
    LT_ESTATICO,
    LT_LOCAL(Entero),
    LT_PARAMETRICO,
    LT_ELIDIDO
}
```

**Algoritmo de Verificación:**

1. Recolectar variables y sus ámbitos.
2. Asignar lifetimes.
3. Recolectar restricciones de usos.
4. Resolver restricciones (grafo de subtipeo).
5. Verificar consistencia (ciclos → `ERR_MEM_LIFETIME_CYCLE`).
6. Verificar que ningún lifetime exceda su ámbito (`ERR_MEM_LIFETIME_TOO_LONG`, `ERR_MEM_LIFETIME_TOO_SHORT`).

**Reglas de Elisión:**

- `fn foo(x: &Entero) -> &Entero` → `fn foo<'a>(x: &'a Entero) -> &'a Entero`.
- Múltiples parámetros, uno es `self` → el lifetime de retorno se asocia a `self`.

**Caso de Borde: Estructuras con Referencias**

```synapse
estructura Contenedor<'a>:
    dato: &'a Entero
```

---

## 8. CONCURRENCIA AISLADA Y DISEÑO POR CONTRATO

### 8.1. Concurrencia por Canales Tipados (`std::concurrencia`)

```synapse
lanzar hilo_mi_hilo := fn():
    let mensaje = canal.recibir()
    procesar(mensaje)
```

| Regla | Descripción |
| :--- | :--- |
| **Sin Memoria Compartida** | Comunicación exclusiva mediante canales. |
| **Transferencia de Ownership** | El envío mueve la posesión. |
| **Zero Data Races** | Verificado en tiempo de compilación. |

### 8.2. Concurrencia Distribuida (`std::cluster`)

```synapse
let canal_remoto = CanalRemoto<T>::conectar("tcp://192.168.1.100:8080")
```

- TCP cifrado por defecto.
- Serializació n automática de tipos algebraicos.

### 8.3. Diseño por Contrato

```synapse
fn dividir(a: Entero, b: Entero) -> Entero
    requiere b != 0
    garantiza resultado * b + (a % b) == a
:
    retornar a / b
```

| Cláusula | Evaluación | Modo `--release` |
| :--- | :--- | :--- |
| `requiere` | Inicio de función | Desactivada |
| `garantiza` | Antes del retorno | Desactivada |
| `invariantes` | Iteraciones de bucle | Desactivadas |
| `puro` | Verificación formal | Siempre activa |

### 8.4. Verificación Formal Pragmática (Modo `--safe`)

- Sin bucles (solo recursión primitiva).
- Sin efectos secundarios.
- Sin acceso a memoria mutable.
- Terminación demostrable por inducción estructural.

---

## 9. GENERADOR DE CÓDIGO C Y OPTIMIZACIONES (`generator.syn`)

### 9.1. Modos de Generación

| Modo | Banderas | Propósito |
| :--- | :--- | :--- |
| `debug` | `-O0 -g` | Desarrollo |
| `release` | `-O2` | Producción |
| `release-pgo` | `-O3 -fprofile-generate` | Generación de perfiles |
| `release-pgo-use` | `-O3 -fprofile-use -flto` | Optimización PGO |
| `safe` | `-O2 -fsanitize=address,undefined` | Verificación + sanitizadores |
| `wasm` | `emcc -O3 -s WASM=1` | WebAssembly |
| `incremental` | `-O2 -fno-whole-program` | Caché incremental |

### 9.2. Optimización Guiada por Perfil (PGO)

**Niveles de Instrumentación:**

1. **Nivel 1 (Counters):** Contadores de bloques básicos y bordes (10-15% mejora).
2. **Nivel 2 (Value Profiling):** Registro de valores de ramas (+5-10%).
3. **Nivel 3 (Memory Profiling):** Registro de asignaciones (+3-5%).

**Pipeline:**
```bash
synapse build --release --pgo=instrument
./bin/instrumented --benchmark
synapse build --release --pgo=use
```

### 9.3. Optimizaciones del Compilador (Fase Intermedia)

- **Propagación de Constantes:** Evaluación de expresiones constantes.
- **Eliminación de Código Muerto:** Análisis de variables vivas.
- **Inlining:** Heurística (≤5 líneas siempre, ≤10 líneas si <3 llamadas, recursivas nunca).
- **Levantamiento de Invariantes:** Extraer expresiones invariantes de bucles.

### 9.4. Emisión de Código para WebAssembly

**Mapeo AST → WASM:**

```synapse
fn _ast_a_wasm(nodo: Nodo) -> Lista<InstruccionWASM>:
    coincidir nodo:
        NodoLiteralEntero(valor) => [I32_CONST(valor)]
        NodoSuma(izq, der) => _ast_a_wasm(izq) + _ast_a_wasm(der) + [I32_ADD]
        NodoLlamada(funcion, args) =>
            let codigo = args.map(_ast_a_wasm).flatten()
            codigo.append(CALL(funcion))
            retornar codigo
        _ => err("Nodo no soportado")
```

---

## 10. COMPILACIÓN INCREMENTAL Y CACHÉ DETERMINISTA

### 10.1. Arquitectura de Caché

**Generación de Clave:**
```
clave = SHA-256( contenido_archivo + hash_dependencias + flags_compilacion + version_compilador )
```

**Estructura de Entrada (`CacheEntry`):**
```synapse
tipo CacheEntry = estructura:
    key: String
    ast_hash: String
    codigo_c: String
    objeto: Bytes
    dependencias: Lista<String>
    flags: String
    timestamp: Entero
    metadatos: Metadatos
```

### 10.2. Integración con el Compilador

```synapse
fn compilar_incremental(archivo: String, flags: String) -> Resultado<Bytes, Error>:
    let clave = cache::calcular_clave(archivo, deps, flags)
    coincidir cache::cargar(clave):
        ok(entry) => retornar ok(entry.objeto)  // Caché HIT
        err(ERR_CACHE_MISS) =>
            let ast = parsear(archivo)
            let objeto = compilar(ast, flags)
            cache::guardar(CacheEntry{...})
            retornar ok(objeto)
```

### 10.3. Comandos CLI

```bash
synapse build --incremental main.syn
synapse cache stats
synapse cache clean --days 30
```

---

## 11. DEPURACIÓN ASISTIDA POR IA (TIME-TRAVEL DEBUGGING)

### 11.1. Arquitectura de Traza

El sistema registra eventos durante la ejecución y los analiza con OpenSyn.

**Eventos (`TraceEvent`):**
- `EVENT_ASSIGNMENT`, `EVENT_FUNCTION_CALL`, `EVENT_ERROR`, `EVENT_BRANCH_TAKEN`, `EVENT_USER_TRACE`.

### 11.2. Módulo `std::debug`

```synapse
fn debug::trace(expresion: Expr) -> Resultado<Valor, Error>
fn debug::iniciar_sesion(programa: String) -> TraceSession
fn debug::finalizar_sesion() -> Resultado<TraceSession, Error>
```

### 11.3. Análisis con OpenSyn

```synapse
fn opensyn::analizar_traza(session: TraceSession) -> Resultado<AnalisisTraza, Error>
```

**Análisis devuelve:** Causa raíz, línea del error, pasos relevantes, sugerencias y confianza.

### 11.4. Sintaxis en Código

```synapse
fn procesar(datos: Lista<Entero>) -> Entero:
    let suma = 0
    para i en 0..datos.len():
        let valor = datos[i]
        trace("Procesando: " + valor.to_string())
        suma = suma + valor
    trace("Suma total: " + suma.to_string())
    retornar suma
```

---

## 12. GRAFOS DE DEPENDENCIAS Y ANÁLISIS DE IMPACTO

### 12.1. Estructura del Grafo

```synapse
tipo NodoDependencia = estructura:
    id: String
    tipo: NodoTipo
    nombre: String
    archivo: String
    linea: Entero

tipo AristaDependencia = estructura:
    origen: String
    destino: String
    tipo: TipoDependencia  (* DEP_LLAMADA, DEP_USA, DEP_IMPLEMENTA *)
    linea: Entero
```

### 12.2. Algoritmos

- **Construcción:** Recorrido del AST para registrar nodos y aristas.
- **Cálculo de Impacto:** BFS desde un nodo para encontrar todos los dependientes.
- **Detección de Ciclos:** DFS con coloración (blanco, gris, negro).

### 12.3. Comandos CLI

```bash
synapse analyze --graph main.syn
synapse analyze --impact --function procesar_datos main.syn
synapse analyze --cycles main.syn
synapse analyze --graph --dot main.syn > graph.dot
```

---

## 13. SANDBOX DE EJECUCIÓN PARA IA

### 13.1. Arquitectura

Aísla código generado por IA limitando recursos y restringiendo acceso al sistema.

**Características:**

- Namespace de usuario (Linux).
- Límites de memoria, CPU, procesos y tamaño de archivos.
- Bloqueo de syscalls peligrosas (seccomp): `execve`, `fork`, `socket`, `open`, etc.

### 13.2. Configuración (`sandbox_config.yaml`)

```yaml
sandbox:
  memory_limit_mb: 100
  cpu_time_limit_sec: 5
  process_limit: 1
  network_access: false
  filesystem_access: false
  violation_action: "terminate"
```

### 13.3. Implementación en C

```c
int synapse_sandbox_init(SandboxConfig config) {
    unshare(CLONE_NEWUSER | CLONE_NEWNET | CLONE_NEWPID);
    setrlimit(RLIMIT_AS, &limits);
    setrlimit(RLIMIT_CPU, &limits);
    // Configurar seccomp
    scmp_filter_ctx ctx = seccomp_init(SCMP_ACT_ALLOW);
    seccomp_rule_add(ctx, SCMP_ACT_ERRNO(EPERM), SCMP_SYS(execve), 0);
    seccomp_load(ctx);
}
```

### 13.4. Comandos CLI

```bash
synapse run --sandbox codigo_generado.syn
synapse run --sandbox --max-memory 256MB --max-time 10s
synapse sandbox logs
```

---

## 14. AXON HUB DESCENTRALIZADO

### 14.1. Arquitectura Descentralizada

Utiliza IPFS para almacenamiento y verificación distribuida.

**Reglas:**

- Mínimo 3 firmas Ed25519 de mantenedores distintos.
- Tests de verificación obligatorios.
- Reputación de mantenedores (0.0 - 5.0).

### 14.2. Estructura de Paquete

```synapse
tipo PaqueteAxon = estructura:
    nombre: String
    version: String
    mantenedores: Lista<ClavePublica>
    hash_sha256: String
    hash_ipfs: String          (* CID de IPFS *)
    firmas: Lista<FirmaEd25519>
    tests_verificacion: Lista<CasoPrueba>
    reputacion: Flotante
```

### 14.3. Funciones Clave

- `axon::hub_publicar()`: Valida tests, firmas (≥3), reputación, publica en IPFS.
- `axon::hub_verificar()`: Valida firmas, hashes y replicas en IPFS (≥2 nodos).
- `axon::hub_buscar()`: Consulta el índice descentralizado.

### 14.4. Comandos CLI

```bash
synapse axon publish --nombre mi-paquete --version 1.0.0
synapse axon verify mi-paquete@1.0.0
synapse axon search "procesamiento json"
```

---

## 15. ECOSISTEMA DE IA LOCAL Y LSP — ARQUITECTURA DESACOPLADA

### 15.1. Principio de Desacoplamiento

OpenSyn opera como un servicio independiente (demonio) comunicándose con el LSP mediante IPC local (sockets Unix / named pipes).

```
┌─────────────┐   IPC (JSON-RPC)   ┌─────────────┐
│ synapse_lsp │◄──────────────────►│  OpenSyn    │
└─────────────┘                    │  (Demonio)  │
                                   └─────────────┘
```

### 15.2. LSP (`synapse_lsp`)

- JSON-RPC 2.0 sobre `stdio`.
- Diagnósticos en tiempo real, autocompletado, navegación.
- Consulta a OpenSyn vía IPC para asistencia IA.

### 15.3. Pipeline RAG Quirúrgico

- Contexto: nodo AST actual, línea, columna, diagnósticos.
- Gestión `n_ctx`: 30% para contexto, 70% para generación.

### 15.4. Enrutador Determinista Basado en AST

```synapse
fn enrutar(consulta: Consulta) -> AccionRouter:
    // ERR_* → RAG
    // Función sin contratos → GENERATE_CONTRACT
    // Función pura → RAG de ejemplos
    // Solicitud de código → GENERATE_CODE
    // Pregunta de sintaxis → PARAMETRIC_RESPONSE
```

---

## 16. GESTOR DE PAQUETES INMUTABLE (AXON)

### 16.1. Reglas de Hierro

| Regla | Descripción |
| :--- | :--- |
| **Prohibición de Scripts** | No permite `preinstall`/`postinstall`. |
| **Firma Obligatoria** | Ed25519 (TweetNaCl). |
| **Firmas Múltiples** | Mínimo 3 firmas en Axon Hub. |
| **Bloqueo Determinista** | `axon.lock` con SHA-256. |
| **Protección Path Traversal** | Bloqueo de `../`. |
| **Almacenamiento IPFS** | Contenido descentralizado. |

### 16.2. Registro de Paquetes (`axon.toml`)

```toml
[paquete]
nombre = "mi-biblioteca"
version = "1.0.0"
authors = ["dev@ejemplo.com"]

[firma]
ed25519 = "K2x..."
```

---

## 17. ESPECIFICACIÓN DE LA BIBLIOTECA ESTÁNDAR (`std`)

### 17.1. Módulo de Red (`std::net`)

- Abstracción TCP/HTTP con `Resultado<Conexion, ErrorRed>`.

### 17.2. Módulo JSON (`std::json`)

- Aceleración SIMD (SSE/AVX) para parsing.

### 17.3. Módulo de Concurrencia (`std::concurrencia`)

- Canales tipados `Canal<T>`.

### 17.4. Módulo de Observabilidad (`std::telemetry`)

- Logs estructurados JSON, niveles y exportación OpenTelemetry.

### 17.5. Módulo de Depuración (`std::debug`)

- Trazas, sesiones y análisis con IA.

### 17.6. Módulo de Sandbox (`std::sandbox`)

- Interfaz para ejecutar código con límites.

```synapse
sandbox::ejecutar({ memoria_max: 100, tiempo_max: 5, codigo: "fn main() { ... }" })
```

---

## 18. PRUEBAS, FUZZING Y ASEGURAMIENTO DE CALIDAD

### 18.1. Arquitectura de Testing

| Tipo | Número | Alcance |
| :--- | :--- | :--- |
| **Unitarias** | 350+ | Lexer, Parser, Semántico, Generador C, Caché, Grafo, Sandbox |
| **Integración** | 30+ | End-to-end, LSP, Axon, Axon Hub, Depuración |
| **Fuzzing** | 1000+ | Entradas corruptas y maliciosas |
| **Benchmarks** | (Abiertos) | Vs CPython, PyPy, Java, C++ |

### 18.2. Pruebas Específicas (Extraídas de v4.0 y v5.0)

- **Caché:** `test_cache_hit`, `test_cache_invalidation`.
- **Sandbox:** `test_sandbox_limits`, `test_sandbox_network_block`.
- **Axon Hub:** `test_axon_hub_publicar`, `test_axon_hub_verificar`.
- **Seguridad:** Inyección en Axon y pruebas de escape del sandbox.

### 18.3. Sanitizadores Obligatorios

- **AddressSanitizer:** 0 fugas de memoria.
- **UndefinedBehaviorSanitizer:** 0 comportamientos indefinidos.

---

## 19. PROCESO DE BOOTSTRAP Y AUTO-HOSPEDAJE (SELF-HOSTING)

### 19.1. Pipeline de Compilación en Cascada

```
Stage 0: Compilador Python/C (semilla)
    │
    ▼
Stage 1: Compila nucleo/*.syn → synapse_v1
    │
    ▼
Stage 2: synapse_v1 recompila nucleo/*.syn → synapse_v2
    │
    ▼
Stage 3: synapse_v2 recompila nucleo/*.syn → synapse_v3
    │
    ▼
Verificación: diff synapse_v2 synapse_v3 → 0 bytes
```

**Certificación:** La igualdad binaria entre Stage 2 y Stage 3 certifica que el compilador es completamente autónomo, determinista y libre de dependencias externas.

---

## 20. GUÍAS DE CONTRIBUCIÓN Y REGLAS DE INGENIERÍA

### 20.1. Normas de Estilo

| Regla | Implementación |
| :--- | :--- |
| Indentación | 4 espacios estrictos (prohibido `\t`) |
| Nombres de variables | `snake_case` |
| Nombres de tipos | `PascalCase` |
| Nombres de constantes | `SCREAMING_SNAKE_CASE` |
| Longitud máxima | 100 caracteres |

### 20.2. Filosofía de Seguridad

- **Cero Telemetría:** Sin conexiones en red ocultas.
- **Opt-in de IA:** OpenSyn solo se activa por solicitud explícita.
- **Soberanía de Datos:** Procesamiento local; sin exportación.
- **Sandbox por Defecto:** Código generado por IA ejecutado en sandbox.

---

## 21. ARQUITECTURA DEL TOOLCHAIN Y CLI (`synapse` CLI)

### 21.1. Comandos Principales

| Comando | Función |
| :--- | :--- |
| `synapse build` | Compila y genera binario nativo |
| `synapse build --release` | Compilación optimizada (`-O2`) |
| `synapse build --release --pgo` | Optimización guiada por perfil |
| `synapse build --target wasm` | Compilación a WebAssembly |
| `synapse build --incremental` | Compilación incremental con caché |
| `synapse build --safe` | Verificación formal |
| `synapse run` | Compila y ejecuta |
| `synapse run --debug` | Ejecución con depuración activa |
| `synapse run --debug --ai-trace` | Depuración asistida por IA |
| `synapse run --sandbox` | Ejecución en sandbox |
| `synapse test` | Ejecuta suite de pruebas |
| `synapse fetch` | Resuelve dependencias con Axon |
| `synapse migrate` | Transpila código Python a Synapse |
| `synapse bridge python` | Genera módulo Python nativo |
| `synapse bridge java` | Genera bindings JNI |
| `synapse bridge ts` | Genera definiciones TypeScript |
| `synapse analyze --graph` | Genera grafo de dependencias |
| `synapse analyze --impact` | Calcula impacto de cambio |
| `synapse analyze --cycles` | Detecta ciclos en dependencias |
| `synapse cache stats` | Estadísticas de caché |
| `synapse cache clean` | Limpia caché |
| `synapse debug analyze` | Analiza traza de depuración |
| `synapse debug view` | Visualiza traza |
| `synapse sandbox logs` | Ver logs del sandbox |
| `synapse axon publish` | Publica paquete en Axon Hub |
| `synapse axon verify` | Verifica paquete |
| `synapse axon search` | Busca paquetes |

---

## 22. INTEROPERABILIDAD Y FFI

### 22.1. FFI con C

```synapse
extern "C" fn strlen(s: *const Char) -> Entero
```

### 22.2. Generación de Módulos Python

```synapse
@export(python)
fn procesar_datos(datos: Lista<Entero>) -> Resultado<Flotante, Error>:
```

### 22.3. Generación de Bindings Java (JNI)

```synapse
@export(java)
class Procesador:
    fn calcular(entrada: Entero) -> Entero
```

### 22.4. Generación de Bindings TypeScript

```synapse
@export(typescript)
fn validar_usuario(id: String) -> Resultado<Booleano, Error>
```

---

## 23. TAXONOMÍA DE ERRORES DEL COMPILADOR

### 23.1. Errores Léxicos (`ERR_LEX_*`)
- `ERR_LEX_MISSING_LANG`
- `ERR_LEX_TAB_DETECTED`
- `ERR_LEX_INVALID_CHAR`
- `ERR_LEX_INVALID_INDENT`

### 23.2. Errores Semánticos (`ERR_SEM_*`)
- `ERR_SEM_TYPE_AMBIGUOUS`
- `ERR_SEM_TYPE_UNIFICATION_FAILED`
- `ERR_SEM_EXHAUSTIVE_MATCH_REQUIRED`
- `ERR_SEM_UNDEFINED_SYMBOL`
- `ERR_SEM_CYCLIC_DEPENDENCY`
- `ERR_SEM_STACK_OVERFLOW`
- `ERR_SEM_OVERFLOW`

### 23.3. Errores de Memoria (`ERR_MEM_*`)
- `ERR_MEM_USE_AFTER_MOVE`
- `ERR_MEM_BORROW_CHECK_FAILED`
- `ERR_MEM_LIFETIME_MISMATCH`
- `ERR_MEM_LIFETIME_CYCLE`
- `ERR_MEM_LIFETIME_TOO_LONG`
- `ERR_MEM_LIFETIME_INVALID_PARAM`
- `ERR_MEM_LIFETIME_TOO_SHORT`

### 23.4. Errores de Caché (`ERR_CACHE_*`)
- `ERR_CACHE_MISS`
- `ERR_CACHE_CORRUPT`
- `ERR_CACHE_VERSION_MISMATCH`
- `ERR_CACHE_FULL`

### 23.5. Errores de Sandbox (`ERR_SANDBOX_*`)
- `ERR_SANDBOX_MEMORY_LIMIT`
- `ERR_SANDBOX_CPU_LIMIT`
- `ERR_SANDBOX_NETWORK_BLOCKED`
- `ERR_SANDBOX_FILESYSTEM_BLOCKED`
- `ERR_SANDBOX_SYSCALL_BLOCKED`
- `ERR_SANDBOX_FORK_BLOCKED`

### 23.6. Errores de Axon Hub (`ERR_AXON_*`)
- `ERR_AXON_TEST_FAILED`
- `ERR_AXON_INSUFFICIENT_SIGNATURES`
- `ERR_AXON_REPUTATION_TOO_LOW`
- `ERR_AXON_INVALID_SIGNATURE`
- `ERR_AXON_HASH_MISMATCH`
- `ERR_AXON_IPFS_MISMATCH`
- `ERR_AXON_INSUFFICIENT_REPLICAS`
- `ERR_AXON_SIG_INVALID`
- `ERR_AXON_PATH_TRAVERSAL`
- `ERR_AXON_COMPROMISED`

### 23.7. Errores de Depuración (`ERR_DEBUG_*`)
- `ERR_DEBUG_NO_ERROR`
- `ERR_DEBUG_ANALYSIS_FAILED`
- `ERR_DEBUG_SESSION_NOT_FOUND`

### 23.8. Errores de Verificación Formal (`ERR_VER_*`)
- `ERR_VER_NON_TERMINATING`
- `ERR_VER_IMPURE`
- `ERR_VER_MUTABLE_ACCESS`
- `ERR_VER_MISSING_PRECONDITION`
- `ERR_VER_MISSING_POSTCONDITION`
- `ERR_VER_PRECONDITION_NOT_BOOLEAN`
- `ERR_VER_INVARIANT_NOT_BOOLEAN`

---

## 24. SEGURIDAD — VECTORES DE ATAQUE Y MITIGACIONES

| Vector de Ataque | Mitigación |
| :--- | :--- |
| **Inyección de Código** | Axon: Ed25519 + prohibición de scripts |
| **Desbordamiento de Búfer** | Ownership + AddressSanitizer |
| **Use-After-Free** | Ownership + Use-After-Move detection |
| **Data Races** | Canal<T> + sin memoria compartida mutable |
| **Path Traversal** | Axon: bloqueo de `../` |
| **Denegación de Servicio** | Verificación formal `--safe` |
| **Integer Overflow** | Verificación formal `--safe` + sanitizadores |
| **Type Confusion** | Tipado estricto inferido |
| **Ataque a la Caché** | Firma SHA-256 + verificación de integridad |
| **Ataque al Sandbox** | seccomp + namespaces + límites de recursos |
| **Ataque a Axon Hub** | Firmas múltiples + reputación + tests |
| **Ataque a IPFS** | Verificación de hash + replicación |

**Política de OpenSyn:**
- Aislamiento de procesos (namespaces).
- Límites de recursos (CPU, memoria).
- Validación de entradas (longitud, caracteres, escape HTML).

---

## 25. ANEXOS: DIAGRAMAS, CHECKLISTS Y CASOS DE PRUEBA

### 25.1. Diagrama de Flujo del Compilador (v5.0)

```
[Fuente (.syn)] → [Lexer] → [Parser] → [Caché: Hash de clave]
                                          │
                    ┌─────────────────────┼─────────────────────┐
                    ▼                     ▼                     ▼
              [Caché HIT]          [Caché MISS]         [Caché STALE]
              Cargar objeto        Analizador           Recompilar
                                   Semántico            Actualizar
                                   (3 Pasadas)
                                   Generador C/WASM
                                   Guardar Caché
```

### 25.2. Checklist de Verificación de Calidad (Definition of Done) v5.0

- [ ] **Cumplimiento Léxico y Sintáctico**
  - [ ] `#lang: es` en línea 1.
  - [ ] Indentación a 4 espacios (sin tabuladores).
  - [ ] Sin `ERR_LEX_*`.
- [ ] **Seguridad de Memoria**
  - [ ] Cero `malloc`/`free` manual.
  - [ ] Sin Use-After-Move.
  - [ ] 0 fugas (AddressSanitizer).
- [ ] **Concurrencia**
  - [ ] Cero variables globales mutables entre hilos.
  - [ ] Comunicación mediante `Canal<T>`.
- [ ] **Compilación Incremental**
  - [ ] Caché funciona (hit/miss/stale).
  - [ ] Tiempo de compilación 10-50x más rápido.
- [ ] **Depuración y Sandbox**
  - [ ] Trazas registradas correctamente.
  - [ ] OpenSyn analiza trazas.
  - [ ] Sandbox bloquea syscalls peligrosas.
  - [ ] Límites de memoria y CPU funcionan.
- [ ] **Validación de Pruebas**
  - [ ] 100% tests unitarios aprobados (350+).
  - [ ] 100% tests de integración aprobados (30+).
  - [ ] Fuzzing sin crashes (1000+ entradas).
- [ ] **Cadena de Suministro**
  - [ ] SHA-256 generado.
  - [ ] Firma Ed25519 validada.
  - [ ] Axon Hub funciona (publicar/verificar/buscar).
- [ ] **Interoperabilidad**
  - [ ] Bindings TypeScript generados.
  - [ ] Módulo Python exportable.
  - [ ] Bindings JNI generados.

---

## 26. FIRMA Y CERTIFICACIÓN TÉCNICA

El **Manual de Ingeniería y Desarrollo de Synapse (v5.0) — Unificado** queda formalmente consolidado como el documento maestro de especificación técnica del proyecto, abarcando desde los fundamentos del núcleo hasta las capacidades de la revolución cognitiva.

```text
================================================================================
  DOCUMENTO OFICIAL DE ARQUITECTURA E INGENIERÍA — SYNAPSE v5.0 (UNIFICADO)
  Estado: APROBADO Y SELLADO

  Principios Rectores:
    - "El Pacto": Tipado Estricto Inferido | Zero-GC | Ownership & Borrowing
    - Soberanía del Usuario: Cero Telemetría | Procesamiento Local
    - Interoperabilidad Total: WASM+TS | Python | Java | C
    - Revolución Cognitiva: Caché | Time-Travel IA | Sandbox | Axon Hub

  Especificaciones de Ingeniería Completadas (Base → v5.0):
    ✓ Algoritmo de Inferencia de Tipos (Hindley-Milner)
    ✓ Análisis de Lifetimes y Verificación de Préstamos
    ✓ Optimizaciones PGO (3 niveles, pipeline completo)
    ✓ Backend WASM con mapeo AST→instrucciones
    ✓ Enrutador Determinista para OpenSyn
    ✓ Compilación Incremental con Caché Determinista
    ✓ Depuración Asistida por IA (Time-Travel Debugging)
    ✓ Grafos de Dependencias y Análisis de Impacto
    ✓ Sandbox de Ejecución para IA (seccomp + namespaces)
    ✓ Axon Hub Descentralizado (IPFS + firmas múltiples)
    ✓ Matriz de Vectores de Ataque y Mitigaciones

  Versión: 5.0
  Fecha de Ratificación: 2026-07-26
================================================================================
```

---

**Fin del Manual de Ingeniería y Desarrollo de Synapse (v5.0) — Unificado**