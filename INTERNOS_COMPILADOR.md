# Synapse: Guía de Contribución a Internos (Compiler Internals)

## 1. Anatomía del Pipeline de Compilación
Si necesitas añadir una nueva característica al lenguaje (ej. un nuevo operador matemático), debes atravesar las 4 capas del compilador en este orden estricto. Un salto en cualquier capa romperá el Bootstrap.

### Paso 1: El Lexer (`src/lexer.syn`)
El vocabulario. Define cómo la cadena de texto se convierte en un `Token`.
* Localiza el diccionario de palabras reservadas o símbolos.
* Añade la nueva constante (ej. `TOKEN_MODULO` para `%`).
* *Regla:* Si añades un símbolo multicácter (ej. `**`), asegúrate de que el puntero de lectura no colisione con el símbolo de un solo carácter (`*`).

### Paso 2: El Parser (`src/parser.syn`)
La gramática. Transforma la lista plana de tokens en el Árbol de Sintaxis Abstracta (AST).
* Crea el nuevo `struct` en `ast_nodes.syn` (ej. `NodoOperacionModulo`).
* Actualiza la función correspondiente según la precedencia (ej. `parsear_termino()` para operadores multiplicativos).

### Paso 3: El Analizador Semántico (`src/analizador_semantico.syn`)
La ley. Valida que la operación sea legal en memoria y tipos.
* Añade la función `visitar_nodo_operacion_modulo`.
* Implementa la lógica: "El operador módulo solo es válido si ambos operandos son `entero`. Si son `flotante`, lanza `ErrorSemantico`".

### Paso 4: El Generador C (`src/generator.syn`)
El metal. Traduce el nodo validado a su contraparte en C.
* Añade el método de generación.
* *Regla:* Nunca emitas código C que asuma el tipo de dato subyacente. Usa la propiedad `tipo_resuelto` que el Analizador Semántico adjuntó al nodo.