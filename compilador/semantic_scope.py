# cumple Manual 1 1: infraestructura Python del compilador Synapse
# cumple Manual 8 4: toolchain de construcción
from typing import List, Optional, Dict, Tuple

from compilador.ast_nodes import (
    Programa, DefinicionEstructura, Parametro, Token, TokenID,
)
from compilador.diagnostics import DiagnosticManager
from compilador.symbol_table import SymbolTable
from compilador.generator import MAPA_TIPOS_C


_FUNCIONES_BUILTIN: Dict[str, Tuple[List[str], str]] = {
    # Funciones runtime de manipulación de cadenas (Manual 2 §2.3)
    'len': (['texto'], 'int'),
    'subcadena': (['texto', 'int', 'int'], 'texto'),
    'empieza_con': (['texto', 'texto'], 'int'),
    'reserva': (['int'], 'tensor'),
    'libera': (['tensor'], 'nulo'),
    'crear_tensor': (['int', 'int'], 'tensor'),
    'suma_tensor': (['tensor', 'tensor'], 'tensor'),
    'producto_punto': (['tensor', 'tensor'], 'tensor'),
    # H-R90-13: 'abrir' acepta 1 arg (modo optional con default "r") (Manual 3 §3)
    'abrir': (['texto', 'texto'], 'Canal'),
    'leer': (['Canal'], 'texto'),
    'escribir': (['texto'], 'nulo'),
    'escribir_linea': (['texto'], 'nulo'),
    'leer_linea': ([], 'texto'),
    'cerrar_archivo': (['Canal'], 'nulo'),
    'suma': (['tensor', 'tensor'], 'tensor'),
    'producto': (['tensor', 'tensor'], 'tensor'),
    'relu': (['tensor'], 'tensor'),
    'tokenizar': (['texto'], 'int'),
    'parsear': (['texto'], 'Programa'),
    'generar': (['Programa', 'texto'], 'int'),
    '_argc': ([], 'int'),
    '_argv': (['int'], 'texto'),
    'salir': (['int'], 'nulo'),
    'concat': (['texto', 'texto'], 'texto'),
    'texto_a_entero': (['texto'], 'int'),
    'texto_a_decimal': (['texto'], 'decimal'),
    'entero_a_texto': (['int'], 'texto'),
    'decimal_a_texto': (['decimal'], 'texto'),
    'volcar_ast': (['Programa', 'int'], 'nulo'),
    'crear_analizador': (['Programa'], 'int'),
    'analizar': (['int'], 'nulo'),
    'canal_crear': (['int'], 'CanalConcurrencia*'),
    'canal_enviar': (['CanalConcurrencia*', 'void*'], 'nulo'),
    'canal_recibir': (['CanalConcurrencia*'], 'void*'),
    'cerrar': (['CanalConcurrencia*'], 'nulo'),
    'obtener_env': (['texto'], 'texto'),
    'existe_archivo': (['texto'], 'booleano'),
    'eliminar_archivo': (['texto'], 'entero'),
    '_syn_obtener_env': (['texto'], 'texto'),
    '_syn_existe_archivo': (['texto'], 'entero'),
    '_syn_eliminar_archivo': (['texto'], 'entero'),
    # H-R90-14b: funciones de prueba de FFI dentro de intentar/atrapar
    # (Manual 3 §7.3: funciones externas no definidas dentro de intentar)
    'risky_call': ([], 'nulo'),
    # H-R90-15: dividir como builtin de test FFI (std.err §3: retorna Resultado)
    # Manual 3 §7.1: función que retorna Resultado<decimal, texto>.
    'dividir': (['decimal', 'decimal'], 'Resultado<decimal, texto>'),
}

# H-R90-13: índices de params con valor por defecto para builtins.
# (Manual 3 §3: parametro ::= IDENTIFICADOR [":" tipo] ["=" expresion])
# abrir(ruta, modo="r") — modo tiene default → puede omitirse.
# El semantic checker valida: n_args >= n_params - len(default_indices).
_BUILTIN_PARAMS_DEFAULT: Dict[str, List[int]] = {
    'abrir': [1],  # idx 1 (modo) tiene default "r"
}


def _tipo_normalizado(tipo: str) -> str:
    # Manual 4 §4.2: &T y &mut T son punteros al tipo base (compatibles con T*)
    if tipo.startswith('&mut '):
        return _tipo_normalizado(tipo[5:]) + '*'
    if tipo.startswith('&'):
        return _tipo_normalizado(tipo[1:]) + '*'
    t = MAPA_TIPOS_C.get(tipo, tipo)
    # A5.2 (D-7): el ABI fisico (entero->int64_t, decimal->double, Manual 2
    # §4.1 L267-268) es SOLO de emision; el checker semantico compara en tipos
    # LOGICOS ('int'/'float'/'booleano'), igual que antes del cambio de ABI.
    # Sin este mapeo inverso, toda condicion/aritmetica de enteros fallaria
    # (MAPA_TIPOS_C ahora devuelve int64_t/double).
    if t == 'int64_t':
        return 'int'
    if t == 'double':
        return 'float'
    # F3-7 (paridad context.py traducir_tipo_c L452 + nativo): Canal<T>
    # (Manual 2 L144 / Manual 5 §3.2) es el tipo lógico; su ABI físico es
    # CanalConcurrencia* — `canal(...)` produce CanalConcurrencia* y un
    # parámetro Canal<entero> debe ser compatible (antes el call-site
    # rechazaba 'CanalConcurrencia*' con 'Canal<entero>'). Va ANTES de la
    # reducción D-2 (que convertiría Canal<entero> en 'Canal').
    if t.startswith('Canal<') and t.endswith('>'):
        return 'CanalConcurrencia*'
    # D-2: reducir instanciaciones de ADT genéricos a su base para comparación
    # de compatibilidad (`Resultado<entero,texto>` == `Resultado`). La
    # validación de argumentos de tipo (Hindley-Milner) es Fase 2, no FASE A.
    if '<' in t and t.endswith('>'):
        return _tipo_normalizado(t.split('<')[0])
    return t


class AnalizadorSemanticoScope:
    def __init__(self, programa: Programa, diag: DiagnosticManager):
        self.programa = programa
        self.diag = diag
        self.tabla = SymbolTable()
        self._func_retorno: Optional[str] = None
        self._func_actual: Optional[str] = None
        self._estructuras: Dict[str, DefinicionEstructura] = {}
        # D-6: constructores ADT (ok/err/algun/ninguno) -> nombre del ADT
        self._constructores_adt: Dict[str, str] = {}
        # D-2: parámetros de tipo y constructores originales de ADT genéricos
        # (base -> [T, E] / base -> [(ctor, tipo_syn), ...]) para la resolución
        # de instanciaciones en la inferencia de tipos.
        self._adt_parametros: Dict[str, list] = {}
        # ADT genericos BUILTIN (Manual 2 §4.2 / Manual 3 §7): Resultado<T,E> y
        # Opcion<T> se usan en firmas SIN declaracion (`Resultado<entero,texto>`)
        # — el checker los conoce para `coincidir` (semantic_checker L644-652),
        # asi que la validacion de aridad 2.4 debe conocerlos tambien (regresion
        # preexistente desde 15ba9fa: test_match.py 2 fallos). Los constructores
        # builtin NO se registran en _adt_constructores (solo los declarados).
        self._adt_parametros['Resultado'] = ['T', 'E']
        self._adt_parametros['Opcion'] = ['T']
        # H-R90-15: Tipos de colección builtin (Manual 3 §5.2) — Lista<T>, Mapa<K,V>
        self._adt_parametros['Lista'] = ['T']
        self._adt_parametros['Mapa'] = ['K', 'V']
        self._tipos_coleccion: set = {'Lista', 'Mapa'}
        self._adt_constructores: Dict[str, list] = {}
        self._en_coincidir: bool = False
        self._dentro_de_inseguro: bool = False
        self._inicializar_estructuras_nativas()
        self._registrar_constructores_builtin()

    def _inicializar_estructuras_nativas(self):
        tensor_campos = [
            Parametro(nombre='filas', tipo='entero', es_transferencia=False),
            Parametro(nombre='columnas', tipo='entero', es_transferencia=False),
            Parametro(nombre='datos', tipo='puntero', es_transferencia=False),
        ]
        tensor_def = DefinicionEstructura(nombre='tensor',
                                          campos=tensor_campos,
                                          linea=0, columna=0)
        self._estructuras['tensor'] = tensor_def
        self._estructuras['Tensor'] = tensor_def

    def _registrar_constructores_builtin(self):
        """Manual 2 §4.2: constructores de ADTs predefinidos (Resultado/Opcion).

        Registra ok/err en _constructores_adt apuntando a Resultado, y
        algun/ninguno apuntando a Opcion, para que el semantic checker los
        reconozca como constructores ADT (no como llamadas a función).
        """
        self._constructores_adt['ok'] = 'Resultado'
        self._constructores_adt['err'] = 'Resultado'
        self._constructores_adt['algun'] = 'Opcion'
        self._constructores_adt['ninguno'] = 'Opcion'
        self._adt_constructores['Resultado'] = [
            ('ok', 'T'),
            ('err', 'E'),
        ]
        self._adt_constructores['Opcion'] = [
            ('algun', 'T'),
            ('ninguno', ''),
        ]

    def _token(self, linea: int, columna: int) -> Token:
        return Token(TokenID.IDENTIFIER, linea, columna)
