# MANUAL 2: SINTAXIS Y SEMÁNTICA DE SYNAPSE

**Archivo:** `02_SINTAXIS_Y_SEMANTICA_SYNAPSE.md`  
**Versión:** 8.0.0-industrial  
**Propósito:** Definir la gramática formal del lenguaje Synapse, su sistema de tipos, las reglas semánticas fundamentales (contratos, patrones, importaciones), y la estructura del Árbol de Sintaxis Abstracta (AST). Este manual establece las bases del compilador de Synapse y su integración con el ecosistema.

---

## 1. DIRECTIVA DE ARCHIVO Y CODIFICACIÓN

### 1.1. Directiva de Idioma

Todo archivo fuente de Synapse **debe** comenzar con la directiva de idioma en la **línea 1**:

```synapse
#lang: es
```

Idiomas soportados: `es` (español), `en` (inglés), `fr` (francés), `pt` (portugués), `ja` (japonés), `de` (alemán), `zh` (chino).

La directiva debe aparecer exactamente como se muestra, sin espacios adicionales antes del `#` y con un solo espacio después de los dos puntos. Si el archivo omite esta directiva, el lexer rechazará el archivo con el error `ERR_LEX_MISSING_LANG`.

### 1.2. Codificación

Todos los archivos fuente deben estar codificados en **UTF‑8 sin BOM**. El lexer rechazará cualquier archivo que contenga caracteres no válidos en UTF‑8.

### 1.3. Comentarios

Synapse soporta dos estilos de comentarios:

- **Comentarios de línea:** comienzan con `//` y se extienden hasta el final de la línea.
- **Comentarios de bloque:** comienzan con `/*` y terminan con `*/`, pueden abarcar múltiples líneas y anidarse.

---

## 2. GRAMÁTICA FORMAL DE SYNAPSE (EBNF COMPLETA)

La gramática de Synapse se define mediante una notación EBNF extendida. Los símbolos terminales se escriben en **mayúsculas** (ej. `IDENTIFICADOR`, `NUMERO`). Los no terminales se escriben en **minúscula** (ej. `programa`, `sentencia`). Los operadores de repetición son `*` (cero o más), `+` (uno o más) y `?` (opcional). La concatenación se indica con espacios o coma. La alternativa se indica con `|`. La agrupación se indica con paréntesis `( )`. Los tokens literales se escriben entre comillas simples o dobles.

```ebnf
(* Programa principal *)
programa         ::= directiva_lang { declaracion } EOF

(* Directiva de idioma *)
directiva_lang   ::= "#lang:" IDENTIFICADOR NEWLINE

(* Declaraciones a nivel de módulo *)
declaracion      ::= declaracion_funcion
                   | declaracion_estructura
                   | declaracion_constante
                   | declaracion_tipo
                   | importacion
                   | declaracion_export

(* Funciones *)
declaracion_funcion ::= "funcion" IDENTIFICADOR "(" [ parametros ] ")" [ "->" tipo ] [ contratos ] ":" NEWLINE INDENT bloque DEDENT

parametros       ::= parametro { "," parametro }
parametro        ::= [ "->" ] IDENTIFICADOR ":" tipo
                     (* "->" indica transferencia de ownership (move) *)

contratos        ::= [ bloque_requiere ] [ bloque_garantiza ]
bloque_requiere  ::= "requiere" ":" NEWLINE INDENT { expresion NEWLINE } DEDENT
bloque_garantiza ::= "garantiza" ":" NEWLINE INDENT { expresion NEWLINE } DEDENT

(* Estructuras *)
declaracion_estructura ::= "estructura" IDENTIFICADOR [ "(" IDENTIFICADOR ")" ]? ":" NEWLINE INDENT { campo } DEDENT
campo            ::= IDENTIFICADOR ":" tipo NEWLINE

(* Constantes *)
declaracion_constante ::= "constante" IDENTIFICADOR "=" expresion NEWLINE

(* Tipos algebraicos *)
declaracion_tipo ::= "tipo" IDENTIFICADOR "=" "(" constructor { "|" constructor } ")" NEWLINE
constructor      ::= IDENTIFICADOR [ "(" tipo { "," tipo } ")" ]

(* Importaciones *)
importacion      ::= "importar" IDENTIFICADOR { "." IDENTIFICADOR } [ "como" IDENTIFICADOR ] NEWLINE

(* Exportaciones (para FFI con Syquex) *)
declaracion_export ::= "@export" "(" IDENTIFICADOR ")" declaracion_funcion

(* Bloques y sentencias *)
bloque           ::= { sentencia NEWLINE }
sentencia        ::= sentencia_control
                   | asignacion
                   | expresion
                   | declaracion_variable
                   | sentencia_vacia

sentencia_control ::= condicional_si
                    | bucle_mientras
                    | bucle_para
                    | lanzar_hilo
                    | escuchar_canal
                    | recuperar_error
                    | romper
                    | siguiente
                    | bloque_inseguro
                    | coincidir_patron
                    | retornar
                    | delegar

condicional_si   ::= "si" expresion ":" NEWLINE INDENT bloque DEDENT [ "sino" ":" NEWLINE INDENT bloque DEDENT ]

bucle_mientras   ::= "mientras" expresion ":" NEWLINE INDENT bloque DEDENT

bucle_para       ::= "para" IDENTIFICADOR "=" expresion "mientras" expresion ":" NEWLINE INDENT bloque DEDENT
                     (* Ej: para i = 0 mientras i < 10: *)

lanzar_hilo      ::= "lanzar" llamada_funcion [ "recuperar" expresion ]

escuchar_canal   ::= "escuchar" expresion ":" NEWLINE INDENT bloque DEDENT

recuperar_error  ::= expresion "recuperar" ":" expresion
                     (* Ej: abrir("archivo.txt") recuperar: log("Error al abrir") *)

romper           ::= "romper"
siguiente        ::= "siguiente"

bloque_inseguro  ::= "inseguro" ":" NEWLINE INDENT bloque DEDENT

coincidir_patron ::= "coincidir" expresion ":" NEWLINE INDENT { caso_coincidir } DEDENT
caso_coincidir   ::= patron "=>" ( sentencia | NEWLINE INDENT bloque DEDENT )
patron           ::= IDENTIFICADOR "(" IDENTIFICADOR ")"   (* ej: ok(valor), err(e) *)
                   | IDENTIFICADOR                         (* ej: ninguno *)
                   | "_"                                  (* wildcard *)

retornar         ::= "retornar" [ "->" ] expresion?
                     (* La flecha indica transferencia de ownership *)

delegar          ::= "delegar" expresion  (* Para el operador ? en Syquex, traducido a retornar err(...) *)

declaracion_variable ::= "let" IDENTIFICADOR [ ":" tipo ] [ "=" expresion ] NEWLINE

asignacion       ::= IDENTIFICADOR "=" expresion
                   | IDENTIFICADOR "." IDENTIFICADOR "=" expresion   (* asignación a campo de struct *)

sentencia_vacia  ::= NEWLINE

(* Tipos *)
tipo             ::= tipo_primitivo
                   | IDENTIFICADOR                     (* struct definido por usuario *)
                   | "Canal" "<" tipo ">"
                   | "Resultado" "<" tipo "," tipo ">"
                   | "Opcion" "<" tipo ">"
                   | "&" tipo                         (* préstamo inmutable *)
                   | "&mut" tipo                      (* préstamo mutable *)
                   | "[" tipo "]"                     (* array *)
                   | "funcion" "(" [ tipos ] ")" "->" tipo
                   | "rc" tipo                        (* conteo de referencias *)
                   | "arc" tipo                       (* conteo atómico *)
                   | "débil" tipo                     (* referencia débil *)

tipo_primitivo   ::= "entero"  | "int"
                   | "decimal" | "real" | "float"
                   | "booleano" | "bool"
                   | "texto"   | "cadena" | "string"
                   | "caracter" | "char"
                   | "nulo"    | "void"
                   | "puntero" | "ptr"
                   | "tensor"  (* tipo nativo de Synapse *)

tipos            ::= tipo { "," tipo }

(* Expresiones *)
expresion        ::= expresion_logica

expresion_logica ::= expresion_rel { ("y" | "o" | "and" | "or") expresion_rel }*

expresion_rel    ::= expresion_arit { ("==" | "!=" | "<" | ">" | "<=" | ">=") expresion_arit }*

expresion_arit   ::= termino { ("+" | "-") termino }*

termino          ::= factor { ("*" | "/" | "%") factor }*

factor           ::= [ "-" | "!" | "no" ] primario

primario         ::= numero
                   | cadena_literal
                   | IDENTIFICADOR
                   | llamada_funcion
                   | tensor
                   | "(" expresion ")"
                   | "[" [ expresiones ] "]"
                   | IDENTIFICADOR "." IDENTIFICADOR      (* acceso a campo *)
                   | "&" IDENTIFICADOR                   (* préstamo *)
                   | "&mut" IDENTIFICADOR
                   | "?" IDENTIFICADOR                   (* propagación de error *)

llamada_funcion  ::= IDENTIFICADOR "(" [ argumentos ] ")"
argumentos       ::= expresion { "," expresion }

tensor           ::= "tensor" "(" expresion "," expresion ")"
                     (* Crea un tensor de dimensiones [filas, columnas] *)

expresiones      ::= expresion { "," expresion }

numero           ::= [ "-" ] DIGITO+ [ "." DIGITO+ ] [ "e" [ "-" ] DIGITO+ ]
cadena_literal   ::= '"' { caracter_escapado | cualquier_caracter } '"'
caracter_escapado ::= "\n" | "\t" | "\r" | "\\" | "\"" | "\u" HEX HEX HEX HEX

IDENTIFICADOR    ::= [A-Za-z_] [A-Za-z0-9_]*
DIGITO           ::= [0-9]
NEWLINE          ::= "\n" | "\r\n"
INDENT           ::= 4 espacios (inyectado por el lexer)
DEDENT           ::= (inyectado por el lexer)
EOF              ::= fin de archivo
```

---

## 3. TABLA DE PALABRAS RESERVADAS (MULTI‑IDIOMA)

El lexer utiliza diccionarios por idioma. Los TokenID son universales, lo que permite la arquitectura poliglota del ecosistema.

| TokenID | Español (es) | Inglés (en) | Francés (fr) | Portugués (pt) |
|---------|--------------|-------------|--------------|----------------|
| T_FUNCION | funcion | function | fonction | funcao |
| T_RETORNAR | retornar | return | retourner | retornar |
| T_SI | si | if | si | se |
| T_SINO | sino | else | sinon | senao |
| T_MIENTRAS | mientras | while | tantque | enquanto |
| T_PARA | para | for | pour | para |
| T_LANZAR | lanzar | spawn | lancer | lancar |
| T_RECUPERAR | recuperar | recover | recuperer | recuperar |
| T_ESCUCHAR | escuchar | listen | ecouter | escutar |
| T_IMPORTAR | importar | import | importer | importar |
| T_ESTRUCTURA | estructura | struct | structure | estrutura |
| T_CONSTANTE | constante | const | constante | constante |
| T_INSEGURO | inseguro | unsafe | non_securise | inseguro |
| T_EXTERNO | externo | extern | externe | externo |
| T_COINCIDIR | coincidir | match | correspondre | coincidir |
| T_REQUIERE | requiere | requires | exige | requer |
| T_GARANTIZA | garantiza | ensures | garantit | garante |
| T_LET | let | let | let | let |
| T_TIPO | tipo | type | type | tipo |
| T_TENSOR | tensor | tensor | tenseur | tensor |
| T_CANAL | canal | channel | canal | canal |
| T_NULO | nulo | null | nul | nulo |
| T_VERDADERO | verdadero | true | vrai | verdadeiro |
| T_FALSO | falso | false | faux | falso |
| T_OK | ok | ok | ok | ok |
| T_ERR | err | err | err | err |
| T_ALGUN | algun | some | some | algum |
| T_NINGUNO | ninguno | none | aucun | nenhum |
| T_ROMBER | romper | break | casser | quebrar |
| T_SIGUIENTE | siguiente | continue | continuer | continuar |
| T_MODULO | modulo | module | module | modulo |
| T_AND | y | and | et | e |
| T_OR | o | or | ou | ou |
| T_NOT | no | not | pas | nao |
| T_DELEGAR | delegar | delegate | déléguer | delegar |
| T_EXPORT | @export | @export | @export | @export |
| T_RC | rc | rc | rc | rc |
| T_ARC | arc | arc | arc | arc |
| T_DEBIL | débil | weak | faible | fraco |

---

## 4. TIPOS PRIMITIVOS Y ALGEBRAICOS

### 4.1. Tipos Primitivos

| Tipo Sintáctico | Semántica | Tamaño (ABI) | Notas |
|-----------------|-----------|--------------|-------|
| `entero` / `int` | Entero con signo de 64 bits | 8 bytes | Alias de `int64_t` |
| `decimal` / `float` / `real` | Punto flotante doble precisión | 8 bytes | Alias de `double` |
| `booleano` / `bool` | Booleano lógico | 1 byte | `verdadero` / `falso` |
| `texto` / `cadena` / `string` | Cadena UTF-8 segura (longitud + buffer) | 16 bytes | No termina en `\0` internamente, se convierte para FFI |
| `caracter` / `char` | Carácter UTF-8 (punto de código) | 1-4 bytes | Alias de `char` (C) |
| `nulo` / `void` | Ausencia de valor | 0 bytes | Solo para funciones sin retorno |
| `puntero` / `ptr` | Puntero opaco (`void*`) | 8 bytes | Solo dentro de `inseguro` |
| `tensor` | Matriz multidimensional de flotantes | Estructura variable | Tipo nativo para IA |

### 4.2. Tipos Algebraicos (Predefinidos en el Prelude)

```synapse
tipo Resultado<T, E> = ok(T) | err(E)
tipo Opcion<T> = algun(T) | ninguno
```

**Regla Semántica:** El uso de estos tipos exige de manera obligatoria la instrucción de control `coincidir`. Omitir un caso en la coincidencia genera un error de compilación estático (`ERR_SEM_EXHAUSTIVE_MATCH_REQUIRED`).

### 4.3. Tipos Compuestos

- **Arrays:** `[T]` (tamaño fijo en tiempo de compilación).
- **Listas:** `Lista<T>` (dinámica, definida en la biblioteca estándar).
- **Mapas:** `Mapa<K,V>` (diccionario, definido en la biblioteca estándar).
- **Canales:** `Canal<T>` (primitiva de concurrencia).
- **Punteros y referencias:** `&T` (préstamo inmutable), `&mut T` (préstamo mutable).
- **Conteo de referencias:** `rc<T>` (no atómico), `arc<T>` (atómico), `débil<T>` (débil).

---

## 5. CONTRATOS LÓGICOS (`requiere` / `garantiza`)

### 5.1. Semántica Formal

- **`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas.
- **`garantiza`:** Se evalúa inmediatamente antes de cada `retornar`. La variable `_resultado_` contiene el valor que se va a retornar.

### 5.2. Ejemplo

```synapse
funcion dividir(a: entero, b: entero) -> entero:
    requiere:
        b != 0
    garantiza:
        _resultado_ * b + (a % b) == a
    retornar a / b
```

### 5.3. Modos de Compilación

| Modo | Comportamiento |
|------|----------------|
| `debug` (default) | Las aserciones se compilan como `assert()` en C. Fallo → SIGABRT. |
| `release` | Se define `#define NDEBUG` en el C generado. Las aserciones se eliminan (costo cero). |
| `--safe` | Se activa verificación formal (ATP engine) en lugar de aserciones en tiempo de ejecución. |

---

## 6. PRECEDENCIA DE OPERADORES

| Nivel | Operadores | Asociatividad |
|-------|------------|---------------|
| 1 (máxima) | `f(x)` (llamada), `canal ->` (recibir), `.` (acceso a campo) | Izquierda |
| 2 | `-` (unario), `!`, `no`, `&`, `&mut` | Derecha |
| 3 | `*`, `/`, `%` | Izquierda |
| 4 | `+`, `-` | Izquierda |
| 5 | `<`, `>`, `<=`, `>=` | Izquierda |
| 6 | `==`, `!=` | Izquierda |
| 7 | `y`, `and` | Izquierda |
| 8 | `o`, `or` | Izquierda |
| 9 (mínima) | `=`, `<-` (enviar canal) | Derecha |

---

## 7. EL ÁRBOL DE SINTAXIS ABSTRACTA (AST)

### 7.1. Estructura Base del Nodo

El AST de Synapse se serializa internamente en estructuras de nodos fuertemente tipadas, convertibles a formato `.syn.json` para herramientas de migración y análisis estático.

```c
// Estructura base del nodo en C (para el runtime)
typedef struct Nodo {
    int tipo;               // NODO_PROGRAMA, NODO_FUNCION, NODO_ESTRUCTURA, ...
    int linea;
    int columna;
    char* archivo;          // Ruta del archivo fuente
    struct Nodo* siguiente; // Linked-list (hermanos)
    union {
        struct {
            char nombre[64];
            int num_params;
            struct Nodo* params;
            struct Nodo* cuerpo;
            struct Nodo* contratos;
        } funcion;
        struct {
            struct Nodo* condicion;
            struct Nodo* cuerpo_si;
            struct Nodo* cuerpo_sino;
        } si;
        struct {
            char nombre[64];
            struct Nodo* expr;
        } asignacion;
        struct {
            char nombre[64];
            struct Nodo* args;
        } llamada;
        struct {
            char nombre[64];
            struct Nodo* campos;
        } estructura;
        // ... más uniones para cada tipo de nodo
    };
} Nodo;
```

### 7.2. Constantes de Tipo de Nodo (Extracto)

| Constante | Valor | Descripción |
|-----------|-------|-------------|
| `NODO_PROGRAMA` | 1 | Raíz del archivo |
| `NODO_FUNCION` | 2 | Definición de función |
| `NODO_SI` | 3 | Condicional `si` |
| `NODO_MIENTRAS` | 4 | Bucle `mientras` |
| `NODO_RETORNAR` | 5 | Sentencia `retornar` |
| `NODO_ASIGNACION` | 6 | Asignación `=` |
| `NODO_LLAMADA` | 8 | Llamada a función |
| `NODO_ESTRUCTURA` | 13 | Definición de estructura |
| `NODO_CANAL` | 22 | Creación de canal |
| `NODO_CONTRATO` | 46 | Bloque `requiere`/`garantiza` |
| `NODO_PARA` | 45 | Bucle `para` |
| `NODO_LANZAR` | 47 | `lanzar` (spawn) |
| `NODO_ESCUCHAR` | 48 | `escuchar` (listen) |
| `NODO_RECUPERAR` | 49 | `recuperar` |
| `NODO_TENSOR` | 50 | Creación de tensor |
| `NODO_IMPORT` | 51 | Importación |
| `NODO_EXPORT` | 52 | Exportación (@export) |
| `NODO_INSEGURO` | 53 | Bloque `inseguro` |
| `NODO_COINCIDIR` | 54 | `coincidir` (match) |
| `NODO_DELEGAR` | 55 | `delegar` (propagación de error) |

### 7.3. AST Aplanado (`SemNodo[]`)

Para el análisis semántico, la linked-list se aplana a un array contiguo. Este es el **AST canónico unificado** que comparten Synapse y Syquex.

```c
#define F8_MAX_NODOS 65536

typedef struct {
    int tipo_nodo;
    int linea;
    int columna;
    char* archivo;
    int owner_id;           // ID del propietario (para ownership)
    int scope_id;           // ID del ámbito (para scopes)
    bool is_owned;          // Indica si el nodo es propietario de memoria
    bool es_prestado_inmutable;
    bool es_prestado_mutable;
    bool es_transferido;    // Para movimiento (->)
    union {
        struct {
            char nombre[64];
            int num_params;
            int* params_ids;    // Índices de los parámetros en el array
        } funcion;
        struct {
            int condicion_id;
            int cuerpo_si_id;
            int cuerpo_sino_id;
        } si;
        struct {
            char nombre[64];
            int expr_id;
        } asignacion;
        // ... igual que Nodo pero sin punteros (solo datos planos)
    };
} SemNodo;
```

**Regla de determinismo:** La tabla de símbolos se serializa y se itera siempre en orden lexicográfico por nombre para garantizar que el código generado y los hashes de caché sean idénticos en todas las ejecuciones.

---

## 8. ANÁLISIS SEMÁNTICO Y SISTEMA DE TIPOS

### 8.1. Ejecución en Tres Fases

El analizador semántico opera estrictamente en tres pasadas secuenciales:

1. **Pasada 1 (Estructuras y Tipos Globales):** Recorre el AST para registrar todas las definiciones de estructuras, tipos algebraicos y constantes globales en la tabla de símbolos principal.

2. **Pasada 2 (Firmas de Funciones):** Analiza las cabeceras de todas las funciones, validando los tipos de los parámetros, los tipos de retorno y los contratos lógicos (`requiere`/`garantiza`).

3. **Pasada 3 (Cuerpos de Código y Verificación de Ownership):** Analiza sintácticamente los bloques internos de cada función, evaluando expresiones, asignaciones, llamadas y flujos de control. Además, verifica el ownership, el borrowing y los lifetimes, y ejecuta el motor ATP en modo `--safe`.

### 8.2. Inferencia de Tipos (Hindley‑Milner)

Synapse utiliza un algoritmo de inferencia de tipos basado en **Hindley‑Milner** (algoritmo W). Las variables de tipo se representan como `TVar(id)`. La unificación incluye *occurs check* para evitar tipos recursivos. Si una expresión tiene tipo ambiguo (ej. `[]`), se emite `ERR_SEM_TYPE_AMBIGUOUS`.

**Representación interna:**

```c
typedef enum {
    TIPO_PRIMITIVO,
    TIPO_FUNCION,
    TIPO_ESTRUCTURA,
    TIPO_VARIABLE,
    TIPO_ALGEBRAICO,
    TIPO_CANAL,
    TIPO_TENSOR,
    TIPO_PUNTERO,
    TIPO_REFERENCIA
} TipoKind;

typedef struct Tipo {
    TipoKind kind;
    union {
        struct { int primitivo_id; } primitivo;
        struct { struct Tipo* retorno; struct Tipo** params; int num_params; } funcion;
        struct { char nombre[64]; } estructura;
        struct { int var_id; } variable;
        struct { struct Tipo* tipo_base; } canal;
        // ...
    };
} Tipo;
```

### 8.3. Tipos Algebraicos de Datos (ADTs)

El sistema de tipos incorpora uniones etiquetadas nativas para representar estados de éxito o fallo:

- `Resultado<T, E>`: Envuelve un valor de éxito tipo `T` (`ok`) o un error tipo `E` (`err`).
- `Opcion<T>`: Envuelve un valor existente `T` (`algun`) o la ausencia de valor (`ninguno`).

**Regla Semántica:** El uso de estos tipos exige de manera obligatoria la instrucción de control `coincidir`. Omitir un caso en la coincidencia genera un error de compilación estático (`ERR_SEM_EXHAUSTIVE_MATCH_REQUIRED`).

---

## 9. EL PACTO: SEGURIDAD DE MEMORIA (OWNERSHIP & BORROWING)

Synapse prescinde totalmente de un Recolector de Basura (Garbage Collector) y prohíbe el uso de asignación manual de memoria (`malloc`/`free`) en el código de usuario. La gestión de memoria se rige por un modelo estricto de **Posesión Única**.

### 9.1. Reglas de Posesión (Ownership)

1. Cada recurso en memoria (heap, canal, archivo, tensor) tiene un **único propietario** (una variable o ámbito que lo enlaza).

2. Cuando el propietario actual sale de su ámbito de visibilidad (*scope*), el compilador inyecta de forma automática y determinista el código de liberación en el emisor C (RAII estático).

3. **Semántica de Movimiento (*Move Semantics*):** Al asignar una variable propietaria a otra o pasarla como argumento de función por valor, la posesión se transfiere (*move*). La variable original queda invalidada en el ámbito origen.

4. **Detección de Use‑After‑Move:** Si el analizador semántico detecta que una variable invalidada por un *move* previo es consultada o reutilizada, aborta la compilación de inmediato con el error crítico `ERR_MEM_USE_AFTER_MOVE`.

### 9.2. Préstamo (Borrowing)

| Tipo de préstamo | Sintaxis | Mutabilidad | Regla |
|------------------|----------|-------------|-------|
| Inmutable | `&T` | Solo lectura | Múltiples préstamos inmutables simultáneos permitidos. |
| Mutable | `&mut T` | Lectura + escritura | Solo un préstamo mutable a la vez, y no puede coexistir con inmutables. |

### 9.3. Análisis de Lifetimes

El análisis de lifetimes determina el tiempo de vida de cada referencia. La representación interna es:

```c
typedef enum {
    LT_ESTATICO,       // Toda la vida del programa
    LT_LOCAL,          // Scope de bloque (índice)
    LT_PARAMETRICO,    // Parámetro de función
    LT_ELIDIDO         // Inferido automáticamente
} LifetimeKind;

typedef struct {
    LifetimeKind kind;
    int index;
    char* nombre;
} Lifetime;
```

**Pasos del análisis:**

1. **Recolección:** Recorrer AST para identificar variables y scopes.
2. **Asignación:** Asignar lifetimes a cada variable y préstamo.
3. **Restricciones:** Recolectar restricciones de uso (ej. `'a` debe vivir al menos tanto como `'b`).
4. **Resolución:** Resolver el grafo de restricciones (unificación de regiones).
5. **Verificación:** Confirmar que no hay ciclos y que ningún lifetime excede el ámbito de su propietario.

**Errores posibles:**
- `ERR_MEM_LIFETIME_MISMATCH`: Un préstamo vive más que el valor prestado.
- `ERR_MEM_LIFETIME_CYCLE`: Ciclo en la dependencia de lifetimes.

---

## 10. MANEJO DE ERRORES Y TAXONOMÍA

### 10.1. Categorías de Errores

| Categoría | Rango | Ejemplo |
|-----------|-------|---------|
| Léxico | `ERR_LEX_*` | `ERR_LEX_TAB_DETECTED`, `ERR_LEX_MISSING_LANG` |
| Sintáctico | `ERR_SYNTAX_*` | `ERR_SYNTAX_EXPECTED_TOKEN`, `ERR_INDENT_INVALID` |
| Semántico | `ERR_SEM_*` | `ERR_SEM_TYPE_AMBIGUOUS`, `ERR_SEM_REDEFINICION` |
| Memoria | `ERR_MEM_*` | `ERR_MEM_USE_AFTER_MOVE`, `ERR_MEM_LIFETIME_MISMATCH` |
| Caché | `ERR_CACHE_*` | `ERR_CACHE_CORRUPT`, `ERR_CACHE_VERSION_MISMATCH` |
| Verificación (ATP) | `ERR_ATP_*` | `ERR_ATP_TAUTOLOGY_FAILED`, `ERR_ATP_NON_TERMINATING`, `ERR_ATP_TIMEOUT` |
| Axon | `ERR_AXON_*` | `ERR_AXON_COMPROMISED`, `ERR_AXON_VERSION` |

### 10.2. Manejo de Errores en el Compilador

- El compilador nunca debe detenerse en el primer error; debe continuar analizando para detectar tantos errores como sea posible.
- Los errores se reportan a través del `DiagnosticManager` con mensajes en el idioma del archivo (según `#lang:`).
- Cada error incluye: código de error, ubicación exacta (archivo, línea, columna), mensaje explicativo y, cuando sea posible, sugerencias de corrección.

---

## 11. INTEGRACIÓN CON SYQUEX Y OPENSYN

### 11.1. AST Canónico Unificado

Syquex traduce su AST al mismo `SemNodo[]` que Synapse. Esto permite:

- Compartir el 100% del backend (generación de C/LLVM/WASM).
- Compatibilidad binaria absoluta entre ambos lenguajes.
- Herencia del optimizador, sanitizadores y motor ATP.

### 11.2. Exportación para FFI

La directiva `@export` permite que funciones de Synapse sean visibles desde Syquex y desde otros lenguajes (Python, Java, TypeScript) mediante bindings generados automáticamente.

```synapse
@export(python) fn procesar(datos: Lista<Entero>) -> Resultado<Flotante, Error>
```

### 11.3. OpenSyn como Asistente

OpenSyn opera sobre el AST unificado, por lo que puede:
- Explicar código Synapse o Syquex.
- Generar código Synapse o Syquex a partir de descripciones en lenguaje natural.
- Transpilar código Python a Syquex.
- Generar bindings automáticos para librerías C.

---

## 12. PRUEBAS OBLIGATORIAS PARA ESTA ETAPA

| Test | Comando | Criterio |
|------|---------|----------|
| Lexer multi‑idioma | `pytest tests/unit/test_lexer.py -v` | 100% pass, >95% cobertura |
| Parser EBNF | `pytest tests/unit/test_parser.py -v` | 100% pass, >95% cobertura |
| Contratos requiere/garantiza | `pytest tests/integration/test_contracts.py -v` | 100% pass |
| Tipos algebraicos (match exhaustivo) | `pytest tests/integration/test_match.py -v` | Detección de ERR_SEM_EXHAUSTIVE_MATCH_REQUIRED |
| Ownership (move) | `pytest tests/integration/test_ownership.py -v` | Detección de ERR_MEM_USE_AFTER_MOVE |
| Borrowing checker | `pytest tests/integration/test_borrowing.py -v` | 100% pass |
| Lifetimes | `pytest tests/integration/test_lifetimes.py -v` | 0 errores de compilación |
| Inferencia de tipos (Hindley‑Milner) | `pytest tests/unit/test_type_inference.py -v` | Casos de inferencia básica y polimórfica |
| Serialización AST | `pytest tests/unit/test_ast_serialization.py -v` | Serialización y deserialización correcta a `.syn.json` |

---

## 13. EJEMPLO COMPLETO

**Código fuente (`programa.syn`):**

```synapse
#lang: es

funcion sumar(a: int, b: int) -> int:
    retornar a + b

funcion principal() -> nulo:
    resultado = sumar(5, 3)
    log("Resultado: ", resultado)
```

**AST simplificado (JSON):**

```json
{
  "tipo": "Programa",
  "declaraciones": [
    {
      "tipo": "FuncionDef",
      "nombre": "sumar",
      "parametros": [
        { "nombre": "a", "tipo": "int", "es_transferencia": false },
        { "nombre": "b", "tipo": "int", "es_transferencia": false }
      ],
      "tipo_retorno": "int",
      "contratos": null,
      "cuerpo": {
        "tipo": "Bloque",
        "sentencias": [
          {
            "tipo": "SentenciaRetornar",
            "es_transferencia": false,
            "valor": {
              "tipo": "ExpresionArit",
              "operador": "+",
              "izquierda": { "tipo": "Identificador", "nombre": "a" },
              "derecha": { "tipo": "Identificador", "nombre": "b" }
            }
          }
        ]
      }
    },
    {
      "tipo": "FuncionDef",
      "nombre": "principal",
      "parametros": [],
      "tipo_retorno": "nulo",
      "contratos": null,
      "cuerpo": {
        "tipo": "Bloque",
        "sentencias": [
          {
            "tipo": "Asignacion",
            "variable": "resultado",
            "expresion": {
              "tipo": "LlamadaFuncion",
              "nombre": "sumar",
              "argumentos": [
                { "tipo": "LiteralNumero", "valor": 5 },
                { "tipo": "LiteralNumero", "valor": 3 }
              ]
            }
          },
          {
            "tipo": "LlamadaFuncion",
            "nombre": "log",
            "argumentos": [
              { "tipo": "LiteralCadena", "valor": "Resultado: " },
              { "tipo": "Identificador", "nombre": "resultado" }
            ]
          }
        ]
      }
    }
  ]
}
```

---

## 14. SIGUIENTES PASOS

Con la sintaxis y semántica de Synapse definidas, el siguiente manual (Manual 3) se centrará en la **sintaxis y semántica de Syquex**, el lenguaje de alto nivel hermano de Synapse.

---

*Este manual proporciona la base sintáctica y semántica de Synapse. La implementación del compilador debe seguir fielmente esta especificación para garantizar la compatibilidad y el determinismo.*

**Fin del Manual 2**