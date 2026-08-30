# MANUAL 3: SINTAXIS Y SEMÁNTICA DE SYQUEX

**Archivo:** `03_SINTAXIS_Y_SEMANTICA_SYQUEX.md`  
**Versión:** 8.0.0-industrial  
**Propósito:** Definir la gramática formal del lenguaje Syquex, su sistema de tipos de alto nivel, las reglas semánticas (estructuras, métodos, manejo de errores algebraico, concurrencia), y la integración con el AST canónico de Synapse. Este manual establece las bases del frontend de productividad del ecosistema, diseñado para superar a Python en ergonomía y rendimiento.

---

## 1. DIRECTIVA DE ARCHIVO Y CODIFICACIÓN

### 1.1. Directiva de Idioma

Todo archivo fuente de Syquex **debe** comenzar con la directiva de idioma en la **línea 1**:

```syquex
#lang: es
```

Idiomas soportados: `es` (español), `en` (inglés), `fr` (francés), `pt` (portugués).

La directiva obliga al lexer a cargar el diccionario correspondiente. Si el archivo omite esta directiva, el lexer rechazará el archivo con el error `ERR_LEX_MISSING_LANG`.

### 1.2. Codificación

Todos los archivos fuente deben estar codificados en **UTF‑8 sin BOM**.

### 1.3. Comentarios

Syquex soporta los mismos comentarios que Synapse:
- **Comentarios de línea:** `//` hasta el final de la línea.
- **Comentarios de bloque:** `/* ... */`, anidables.

---

## 2. FILOSOFÍA DE SYQUEX VS SYNAPSE

Syquex es el **hermano de alto nivel** de Synapse. Mientras Synapse se enfoca en el control total de la memoria, el rendimiento extremo y el bare metal, Syquex se enfoca en la **productividad del desarrollador**, la claridad del código y la velocidad de escritura.

| Aspecto | Synapse | Syquex |
|---------|---------|--------|
| **Gestión de Memoria** | Manual (Ownership, Borrowing, Lifetimes) | Automática (Arenas + RC + Análisis de alcance) |
| **Curva de Aprendizaje** | Media-Alta | Baja (similar a Python) |
| **Tipado** | Estático inferido (Hindley-Milner) | Estático inferido (Hindley-Milner) |
| **Concurrencia** | Fibras + Canales | Fibras + Canales (misma implementación) |
| **Ecosistema** | Núcleo de sistemas | Aplicaciones, Web, GUI, Scripting |
| **Propósito** | Motores, Kernels, IA de alto rendimiento | APIs, GUI, Automatización, Prototipado |

**La regla de oro de Syquex:** El desarrollador nunca escribe `free`, `&`, `mut` o lifetimes explícitos. El compilador deduce todo automáticamente mediante análisis de alcance y gestión por arenas.

---

## 3. GRAMÁTICA FORMAL DE SYQUEX (EBNF COMPLETA)

La gramática de Syquex es más expresiva que la de Synapse, incorporando elementos de programación orientada a objetos (estructuras con métodos y constructores) y manejo de errores algebraico integrado.

```ebnf
(* Programa principal *)
programa          ::= lang_directive { declaracion } EOF
lang_directive    ::= "#lang:" IDENTIFICADOR NEWLINE

(* Declaraciones a nivel de módulo *)
declaracion       ::= importacion
                    | constante
                    | variable
                    | funcion
                    | estructura
                    | enumeracion
                    | tipo_sinonimo
                    | externo
                    | exportacion

importacion       ::= "importar" IDENTIFICADOR ("." IDENTIFICADOR)* [ "como" IDENTIFICADOR ] NEWLINE
constante         ::= "constante" IDENTIFICADOR "=" expresion NEWLINE
variable          ::= "variable" IDENTIFICADOR [ ":" tipo ] [ "=" expresion ] NEWLINE
tipo_sinonimo     ::= "tipo" IDENTIFICADOR "=" tipo NEWLINE

(* Funciones *)
funcion           ::= "funcion" IDENTIFICADOR "(" [ parametros ] ")" [ "->" tipo ] [ contratos ] ":" NEWLINE INDENT bloque DEDENT
                    | IDENTIFICADOR "(" [ parametros ] ")" "=" expresion   (* Función de una sola expresión *)

parametros        ::= parametro { "," parametro }
parametro         ::= IDENTIFICADOR [ ":" tipo ] [ "=" expresion ]   (* Valor por defecto *)

contratos         ::= "requiere" ":" NEWLINE INDENT expresion NEWLINE DEDENT
                    | "garantiza" ":" NEWLINE INDENT expresion NEWLINE DEDENT

(* Estructuras (Orientación a Objetos) *)
estructura        ::= "estructura" IDENTIFICADOR [ "(" IDENTIFICADOR ")" ]? ":" NEWLINE INDENT { miembro } DEDENT
miembro           ::= campo | metodo | constructor
campo             ::= IDENTIFICADOR ":" tipo [ "=" expresion ] NEWLINE
metodo            ::= "metodo" IDENTIFICADOR "(" [ parametros ] ")" [ "->" tipo ] ":" NEWLINE INDENT bloque DEDENT
constructor       ::= "crear" "(" [ parametros ] ")" ":" NEWLINE INDENT bloque DEDENT

(* Enumeraciones (Tipos Algebraicos) *)
enumeracion       ::= "enumeracion" IDENTIFICADOR ":" NEWLINE INDENT { caso_enum } DEDENT
caso_enum         ::= IDENTIFICADOR [ "(" tipo { "," tipo } ")" ] NEWLINE

(* FFI y Exportaciones *)
externo           ::= "externo" funcion | "externo" estructura | "externo" "constante" IDENTIFICADOR "=" STRING NEWLINE
exportacion       ::= "@export" "(" IDENTIFICADOR ")" funcion
                    | "@export" "(" IDENTIFICADOR ")" estructura

(* Bloques y sentencias *)
bloque           ::= { sentencia NEWLINE }
sentencia        ::= asignacion
                    | llamada_funcion
                    | retornar
                    | condicional_si
                    | bucle_mientras
                    | bucle_para
                    | bucle_para_rango
                    | lanzar
                    | escuchar
                    | coincidir
                    | intentar
                    | romper
                    | continuar
                    | expresion
                    | sentencia_vacia
                    | declaracion_variable_local

declaracion_variable_local ::= "let" IDENTIFICADOR [ ":" tipo ] [ "=" expresion ] NEWLINE

asignacion        ::= IDENTIFICADOR "=" expresion
                    | IDENTIFICADOR "." IDENTIFICADOR "=" expresion
                    | IDENTIFICADOR "[" expresion "]" "=" expresion

retornar          ::= "retornar" [ expresion ] [ "?" ]   (* "?" propaga el error como Resultado *)

condicional_si    ::= "si" expresion ":" NEWLINE INDENT bloque DEDENT [ "sino" ":" NEWLINE INDENT bloque DEDENT ]
bucle_mientras    ::= "mientras" expresion ":" NEWLINE INDENT bloque DEDENT
bucle_para        ::= "para" IDENTIFICADOR "=" expresion ".." expresion [ "paso" expresion ] ":" NEWLINE INDENT bloque DEDENT
bucle_para_rango  ::= "para" IDENTIFICADOR "en" expresion ":" NEWLINE INDENT bloque DEDENT   (* Iteración sobre lista o rango *)

lanzar            ::= "lanzar" llamada_funcion
escuchar          ::= "escuchar" IDENTIFICADOR ":" NEWLINE INDENT bloque DEDENT

(* Pattern Matching *)
coincidir         ::= "coincidir" expresion ":" NEWLINE INDENT { caso } DEDENT
caso              ::= patron "=>" ( sentencia | NEWLINE INDENT bloque DEDENT )
patron            ::= IDENTIFICADOR "(" IDENTIFICADOR ")"   (* ok(valor), err(e) *)
                    | IDENTIFICADOR                         (* ninguno, ok, err *)
                    | "_"                                  (* wildcard *)
                    | numero | cadena                      (* Literales *)

(* Manejo de Errores *)
intentar          ::= "intentar" ":" NEWLINE INDENT bloque DEDENT [ "atrapar" IDENTIFICADOR ":" NEWLINE INDENT bloque DEDENT ]
                    | "intentar" expresion "atrapar" expresion   (* Expresión funcional *)

romper            ::= "romper"
continuar         ::= "continuar"
sentencia_vacia   ::= NEWLINE

(* Tipos *)
tipo              ::= tipo_primitivo
                    | IDENTIFICADOR
                    | "lista" "<" tipo ">"
                    | "mapa" "<" tipo "," tipo ">"
                    | "Resultado" "<" tipo "," tipo ">"
                    | "Opcion" "<" tipo ">"
                    | "Canal" "<" tipo ">"
                    | "funcion" "(" [ tipos ] ")" "->" tipo
                    | "&" tipo                          (* préstamo inmutable (solo modo sistema) *)
                    | "rc" tipo                         (* conteo de referencias no atómico *)
                    | "arc" tipo                        (* conteo de referencias atómico *)
                    | "débil" tipo                      (* referencia débil *)
                    | "arena" tipo                      (* asignación en arena *)
                    | "[" tipo "]"                     (* slice / array *)

tipo_primitivo    ::= "entero" | "int"
                    | "decimal" | "float"
                    | "booleano" | "bool"
                    | "texto" | "string"
                    | "caracter" | "char"
                    | "nulo" | "void"

tipos             ::= tipo { "," tipo }

(* Expresiones *)
expresion         ::= expresion_logica
expresion_logica  ::= expresion_rel { ("y" | "o") expresion_rel }*
expresion_rel     ::= expresion_arit { ("==" | "!=" | "<" | ">" | "<=" | ">=") expresion_arit }*
expresion_arit    ::= termino { ("+" | "-") termino }*
termino           ::= factor { ("*" | "/" | "%") factor }*
factor            ::= [ "-" | "!" ] primario

primario          ::= numero
                    | cadena
                    | IDENTIFICADOR
                    | llamada_funcion
                    | "(" expresion ")"
                    | "[" [ expresiones ] "]"              (* Lista literal *)
                    | "{" [ pares ] "}"                   (* Mapa literal *)
                    | IDENTIFICADOR "." IDENTIFICADOR     (* Acceso a campo / método *)
                    | IDENTIFICADOR "[" expresion "]"     (* Indexación *)
                    | "?" expresion                       (* Propagación de error (operador ?) *)
                    | "arena" "(" expresion ")"           (* Nueva arena *)
                    | "rc" "(" expresion ")"              (* Nuevo RC *)
                    | "arc" "(" expresion ")"             (* Nuevo ARC *)
                    | "débil" "(" expresion ")"           (* Nueva débil *)

llamada_funcion   ::= IDENTIFICADOR "(" [ argumentos ] ")"
argumentos        ::= expresion { "," expresion }
expresiones       ::= expresion { "," expresion }
pares             ::= expresion ":" expresion { "," expresion ":" expresion }

numero            ::= DIGITO+ [ "." DIGITO+ ] [ "e" [ "-" ] DIGITO+ ]
cadena            ::= '"' { caracter } '"'
```

---

## 4. TABLA DE PALABRAS RESERVADAS DE SYQUEX (MULTI‑IDIOMA)

Syquex comparte las palabras clave de Synapse (ver Manual 2) y añade las propias de su dominio de alto nivel:

| TokenID | Español (es) | Inglés (en) | Francés (fr) | Portugués (pt) |
|---------|--------------|-------------|--------------|----------------|
| T_METODO | metodo | method | méthode | metodo |
| T_CREAR | crear | new | créer | criar |
| T_ATRAPAR | atrapar | catch | attraper | capturar |
| T_INTENTAR | intentar | try | essayer | tentar |
| T_DELEGAR | delegar | delegate | déléguer | delegar |
| T_LISTA | lista | list | liste | lista |
| T_MAPA | mapa | map | carte | mapa |
| T_ENUMERACION | enumeracion | enum | énumération | enumeração |
| T_ARENA | arena | arena | arène | arena |
| T_RC | rc | rc | rc | rc |
| T_ARC | arc | arc | arc | arc |
| T_DEBIL | débil | weak | faible | fraco |
| T_EN | en | in | dans | em |
| T_PASO | paso | step | pas | passo |
| T_SINO | sino | else | sinon | senao |

---

## 5. SISTEMA DE TIPOS DE SYQUEX

### 5.1. Tipos Primitivos

Syquex comparte los tipos primitivos de Synapse (`entero`, `decimal`, `booleano`, `texto`, `caracter`, `nulo`), pero los trata con un modelo de memoria automático (arenas por defecto).

### 5.2. Tipos de Colecciones (Nativos en la Biblioteca Estándar)

- **`Lista<T>`**: Lista dinámica (vector). Soporta `[]`, `len()`, `append()`, `pop()`, `iter()`.
- **`Mapa<K,V>`**: Diccionario hash. Soporte `[]`, `keys()`, `values()`, `iter()`.

### 5.3. Tipos de Memoria Especiales (Para el Compilador)

| Tipo | Propósito | Gestión |
|------|-----------|---------|
| `arena<T>` | Asigna `T` en una arena de ámbito. La arena se libera al salir del bloque. | Automática (bump allocator) |
| `rc<T>` | Conteo de referencias no atómico. Para objetos compartidos dentro de una fibra. | Manual (el compilador inyecta `rc_inc`/`rc_dec`) |
| `arc<T>` | Conteo de referencias atómico. Para objetos compartidos entre fibras (canales). | Automática (operaciones atómicas) |
| `débil<T>` | Referencia débil a un `rc<T>`/`arc<T>`. Previene ciclos. | Automática (se invalida al destruir el fuerte) |
| `&T` | Préstamo inmutable (solo en modo sistemas o FFI). | Verificación de alcance en tiempo de compilación |

**Nota:** En Syquex, el 95% de los objetos se asignan implícitamente en la arena del ámbito (sin necesidad de anotar `arena`). El compilador deduce automáticamente que un objeto debe vivir en el heap o en la arena basándose en su uso y alcance.

### 5.4. Tipos Algebraicos de Datos (ADTs) - `Resultado` y `Opcion`

Syquex utiliza los mismos tipos algebraicos que Synapse:
- `Resultado<T, E>`: `ok(T)` o `err(E)`.
- `Opcion<T>`: `algun(T)` o `ninguno`.

**Ergonomía mejorada:** El operador `?` (postfijo) propaga el error automáticamente. Si una expresión retorna `Resultado` y se le aplica `?`, el error se retorna de la función actual, y el éxito se desenvuelve.

---

## 6. ESTRUCTURAS, MÉTODOS Y CONSTRUCTORES (OOP NATIVO)

Syquex adopta un modelo de orientación a objetos práctico, similar a Python o Swift, pero sin herencia compleja (usa composición y traits en su lugar).

### 6.1. Definición de una Estructura

```syquex
estructura Persona:
    nombre: texto
    edad: entero
    activo: booleano = verdadero   // Valor por defecto

    // Constructor
    crear(nombre: texto, edad: entero):
        self.nombre = nombre
        self.edad = edad
        // activo ya tiene valor por defecto

    // Método
    metodo cumpleaños():
        self.edad = self.edad + 1

    metodo es_mayor_de_edad() -> booleano:
        retornar self.edad >= 18
```

### 6.2. Uso de la Estructura

```syquex
funcion principal():
    let ana = Persona("Ana", 28)
    ana.cumpleaños()
    si ana.es_mayor_de_edad():
        log("Ana es mayor de edad")
```

### 6.3. Constructores y Métodos Estáticos

Syquex no tiene métodos estáticos clásicos. Se utilizan funciones de módulo (funciones libres en el mismo archivo) para actuar como constructores alternativos.

```syquex
funcion crear_persona_desde_csv(fila: texto) -> Persona:
    let partes = fila.separar(",")
    retornar Persona(partes[0], entero(partes[1]))
```

---

## 7. MANEJO DE ERRORES CON `Resultado` Y EL OPERADOR `?`

Syquex abandona las excepciones de Python/Java en favor de tipos `Resultado` con propagación explícita pero ergonómica.

### 7.1. Función que Retorna `Resultado`

```syquex
funcion dividir(a: decimal, b: decimal) -> Resultado<decimal, texto>:
    si b == 0.0:
        retornar err("División por cero")
    retornar ok(a / b)
```

### 7.2. Uso del Operador `?` (Propagación Rápida)

El operador `?` se coloca después de una expresión que retorna `Resultado`. Si es `err`, retorna el error de la función actual. Si es `ok`, desempaqueta el valor.

```syquex
funcion calcular_media(operaciones: Lista<decimal>) -> Resultado<decimal, texto>:
    let suma = 0.0
    para i en operaciones:
        // Si dividir falla, la función retorna err(...) inmediatamente
        suma = suma + dividir(i, 2.0)?
    retornar ok(suma / operaciones.len())
```

### 7.3. `intentar` / `atrapar` (Para Interoperabilidad con Código que Lanza Excepciones)

Syquex no tiene excepciones nativas, pero proporciona `intentar`/`atrapar` para envolver FFI o código que pueda generar pánicos.

```syquex
funcion operacion_riesgosa() -> Resultado<nulo, texto>:
    intentar:
        let archivo = abrir("datos.txt")
        let contenido = archivo.leer()
        // ...
    atrapar e:
        retornar err("Error en operación riesgosa: " + e)
    retornar ok()
```

---

## 8. CONCURRENCIA Y COMUNICACIÓN EN SYQUEX

Syquex hereda el modelo de concurrencia de Synapse (fibras + canales), pero con una sintaxis aún más limpia.

### 8.1. Lanzar una Fibra

```syquex
funcion trabajador(id: entero, canal: Canal<texto>):
    canal <- "Hilo " + id.texto() + " listo"

funcion principal():
    let c = Canal<texto>(10)
    lanzar trabajador(1, c)
    lanzar trabajador(2, c)
    
    escuchar c:
        let mensaje = c ->
        log(mensaje)
```

### 8.2. Canales y Move Semantics (Automático)

Syquex aplica Move Semantics al enviar objetos por un canal: la variable origen se invalida (como en Rust, pero sin que el usuario tenga que pensarlo).

```syquex
estructura Dato:
    contenido: texto

funcion enviar(c: Canal<Dato>):
    let d = Dato("Secreto")
    c <- d   // d se mueve, no se puede usar después de esta línea
```

---

## 9. FFI E INTEGRACIÓN CON C (`externo`)

Syquex se integra con C mediante la palabra clave `externo`. Es la puerta de entrada a todo el ecosistema de librerías C (libcurl, SQLite, GTK, etc.).

### 9.1. Declaración de Función C

```syquex
externo funcion strlen(s: &texto) -> entero
```

### 9.2. Uso en Código Seguro (FFI Automático)

```syquex
funcion longitud(s: texto) -> entero:
    retornar strlen(&s)   // El compilador maneja el marshaling
```

### 9.3. Marshaling Automático (Estrategia Zero-Copy)

Cuando se pasa un `texto` a C, el compilador añade un byte `\0` al final en la arena (sin copiar todo el buffer). Este es un detalle de implementación que el desarrollador no necesita conocer.

---

## 10. EXPORTACIÓN A OTROS LENGUAJES (`@export`)

Syquex puede exportar funciones y estructuras para ser usadas desde Python, JavaScript (via WASM), Java, etc.

```syquex
@export(python) funcion procesar(data: Lista<Decimal>) -> Resultado<Decimal, Texto>

@export(typescript) estructura Usuario:
    nombre: Texto
    edad: Entero
```

El compilador genera automáticamente los bindings (archivos `.py`, `.d.ts`, `.java`) en la fase de generación de código.

---

## 11. INTEGRACIÓN CON EL AST CANÓNICO DE SYNAPSE (El Traductor)

Syquex no tiene su propio backend. Cada nodo del AST de Syquex se traduce al `SemNodo[]` canónico de Synapse.

### 11.1. Mapeo de Nodos Clave

| Nodo Syquex | Nodo Synapse (SemNodo) | Notas |
|-------------|------------------------|-------|
| `FuncionDef` | `NODO_FUNCION` | Se añaden metadatos de Syquex (ej. `es_metodo`) |
| `EstructuraDef` | `NODO_ESTRUCTURA` | Se registran campos y métodos |
| `MetodoDef` | `NODO_FUNCION` con `self` como primer parámetro implícito |
| `ConstructorDef` | `NODO_FUNCION` especial que retorna la estructura |
| `Coincidir` | `NODO_COINCIDIR` | Exhaustividad verificada por el analizador semántico de Synapse |
| `Intento` | `NODO_INTENTO` | Traducido a un bloque `try` en C (via FFI) |

### 11.2. Preservación de Metadatos de Depuración

El traductor conserva `archivo`, `linea` y `columna` originales para que los errores del compilador de Synapse apunten a la fuente `.syq`.

---

## 12. BIBLIOTECA ESTÁNDAR DE SYQUEX (`lib/`)

Syquex incluye una biblioteca estándar modular ubicada en `lib/`, con archivos `.syq` que proporcionan funcionalidad de alto nivel. Esta sección describe la estructura general de la biblioteca; **las APIs específicas de cada módulo se especifican en los archivos `.syq` de la biblioteca estándar, cuyo diseño se detalla en la documentación de la Fase 24** (`docs/manuales/MANUAL 4.md`, §6; `ROADMAP.md`, Fase 24).

### 12.1. Estructura de Módulos

| Módulo | Archivo | Descripción |
|--------|---------|-------------|
| IO | `lib/io.syq` | Entrada/salida (consola, archivos). |
| Web | `lib/web.syq` | Servidor HTTP basado en fibras (no bloqueante). |
| DOM | `lib/dom.syq` | Manipulación del DOM para WASM con arenas de componente. |
| JSON | `std/json.syn` | Serialización/deserialización JSON (ADT; FFI a cJSON en runtime). |
| Lista | `lib/lista.syq` | Operaciones con listas (map, filter, reduce, sort). |
| Mapa | `lib/mapa.syq` | Operaciones con mapas/diccionarios. |
| DB | `lib/db.syq` | Conexión a SQLite (FFI a libsqlite3) y PostgreSQL. |
| Tiempo | `lib/tiempo.syq` | Fechas y tiempos. |
| Pruebas | `lib/pruebas.syq` | Framework de testing (similar a unittest). |
| IA | `lib/ia.syq` | Integración con OpenSyn. |
| FFI | `lib/ffi.syq` | Utilidades para interoperabilidad. |

### 12.2. Importación

Los módulos se importan con `importar lib.modulo`:

```syquex
importar lib.io
importar lib.web
importar lib.json
```

### 12.3. Nota sobre FFI

El servidor web (`lib/web.syq`) utiliza FFI a libmicrohttpd o sockets nativos. Cada conexión entrante se maneja en una fibra separada, según el modelo de fibras M:N del Manual 5. Para detalles de la API, consulte los archivos fuente en `lib/web.syq`.

---

## 13. PRUEBAS OBLIGATORIAS PARA ESTA ETAPA

| Test | Comando | Criterio |
|------|---------|----------|
| Lexer Syquex | `pytest tests/syquex/test_lexer.py -v` | 100% pass |
| Parser Syquex (EBNF) | `pytest tests/syquex/test_parser.py -v` | 100% pass |
| Estructuras y Métodos | `pytest tests/syquex/test_structs.py -v` | 100% pass |
| Operador `?` y `Resultado` | `pytest tests/syquex/test_result.py -v` | Propagación correcta de errores |
| Concurrencia (`lanzar`, canales) | `pytest tests/syquex/test_concurrency.py -v` | 0 deadlocks |
| FFI y `externo` | `pytest tests/syquex/test_ffi.py -v` | 100% pass |
| Exportación (`@export`) | `pytest tests/syquex/test_export.py -v` | Bindings generados correctamente |
| Traductor a Synapse | `pytest tests/syquex/test_traductor.py -v` | AST canónico válido y compilable |

---

## 14. EJEMPLO COMPLETO DE PROGRAMA SYQUEX

**Código fuente (`ejemplo.syq`):**

```syquex
#lang: es

importar lib.io
importar lib.web
importar synapse.audio   // Módulo de Synapse

estructura Usuario:
    nombre: texto
    edad: entero

    crear(nombre: texto, edad: entero):
        self.nombre = nombre
        self.edad = edad

    metodo saludar():
        io.escribir_linea("Hola, soy " + self.nombre)

funcion generar_audio(frecuencia: decimal, duracion: decimal) -> Resultado<tensor, texto>:
    si frecuencia <= 0.0:
        retornar err("Frecuencia inválida")
    retornar ok(synapse.audio.generar(frecuencia, duracion, 1000.0))

funcion principal() -> Resultado<nulo, texto>:
    let usuario = Usuario("Ana", 28)
    usuario.saludar()

    // Usar el operador ? para propagar errores
    let audio = generar_audio(440.0, 3.0)?
    io.escribir_linea("Audio generado: " + audio.filas.texto() + " muestras")

    // Servidor web simple
    let servidor = web.servidor(8080)
    servidor.get("/saludar", funcion(req):
        retornar web.respuesta(200, "Hola desde Syquex")
    )
    servidor.iniciar()?
    retornar ok()
```

**Explicación del flujo:**
1. El lexer y parser leen el archivo `.syq`.
2. El traductor convierte las estructuras, métodos y funciones a `SemNodo[]`.
3. El analizador semántico de Synapse verifica tipos y ownership.
4. El generador emite código C con arenas (para objetos de Syquex).
5. GCC/Clang produce el binario final.

---

## 15. SIGUIENTES PASOS

Con la sintaxis y semántica de Syquex definidas, el siguiente manual (Manual 4) se centrará en el **Modelo de Memoria de Syquex**: Arenas por ámbito, conteo de referencias, análisis de alcance, Cleanup Blocks y FFI Marshaling.

---

*Este manual proporciona la base sintáctica y semántica de Syquex. La implementación del frontend debe seguir fielmente esta especificación para garantizar una experiencia de desarrollo productiva y segura.*

**Fin del Manual 3**