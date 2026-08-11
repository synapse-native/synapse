# -*- coding: utf-8 -*-
"""compilador/tipos.py — Representación estructurada de tipos (Manual 2 §8.2).

Migración a `TipoKind` (Opción B del Arquitecto, Fase 2 / checklist 2.4).
El Manual 2 §8.2 define la representación interna de tipos:

    typedef enum { TIPO_PRIMITIVO, TIPO_FUNCION, TIPO_ESTRUCTURA,
                   TIPO_VARIABLE, TIPO_ALGEBRAICO, TIPO_CANAL,
                   TIPO_TENSOR, TIPO_PUNTERO, TIPO_REFERENCIA } TipoKind;

Este módulo aporta:
  1. La representación estructurada (`Tipo` + `TipoKind`) con la que la Fase 2
     VALIDA tipos (aridad de ADT, argumentos conocidos, compatibilidad).
  2. La máquina Hindley-Milner (algoritmo W) del Manual 2 §8.2: variables de
     tipo `TVar(id)`, unificación con *occurs check* (evita tipos recursivos)
     y `ERR_SEM_TYPE_AMBIGUOUS` para expresiones con tipo ambiguo.

Compatibilidad: el pipeline actual representa los tipos como cadenas
normalizadas (p. ej. "Resultado<entero,texto>"); `tipo_desde_cadena` /
`tipo_a_cadena` convierten entre ambas representaciones sin tocar el resto
del compilador (parser, codegen, puente).
"""
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Set, Union


# ---------------------------------------------------------------------------
# TipoKind — Manual 2 §8.2
# ---------------------------------------------------------------------------

class TipoKind(Enum):
    PRIMITIVO = auto()    # entero/int, decimal/float, texto, booleano, nulo, void
    FUNCION = auto()      # (params...) -> retorno
    ESTRUCTURA = auto()   # struct definida por el usuario (nombre)
    VARIABLE = auto()     # TVar(id) — parámetro de tipo T/E (Manual 2 §8.2)
    ALGEBRAICO = auto()   # ADT instanciado: Resultado<entero,texto>
    CANAL = auto()        # CanalConcurrencia*
    TENSOR = auto()       # tensor
    PUNTERO = auto()      # T*
    REFERENCIA = auto()   # &T / &mut T


@dataclass
class Tipo:
    """Tipo estructurado (Manual 2 §8.2). Los campos se activan según `kind`.

    - PRIMITIVO/ESTRUCTURA/CANAL/TENSOR: `nombre`.
    - VARIABLE: `var_id` (TVar(id)).
    - ALGEBRAICO: `nombre` (base) + `argumentos` (tipos concretos o TVar).
    - PUNTERO/REFERENCIA: `tipo_base` (+ `es_mut` para REFERENCIA).
    - FUNCION: `parametros` + `retorno`.
    """
    kind: TipoKind
    nombre: str = ''
    argumentos: List['Tipo'] = field(default_factory=list)
    var_id: int = -1
    tipo_base: Optional['Tipo'] = None
    es_mut: bool = False
    parametros: List['Tipo'] = field(default_factory=list)
    retorno: Optional['Tipo'] = None

    def __repr__(self) -> str:
        return f"Tipo({self.kind.name}, {self.nombre}, args={self.argumentos}, v={self.var_id})"


# ---------------------------------------------------------------------------
# Constructores y serialización (compatibilidad con cadenas del pipeline)
# ---------------------------------------------------------------------------

_TIPOS_PRIMITIVOS = frozenset({
    'int', 'entero', 'int64_t', 'long',
    'float', 'decimal', 'double', 'real', 'flotante',
    'texto', 'cadena', 'CadenaSegura', 'string',
    'booleano', 'logico', 'bool',
    'nulo', 'vacio', 'void',
    'puntero', 'void*',
})
_TIPOS_RC = frozenset({'rc', 'arc', 'debil', 'débil', 'weak', 'faible', 'fraco'})
_TENSOR = frozenset({'tensor'})
_CANAL = frozenset({'CanalConcurrencia'})


def _normalizar_primitivo(nombre: str) -> str:
    """Normaliza un primitivo al tipo lógico del checker ('int'/'float'/...)."""
    n = nombre.strip()
    if n in ('int', 'entero', 'int64_t', 'long'):
        return 'int'
    if n in ('float', 'decimal', 'double', 'real', 'flotante'):
        return 'float'
    if n in ('texto', 'cadena', 'CadenaSegura', 'string'):
        return 'texto'
    if n in ('booleano', 'logico', 'bool'):
        return 'booleano'
    if n in ('nulo', 'vacio', 'void'):
        return 'nulo'
    if n == 'void*':
        return 'void*'
    if n == 'puntero':
        return 'puntero'
    return n


def _dividir_argumentos(cuerpo: str) -> List[str]:
    """Divide el cuerpo de una instanciación `A,B` respetando < > anidados
    (p. ej. "Resultado<int,texto>,float" -> ["Resultado<int,texto>", "float"])."""
    partes: List[str] = []
    profundidad = 0
    actual: List[str] = []
    for ch in cuerpo:
        if ch == '<':
            profundidad += 1
        elif ch == '>':
            profundidad -= 1
        if ch == ',' and profundidad == 0:
            partes.append(''.join(actual).strip())
            actual = []
        else:
            actual.append(ch)
    partes.append(''.join(actual).strip())
    return partes


class ContadorTVar:
    """Contador global de TVar(id) — Manual 2 §8.2."""
    def __init__(self):
        self.n = 0

    def nuevo(self) -> int:
        self.n += 1
        return self.n


def tipo_desde_cadena(cadena: str, contador: Optional[ContadorTVar] = None,
                      parametros_tipo: Optional[Set[str]] = None,
                      tvar_cache: Optional[Dict[str, int]] = None,
                      estructuras_conocidas: Optional[Set[str]] = None) -> Optional['Tipo']:
    """Convierte una cadena de tipo del pipeline en un `Tipo` estructurado.

    - '&mut X' / '&X'  -> REFERENCIA
    - 'X*'             -> PUNTERO (recursivo)
    - 'X<A,B>'         -> ALGEBRAICO con argumentos parseados (anidados ok)
    - primitivos       -> PRIMITIVO (nombre lógico normalizado)
    - 'tensor'         -> TENSOR ; 'CanalConcurrencia' -> CANAL
    - 'T'/'E'          -> VARIABLE (TVar) si está en `parametros_tipo` o es
                          mayúscula DESCONOCIDA (el caller distingue)
    - resto            -> ESTRUCTURA (nombre de struct/ADT definido por el usuario)

    `tvar_cache` (nombre -> TVar(id)) garantiza que el MISMO nombre de variable
    de tipo (p. ej. 'T') mapee al MISMO TVar dentro de una instanciación de
    firma (requisito de la unificación HM — Manual 2 §8.2): si no se comparte,
    cada aparición de 'T' generaría un TVar distinto y la unificación fallaría.

    `estructuras_conocidas` (nombres de structs/ADTs registrados): evita que un
    tipo de usuario en mayúscula (p. ej. 'Persona' o 'Resultado' desnudo) se
    confunda con una variable de tipo TVar — se emite ESTRUCTURA.

    Devuelve None si la cadena está vacía o es ilegible.
    """
    def _tvar(nombre: str) -> int:
        """TVar id para `nombre`: reutiliza el del cache o crea uno nuevo."""
        if tvar_cache is not None and nombre in tvar_cache:
            return tvar_cache[nombre]
        vid = contador.nuevo() if contador is not None else 1
        if tvar_cache is not None:
            tvar_cache[nombre] = vid
        return vid

    s = cadena.strip()
    if not s:
        return None
    if s.startswith('&mut '):
        base = tipo_desde_cadena(s[5:].strip(), contador, parametros_tipo,
                                 tvar_cache, estructuras_conocidas)
        return Tipo(TipoKind.REFERENCIA, tipo_base=base, es_mut=True)
    if s.startswith('&'):
        base = tipo_desde_cadena(s[1:].strip(), contador, parametros_tipo,
                                 tvar_cache, estructuras_conocidas)
        return Tipo(TipoKind.REFERENCIA, tipo_base=base, es_mut=False)
    if s.endswith('*'):
        base = tipo_desde_cadena(s[:-1].strip(), contador, parametros_tipo,
                                 tvar_cache, estructuras_conocidas)
        return Tipo(TipoKind.PUNTERO, tipo_base=base)
    if '<' in s and s.endswith('>'):
        nombre = s.split('<')[0].strip()
        cuerpo = s[len(nombre) + 1:-1]
        argumentos = [tipo_desde_cadena(a, contador, parametros_tipo,
                                        tvar_cache, estructuras_conocidas)
                      for a in _dividir_argumentos(cuerpo)]
        args = [a for a in argumentos if a is not None]
        return Tipo(TipoKind.ALGEBRAICO, nombre=nombre, argumentos=args)
    if s in _TIPOS_PRIMITIVOS:
        return Tipo(TipoKind.PRIMITIVO, nombre=_normalizar_primitivo(s))
    if s in _TIPOS_RC:
        return Tipo(TipoKind.ESTRUCTURA, nombre=s)  # rc/arc/débil: ABI placeholder void*
    if s in _TENSOR:
        return Tipo(TipoKind.TENSOR, nombre='tensor')
    if s in _CANAL:
        return Tipo(TipoKind.CANAL, nombre='CanalConcurrencia')
    if parametros_tipo is not None and s in parametros_tipo:
        return Tipo(TipoKind.VARIABLE, var_id=_tvar(s))
    if s and s[0].isupper():
        # Struct/ADT de usuario registrado: NUNCA es una variable de tipo
        # (revisión code-reviewer 2.4: 'Persona'/'Resultado' desnudo -> TVar
        # habría unificado erróneamente en funciones genéricas).
        if estructuras_conocidas is not None and s in estructuras_conocidas:
            return Tipo(TipoKind.ESTRUCTURA, nombre=s)
        # Mayúscula desconocida: variable de tipo (TVar) — p. ej. 'T'/'E'
        # declarados en `tipo X<T,E>`. El caller distingue con el set.
        return Tipo(TipoKind.VARIABLE, var_id=_tvar(s))
    return Tipo(TipoKind.ESTRUCTURA, nombre=s)


def tipo_a_cadena(tipo: Optional['Tipo']) -> str:
    """Serializa un `Tipo` a la cadena normalizada del pipeline (inverso de
    tipo_desde_cadena). Las VARIABLE sin resolver se emiten como su TVar."""
    if tipo is None:
        return ''
    if tipo.kind == TipoKind.PRIMITIVO:
        return tipo.nombre
    if tipo.kind == TipoKind.ESTRUCTURA:
        return tipo.nombre
    if tipo.kind == TipoKind.VARIABLE:
        return f"TVar({tipo.var_id})"
    if tipo.kind == TipoKind.ALGEBRAICO:
        args = ','.join(tipo_a_cadena(a) for a in tipo.argumentos)
        return f"{tipo.nombre}<{args}>"
    if tipo.kind == TipoKind.PUNTERO:
        return f"{tipo_a_cadena(tipo.tipo_base)}*"
    if tipo.kind == TipoKind.REFERENCIA:
        prefijo = '&mut ' if tipo.es_mut else '&'
        return f"{prefijo}{tipo_a_cadena(tipo.tipo_base)}"
    if tipo.kind == TipoKind.CANAL:
        return 'CanalConcurrencia*'
    if tipo.kind == TipoKind.TENSOR:
        return 'tensor'
    if tipo.kind == TipoKind.FUNCION:
        params = ','.join(tipo_a_cadena(p) for p in tipo.parametros)
        return f"({params}) -> {tipo_a_cadena(tipo.retorno)}"
    return tipo.nombre


def es_tipo_conocido(cadena: str, estructuras: Optional[Set[str]] = None,
                     adt_parametros: Optional[Dict[str, Union[int, List[str]]]] = None) -> bool:
    """Valida que una cadena de tipo sea un tipo CONOCIDO: primitivo lógico,
    struct registrado, ADT registrado, rc/arc/débil, tensor, canal, puntero o
    referencia de un tipo conocido. Manual 2 §8.2 (argumentos de tipo válidos)."""
    s = cadena.strip()
    if not s:
        return False
    if s.startswith('&mut ') or s.startswith('&'):
        base = s[5:].strip() if s.startswith('&mut ') else s[1:].strip()
        return es_tipo_conocido(base, estructuras, adt_parametros)
    if s.endswith('*'):
        return es_tipo_conocido(s[:-1].strip(), estructuras, adt_parametros)
    if s in _TIPOS_PRIMITIVOS or s in _TIPOS_RC or s in _TENSOR or s in _CANAL:
        return True
    if '<' in s and s.endswith('>'):
        nombre = s.split('<')[0].strip()
        cuerpo = s[len(nombre) + 1:-1]
        args = _dividir_argumentos(cuerpo)
        # Aridad: el ADT debe estar registrado y coincidir el número de parámetros
        if adt_parametros is not None and nombre in adt_parametros:
            # `adt_parametros[nombre]` es la LISTA de nombres de parámetros de
            # tipo del ADT (p. ej. ['T','E'] para Resultado) en el flujo real,
            # o un CONTEo entero en los tests unitarios ({'Resultado': 2}).
            # R13: comparar contra el número esperado; antes se comparaba int
            # contra lista y TODO ADT registrado devolvía False (falsos
            # positivos en argumentos ADT anidados, p. ej.
            # `Resultado<Resultado<entero,texto>,texto>`).
            np = adt_parametros[nombre]
            esperados = np if isinstance(np, int) else len(np)
            if len(args) != esperados:
                return False
        elif nombre in _TIPOS_RC:
            # rc/arc/débil<T> son tipos de conteo de referencias válidos
            # (Manual 2 §4.3; ABI placeholder void* hasta Fase 23)
            return all(es_tipo_conocido(a, estructuras, adt_parametros) for a in args)
        else:
            # Instanciación de un ADT no registrado: la base debe existir como struct
            if estructuras is not None and nombre not in estructuras:
                return False
        return all(es_tipo_conocido(a, estructuras, adt_parametros) for a in args)
    if estructuras is not None and s in estructuras:
        return True
    return False


# ---------------------------------------------------------------------------
# Unificación Hindley-Milner — Manual 2 §8.2
# ---------------------------------------------------------------------------

class UnificadorHM:
    """Unificación de tipos con *occurs check* (algoritmo W simplificado).

    Las variables de tipo son `Tipo(TipoKind.VARIABLE, var_id=n)` (TVar(n)).
    La sustitución acumulada mapea TVar -> Tipo; `unificar` la extiende y
    devuelve True/False. `resolver` aplica la sustitución (recursiva).
    """

    def __init__(self):
        self.sustitucion: Dict[int, 'Tipo'] = {}

    def resolver(self, t: Optional['Tipo']) -> Optional['Tipo']:
        if t is None:
            return None
        if t.kind == TipoKind.VARIABLE:
            if t.var_id in self.sustitucion:
                return self.resolver(self.sustitucion[t.var_id])
            return t
        if t.kind == TipoKind.PUNTERO or t.kind == TipoKind.REFERENCIA:
            return Tipo(t.kind, tipo_base=self.resolver(t.tipo_base),
                        es_mut=t.es_mut)
        if t.kind == TipoKind.ALGEBRAICO:
            return Tipo(TipoKind.ALGEBRAICO, nombre=t.nombre,
                        argumentos=[self.resolver(a) for a in t.argumentos])
        if t.kind == TipoKind.FUNCION:
            return Tipo(TipoKind.FUNCION,
                        parametros=[self.resolver(p) for p in t.parametros],
                        retorno=self.resolver(t.retorno))
        return t

    def _contiene(self, var_id: int, t: Optional['Tipo']) -> bool:
        """Occurs check (Manual 2 §8.2): ¿el TVar(var_id) aparece dentro de t?
        Prohíbe tipos recursivos (p. ej. T = T* o T = arreglo(T))."""
        if t is None:
            return False
        if t.kind == TipoKind.VARIABLE:
            r = self.resolver(t)
            if r.kind == TipoKind.VARIABLE:
                return r.var_id == var_id
            return self._contiene(var_id, r)
        if t.kind in (TipoKind.PUNTERO, TipoKind.REFERENCIA):
            return self._contiene(var_id, t.tipo_base)
        if t.kind == TipoKind.ALGEBRAICO:
            return any(self._contiene(var_id, a) for a in t.argumentos)
        if t.kind == TipoKind.FUNCION:
            return (self._contiene(var_id, t.retorno)
                    or any(self._contiene(var_id, p) for p in t.parametros))
        return False

    def unificar(self, a: Optional['Tipo'], b: Optional['Tipo']) -> bool:
        """Unifica dos tipos. True si son compatibles (extiende la sustitución);
        False si hay conflicto (tipos distintos u occurs check fallido)."""
        a = self.resolver(a)
        b = self.resolver(b)
        if a is None or b is None:
            return a is None and b is None
        if a.kind == TipoKind.VARIABLE:
            if self._contiene(a.var_id, b):
                return False  # occurs check: tipo recursivo
            self.sustitucion[a.var_id] = b
            return True
        if b.kind == TipoKind.VARIABLE:
            return self.unificar(b, a)
        # Ambos concretos: mismo kind + misma base + argumentos unificables
        if a.kind == TipoKind.PRIMITIVO and b.kind == TipoKind.PRIMITIVO:
            return _normalizar_primitivo(a.nombre) == _normalizar_primitivo(b.nombre)
        if a.kind != b.kind:
            return False
        if a.kind == TipoKind.ALGEBRAICO:
            if a.nombre != b.nombre or len(a.argumentos) != len(b.argumentos):
                return False
            return all(self.unificar(x, y)
                       for x, y in zip(a.argumentos, b.argumentos))
        if a.kind in (TipoKind.PUNTERO, TipoKind.REFERENCIA):
            if a.kind == TipoKind.REFERENCIA and a.es_mut != b.es_mut:
                # &T y &mut T no unifican (Manual 4 §4.2)
                return False
            return self.unificar(a.tipo_base, b.tipo_base)
        if a.kind == TipoKind.FUNCION:
            if len(a.parametros) != len(b.parametros):
                return False
            return (all(self.unificar(x, y)
                        for x, y in zip(a.parametros, b.parametros))
                    and self.unificar(a.retorno, b.retorno))
        # ESTRUCTURA/CANAL/TENSOR: mismo nombre
        return a.nombre == b.nombre

    def instanciar(self, t: Optional['Tipo']) -> Optional['Tipo']:
        """Instancia un tipo de firma sustituyendo los TVar según la
        sustitución acumulada y devolviendo el tipo concreto resultante."""
        return self.resolver(t)
