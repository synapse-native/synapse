from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Dict, Optional

from compilador.ast_nodes import Nodo


class Propiedad(Enum):
    VIVO = auto()
    MOVIDO = auto()


@dataclass
class Simbolo:
    nombre: str
    tipo: str
    nodo: Optional[Nodo] = None
    scope_level: int = 0
    propiedad: Propiedad = Propiedad.VIVO
    es_constante: bool = False
    uri: str = ''
    linea: int = 0
    columna: int = 0


class SymbolTable:
    def __init__(self):
        self._scopes: List[Dict[str, Simbolo]] = [{}]
        self._scope_level = 0

    def entrar_scope(self):
        self._scopes.append({})
        self._scope_level += 1

    def salir_scope(self):
        if len(self._scopes) > 1:
            self._scopes.pop()
            self._scope_level -= 1

    @property
    def scope_nivel(self) -> int:
        return self._scope_level

    def simbolos_ordenados(self) -> List[Simbolo]:
        """Retorna todos los símbolos del ámbito actual ordenados lexicográficamente por nombre.
        Cumple Manual 1 §1.2 y Manual 3 §3.3: toda iteración sobre mapas/diccionarios
        debe realizarse en orden lexicográfico de claves."""
        return sorted(self._scopes[-1].values(), key=lambda s: s.nombre)

    def entradas_ordenadas(self) -> List[tuple[str, Simbolo]]:
        """Retorna las entradas (nombre, símbolo) del ámbito actual ordenadas lexicográficamente."""
        return sorted(self._scopes[-1].items(), key=lambda item: item[0])

    def declarar(self, nombre: str, tipo: str, nodo: Optional[Nodo] = None, uri: str = '', linea: int = 0, columna: int = 0) -> bool:
        cur = self._scopes[-1]
        if nombre in cur:
            return False
        cur[nombre] = Simbolo(
            nombre=nombre,
            tipo=tipo,
            nodo=nodo,
            scope_level=self._scope_level,
            uri=uri,
            linea=linea if linea else (nodo.linea if nodo else 0),
            columna=columna if columna else (nodo.columna if nodo else 0),
        )
        return True

    def buscar(self, nombre: str) -> Optional[Simbolo]:
        for scope in reversed(self._scopes):
            if nombre in scope:
                return scope[nombre]
        return None

    def marcar_movido(self, nombre: str) -> bool:
        sim = self.buscar(nombre)
        if sim is None:
            return False
        sim.propiedad = Propiedad.MOVIDO
        return True

    def esta_movido(self, nombre: str) -> bool:
        sim = self.buscar(nombre)
        if sim is None:
            return False
        return sim.propiedad == Propiedad.MOVIDO