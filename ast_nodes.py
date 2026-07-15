from enum import Enum, auto
from dataclasses import dataclass, field
from typing import List, Optional, Any


class TokenID(Enum):
    IF = auto()
    ELSE = auto()
    FUNCTION = auto()
    RETURN = auto()
    SPAWN = auto()
    RECOVER = auto()
    LISTEN = auto()
    WHILE = auto()
    IMPORT = auto()
    STRUCT = auto()
    BREAK = auto()
    CONTINUE = auto()
    DOT = auto()
    AND = auto()
    OR = auto()
    NOT = auto()
    TRUE = auto()
    FALSE = auto()

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
    MODULO = auto()
    ARROW = auto()
    MATCH = auto()
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
class SentenciaExpr(Nodo):
    expr: Optional[Nodo] = None


@dataclass
class AsignacionVariable(Nodo):
    nombre: str = ''
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

