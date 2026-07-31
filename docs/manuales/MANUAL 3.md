MANUAL 3: ARQUITECTURA DEL COMPILADOR (PIPELINE) — COMPLETO (con adición 3.6.4)

Archivo: 03\_COMPILADOR\_PIPELINE.md

Versión: 5.1.1-industrial

Propósito: Describir las 5 etapas del compilador, el AST, la tabla de símbolos, el sistema de errores, la compilación incremental y el motor ATP con guardas de seguridad.



3.1 Las 5 Etapas del Pipeline

text

┌─────────────┐

│ fuente.syn  │ (UTF-8)

└──────┬──────┘

&#x20;      ▼

┌─────────────────────────────────────────────────────────────┐

│ ETAPA 1: LEXER (lexer.syn)                                  │

│  - Lee caracteres, inyecta INDENT/DEDENT por indentación.   │

│  - Detecta #lang: y selecciona diccionario multi-idioma.   │

│  - Salida: flujo de tokens (TokenID + valor + ubicación).  │

└─────────────────────────────────────────────────────────────┘

&#x20;      ▼

┌─────────────────────────────────────────────────────────────┐

│ ETAPA 2: PARSER (parser.syn)                                │

│  - Descenso recursivo puro.                                 │

│  - Construye AST (linked-list de Nodo\*).                   │

│  - Salida: AST enlazado.                                   │

└─────────────────────────────────────────────────────────────┘

&#x20;      ▼

┌─────────────────────────────────────────────────────────────┐

│ ETAPA 3: ANALIZADOR SEMÁNTICO (analizador\_semantico.syn)   │

│  - 3 pasadas: 1) Estructuras, 2) Firmas, 3) Cuerpos.       │

│  - Inferencia de tipos (Hindley-Milner).                   │

│  - Verificación de Ownership y Lifetimes.                  │

│  - Motor ATP (modo --safe) con guardas de profundidad.    │

│  - Salida: SemNodo\[] aplanado + Tabla de Símbolos.         │

└─────────────────────────────────────────────────────────────┘

&#x20;      ▼

┌─────────────────────────────────────────────────────────────┐

│ ETAPA 4: GENERADOR (generator.syn / llvm\_backend.syn)      │

│  - Traduce SemNodo\[] a código C estándar o LLVM IR.        │

│  - Emite funciones en orden alfabético (determinismo).     │

│  - Inyecta contratos como assert() o llvm.assume.          │

│  - Salida: synapse\_unity.c (o .ll).                       │

└─────────────────────────────────────────────────────────────┘

&#x20;      ▼

┌─────────────────────────────────────────────────────────────┐

│ ETAPA 5: BACKEND (GCC/Clang/LLVM/emcc)                     │

│  - Compila .c/.ll + runtime modular (core, net, quantum).  │

│  - Enlaza con -lpthread -lm (y -lws2\_32 en Windows).     │

│  - Salida: binario nativo (.exe, ELF) o WASM (.wat/.wasm).│

└─────────────────────────────────────────────────────────────┘

3.2 El AST (Árbol de Sintaxis Abstracta)

Estructura base del Nodo (C):



c

typedef struct Nodo {

&#x20;   int tipo;               // NODO\_PROGRAMA, NODO\_FUNCION, ...

&#x20;   int linea;

&#x20;   int columna;

&#x20;   struct Nodo\* siguiente; // Linked-list (hermanos)

&#x20;   union {

&#x20;       struct {

&#x20;           char nombre\[64];

&#x20;           int num\_params;

&#x20;           struct Nodo\* params;

&#x20;           struct Nodo\* cuerpo;

&#x20;           struct Nodo\* contratos;

&#x20;       } funcion;

&#x20;       struct {

&#x20;           struct Nodo\* condicion;

&#x20;           struct Nodo\* cuerpo\_si;

&#x20;           struct Nodo\* cuerpo\_sino;

&#x20;       } si;

&#x20;       struct {

&#x20;           char nombre\[64];

&#x20;           struct Nodo\* expr;

&#x20;       } asignacion;

&#x20;       struct {

&#x20;           char nombre\[64];

&#x20;           struct Nodo\* args;

&#x20;       } llamada;

&#x20;       // ... más uniones para cada tipo de nodo

&#x20;   };

} Nodo;

Constantes de tipo de nodo (tabla completa — 46 tipos reales definidos en nucleo/parser_constantes.syn):



Constante	Valor	Descripción

NODO\_PROGRAMA	1	Raíz del archivo

NODO\_FUNCION	2	Definición de función

NODO\_SI	3	Condicional si

NODO\_MIENTRAS	4	Bucle mientras

NODO\_RETORNAR	5	Sentencia retornar

NODO\_EXPR	6	Sentencia de expresión

NODO\_ASIGNACION	7	Asignación =

NODO\_IDENTIFICADOR	8	Referencia a identificador

NODO\_NUMERO	9	Literal numérico (entero)

NODO\_DECIMAL	10	Literal numérico (decimal)

NODO\_CADENA\_LIT	11	Literal de cadena

NODO\_BINARIA	12	Operación binaria (+, -, *, /, ...)

NODO\_UNARIA	13	Operación unaria (-, !, ...)

NODO\_LLAMADA	14	Llamada a función

NODO\_PARAMETRO	15	Parámetro de función

NODO\_ESTRUCTURA	16	Definición de estructura

NODO\_IMPORTAR	17	Sentencia importar

NODO\_LANZAR	18	Sentencia lanzar (spawn)

NODO\_ESCUCHAR	19	Sentencia escuchar (listen)

NODO\_ROMPER	20	Sentencia romper (break)

NODO\_SIGUIENTE	21	Sentencia siguiente (continue)

NODO\_BOOLEANO	22	Literal booleano (verdadero/falso)

NODO\_CONSTANTE	23	Declaración de constante

NODO\_INSEGURO	24	Bloque inseguro

NODO\_IMPORTAR\_C	25	Importar código C

NODO\_EXTERNO	26	Declaración externa

NODO\_RECUPERAR	27	Sentencia recuperar (recover)

NODO\_TENSOR	28	Expresión tensor

NODO\_INDICE	29	Acceso por índice []

NODO\_TRANSFERIDO	30	Argumento transferido (ownership move)

NODO\_ACCESO\_CAMPO	31	Acceso a campo (objeto.campo)

NODO\_ASIGNACION\_CAMPO	32	Asignación a campo

NODO\_PARRAFO	33	Párrafo (bloque de sentencias)

NODO\_DECLARACION	34	Declaración de variable

NODO\_LOG	35	Llamada de log

NODO\_PUNTERO	36	Tipo puntero

NODO\_DEREF	37	Desreferencia de puntero

NODO\_COINCIDIR	38	Sentencia coincidir (match)

NODO\_CASO	39	Caso de coincidir

NODO\_ASM	40	Bloque asm

NODO\_CANAL\_CREAR	41	Creación de canal

NODO\_ENVIAR\_CANAL	42	Envío a canal

NODO\_RECIBIR\_CANAL	43	Recepción de canal

NODO\_VACIO	44	Nodo vacío

NODO\_PARA	45	Bucle para

NODO\_CONTRATO	46	Bloque requiere/garantiza

AST Aplanado (SemNodo\[]): Para el análisis semántico, la linked-list se aplana a un array contiguo:



c

\#define F8\_MAX\_NODOS 65536

typedef struct {

&#x20;   int tipo\_nodo;

&#x20;   int linea, columna;

&#x20;   int owner\_id;

&#x20;   int scope\_id;

&#x20;   bool is\_owned;

&#x20;   bool es\_prestado\_inmutable;

&#x20;   bool es\_prestado\_mutable;

&#x20;   union {

&#x20;       struct { char nombre\[64]; int num\_params; } funcion;

&#x20;       // ... igual que Nodo pero sin punteros (solo datos planos)

&#x20;   };

} SemNodo;

3.3 El Analizador Semántico (3 Pasadas)

c

void analizar(AnalizadorSemanticoEst\* est) {

&#x20;   // PASADA 1: ESTRUCTURAS Y TIPOS GLOBALES

&#x20;   for (int i = 0; i < est->total\_nodos; i++) {

&#x20;       if (est->nodos\[i].tipo\_nodo == NODO\_ESTRUCTURA) {

&#x20;           \_sem\_registrar\_struct(est, \&est->nodos\[i]);

&#x20;       }

&#x20;   }

&#x20;   // PASADA 2: FIRMAS DE FUNCIONES (sin cuerpos)

&#x20;   for (int i = 0; i < est->total\_nodos; i++) {

&#x20;       if (est->nodos\[i].tipo\_nodo == NODO\_FUNCION) {

&#x20;           \_sem\_registrar\_funcion(est, \&est->nodos\[i]);

&#x20;       }

&#x20;   }

&#x20;   // PASADA 3: CUERPOS DE FUNCIÓN + OWNERSHIP + LIFETIMES + ATP

&#x20;   for (int i = 0; i < est->total\_nodos; i++) {

&#x20;       if (est->nodos\[i].tipo\_nodo == NODO\_FUNCION) {

&#x20;           \_sem\_analizar\_cuerpo(est, \&est->nodos\[i]);

&#x20;           if (est->modo\_safe) {

&#x20;               atp\_verificar\_funcion(est, \&est->nodos\[i]);

&#x20;           }

&#x20;       }

&#x20;   }

}

Tabla de Símbolos (estructura interna):



c

typedef struct {

&#x20;   char nombre\[64];

&#x20;   int tipo;           // TIPO\_ENTERO, TIPO\_FUNCION, TIPO\_ESTRUCTURA, ...

&#x20;   int scope\_id;

&#x20;   int owner\_id;

&#x20;   bool es\_movido;

&#x20;   int num\_referencias;

&#x20;   bool tiene\_mut\_borrow;

} Simbolo;

Regla de determinismo: La tabla de símbolos se serializa y se itera siempre en orden lexicográfico por nombre para garantizar que el código generado y los hashes de caché sean idénticos en todas las ejecuciones.



Inferencia de Tipos (Hindley-Milner): Variables de tipo se representan como TVar(id). Unificación con occurs check. Si una expresión tiene tipo ambiguo (ej. \[]), se emite ERR\_SEM\_TYPE\_AMBIGUOUS.



3.4 Sistema de Caché Incremental (v5.0)

Clave de caché: SHA-256(contenido\_archivo + hash\_dependencias (ordenadas) + flags\_compilacion + version\_compilador). Importante: Las dependencias se ordenan alfabéticamente antes de ser hasheadas.



Estructura de la entrada de caché:



c

typedef struct {

&#x20;   char key\[65];              // SHA-256 hex

&#x20;   char ast\_hash\[65];

&#x20;   char\* codigo\_c;

&#x20;   size\_t codigo\_len;

&#x20;   char\*\* dependencias;       // Lista ordenada alfabéticamente

&#x20;   int num\_deps;

&#x20;   char flags\[256];

&#x20;   time\_t timestamp;

} CacheEntry;

Flujo:



Calcular clave.



Buscar en \~/.synapse/cache/.



Si existe y el ast\_hash coincide → CACHÉ HIT (usar objeto compilado).



Si existe pero ast\_hash no coincide → CACHÉ STALE (recompilar y actualizar).



Si no existe → CACHÉ MISS (compilar y guardar).



3.5 Taxonomía de Errores del Compilador

Categoría	Rango	Ejemplo

Léxico	ERR\_LEX\_\*	ERR\_LEX\_TAB\_DETECTED, ERR\_LEX\_MISSING\_LANG

Sintáctico	ERR\_SYNTAX\_\*	ERR\_SYNTAX\_EXPECTED\_TOKEN, ERR\_INDENT\_INVALID

Semántico	ERR\_SEM\_\*	ERR\_SEM\_TYPE\_AMBIGUOUS, ERR\_SEM\_REDEFINICION

Memoria	ERR\_MEM\_\*	ERR\_MEM\_USE\_AFTER\_MOVE, ERR\_MEM\_LIFETIME\_MISMATCH

Caché	ERR\_CACHE\_\*	ERR\_CACHE\_CORRUPT, ERR\_CACHE\_VERSION\_MISMATCH

Verificación (ATP)	ERR\_ATP\_\*	ERR\_ATP\_TAUTOLOGY\_FAILED, ERR\_ATP\_NON\_TERMINATING, ERR\_ATP\_TIMEOUT

3.6 Motor de Verificación Formal (ATP) — Modo --safe

El motor ATP (Automated Theorem Proving) se activa con la flag --safe y opera como una extensión de la Pasada 3. Su objetivo es demostrar matemáticamente que los contratos (requiere / garantiza) se cumplen para todas las entradas posibles.



3.6.1 Flujo del ATP:



Extracción de Fórmulas: Convierte requiere y garantiza a lógica de primer orden.



Simbolización del Cuerpo: Traduce el AST de la función a una fórmula lógica.



Verificación de Contratos: Demuestra que precondición ∧ cuerpo → postcondición.



Terminación: Verifica que las funciones recursivas decrementan un well‑founded order (ej. n-1).



Ejecución Simbólica: Explora caminos críticos para detectar violaciones de contratos.



3.6.2 Guardas de Seguridad (Anti-Explosión Combinatoria):

Para evitar que el ATP consuma recursos infinitos en contratos complejos, se aplican las siguientes restricciones obligatorias:



max\_depth: Profundidad máxima de búsqueda en el árbol de resolución (por defecto 10, configurable con --atp-depth N).



timeout\_seconds: Tiempo límite de ejecución del ATP por función (por defecto 2 segundos, configurable con --atp-timeout S).



Si se excede el tiempo o la profundidad, el compilador emite ERR\_ATP\_TIMEOUT y aborta la compilación en modo --safe.



3.6.3 Estructuras y API (C):



c

// validate\_atp\_engine.c

typedef struct {

&#x20;   int max\_depth;          // Obligatorio: por defecto 10

&#x20;   int timeout\_seconds;    // Obligatorio: por defecto 2

&#x20;   int use\_arithmetic;

&#x20;   int use\_induction;

} ATPConfig;



ATPResult atp\_prove(const char\* pre, const char\* post, const char\* body);

int atp\_verify\_termination(const char\* function\_def);

3.6.4 Proof Bridge (Coq/Lean) — Adición v5.1.1-industrial



El motor ATP puede exportar los teoremas verificados (contratos, terminación) a lenguajes de prueba formales como Coq o Lean, permitiendo una verificación externa más profunda.



Exportación a Coq: Genera un archivo .v con las definiciones de las funciones y los lemas de los contratos.



Exportación a Lean: Genera un archivo .lean con teoremas y pruebas tácticas.



Comando: synapse build --safe --export-proof=coq main.syn o --export-proof=lean.



Estructura del bridge (C):



c

// nucleo/proof\_bridge.c

int proof\_bridge\_export\_coq(const char\* function\_name, const char\* pre, const char\* post, const char\* filename);

int proof\_bridge\_export\_lean(const char\* function\_name, const char\* pre, const char\* post, const char\* filename);

Test de validación:



bash

gcc -o test\_proof\_bridge validate\_formal\_proof.c -lm \&\& ./test\_proof\_bridge --test export\_coq

\# Verifica que el archivo .v generado es sintácticamente válido.

3.6.5 Tests Obligatorios para esta Etapa:



Test	Comando	Criterio

ATP Tautología simple	gcc -o test\_atp validate\_atp\_engine.c -lm \&\& ./test\_atp --test prove\_tautology	PASS

ATP Contrato factorial	./test\_atp --test verify\_factorial	PASS

ATP Detección de no-terminación	./test\_atp --test detect\_non\_termination	Detectar ERR\_ATP\_NON\_TERMINATING

ATP Timeout (protección)	./test\_atp --test timeout --timeout 1	Debe fallar con ERR\_ATP\_TIMEOUT

Ejecución simbólica	./test\_atp --test symbolic\_execution	PASS

Proof Bridge Coq	./test\_proof\_bridge --test export\_coq	Archivo .v generado y sintácticamente válido

Proof Bridge Lean	./test\_proof\_bridge --test export\_lean	Archivo .lean generado y sintácticamente válido

