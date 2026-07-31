MANUAL 2: ESPECIFICACIÓN SINTÁCTICA Y SEMÁNTICA
Archivo: 02_SINTAXIS_Y_SEMANTICA.md
Versión: 5.0.0
Propósito: Definir la gramática formal del lenguaje, las palabras reservadas, los tipos, los operadores y las reglas semánticas fundamentales (contratos, patrones, importaciones).

2.1 Directiva de Archivo y Codificación
Todo archivo fuente debe comenzar con la directiva de idioma en la línea 1:

synapse
#lang: es
Idiomas soportados: es (español), en (inglés), fr (francés), pt (portugués).
Codificación: UTF-8 estricto.
Comentarios: // línea y /* bloque */.

2.2 Gramática Formal (EBNF) — Completa
ebnf
Programa        ::= DirectivaLang (Sentencia)* EOF
DirectivaLang   ::= "#lang:" Identificador NEWLINE

Sentencia       ::= DeclaracionFuncion
                  | DeclaracionEstructura
                  | DeclaracionConstante
                  | Importacion
                  | SentenciaControl
                  | Asignacion
                  | Expresion NEWLINE

DeclaracionFuncion ::= "funcion" Identificador "(" Parametros? ")" "->" TipoRetorno ":"
                       NEWLINE (ContratoRequiere)? (ContratoGarantiza)? Bloque

Parametros      ::= Parametro ("," Parametro)*
Parametro       ::= ("->")? Identificador ":" Tipo
                   (* "->" indica transferencia de ownership (move) *)

Bloque          ::= INDENT (Sentencia)+ DEDENT
                   (* INDENT = exactamente 4 espacios, prohibido \t *)

ContratoRequiere  ::= "requiere" ":" NEWLINE INDENT (Expresion NEWLINE)+ DEDENT
ContratoGarantiza ::= "garantiza" ":" NEWLINE INDENT (Expresion NEWLINE)+ DEDENT

SentenciaControl ::= CondicionalSi | BucleMientras | BuclePara
                    | LanzarHilo | EscucharCanal | RecuperarError
                    | Romper | Siguiente | BloqueInseguro | CoincidirPatron

CondicionalSi   ::= "si" Expresion ":" NEWLINE Bloque ("sino" ":" NEWLINE Bloque)?
BucleMientras   ::= "mientras" Expresion ":" NEWLINE Bloque
BuclePara       ::= "para" Identificador "=" Expresion "mientras" Expresion ":" NEWLINE Bloque
                   (* Ej: para i = 0 mientras i < 10: *)

LanzarHilo      ::= "lanzar" LlamadaFuncion ("recuperar" Expresion)?
EscucharCanal   ::= "escuchar" Expresion ":" NEWLINE Bloque

CrearCanal      ::= "canal" "<" Tipo ">" "(" Expresion ")"
                   (* cap = 0 → síncrono; cap > 0 → buffer asíncrono *)
EnviarCanal     ::= Expresion "<-" Expresion
RecibirCanal    ::= Expresion "->"

CoincidirPatron ::= "coincidir" Expresion ":" NEWLINE INDENT (CasoCoincidir)+ DEDENT
CasoCoincidir   ::= Patron "=>" (Sentencia | NEWLINE Bloque)
Patron          ::= Identificador "(" Identificador ")"   (* ej: ok(valor), err(e) *)

EstructuraDef   ::= "estructura" Identificador ":" NEWLINE INDENT { Campo } DEDENT
Campo           ::= Identificador ":" Tipo NEWLINE

DeclaracionConstante ::= "constante" Identificador "=" Expresion NEWLINE

Importacion     ::= "importar" Identificador ("." Identificador)* NEWLINE
                   (* ej: importar std.io *)

Tipo            ::= "entero" | "decimal" | "booleano" | "texto" | "caracter"
                  | "nulo" | "puntero"
                  | Identificador                    (* struct definido por usuario *)
                  | "Canal" "<" Tipo ">"
                  | "Resultado" "<" Tipo "," Tipo ">"
                  | "Opcion" "<" Tipo ">"

Expresion       ::= ExpresionLogica
ExpresionLogica ::= ExpresionRel ( ("y" | "o") ExpresionRel )*
ExpresionRel    ::= ExpresionArit ( ("==" | "!=" | "<" | ">" | "<=" | ">=") ExpresionArit )*
ExpresionArit   ::= Termino ( ("+" | "-") Termino )*
Termino         ::= Factor ( ("*" | "/" | "%") Factor )*
Factor          ::= ("-" | "!")? Primario

Primario        ::= Numero | CadenaLiteral | Identificador | LlamadaFuncion
                  | "(" Expresion ")"
LlamadaFuncion  ::= Identificador "(" Argumentos? ")"
Argumentos      ::= Expresion ("," Expresion)*

Identificador   ::= [A-Za-z_] [A-Za-z0-9_]*
Numero          ::= [0-9]+ ("." [0-9]+)?
CadenaLiteral   ::= '"' ([^"\\] | "\\" .)* '"'   (* soporta \n, \t, \\, \" *)
2.3 Tabla de Palabras Reservadas (Multi-idioma)
El lexer utiliza diccionarios por idioma. Los TokenID son universales.

TokenID	Español (es)	Inglés (en)	Francés (fr)	Portugués (pt)
T_FUNCION	funcion	function	fonction	funcao
T_RETORNAR	retornar	return	retourner	retornar
T_SI	si	if	si	se
T_SINO	sino	else	sinon	senao
T_MIENTRAS	mientras	while	tantque	enquanto
T_PARA	para	for	pour	para
T_LANZAR	lanzar	spawn	lancer	lancar
T_RECUPERAR	recuperar	recover	recuperer	recuperar
T_ESCUCHAR	escuchar	listen	ecouter	escutar
T_IMPORTAR	importar	import	importer	importar
T_ESTRUCTURA	estructura	struct	structure	estrutura
T_CONSTANTE	constante	const	constante	constante
T_INSEGURO	inseguro	unsafe	non_securise	inseguro
T_EXTERNO	externo	extern	externe	externo
T_COINCIDIR	coincidir	match	correspondre	coincidir
T_REQUIERE	requiere	requires	exige	requer
T_GARANTIZA	garantiza	ensures	garantit	garante
2.4 Tipos Primitivos y Algebraicos
Tipo Sintáctico	Semántica	Tamaño (ABI)	Notas
entero	Entero con signo de 64 bits	8 bytes	Alias de int64_t
decimal	Punto flotante doble precisión	8 bytes	Alias de double
booleano	Booleano lógico	1 byte	verdadero / falso
texto	Cadena UTF-8 segura (longitud + buffer)	16 bytes (estructura)	No termina en \0 internamente, pero se convierte para FFI
caracter	Carácter UTF-8 (punto de código)	1-4 bytes	Alias de char (C)
nulo	Ausencia de valor	0 bytes	Solo para funciones sin retorno
puntero	Puntero opaco (void*)	8 bytes	Solo dentro de inseguro
Tipos Algebraicos (predefinidos en el prelude):

synapse
tipo Resultado<T, E> = ok(T) | err(E)
tipo Opcion<T> = algun(T) | ninguno
El analizador semántico obliga a usar coincidir para desempaquetar estos tipos. Si falta un caso, se emite ERR_SEM_EXHAUSTIVE_MATCH_REQUIRED.

2.5 Contratos Lógicos (requiere / garantiza)
Semántica formal:

requiere: Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas.

garantiza: Se evalúa inmediatamente antes de cada retornar. La variable _resultado_ contiene el valor que se va a retornar.

Ejemplo:

synapse
funcion dividir(a: entero, b: entero) -> entero:
    requiere:
        b != 0
    garantiza:
        _resultado_ * b + (a % b) == a
    retornar a / b
Modos de compilación:

Modo	Comportamiento
debug (default)	Las aserciones se compilan como assert() en C. Fallo → SIGABRT.
release	Se define #define NDEBUG en el C generado. Las aserciones se eliminan (costo cero).
--safe	Se activa verificación formal (ATP engine) en lugar de aserciones en tiempo de ejecución.
2.6 Precedencia de Operadores
Nivel	Operadores	Asociatividad
1 (máxima)	f(x) (llamada), canal-> (recibir)	Izquierda
2	- (unario), ! (NOT)	Derecha
3	* / %	Izquierda
4	+ -	Izquierda
5	< > <= >=	Izquierda
6	== !=	Izquierda
7	y (AND lógico)	Izquierda
8	o (OR lógico)	Izquierda
9 (mínima)	= (asignación), <- (enviar canal)	Derecha
