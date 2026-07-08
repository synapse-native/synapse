# Auditoría de Lexer: `lexer.py`

Este documento resume los tokens reconocidos por el lexer actual de Synapse y los patrones de análisis usados en `lexer.py`.

## Resumen
- Tokens definidos en `TokenID`: 47.
- Tokens reconocidos directamente por el lexer: 43 de sintaxis más 4 tokens estructurales (`NEWLINE`, `INDENT`, `DEDENT`, `EOF`).
- El lexer no usa regex de Python, pero las reglas son equivalentes a las expresiones regulares indicadas.

## Tabla de tokens
| Nombre Token | Regex actual (equivalente) | Descripción |
| :--- | :--- | :--- |
| `STRING` | `"(?:\\.|[^"\\])*"` o `'(?:(?:\\.)|[^'\\])*'` | Literal de cadena con escapes `\\`, `\n`, `\t` y comilla escapada. |
| `FLOAT` | `[0-9]+\.[0-9]+` | Literal numérico con punto decimal. |
| `NUMBER` | `[0-9]+` | Literal entero decimal. |
| `IDENTIFIER` | `[A-Za-z_][A-Za-z0-9_]*` | Identificador de variable/nombre de función/estructura. Palabras reservadas se mapean después a tokens especiales. |
| `IF` | multilenguaje: `si|if|se|wenn` | Palabra clave de condicional. |
| `ELSE` | `sino|else|sinon|senao|sonst|altrimenti` | Bloque alternativo en condicional. |
| `FUNCTION` | `funcion|function|fonction|funcao|funktion|funzione` | Declaración de función. |
| `RETURN` | `retornar|return|retourner|rueckgabe|restituisci` | Retorno de función. |
| `SPAWN` | `lanzar|spawn|lancer|lancar|starten|lancia` | Inicio de ejecución asíncrona/hilo. |
| `RECOVER` | `recuperar|recover|recuperer|wiederherstellen|recupera` | Manejo de recuperación en expresión. |
| `LISTEN` | `escuchar|listen|ecouter|escutar|hoeren|ascolta` | Listener/espera de respuestas. |
| `WHILE` | `mientras|while|tantque|enquanto|waehrend|mentre` | Bucle while. |
| `IMPORT` | `importar|import|importer|importieren|importa` | Declaración de importación. |
| `STRUCT` | `estructura|struct|structure|estrutura|struktur|struttura` | Definición de estructura. |
| `BREAK` | `romper|break|rompre|parar|abbrechen|interrompi` | Salir de bucle. |
| `CONTINUE` | `siguiente|continue|continuer|continuar|fortsetzen|continua` | Continuar bucle. |
| `AND` | `y|and|et|e|und` | Operador lógico AND. |
| `OR` | `o|or|ou|oder` | Operador lógico OR. |
| `NOT` | `no|not|non|nao|nicht` | Operador lógico NOT. |
| `TRUE` | `verdadero|true|vrai|verdadeiro|wahr|vero` | Literal booleano verdadero. |
| `FALSE` | `falso|false|faux|falsch` | Literal booleano falso. |
| `INSEGURO` | `inseguro|unsafe` | Inicio de bloque inseguro. |
| `IMPORTAR_C` | `importar_c|import_c|importer_c|importa_c` | Importación de C nativo. |
| `EXTERNO` | `externo|extern|externe|esterno` | Declaración externa de función. |
| `ARROW` | `->` | Operador de transferencia o flecha. |
| `EQUALS` | `==` | Comparación de igualdad. |
| `NOT_EQUALS` | `!=` | Comparación de desigualdad. |
| `LESS_EQUALS` | `<=` | Comparación menor o igual. |
| `GREATER_EQUALS` | `>=` | Comparación mayor o igual. |
| `ASSIGN` | `=` | Asignación. |
| `GREATER` | `>` | Operador mayor que. |
| `LESS` | `<` | Operador menor que. |
| `PLUS` | `+` | Suma / operador unario más. |
| `MINUS` | `-` | Resta / operador unario menos. |
| `STAR` | `*` | Multiplicación / puntero / operador de desreferencia. |
| `SLASH` | `/` | División / inicio de comentario con `//`. |
| `MODULO` | `%` | Módulo. |
| `LPAREN` | `(` | Paréntesis izquierdo. |
| `RPAREN` | `)` | Paréntesis derecho. |
| `COLON` | `:` | Dos puntos. |
| `COMMA` | `,` | Coma. |
| `DOT` | `.` | Punto. |
| `AMPERSAND` | `&` | Ampersand para direcciones/punteros. |
| `NEWLINE` | `\n` | Fin de línea lógico después de cada línea no vacía. |
| `INDENT` | `^( {4})+` | Aumento de nivel de indentación. |
| `DEDENT` | `^( {4})*` | Disminución de nivel de indentación. |
| `EOF` | fin de archivo | Token final. |

## Reglas especiales del lexer
- Comentarios de línea: `//.*` son descartados.
- Las líneas que comienzan con `#` son ignoradas (incluyendo `#lang:`).
- Espacios internos en una línea son consumidos pero no generan token.
- Indentación válida debe ser múltiplo de 4 espacios; de lo contrario lanza `SyntaxError`.
- Los literales negativos no se tokenizan como `NUMBER`; el guion `-` es siempre `MINUS` y el signo negativo se forma en el parser.

## Datos relevantes para migración a Synapse
1. Las palabras clave son multilingües; se debe conservar la tabla de traducción a `TokenID`.
2. No hay soporte de literales hexadecimales, binarios ni exponentes.
3. `STRING` admite escapes simples `\n`, `\t`, `\\` y comilla dentro de la misma comilla de apertura.
4. `IMPORTAR_C` y `EXTERNO` son tokens especiales que habilitan FFI y se tratan como palabras clave.
