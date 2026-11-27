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
        self._prestamos: List[Dict[str, dict]] = [{}]  # Manual 4 S4.2: prestamos activos por scope
        self._scope_level = 0

    def entrar_scope(self):
        self._scopes.append({})
        self._prestamos.append({})
        self._scope_level += 1

    def salir_scope(self):
        if len(self._scopes) > 1:
            self._scopes.pop()
            self._prestamos.pop()
            self._scope_level -= 1

    def prestamo_activo(self, nombre: str) -> tuple:
        """Manual 4 S4.2: retorna (total_inmutables, hay_mutable) visibles en todos los scopes."""
        inmutable_total = 0
        hay_mutable = False
        for layer in reversed(self._prestamos):
            est = layer.get(nombre)
            if est:
                inmutable_total += est.get('inmutable', 0)
                hay_mutable = hay_mutable or est.get('mutable', False)
        return inmutable_total, hay_mutable

    def registrar_prestamo(self, nombre: str, es_mutable: bool) -> bool:
        """Manual 4 S4.2: registra un prestamo sobre 'nombre'.

        Reglas: multiples inmutables simultaneos OK; un solo mutable a la vez
        y sin coexistencia con inmutables.
        Retorna True si el prestamo es permitido, False si viola coexistencia.
        """
        inmutables, hay_mutable = self.prestamo_activo(nombre)
        if es_mutable:
            if hay_mutable or inmutables > 0:
                return False
            self._prestamos[-1][nombre] = {'inmutable': 0, 'mutable': True}
        else:
            if hay_mutable:
                return False
            est = self._prestamos[-1].get(nombre, {'inmutable': 0, 'mutable': False})
            est['inmutable'] += 1
            self._prestamos[-1][nombre] = est
        return True

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

    def desmarcar_movido(self, nombre: str) -> bool:
        """Desmarca una variable como movida (reassessment resetea ownership)."""
        sim = self.buscar(nombre)
        if sim is None:
            return False
        if sim.propiedad == Propiedad.MOVIDO:
            sim.propiedad = Propiedad.VIVO
        return True

    def esta_movido(self, nombre: str) -> bool:
        sim = self.buscar(nombre)
        if sim is None:
            return False
        return sim.propiedad == Propiedad.MOVIDO