from enum import Enum, auto
from dataclasses import dataclass, field
from typing import List, Optional, Any


# TokenID alineados al Manual 2 §3 (nombres universales multi-idioma).
# AUDITORIA F1 (H23): renombrados a los TokenID del manual (T_SI, T_SINO,
# T_FUNCION, T_RETORNAR, ...) y añadidos los 14 faltantes (T_LET, T_TIPO,
# T_TENSOR, T_NULO, T_OK, T_ERR, T_ALGUN, T_NINGUNO, T_MODULO, T_DELEGAR,
# T_EXPORT, T_RC, T_ARC, T_DEBIL).
class TokenID(Enum):
    SI = auto()          # T_SI     (si / if)
    SINO = auto()        # T_SINO   (sino / else)
    FUNCION = auto()     # T_FUNCION (funcion / function)
    RETORNAR = auto()    # T_RETORNAR (retornar / return)
    LANZAR = auto()      # T_LANZAR (lanzar / spawn)
    RECUPERAR = auto()   # T_RECUPERAR (recuperar / recover)
    ESCUCHAR = auto()    # T_ESCUCHAR (escuchar / listen)
    MIENTRAS = auto()    # T_MIENTRAS (mientras / while)
    IMPORTAR = auto()    # T_IMPORTAR (importar / import)
    ESTRUCTURA = auto()  # T_ESTRUCTURA (estructura / struct)
    ROMPER = auto()      # T_ROMPER (romper / break)
    SIGUIENTE = auto()   # T_SIGUIENTE (siguiente / continue)
    DOT = auto()
    AND = auto()         # T_AND (y / and)
    OR = auto()          # T_OR (o / or)
    NOT = auto()         # T_NOT (no / not)
    VERDADERO = auto()   # T_VERDADERO (verdadero / true)
    FALSO = auto()       # T_FALSO (falso / false)

    IDENTIFIER = auto()
    NUMBER = auto()
    FLOAT = auto()
    STRING = auto()

    GREATER = auto()
    LESS = auto()
    EQUALS = auto()
    NOT_EQUALS = auto()
    LESS_EQUALS = auto()
    GREATER_EQUALS = auto()
    ASSIGN = auto()
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    MOD = auto()           # T_MOD (% — operador módulo; el keyword T_MODULO está abajo)
    ARROW = auto()
    COINCIDIR = auto()   # T_COINCIDIR (coincidir / match)
    ARROW_RIGHT = auto()

    LPAREN = auto()
    RPAREN = auto()
    COLON = auto()
    COMMA = auto()
    NEWLINE = auto()
    INDENT = auto()
    DEDENT = auto()
    AMPERSAND = auto()
    INSEGURO = auto()
    IMPORTAR_C = auto()
    EXTERNO = auto()
    ARROW_LEFT = auto()   # <-  operador de envío de canal
    REQUIERE = auto()     # palabra clave bloque de contrato
    GARANTIZA = auto()    # palabra clave bloque de contrato
    CANAL = auto()        # tipo Canal<T>
    ASM = auto()          # asm("instruccion")
    CONSTANTE = auto()    # constante IDENTIFICADOR = EXPR
    SEMICOLON = auto()    # ; separador de sentencias
    PARA = auto()         # para (bucle for)
    LBRACKET = auto()     # [ índice de arreglo/tensor
    RBRACKET = auto()     # ]
    PIPE = auto()         # | separador de constructores en declaración de tipo (Manual 2 §2 declaracion_tipo)

    # AUDITORIA F1 (H22): palabras reservadas del Manual 2 §3 que faltaban.
    LET = auto()          # T_LET (let)
    TIPO = auto()         # T_TIPO (tipo / type)
    TENSOR = auto()       # T_TENSOR (tensor)
    NULO = auto()         # T_NULO (nulo / null)
    OK = auto()           # T_OK (ok) — constructor Resultado
    ERR = auto()          # T_ERR (err) — constructor Resultado
    ALGUN = auto()        # T_ALGUN (algun / some) — constructor Opcion
    NINGUNO = auto()      # T_NINGUNO (ninguno / none) — constructor Opcion
    MODULO = auto()       # T_MODULO (modulo / module) — keyword reservado (Manual 2 §3)
    DELEGAR = auto()      # T_DELEGAR (delegar / delegate)
    EXPORT = auto()       # T_EXPORT (@export)
    RC = auto()           # T_RC (rc / rc)
    ARC = auto()          # T_ARC (arc / arc)
    DEBIL = auto()        # T_DEBIL (débil / weak)

    EOF = auto()


@dataclass
class Token:
    tipo: TokenID
    linea: int
    columna: int
    valor: Any = None

    def __repr__(self):
        if self.valor is not None:
            return f"Token({self.tipo.name}, {self.valor!r}) [L{self.linea}:{self.columna}]"
        return f"Token({self.tipo.name}) [L{self.linea}:{self.columna}]"


@dataclass
class Nodo:
    linea: int = 0
    columna: int = 0


@dataclass
class Programa(Nodo):
    sentencias: List[Nodo] = field(default_factory=list)
    is_no_std: bool = False


@dataclass
class Parametro:
    nombre: str = ''
    tipo: str = 'entero'
    es_transferencia: bool = False


@dataclass
class DefinicionFuncion(Nodo):
    nombre: str = ''
    parametros: List[Parametro] = field(default_factory=list)
    tipo_retorno: str = ''
    requiere: List[Nodo] = field(default_factory=list)
    garantiza: List[Nodo] = field(default_factory=list)
    cuerpo: List[Nodo] = field(default_factory=list)


@dataclass
class SentenciaSi(Nodo):
    condicion: Optional[Nodo] = None
    cuerpo: List[Nodo] = field(default_factory=list)
    cuerpo_sino: Optional[List[Nodo]] = None


@dataclass
class SentenciaLanzar(Nodo):
    llamada: Optional[Nodo] = None


@dataclass
class SentenciaRecuperar(Nodo):
    accion_critica: Optional[Nodo] = None
    plan_b: Optional[Nodo] = None


@dataclass
class SentenciaRetornar(Nodo):
    expr: Optional[Nodo] = None
    es_transferencia: bool = False


@dataclass
class SentenciaEscuchar(Nodo):
    canal: Optional[Nodo] = None
    respuesta: Optional[Nodo] = None


@dataclass
class SentenciaMientras(Nodo):
    condicion: Optional[Nodo] = None
    cuerpo: List[Nodo] = field(default_factory=list)


@dataclass
class SentenciaPara(Nodo):
    inicializacion: Optional[Nodo] = None
    condicion: Optional[Nodo] = None
    incremento: Optional[Nodo] = None
    cuerpo: List[Nodo] = field(default_factory=list)


@dataclass
class SentenciaRomper(Nodo):
    pass


@dataclass
class SentenciaSiguiente(Nodo):
    pass


@dataclass
class OpBinaria(Nodo):
    izquierdo: Optional[Nodo] = None
    operador: str = ''
    derecho: Optional[Nodo] = None


@dataclass
class OpUnaria(Nodo):
    operador: str = ''
    expr: Optional[Nodo] = None


@dataclass
class LlamadaFuncion(Nodo):
    nombre: str = ''
    argumentos: List[Nodo] = field(default_factory=list)


@dataclass
class Identificador(Nodo):
    nombre: str = ''


@dataclass
class LiteralNumero(Nodo):
    valor: int = 0


@dataclass
class LiteralDecimal(Nodo):
    valor: float = 0.0


@dataclass
class LiteralCadena(Nodo):
    valor: str = ''


@dataclass
class LiteralBooleano(Nodo):
    valor: bool = False


@dataclass
class SentenciaExpr(Nodo):
    expr: Optional[Nodo] = None


@dataclass
class AsignacionVariable(Nodo):
    nombre: str = ''
    expresion: Optional[Nodo] = None

@dataclass
class DeclaracionVariable(Nodo):
    nombre: str = ''
    tipo: str = ''
    expresion: Optional[Nodo] = None


@dataclass
class LogLlamada(Nodo):
    argumentos: List[Nodo] = field(default_factory=list)


@dataclass
class SentenciaImportar(Nodo):
    ruta: str = ''

@dataclass
class BloqueInseguro(Nodo):
    cuerpo: List[Nodo] = field(default_factory=list)

@dataclass
class ExprObtenerDireccion(Nodo):
    expr: Optional[Nodo] = None
    es_mutable: bool = False  # Manual 4 §4.2: &mut T (mutable) vs &T (inmutable)

@dataclass
class ExprDereferencia(Nodo):
    expr: Optional[Nodo] = None

@dataclass
class TipoPuntero:
    tipo_base: str = ''

@dataclass
class ImportarC(Nodo):
    ruta: str = ''
    es_sistema: bool = False

@dataclass
class DeclaracionExterna(Nodo):
    nombre: str = ''
    parametros: List[Parametro] = field(default_factory=list)
    tipo_retorno: str = ''


@dataclass
class ExprTensor(Nodo):
    filas: Optional[Nodo] = None
    columnas: Optional[Nodo] = None


@dataclass
class LiteralNulo(Nodo):
    """Literal `nulo` (Manual 2 §2: tipo_primitivo nulo / §4.1 ausencia de valor).
    En C se emite como la macro `nulo` (((void*)0)) que ya emite el generador;
    en inferencia de tipos equivale a 'puntero' (paridad con el tratamiento
    previo del identificador 'nulo').
    """
    pass


@dataclass
class ConstructorTipo:
    nombre: str = ''
    tipos: List[str] = field(default_factory=list)


@dataclass
class DeclaracionTipo(Nodo):
    """Declaración de tipo (Manual 2 §2 declaracion_tipo / §4.2).
    - Alias simple: `tipo X = entero`
    - Tipo algebraico: `tipo X = ok(entero) | err(texto)`
    El LHS puede llevar parámetros de tipo: `tipo Opcion<T> = algun(T) | ninguno`
    (se registran en `parametros_tipo`; la emisión C usa el nombre base).
    """
    nombre: str = ''
    parametros_tipo: List[str] = field(default_factory=list)
    tipo_base: str = ''            # alias simple: tipo al que se iguala
    constructores: List[ConstructorTipo] = field(default_factory=list)


@dataclass
class ExprIndice(Nodo):
    expr: Optional[Nodo] = None
    indice: Optional[Nodo] = None


@dataclass
class ArgumentoTransferido(Nodo):
    expr: Optional[Nodo] = None


@dataclass
class DefinicionEstructura(Nodo):
    nombre: str = ''
    campos: List[Parametro] = field(default_factory=list)


@dataclass
class ExprAccesoCampo(Nodo):
    objeto: Optional[Nodo] = None
    nombre_campo: str = ''


@dataclass
class AsignacionCampo(Nodo):
    objeto: Optional[Nodo] = None
    nombre_campo: str = ''
    expresion: Optional[Nodo] = None


@dataclass
class StmtConstante(Nodo):
    nombre: str = ''
    tipo: str = ''      # opcional, vacio si se infiere
    valor: Optional[Nodo] = None


@dataclass
class NodoCaso(Nodo):
    patron: str = ''
    cuerpo: List[Nodo] = field(default_factory=list)
    tipo_extraido: str = ''  # Tipo resuelto de la variable extraída (ej. 'cadena', 'entero', 'flotante')


@dataclass
class NodoCoincidir(Nodo):
    expresion: Optional[Nodo] = None
    casos: List[NodoCaso] = field(default_factory=list)

@dataclass
class ExprAsm(Nodo):
    instruccion: str = ''
    expr: Optional[Nodo] = None

@dataclass
class ExprCrearCanal(Nodo):
    tipo_contenido: str = ''
    capacidad: Optional[Nodo] = None

@dataclass
class SentenciaEnviarCanal(Nodo):
    canal: Optional[Nodo] = None
    valor: Optional[Nodo] = None

@dataclass
class ExprRecibirCanal(Nodo):
    canal: Optional[Nodo] = None

