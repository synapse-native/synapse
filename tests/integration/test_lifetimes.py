"""M21.5: Pruebas unitarias del sistema de lifetimes (Manual 4.3)."""
import pytest

pytestmark = pytest.mark.integration
from compilador.semantic_checker import (
    RegionGraph, UnionFind, Lifetime,
    LT_ESTATICO, LT_LOCAL, LT_PARAMETRICO,
    REGION_OUTLIVES, REGION_EQUALS, REGION_SUBSCOPE,
)


def _resolver_con_errores(rg, uf):
    errores = []
    def reportar(codigo, linea, mensaje):
        errores.append({'codigo': codigo, 'linea': linea, 'mensaje': mensaje})
    tiene_problema = rg.resolver(uf, reportar)
    return errores, tiene_problema


def test_ciclo_directo():
    rg = RegionGraph()
    uf = UnionFind(256)
    lt_a = Lifetime(LT_LOCAL, 0, 0, -1)
    lt_b = Lifetime(LT_LOCAL, 0, 1, -1)
    rg.agregar_restriccion(REGION_OUTLIVES, lt_a, lt_b, 10)
    rg.agregar_restriccion(REGION_OUTLIVES, lt_b, lt_a, 20)
    errores, tiene_problema = _resolver_con_errores(rg, uf)
    assert tiene_problema
    assert errores[0]['codigo'] == 'ERR_MEM_LIFETIME_CYCLE'


def test_sin_ciclo():
    rg = RegionGraph()
    uf = UnionFind(256)
    lt_a = Lifetime(LT_LOCAL, 0, 0, -1)
    lt_b = Lifetime(LT_LOCAL, 1, 1, -1)
    lt_c = Lifetime(LT_LOCAL, 2, 2, -1)
    rg.agregar_restriccion(REGION_OUTLIVES, lt_a, lt_b, 10)
    rg.agregar_restriccion(REGION_OUTLIVES, lt_b, lt_c, 20)
    errores, tiene_problema = _resolver_con_errores(rg, uf)
    assert not tiene_problema


def test_mismatch_scope():
    rg = RegionGraph()
    uf = UnionFind(256)
    lt_inner = Lifetime(LT_LOCAL, 1, 0, -1)
    lt_outer = Lifetime(LT_LOCAL, 0, 1, -1)
    rg.agregar_restriccion(REGION_OUTLIVES, lt_inner, lt_outer, 42)
    errores, tiene_problema = _resolver_con_errores(rg, uf)
    assert tiene_problema
    assert errores[0]['codigo'] == 'ERR_MEM_LIFETIME_MISMATCH'


def test_static_outlives_anything():
    rg = RegionGraph()
    uf = UnionFind(256)
    lt_s = Lifetime(LT_ESTATICO, -1, 0, -1)
    lt_l = Lifetime(LT_LOCAL, 5, 1, -1)
    rg.agregar_restriccion(REGION_OUTLIVES, lt_s, lt_l, 1)
    errores, tiene_problema = _resolver_con_errores(rg, uf)
    assert not tiene_problema


def test_param_outlives_local():
    rg = RegionGraph()
    uf = UnionFind(256)
    lt_p = Lifetime(LT_PARAMETRICO, 0, 0, -1)
    lt_l = Lifetime(LT_LOCAL, 2, 1, -1)
    rg.agregar_restriccion(REGION_OUTLIVES, lt_p, lt_l, 1)
    errores, tiene_problema = _resolver_con_errores(rg, uf)
    assert not tiene_problema


def test_equals_unifica():
    rg = RegionGraph()
    uf = UnionFind(256)
    lt_a = Lifetime(LT_LOCAL, 0, 0, -1)
    lt_b = Lifetime(LT_LOCAL, 1, 1, -1)
    lt_c = Lifetime(LT_LOCAL, 2, 2, -1)
    rg.agregar_restriccion(REGION_EQUALS, lt_a, lt_b, 1)
    rg.agregar_restriccion(REGION_OUTLIVES, lt_a, lt_c, 2)
    errores, tiene_problema = _resolver_con_errores(rg, uf)
    assert uf.mismo_set(0, 1)
    assert not tiene_problema


def test_local_fails_vs_param():
    rg = RegionGraph()
    uf = UnionFind(256)
    lt_l = Lifetime(LT_LOCAL, 2, 0, -1)
    lt_p = Lifetime(LT_PARAMETRICO, 0, 1, -1)
    rg.agregar_restriccion(REGION_OUTLIVES, lt_l, lt_p, 15)
    errores, _ = _resolver_con_errores(rg, uf)
    assert len(errores) == 1
    assert errores[0]['codigo'] == 'ERR_MEM_LIFETIME_MISMATCH'
