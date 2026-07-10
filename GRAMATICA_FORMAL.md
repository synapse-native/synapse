# Synapse: Especificación de Gramática Formal (EBNF)

## 1. Reglas Léxicas Fundamentales
Synapse es un lenguaje sensible a la indentación (Off-side rule). El analizador léxico inyecta tokens sintéticos `INDENT` y `DEDENT` al detectar cambios en el nivel de sangría (estrictamente múltiplos de 4 espacios). Los tabuladores (`\t`) están prohibidos y generan un error léxico fatal.

* **Codificación:** UTF-8 estricto.
* **Comentarios:** * Línea: `// comentario`
  * Bloque: `/* comentario */`
* **Directiva obligatoria:** Todo archivo debe comenzar con `#lang: es\n`.

## 2. Palabras Reservadas (Keywords)
`funcion`, `retornar`, `si`, `sino`, `mientras`, `coincidir`, `importar`, `inseguro`, `lanzar`, `requiere`, `garantiza`, `externo`, `nulo`.

## 3. Tipos Nativos Primitivos
`entero` (i64), `flotante` (f64), `booleano` (bool), `cadena` (CadenaSegura interna), `caracter` (char).

## 4. Definición de la Gramática (Extended Backus-Naur Form)

```ebnf
Programa        ::= DirectivaLang (Sentencia)* EOF
DirectivaLang   ::= "#lang:" Identificador NEWLINE

Sentencia       ::= DeclaracionFuncion
                  | Importacion
                  | SentenciaControl
                  | Asignacion
                  | Expresion NEWLINE

Importacion     ::= "importar" Identificador ("." Identificador)* NEWLINE

DeclaracionFuncion ::= "funcion" Identificador "(" Parametros? ")" "->" TipoRetorno ":" NEWLINE BloqueFuncion

Parametros      ::= Parametro ("," Parametro)*
Parametro       ::= Identificador ":" Tipo
TipoRetorno     ::= Tipo | "nulo"

BloqueFuncion   ::= INDENT (ContratoRequiere)? (ContratoGarantiza)? (Sentencia)+ DEDENT

ContratoRequiere  ::= "requiere" ":" NEWLINE INDENT (ExpresionLogica NEWLINE)+ DEDENT
ContratoGarantiza ::= "garantiza" ":" NEWLINE INDENT (ExpresionLogica NEWLINE)+ DEDENT

SentenciaControl  ::= CondicionalSi | BucleMientras | CoincidirPatron | LanzarHilo | BloqueInseguro

CondicionalSi   ::= "si" Expresion ":" NEWLINE Bloque (Sino)?
Sino            ::= "sino" ":" NEWLINE Bloque
BucleMientras   ::= "mientras" Expresion ":" NEWLINE Bloque

CoincidirPatron ::= "coincidir" Expresion ":" NEWLINE INDENT (CasoCoincidir)+ DEDENT
CasoCoincidir   ::= Identificador "(" Identificador ")" "=>" (Sentencia | NEWLINE Bloque)

LanzarHilo      ::= "lanzar" LlamadaFuncion NEWLINE
BloqueInseguro  ::= "inseguro" ":" NEWLINE Bloque

Bloque          ::= INDENT (Sentencia)+ DEDENT

Asignacion      ::= Identificador "=" Expresion NEWLINE

Expresion       ::= ExpresionLogica
ExpresionLogica ::= ExpresionRel ( ("y" | "o") ExpresionRel )*
ExpresionRel    ::= ExpresionArit ( ("==" | "!=" | "<" | ">" | "<=" | ">=") ExpresionArit )*
ExpresionArit   ::= Termino ( ("+" | "-") Termino )*
Termino         ::= Factor ( ("*" | "/") Factor )*
Factor          ::= ("-" | "!")? Primario

Primario        ::= Numero | CadenaLiteral | Identificador | LlamadaFuncion | "(" Expresion ")"
LlamadaFuncion  ::= Identificador "(" Argumentos? ")"
Argumentos      ::= Expresion ("," Expresion)*

Identificador   ::= [a-zA-Z_] [a-zA-Z0-9_]*
Numero          ::= [0-9]+ ("." [0-9]+)?
CadenaLiteral   ::= '"' [^"]* '"'
5. Precedencia de Operadores (De mayor a menor)
Llamadas a función ()

Unarios: - (negación aritmética), ! (negación lógica)

Multiplicativos: *, /

Aditivos: +, -

Relacionales: <, >, <=, >=

Igualdad: ==, !=

Lógicos: y (AND), o (OR)


***

### Documento 6: `ESPECIFICACION_CONTRATOS.md`

```markdown
# Synapse: Especificación de Contratos Lógicos (El Pacto)

## 1. Propósito
El diseño por contrato en Synapse no es azúcar sintáctico; es una directiva de compilación diseñada para auditar lógicas complejas (especialmente código generado por IA). Garantiza que las pre-condiciones y post-condiciones de una función se cumplan en tiempo de ejecución.

## 2. Anatomía del Contrato
Un contrato se define mediante dos bloques opcionales al inicio de una función:
* `requiere:` Evalúa el estado *antes* de que se ejecute la primera línea de la función. Validando los parámetros de entrada.
* `garantiza:` Evalúa el estado *después* de que la función calcule su resultado, pero *antes* de retornar el valor al llamador. El valor de retorno se captura implícitamente en la variable `_resultado_`.

**Sintaxis estricta:**
```synapse
funcion calcular_descuento(precio: flotante, porcentaje: flotante) -> flotante:
    requiere:
        precio > 0.0
        porcentaje >= 0.0
        porcentaje <= 100.0
    
    garantiza:
        _resultado_ <= precio
        _resultado_ >= 0.0
        
    monto_descuento = precio * (porcentaje / 100.0)
    retornar precio - monto_descuento
3. Implementación en el Árbol de Sintaxis Abstracta (AST)
El Parser intercepta requiere y garantiza y los almacena como listas de expresiones lógicas en el NodoDefinicionFuncion.

4. Generación de Código C (Física de la Aserción)
El Generador (generator.py / generator.syn) inyecta estas expresiones utilizando la librería estándar de C <assert.h>.

Traducción del bloque requiere (inyectado al inicio del bloque de C):

C
assert(precio > 0.0 && "Fallo de contrato (requiere): precio > 0.0");
assert(porcentaje >= 0.0 && "Fallo de contrato (requiere): porcentaje >= 0.0");
Traducción del bloque garantiza (inyectado justo antes de cada instrucción return):
El compilador debe interceptar los retornos, asignar el valor a una variable temporal para validarlo y luego retornarlo:

C
double _temp_ret = precio - monto_descuento;
assert(_temp_ret <= precio && "Fallo de contrato (garantiza): _resultado_ <= precio");
return _temp_ret;
5. Modos de Compilación y Rendimiento
Las aserciones de contrato tienen un costo en CPU. El compilador de Synapse las maneja según el flag de construcción de Axon:

Modo Desarrollo / Debug (Por defecto): Los contratos se compilan como aserciones estrictas. Si fallan, el programa arroja un SIGABRT (core dump) y detiene la ejecución inmediatamente.

Modo Producción (synapse construir --release): El generador de código C define el macro NDEBUG (#define NDEBUG) antes de importar <assert.h>. El compilador C (GCC/Clang) eliminará matemáticamente todas las comprobaciones del contrato, logrando costo cero (Zero-Cost Abstraction) en tiempo de ejecución.
