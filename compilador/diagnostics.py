
import sys
from enum import Enum
from typing import Optional, List, Dict

from compilador.ast_nodes import Token, TokenID


class ErrorCodes(str, Enum):
    ERR_SYNTAX_EXPECTED_TOKEN = 'ERR_SINTAXIS_EXPECTED_TOKEN'
    ERR_SYNTAX_UNEXPECTED_TOKEN = 'ERR_SINTAXIS_UNEXPECTED_TOKEN'
    ERR_SYNTAX_UNEXPECTED_EXPR = 'ERR_SINTAXIS_UNEXPECTED_EXPR'
    ERR_SYNTAX_EXPECTED_NEWLINE = 'ERR_SINTAXIS_EXPECTED_NEWLINE'
    ERR_LANG_MISSING = 'ERR_LEXICO_LANG_MISSING'
    ERR_LANG_UNSUPPORTED = 'ERR_LEXICO_LANG_UNSUPPORTED'
    ERR_INDENT_INVALID = 'ERR_LEXICO_INDENT_INVALID'
    ERR_INDENT_INCONSISTENT = 'ERR_LEXICO_INDENT_INCONSISTENT'
    ERR_STRING_UNCLOSED = 'ERR_LEXICO_STRING_UNCLOSED'
    ERR_LEX_CHAR_UNEXPECTED = 'ERR_LEXICO_CHAR_UNEXPECTED'
    ERR_LEX = 'ERR_LEXICO'
    ERR_FILE_NOT_FOUND = 'ERR_IO_FILE_NOT_FOUND'
    ERR_CANONICAL_FORMAT = 'ERR_CANONICO_FORMAT'
    ERR_SEM_VAR_NO_DECLARADA = 'ERR_SEM_VAR_NO_DECLARADA'
    ERR_SEM_TIPO_INCOMPATIBLE = 'ERR_SEM_TIPO_INCOMPATIBLE'
    ERR_SEM_TIPO_RETORNO = 'ERR_SEM_TIPO_RETORNO'
    ERR_SEM_FUNC_NO_DEFINIDA = 'ERR_SEM_FUNC_NO_DEFINIDA'
    ERR_SEM_REDEFINICION = 'ERR_SEM_REDEFINICION'
    ERR_SEM_ARGUMENTOS_INVALIDOS = 'ERR_SEM_ARGUMENTOS_INVALIDOS'
    ERR_SEM_ESTRUCTURA_NO_DEFINIDA = 'ERR_SEM_ESTRUCTURA_NO_DEFINIDA'
    ERR_SEM_CAMPO_NO_EXISTE = 'ERR_SEM_CAMPO_NO_EXISTE'
    ERR_SEM_VAR_MOVIDA = 'ERR_SEM_VAR_MOVIDA'
    ERR_SEM_ACCESO_MEMORIA_MOVIDA = 'ERR_SEM_ACCESO_MEMORIA_MOVIDA'
    ERR_SEM_RESULTADO_SIN_DESEMPAQUETAR = 'ERR_SEM_RESULTADO_SIN_DESEMPAQUETAR'
    ERR_MANIFEST_NOT_FOUND = 'ERR_IO_MANIFEST_NOT_FOUND'
    ERR_MODULE_STD_NOT_FOUND = 'ERR_MOD_STD_NOT_FOUND'
    ERR_MODULE_AXON_NOT_FOUND = 'ERR_MOD_AXON_NOT_FOUND'
    ERR_DEP_NOT_DECLARED = 'ERR_DEP_NOT_DECLARED'
    ERR_LOCK_HASH_MISMATCH = 'ERR_LOCK_HASH_MISMATCH'
    ERR_GIT_FAILURE = 'ERR_GIT_FAILURE'
    ERR_SEM_ASM_FUERA_INSEGURO = 'ERR_SEM_ASM_FUERA_INSEGURO'
    ERR_SEM_CONSTANTE_INMUTABLE = 'ERR_SEM_CONSTANTE_INMUTABLE'
    ERR_MEM_USE_AFTER_MOVE = 'ERR_MEM_USE_AFTER_MOVE'
    ERR_VER_WHILE_INACOTADO = 'ERR_VER_WHILE_INACOTADO'
    ERR_VER_MUTACION_GLOBAL = 'ERR_VER_MUTACION_GLOBAL'
    ERR_VER_RECURSION_NO_TERMINAL = 'ERR_VER_RECURSION_NO_TERMINAL'
    ERR_VER_CONTRATO_INVALIDO = 'ERR_VER_CONTRATO_INVALIDO'
    ERR_SEM_EXHAUSTIVE_MATCH_REQUIRED = 'ERR_SEM_EXHAUSTIVE_MATCH_REQUIRED'
    ERR_MEM_BORROW_CONFLICT = 'ERR_MEM_BORROW_CONFLICT'
    ERR_SEM_TYPE_AMBIGUOUS = 'ERR_SEM_TYPE_AMBIGUOUS'  # 2.4: Hindley-Milner (Manual 2 §8.2)


ERROR_MESSAGES: Dict[str, Dict[ErrorCodes, str]] = {
    'es': {
        ErrorCodes.ERR_SYNTAX_EXPECTED_TOKEN: "Se esperaba {esperado}, se encontró '{encontrado}'",
        ErrorCodes.ERR_SYNTAX_UNEXPECTED_TOKEN: "Token inesperado '{tok_name}' tras expresión",
        ErrorCodes.ERR_SYNTAX_UNEXPECTED_EXPR: "Expresión inesperada: '{tipo}'",
        ErrorCodes.ERR_SYNTAX_EXPECTED_NEWLINE: "Se esperaba nueva línea después de '{construccion}'",
        ErrorCodes.ERR_LANG_MISSING: "Falta declaración de idioma '#lang: <codigo>' en la línea 1",
        ErrorCodes.ERR_LANG_UNSUPPORTED: "Idioma '{idioma}' no soportado. Idiomas disponibles: {soportados}",
        ErrorCodes.ERR_INDENT_INVALID: "La indentación debe ser múltiplo de 4 espacios",
        ErrorCodes.ERR_INDENT_INCONSISTENT: "Nivel de indentación inconsistente",
        ErrorCodes.ERR_STRING_UNCLOSED: "Cadena sin cerrar",
        ErrorCodes.ERR_LEX: "{mensaje}",
        ErrorCodes.ERR_LEX_CHAR_UNEXPECTED: "Caracter inesperado '{char}'",
        ErrorCodes.ERR_FILE_NOT_FOUND: "Archivo no encontrado: {archivo}",
        ErrorCodes.ERR_CANONICAL_FORMAT: "Formato canónico no reconocido o corrupto",
        ErrorCodes.ERR_SEM_VAR_NO_DECLARADA: "Variable '{nombre}' no declarada en este ámbito",
        ErrorCodes.ERR_SEM_TIPO_INCOMPATIBLE: "Tipos incompatibles: no se puede usar '{tipo1}' con '{tipo2}' en '{operacion}'",
        ErrorCodes.ERR_SEM_TIPO_RETORNO: "Tipo de retorno incorrecto: se esperaba '{esperado}', se obtuvo '{obtenido}'",
        ErrorCodes.ERR_SEM_FUNC_NO_DEFINIDA: "Función '{nombre}' no definida",
        ErrorCodes.ERR_SEM_REDEFINICION: "Redefinición de '{nombre}' en el mismo ámbito",
        ErrorCodes.ERR_SEM_ARGUMENTOS_INVALIDOS: "Cantidad de argumentos inválida para '{nombre}': se esperaban {esperados}",
        ErrorCodes.ERR_SEM_ESTRUCTURA_NO_DEFINIDA: "Estructura '{nombre}' no definida",
        ErrorCodes.ERR_SEM_CAMPO_NO_EXISTE: "La estructura '{struct}' no tiene un campo '{campo}'",
        ErrorCodes.ERR_SEM_VAR_MOVIDA: "Uso ilegal de variable ya movida '{nombre}' (E-501)",
        ErrorCodes.ERR_SEM_ACCESO_MEMORIA_MOVIDA: "Acceso prohibido a memoria movida '{nombre}' (E-502)",
        ErrorCodes.ERR_SEM_RESULTADO_SIN_DESEMPAQUETAR: "Resultado de canal sin desempaquetar '{nombre}' (E-503)",
        ErrorCodes.ERR_SEM_EXHAUSTIVE_MATCH_REQUIRED: "Sentencia 'coincidir' no exhaustiva: faltan {faltan} variante(s). Use '_' como comodin o anada los casos faltantes",
        ErrorCodes.ERR_MEM_BORROW_CONFLICT: "Conflicto de prestamo sobre '{nombre}': prestamo {tipo} incompatible con prestamos activos (Manual 4 S4.2)",
        ErrorCodes.ERR_MANIFEST_NOT_FOUND: "Manifiesto axon.toml no encontrado en el directorio actual (E-600)",
        ErrorCodes.ERR_MODULE_STD_NOT_FOUND: "Módulo estándar '{modulo}' no encontrado. Sysroot corrupto (E-601)",
        ErrorCodes.ERR_MODULE_AXON_NOT_FOUND: "Dependencia '{modulo}' no encontrada en axon_modules. Ejecute 'synapse construir' para descargar (E-602)",
        ErrorCodes.ERR_DEP_NOT_DECLARED: "Dependencia '{modulo}' importada en el código pero no declarada en el manifiesto axon.toml (E-603)",
        ErrorCodes.ERR_LOCK_HASH_MISMATCH: "Infracción criptográfica. El hash de la dependencia '{modulo}' no coincide con axon.lock (E-604)",
        ErrorCodes.ERR_GIT_FAILURE: "Error de red o revisión Git inválida para la dependencia '{modulo}' (E-605)",
        ErrorCodes.ERR_SEM_ASM_FUERA_INSEGURO: "asm() solo puede usarse dentro de un bloque 'inseguro:'",
        ErrorCodes.ERR_SEM_CONSTANTE_INMUTABLE: "No se puede reasignar la constante '{nombre}'",
        ErrorCodes.ERR_MEM_USE_AFTER_MOVE: "Acceso a variable '{nombre}' despues de move por lanzar/concurrencia (E-504)",
        ErrorCodes.ERR_SEM_TYPE_AMBIGUOUS: "Expresion con tipo ambiguo: no se puede inferir '{tipo}'",
        ErrorCodes.ERR_VER_WHILE_INACOTADO: "Bucle 'mientras' sin cota estatica comprobable en modo --safe (E-700). Use 'para' con rango fijo.",
        ErrorCodes.ERR_VER_MUTACION_GLOBAL: "Mutacion de variable global '{nombre}' prohibida en modo --safe (E-701)",
        ErrorCodes.ERR_VER_RECURSION_NO_TERMINAL: "Funcion '{nombre}' recursiva sin convergencia estructural comprobable en modo --safe (E-702)",
        ErrorCodes.ERR_VER_CONTRATO_INVALIDO: "Contrato invalido en funcion '{nombre}': {detalle} (E-703)",
    },
    'en': {
        ErrorCodes.ERR_SYNTAX_EXPECTED_TOKEN: "Expected {esperado}, found '{encontrado}'",
        ErrorCodes.ERR_SYNTAX_UNEXPECTED_TOKEN: "Unexpected token '{tok_name}' after expression",
        ErrorCodes.ERR_SYNTAX_UNEXPECTED_EXPR: "Unexpected expression: '{tipo}'",
        ErrorCodes.ERR_SYNTAX_EXPECTED_NEWLINE: "Expected newline after '{construccion}'",
        ErrorCodes.ERR_LANG_MISSING: "Missing language declaration '#lang: <code>' at line 1",
        ErrorCodes.ERR_LANG_UNSUPPORTED: "Language '{idioma}' not supported. Available: {soportados}",
        ErrorCodes.ERR_INDENT_INVALID: "Indentation must be a multiple of 4 spaces",
        ErrorCodes.ERR_INDENT_INCONSISTENT: "Inconsistent indentation level",
        ErrorCodes.ERR_STRING_UNCLOSED: "Unclosed string literal",
        ErrorCodes.ERR_LEX: "{mensaje}",
        ErrorCodes.ERR_LEX_CHAR_UNEXPECTED: "Unexpected character '{char}'",
        ErrorCodes.ERR_FILE_NOT_FOUND: "File not found: {archivo}",
        ErrorCodes.ERR_CANONICAL_FORMAT: "Unrecognized or corrupted canonical format",
        ErrorCodes.ERR_SEM_VAR_NO_DECLARADA: "Variable '{nombre}' not declared in this scope",
        ErrorCodes.ERR_SEM_TIPO_INCOMPATIBLE: "Incompatible types: cannot use '{tipo1}' with '{tipo2}' in '{operacion}'",
        ErrorCodes.ERR_SEM_TIPO_RETORNO: "Incorrect return type: expected '{esperado}', got '{obtenido}'",
        ErrorCodes.ERR_SEM_FUNC_NO_DEFINIDA: "Function '{nombre}' not defined",
        ErrorCodes.ERR_SEM_REDEFINICION: "Redefinition of '{nombre}' in the same scope",
        ErrorCodes.ERR_SEM_ARGUMENTOS_INVALIDOS: "Invalid argument count for '{nombre}': expected {esperados}",
        ErrorCodes.ERR_SEM_ESTRUCTURA_NO_DEFINIDA: "Struct '{nombre}' not defined",
        ErrorCodes.ERR_SEM_CAMPO_NO_EXISTE: "Struct '{struct}' has no field '{campo}'",
        ErrorCodes.ERR_SEM_VAR_MOVIDA: "Illegal use of already moved variable '{nombre}' (E-501)",
        ErrorCodes.ERR_SEM_ACCESO_MEMORIA_MOVIDA: "Forbidden access to moved memory '{nombre}' (E-502)",
        ErrorCodes.ERR_SEM_RESULTADO_SIN_DESEMPAQUETAR: "Unpacked channel result '{nombre}' (E-503)",
        ErrorCodes.ERR_SEM_EXHAUSTIVE_MATCH_REQUIRED: "Non-exhaustive 'match' pattern: missing {faltan} variant(s). Add remaining cases or use '_' wildcard",
        ErrorCodes.ERR_MEM_BORROW_CONFLICT: "Borrow conflict on '{nombre}': borrow {tipo} incompatible with active borrows (Manual 4 S4.2)",
        ErrorCodes.ERR_MANIFEST_NOT_FOUND: "axon.toml manifest not found in current directory (E-600)",
        ErrorCodes.ERR_MODULE_STD_NOT_FOUND: "Standard module '{modulo}' not found. Corrupt Sysroot (E-601)",
        ErrorCodes.ERR_MODULE_AXON_NOT_FOUND: "Dependency '{modulo}' not found in axon_modules. Run 'synapse construir' to download (E-602)",
        ErrorCodes.ERR_DEP_NOT_DECLARED: "Dependency '{modulo}' imported in code but not declared in axon.toml manifest (E-603)",
        ErrorCodes.ERR_LOCK_HASH_MISMATCH: "Cryptographic breach. Hash of dependency '{modulo}' does not match axon.lock (E-604)",
        ErrorCodes.ERR_GIT_FAILURE: "Network error or invalid Git revision for dependency '{modulo}' (E-605)",
        ErrorCodes.ERR_SEM_ASM_FUERA_INSEGURO: "asm() can only be used inside an 'unsafe:' block",
        ErrorCodes.ERR_SEM_CONSTANTE_INMUTABLE: "Cannot reassign constant '{nombre}'",
        ErrorCodes.ERR_MEM_USE_AFTER_MOVE: "Access to variable '{nombre}' after move by lanzar/concurrency (E-504)",
        ErrorCodes.ERR_SEM_TYPE_AMBIGUOUS: "Ambiguous expression type: cannot infer '{tipo}'",
        ErrorCodes.ERR_VER_WHILE_INACOTADO: "Unbounded 'while' loop without static bound in --safe mode (E-700). Use 'for' with fixed range.",
        ErrorCodes.ERR_VER_MUTACION_GLOBAL: "Global variable '{nombre}' mutation forbidden in --safe mode (E-701)",
        ErrorCodes.ERR_VER_RECURSION_NO_TERMINAL: "Recursive function '{nombre}' without structural convergence in --safe mode (E-702)",
        ErrorCodes.ERR_VER_CONTRATO_INVALIDO: "Invalid contract in function '{nombre}': {detalle} (E-703)",
    },
    'fr': {
        ErrorCodes.ERR_SYNTAX_EXPECTED_TOKEN: "Attendu {esperado}, trouve '{encontrado}'",
        ErrorCodes.ERR_SYNTAX_UNEXPECTED_TOKEN: "Token inattendu '{tok_name}' apres l'expression",
        ErrorCodes.ERR_SYNTAX_UNEXPECTED_EXPR: "Expression inattendue: '{tipo}'",
        ErrorCodes.ERR_SYNTAX_EXPECTED_NEWLINE: "Nouvelle ligne attendue apres '{construccion}'",
        ErrorCodes.ERR_LANG_MISSING: "Declaration de langue manquante '#lang: <code>' a la ligne 1",
        ErrorCodes.ERR_LANG_UNSUPPORTED: "Langue '{idioma}' non prise en charge. Disponibles: {soportados}",
        ErrorCodes.ERR_INDENT_INVALID: "L'indentation doit etre un multiple de 4 espaces",
        ErrorCodes.ERR_INDENT_INCONSISTENT: "Niveau d'indentation incoherent",
        ErrorCodes.ERR_STRING_UNCLOSED: "Chaine non fermee",
        ErrorCodes.ERR_LEX: "{mensaje}",
        ErrorCodes.ERR_LEX_CHAR_UNEXPECTED: "Caractere inattendu '{char}'",
        ErrorCodes.ERR_FILE_NOT_FOUND: "Fichier non trouve: {archivo}",
        ErrorCodes.ERR_CANONICAL_FORMAT: "Format canonique non reconnu ou corrompu",
        ErrorCodes.ERR_SEM_VAR_NO_DECLARADA: "Variable '{nombre}' non declaree dans cette portee",
        ErrorCodes.ERR_SEM_TIPO_INCOMPATIBLE: "Types incompatibles: impossible d'utiliser '{tipo1}' avec '{tipo2}' dans '{operacion}'",
        ErrorCodes.ERR_SEM_TIPO_RETORNO: "Type de retour incorrect: attendu '{esperado}', recu '{obtenido}'",
        ErrorCodes.ERR_SEM_FUNC_NO_DEFINIDA: "Fonction '{nombre}' non definie",
        ErrorCodes.ERR_SEM_REDEFINICION: "Redefinition de '{nombre}' dans la meme portee",
        ErrorCodes.ERR_SEM_ARGUMENTOS_INVALIDOS: "Nombre d'arguments invalide pour '{nombre}': attendu {esperados}",
        ErrorCodes.ERR_SEM_ESTRUCTURA_NO_DEFINIDA: "Structure '{nombre}' non definie",
        ErrorCodes.ERR_SEM_CAMPO_NO_EXISTE: "La structure '{struct}' n'a pas de champ '{campo}'",
        ErrorCodes.ERR_SEM_VAR_MOVIDA: "Utilisation illegale de variable deja deplacee '{nombre}' (E-501)",
        ErrorCodes.ERR_SEM_ACCESO_MEMORIA_MOVIDA: "Acces interdit a la memoire deplacee '{nombre}' (E-502)",
        ErrorCodes.ERR_SEM_RESULTADO_SIN_DESEMPAQUETAR: "Resultat de canal non depaquete '{nombre}' (E-503)",
        ErrorCodes.ERR_SEM_EXHAUSTIVE_MATCH_REQUIRED: "Pattern 'coincidir' non exhaustif: variante(s) manquante(s) {faltan}. Ajoutez les cas restants ou utilisez '_'",
        ErrorCodes.ERR_MEM_BORROW_CONFLICT: "Conflit d'emprunt sur '{nombre}': emprunt {tipo} incompatible avec les emprunts actifs (Manuel 4 S4.2)",
        ErrorCodes.ERR_MANIFEST_NOT_FOUND: "Manifest axon.toml introuvable dans le repertoire actuel (E-600)",
        ErrorCodes.ERR_MODULE_STD_NOT_FOUND: "Module standard '{modulo}' introuvable. Sysroot corrompu (E-601)",
        ErrorCodes.ERR_MODULE_AXON_NOT_FOUND: "Dependance '{modulo}' introuvable dans axon_modules. Executez 'synapse construire' pour telecharger (E-602)",
        ErrorCodes.ERR_DEP_NOT_DECLARED: "Dependance '{modulo}' importee dans le code mais non declaree dans le manifest axon.toml (E-603)",
        ErrorCodes.ERR_LOCK_HASH_MISMATCH: "Breche cryptographique. Le hachage de la dependance '{modulo}' ne correspond pas a axon.lock (E-604)",
        ErrorCodes.ERR_GIT_FAILURE: "Erreur reseau ou revision Git invalide pour la dependance '{modulo}' (E-605)",
        ErrorCodes.ERR_SEM_ASM_FUERA_INSEGURO: "asm() ne peut etre utilise qu'a l'interieur d'un bloc 'dangereux:'",
        ErrorCodes.ERR_SEM_CONSTANTE_INMUTABLE: "Impossible de reassigner la constante '{nombre}'",
        ErrorCodes.ERR_MEM_USE_AFTER_MOVE: "Acces a la variable '{nombre}' apres deplacement par lancer/concurrence (E-504)",
        ErrorCodes.ERR_SEM_TYPE_AMBIGUOUS: "Type d'expression ambigu: impossible de deduire '{tipo}'",
    },
    'pt': {
        ErrorCodes.ERR_SYNTAX_EXPECTED_TOKEN: "Esperado {esperado}, encontrado '{encontrado}'",
        ErrorCodes.ERR_SYNTAX_UNEXPECTED_TOKEN: "Token inesperado '{tok_name}' apos expressao",
        ErrorCodes.ERR_SYNTAX_UNEXPECTED_EXPR: "Expressao inesperada: '{tipo}'",
        ErrorCodes.ERR_SYNTAX_EXPECTED_NEWLINE: "Nova linha esperada apos '{construccion}'",
        ErrorCodes.ERR_LANG_MISSING: "Declaracao de idioma ausente '#lang: <codigo>' na linha 1",
        ErrorCodes.ERR_LANG_UNSUPPORTED: "Idioma '{idioma}' nao suportado. Disponiveis: {soportados}",
        ErrorCodes.ERR_INDENT_INVALID: "A indentacao deve ser multipla de 4 espacos",
        ErrorCodes.ERR_INDENT_INCONSISTENT: "Nivel de indentacao inconsistente",
        ErrorCodes.ERR_STRING_UNCLOSED: "String nao fechada",
        ErrorCodes.ERR_LEX: "{mensaje}",
        ErrorCodes.ERR_LEX_CHAR_UNEXPECTED: "Caractere inesperado '{char}'",
        ErrorCodes.ERR_FILE_NOT_FOUND: "Arquivo nao encontrado: {archivo}",
        ErrorCodes.ERR_CANONICAL_FORMAT: "Formato canonico nao reconhecido ou corrompido",
        ErrorCodes.ERR_SEM_VAR_NO_DECLARADA: "Variavel '{nombre}' nao declarada neste escopo",
        ErrorCodes.ERR_SEM_TIPO_INCOMPATIBLE: "Tipos incompativeis: nao e possivel usar '{tipo1}' com '{tipo2}' em '{operacion}'",
        ErrorCodes.ERR_SEM_TIPO_RETORNO: "Tipo de retorno incorreto: esperado '{esperado}', obtido '{obtenido}'",
        ErrorCodes.ERR_SEM_FUNC_NO_DEFINIDA: "Funcao '{nombre}' nao definida",
        ErrorCodes.ERR_SEM_REDEFINICION: "Redefinicao de '{nombre}' no mesmo escopo",
        ErrorCodes.ERR_SEM_ARGUMENTOS_INVALIDOS: "Numero de argumentos invalido para '{nombre}': esperado {esperados}",
        ErrorCodes.ERR_SEM_ESTRUCTURA_NO_DEFINIDA: "Estrutura '{nombre}' nao definida",
        ErrorCodes.ERR_SEM_CAMPO_NO_EXISTE: "A estrutura '{struct}' nao tem campo '{campo}'",
        ErrorCodes.ERR_SEM_VAR_MOVIDA: "Uso ilegal de variavel ja movida '{nombre}' (E-501)",
        ErrorCodes.ERR_SEM_ACCESO_MEMORIA_MOVIDA: "Acesso proibido a memoria movida '{nombre}' (E-502)",
        ErrorCodes.ERR_SEM_RESULTADO_SIN_DESEMPAQUETAR: "Resultado de canal nao desempacotado '{nombre}' (E-503)",
        ErrorCodes.ERR_SEM_EXHAUSTIVE_MATCH_REQUIRED: "Padrao 'coincidir' nao exaustivo: faltam {faltan} variante(s). Adicione os casos restantes ou use '_'",
        ErrorCodes.ERR_MEM_BORROW_CONFLICT: "Conflito de emprestimo sobre '{nombre}': emprestimo {tipo} incompativel com emprestimos ativos (Manual 4 S4.2)",
        ErrorCodes.ERR_MANIFEST_NOT_FOUND: "Manifesto axon.toml nao encontrado no diretorio atual (E-600)",
        ErrorCodes.ERR_MODULE_STD_NOT_FOUND: "Modulo padrao '{modulo}' nao encontrado. Sysroot corrompido (E-601)",
        ErrorCodes.ERR_MODULE_AXON_NOT_FOUND: "Dependencia '{modulo}' nao encontrada em axon_modules. Execute 'synapse construir' para baixar (E-602)",
        ErrorCodes.ERR_DEP_NOT_DECLARED: "Dependencia '{modulo}' importada no codigo mas nao declarada no manifesto axon.toml (E-603)",
        ErrorCodes.ERR_LOCK_HASH_MISMATCH: "Violacao criptografica. O hash da dependencia '{modulo}' nao corresponde ao axon.lock (E-604)",
        ErrorCodes.ERR_GIT_FAILURE: "Erro de rede ou revisao Git invalida para a dependencia '{modulo}' (E-605)",
        ErrorCodes.ERR_SEM_ASM_FUERA_INSEGURO: "asm() so pode ser usado dentro de um bloco 'inseguro:'",
        ErrorCodes.ERR_SEM_CONSTANTE_INMUTABLE: "Nao e possivel reatribuir a constante '{nombre}'",
        ErrorCodes.ERR_MEM_USE_AFTER_MOVE: "Acesso a variavel '{nombre}' apos move por lancar/concorrencia (E-504)",
        ErrorCodes.ERR_SEM_TYPE_AMBIGUOUS: "Tipo de expressao ambiguo: nao e possivel inferir '{tipo}'",
    },
    'de': {
        ErrorCodes.ERR_SYNTAX_EXPECTED_TOKEN: "Erwartet {esperado}, gefunden '{encontrado}'",
        ErrorCodes.ERR_SYNTAX_UNEXPECTED_TOKEN: "Unerwartetes Token '{tok_name}' nach Ausdruck",
        ErrorCodes.ERR_SYNTAX_UNEXPECTED_EXPR: "Unerwarteter Ausdruck: '{tipo}'",
        ErrorCodes.ERR_SYNTAX_EXPECTED_NEWLINE: "Neue Zeile erwartet nach '{construccion}'",
        ErrorCodes.ERR_LANG_MISSING: "Sprachdeklaration '#lang: <code>' in Zeile 1 fehlt",
        ErrorCodes.ERR_LANG_UNSUPPORTED: "Sprache '{idioma}' nicht unterstuetzt. Verfuegbar: {soportados}",
        ErrorCodes.ERR_INDENT_INVALID: "Einrueckung muss ein Vielfaches von 4 Leerzeichen sein",
        ErrorCodes.ERR_INDENT_INCONSISTENT: "Inkonsistente Einrueckungsebene",
        ErrorCodes.ERR_STRING_UNCLOSED: "Nicht geschlossener String",
        ErrorCodes.ERR_LEX: "{mensaje}",
        ErrorCodes.ERR_LEX_CHAR_UNEXPECTED: "Unerwartetes Zeichen '{char}'",
        ErrorCodes.ERR_FILE_NOT_FOUND: "Datei nicht gefunden: {archivo}",
        ErrorCodes.ERR_CANONICAL_FORMAT: "Nicht erkanntes oder beschaeigtes kanonisches Format",
        ErrorCodes.ERR_SEM_VAR_NO_DECLARADA: "Variable '{nombre}' in diesem Bereich nicht deklariert",
        ErrorCodes.ERR_SEM_TIPO_INCOMPATIBLE: "Inkompatible Typen: '{tipo1}' kann nicht mit '{tipo2}' in '{operacion}' verwendet werden",
        ErrorCodes.ERR_SEM_TIPO_RETORNO: "Falscher Rueckgabetyp: erwartet '{esperado}', erhalten '{obtenido}'",
        ErrorCodes.ERR_SEM_FUNC_NO_DEFINIDA: "Funktion '{nombre}' nicht definiert",
        ErrorCodes.ERR_SEM_REDEFINICION: "Neudefinition von '{nombre}' im selben Bereich",
        ErrorCodes.ERR_SEM_ARGUMENTOS_INVALIDOS: "Ungueltige Argumentanzahl fuer '{nombre}': erwartet {esperados}",
        ErrorCodes.ERR_SEM_ESTRUCTURA_NO_DEFINIDA: "Struktur '{nombre}' nicht definiert",
        ErrorCodes.ERR_SEM_CAMPO_NO_EXISTE: "Struktur '{struct}' hat kein Feld '{campo}'",
        ErrorCodes.ERR_SEM_VAR_MOVIDA: "Ungueltige Verwendung bereits verschobener Variable '{nombre}' (E-501)",
        ErrorCodes.ERR_SEM_ACCESO_MEMORIA_MOVIDA: "Verbotener Zugriff auf verschobenen Speicher '{nombre}' (E-502)",
        ErrorCodes.ERR_SEM_RESULTADO_SIN_DESEMPAQUETAR: "Nicht entpacktes Kanal-Ergebnis '{nombre}' (E-503)",
        ErrorCodes.ERR_SEM_EXHAUSTIVE_MATCH_REQUIRED: "Nicht-exhaustives 'coincidir'-Muster: {faltan} Variante(n) fehlt(en). Fuegen Sie die restlichen Faelle hinzu oder verwenden Sie '_'",
        ErrorCodes.ERR_MEM_BORROW_CONFLICT: "Ausleihkonflikt bei '{nombre}': Ausleihe {tipo} inkompatibel mit aktiven Ausleihen (Handbuch 4 S4.2)",
        ErrorCodes.ERR_MANIFEST_NOT_FOUND: "axon.toml-Manifest im aktuellen Verzeichnis nicht gefunden (E-600)",
        ErrorCodes.ERR_MODULE_STD_NOT_FOUND: "Standardmodul '{modulo}' nicht gefunden. Sysroot beschaeigt (E-601)",
        ErrorCodes.ERR_MODULE_AXON_NOT_FOUND: "Abhaengigkeit '{modulo}' nicht in axon_modules gefunden. Fuehren Sie 'synapse construir' zum Herunterladen aus (E-602)",
        ErrorCodes.ERR_DEP_NOT_DECLARED: "Abhaengigkeit '{modulo}' im Code importiert aber nicht im axon.toml-Manifest deklariert (E-603)",
        ErrorCodes.ERR_LOCK_HASH_MISMATCH: "Kryptographische Sicherheitsverletzung. Der Hash der Abhaengigkeit '{modulo}' stimmt nicht mit axon.lock ueberein (E-604)",
        ErrorCodes.ERR_GIT_FAILURE: "Netzwerkfehler oder ungueltige Git-Revision fuer Abhaengigkeit '{modulo}' (E-605)",
        ErrorCodes.ERR_SEM_ASM_FUERA_INSEGURO: "asm() kann nur innerhalb eines 'unsicher:' Blocks verwendet werden",
        ErrorCodes.ERR_SEM_CONSTANTE_INMUTABLE: "Konstante '{nombre}' kann nicht neu zugewiesen werden",
        ErrorCodes.ERR_MEM_USE_AFTER_MOVE: "Zugriff auf Variable '{nombre}' nach Verschiebung durch lanzar/Nebenlaufigkeit (E-504)",
        ErrorCodes.ERR_SEM_TYPE_AMBIGUOUS: "Mehrdeutiger Ausdruckstyp: '{tipo}' kann nicht abgeleitet werden",
    },
    'it': {
        ErrorCodes.ERR_SYNTAX_EXPECTED_TOKEN: "Previsto {esperado}, trovato '{encontrado}'",
        ErrorCodes.ERR_SYNTAX_UNEXPECTED_TOKEN: "Token inaspettato '{tok_name}' dopo l'espressione",
        ErrorCodes.ERR_SYNTAX_UNEXPECTED_EXPR: "Espressione inaspettata: '{tipo}'",
        ErrorCodes.ERR_SYNTAX_EXPECTED_NEWLINE: "Nuova riga prevista dopo '{construccion}'",
        ErrorCodes.ERR_LANG_MISSING: "Dichiarazione della lingua mancante '#lang: <codice>' alla riga 1",
        ErrorCodes.ERR_LANG_UNSUPPORTED: "Lingua '{idioma}' non supportata. Disponibili: {soportados}",
        ErrorCodes.ERR_INDENT_INVALID: "L'indentazione deve essere un multiplo di 4 spazi",
        ErrorCodes.ERR_INDENT_INCONSISTENT: "Livello di indentazione incoerente",
        ErrorCodes.ERR_STRING_UNCLOSED: "Stringa non chiusa",
        ErrorCodes.ERR_LEX: "{mensaje}",
        ErrorCodes.ERR_LEX_CHAR_UNEXPECTED: "Carattere inaspettato '{char}'",
        ErrorCodes.ERR_FILE_NOT_FOUND: "File non trovato: {archivo}",
        ErrorCodes.ERR_CANONICAL_FORMAT: "Formato canonico non riconosciuto o corrotto",
        ErrorCodes.ERR_SEM_VAR_NO_DECLARADA: "Variabile '{nombre}' non dichiarata in questo ambito",
        ErrorCodes.ERR_SEM_TIPO_INCOMPATIBLE: "Tipi incompatibili: impossibile usare '{tipo1}' con '{tipo2}' in '{operacion}'",
        ErrorCodes.ERR_SEM_TIPO_RETORNO: "Tipo di ritorno errato: previsto '{esperado}', ottenuto '{obtenido}'",
        ErrorCodes.ERR_SEM_FUNC_NO_DEFINIDA: "Funzione '{nombre}' non definita",
        ErrorCodes.ERR_SEM_REDEFINICION: "Ridefinizione di '{nombre}' nello stesso ambito",
        ErrorCodes.ERR_SEM_ARGUMENTOS_INVALIDOS: "Numero di argomenti non valido per '{nombre}': previsti {esperados}",
        ErrorCodes.ERR_SEM_ESTRUCTURA_NO_DEFINIDA: "Struttura '{nombre}' non definita",
        ErrorCodes.ERR_SEM_CAMPO_NO_EXISTE: "La struttura '{struct}' non ha un campo '{campo}'",
        ErrorCodes.ERR_SEM_VAR_MOVIDA: "Uso illegale di variabile gia spostata '{nombre}' (E-501)",
        ErrorCodes.ERR_SEM_ACCESO_MEMORIA_MOVIDA: "Accesso vietato alla memoria spostata '{nombre}' (E-502)",
        ErrorCodes.ERR_SEM_RESULTADO_SIN_DESEMPAQUETAR: "Risultato canale non spacchettato '{nombre}' (E-503)",
        ErrorCodes.ERR_SEM_EXHAUSTIVE_MATCH_REQUIRED: "Pattern 'coincidir' non esaustivo: mancano {faltan} variante/i. Aggiungere i casi rimanenti o usare '_'",
        ErrorCodes.ERR_MEM_BORROW_CONFLICT: "Conflitto di prestito su '{nombre}': prestito {tipo} incompatibile con prestiti attivi (Manuale 4 S4.2)",
        ErrorCodes.ERR_MANIFEST_NOT_FOUND: "Manifesto axon.toml non trovato nella directory corrente (E-600)",
        ErrorCodes.ERR_MODULE_STD_NOT_FOUND: "Modulo standard '{modulo}' non trovato. Sysroot corrotto (E-601)",
        ErrorCodes.ERR_MODULE_AXON_NOT_FOUND: "Dipendenza '{modulo}' non trovata in axon_modules. Eseguire 'synapse costruire' per scaricare (E-602)",
        ErrorCodes.ERR_DEP_NOT_DECLARED: "Dipendenza '{modulo}' importata nel codice ma non dichiarata nel manifesto axon.toml (E-603)",
        ErrorCodes.ERR_LOCK_HASH_MISMATCH: "Violazione crittografica. L'hash della dipendenza '{modulo}' non corrisponde a axon.lock (E-604)",
        ErrorCodes.ERR_GIT_FAILURE: "Errore di rete o revisione Git non valida per la dipendenza '{modulo}' (E-605)",
        ErrorCodes.ERR_SEM_ASM_FUERA_INSEGURO: "asm() puo essere usato solo all'interno di un blocco 'non_sicuro:'",
        ErrorCodes.ERR_SEM_CONSTANTE_INMUTABLE: "Impossibile riassegnare la costante '{nombre}'",
        ErrorCodes.ERR_MEM_USE_AFTER_MOVE: "Accesso alla variabile '{nombre}' dopo spostamento da lanciare/concorrenza (E-504)",
        ErrorCodes.ERR_SEM_TYPE_AMBIGUOUS: "Tipo di espressione ambiguo: impossibile dedurre '{tipo}'",
    },
}


class DiagnosticManager:
    def __init__(self, idioma: str = 'es', fuente_lineas: Optional[List[str]] = None,
                 ruta_archivo: str = '<entrada>'):
        self.errores: List[dict] = []
        self.idioma = idioma if idioma in ERROR_MESSAGES else 'es'
        self.fuente_lineas = fuente_lineas or []
        self.ruta_archivo = ruta_archivo
        self._mensajes = ERROR_MESSAGES[self.idioma]

    def _obtener_linea_contexto(self, linea_num: int) -> str:
        if not self.fuente_lineas or linea_num < 1 or linea_num > len(self.fuente_lineas):
            return ""
        return self.fuente_lineas[linea_num - 1].rstrip('\n')

    def reportar(self, codigo: ErrorCodes, token: Optional[Token] = None,
                 **contexto) -> None:
        linea = token.linea if token else 0
        columna = token.columna if token else 0
        plantilla = self._mensajes.get(codigo, f"Error {codigo.name}")
        mensaje = plantilla.format(**contexto) if contexto else plantilla

        loc = f"{self.ruta_archivo}:{linea}:{columna}" if linea else self.ruta_archivo
        entry = f"[Synapse] {loc} - {mensaje}"

        linea_ctx = self._obtener_linea_contexto(linea)
        if linea_ctx:
            entry += f"\n  --> {linea_ctx}"
            if columna > 0:
                entry += f"\n      {' ' * (columna - 1)}^"

        print(entry, file=sys.stderr)
        self.errores.append({
            'codigo': codigo,
            'linea': linea,
            'columna': columna,
            'mensaje': mensaje,
        })

    def hay_errores(self) -> bool:
        return len(self.errores) > 0

    def contar(self) -> int:
        return len(self.errores)

    def codigo_salida(self) -> int:
        return 1 if self.hay_errores() else 0

    def resumen(self) -> str:
        if not self.hay_errores():
            return "0 errores"
        return f"{self.contar()} error{'es' if self.contar() > 1 else ''} encontrado{'s' if self.contar() > 1 else ''}"
