"""
test_puente_canonico.py — R90 corte 2: SemNodo[] plano -> AST tipado S1
(Manual 1 s3.1 backend compartido; Manual 3 s11.1; Manual 6 s1.2).
Registros planos construidos a mano: sin depender del exe.
"""

import os
import sys

import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from compilador.puente_canonico import (          # noqa: E402
    PuenteError, plano_a_programa,
)
from compilador.ast_nodes import (                # noqa: E402
    Programa, DefinicionFuncion, DefinicionEstructura, SentenciaSi,
    NodoCoincidir, DeclaracionVariable, OpBinaria, LiteralNumero,
    SentenciaRetornar, DeclaracionExterna, Identificador, LlamadaFuncion,
    AsignacionVariable,
)


def _reg(t, vi=0, izq=0, der=0, herm=0, extra=0, t1=None, t2=None, lin=1):
    return [t, lin, 1, vi, izq, der, herm, extra, t1, t2]


def _b(s):
    return list(s.encode("utf-8"))


def _flat(nodos):
    return {"syquex_flat": "2", "total": len(nodos), "raiz": 0,
            "nodos": nodos}


def test_programa_minimo_con_funcion():
    nodos = [
        _reg(1, izq=1),
        _reg(2, izq=2, der=4, t1=_b("sumar"), t2=_b("entero")),
        _reg(15, herm=3, t1=_b("a"), t2=_b("entero")),
        _reg(15, t1=_b("b"), t2=_b("entero")),
        _reg(5, izq=5),
        _reg(12, izq=6, der=7, t1=_b("+")),
        _reg(8, t1=_b("a")),
        _reg(8, t1=_b("b")),
    ]
    prog = plano_a_programa(_flat(nodos))
    assert isinstance(prog, Programa)
    fn = prog.sentencias[0]
    assert isinstance(fn, DefinicionFuncion)
    assert fn.nombre == "sumar" and fn.tipo_retorno == "entero"
    assert [p.nombre for p in fn.parametros] == ["a", "b"]
    ret = fn.cuerpo[0]
    assert isinstance(ret, SentenciaRetornar)
    bin_ = ret.expr
    assert bin_.operador == "+"
    assert bin_.izquierdo.nombre == "a"


def test_operador_fallback_por_codigo():
    # BINARIA sin lexema en slot1 (desugar para-rango): vi=201 -> "<"
    nodos = [
        _reg(1, izq=1),
        _reg(12, izq=2, der=3, vi=201),
        _reg(8, t1=_b("i")),
        _reg(9, t1=_b("10")),
    ]
    op = plano_a_programa(_flat(nodos)).sentencias[0]
    assert op.operador == "<"
    assert isinstance(op.derecho, LiteralNumero)
    assert op.derecho.valor == 10


def test_estructura_y_si_sino():
    nodos = [
        _reg(1, izq=1),
        _reg(16, izq=2, t1=_b("Punto"), herm=4),
        _reg(15, herm=3, t1=_b("x"), t2=_b("entero")),
        _reg(15, t1=_b("yy"), t2=_b("entero")),
        _reg(3, izq=5, der=6, extra=8),
        _reg(9, t1=_b("1")),
        _reg(48, der=7, t1=_b("z"), t2=_b("entero")),
        _reg(9, t1=_b("2")),
        _reg(11, t1=_b("sino")),
    ]
    prog = plano_a_programa(_flat(nodos))
    est, si = prog.sentencias[0], prog.sentencias[1]
    assert [(c.nombre, c.tipo) for c in est.campos] == [("x", "entero"),
                                                        ("yy", "entero")]
    let = si.cuerpo[0]
    assert isinstance(let, DeclaracionVariable) and let.nombre == "z"
    assert si.cuerpo_sino and si.cuerpo_sino[0].valor == "sino"


def test_coincidir_casos_patron_span():
    nodos = [
        _reg(1, izq=1),
        _reg(38, izq=4, der=2),              # sujeto=n; casos: 2->3
        _reg(39, izq=5, herm=3, t1=_b("0"), lin=5),   # caso 0 => ret 1 (body hijo_izq per traductor:547-554)
        _reg(39, izq=7, t1=_b("_"), lin=6),           # caso _ => ret 0 (body hijo_izq)
        _reg(8, t1=_b("n")),
        _reg(5, izq=6),
        _reg(9, t1=_b("1")),
        _reg(9, t1=_b("0")),
    ]
    m = plano_a_programa(_flat(nodos)).sentencias[0]
    assert isinstance(m, NodoCoincidir)
    assert m.expresion.nombre == "n"
    assert [c.patron for c in m.casos] == ["0", "_"]
    assert m.casos[0].linea == 5


def test_no_soportados_fallan_rapido():
    for tid in (54, 55, 56, 57):
        nodos = [_reg(1, izq=1), _reg(tid)]
        with pytest.raises(PuenteError):
            plano_a_programa(_flat(nodos))


def test_asignacion_indexada_rechazada():
    # H-R90-2: a[i] = ... sin clase en el AST tipado S1
    nodos = [
        _reg(1, izq=1),
        _reg(7, izq=2, der=3),
        _reg(29, izq=4, der=5),
        _reg(8, t1=_b("m")),
        _reg(9, t1=_b("0")),
        _reg(9, t1=_b("7")),
    ]
    with pytest.raises(PuenteError):
        plano_a_programa(_flat(nodos))


def test_llamada_args_en_hijo_der():
    # Convención sq_args: LLAMADA(nombre, hijo_der=cadena de argumentos)
    nodos = [
        _reg(1, izq=1),
        _reg(14, der=2, t1=_b("suma_hasta")),
        _reg(9, t1=_b("4")),
    ]
    prog = plano_a_programa(_flat(nodos))
    call = prog.sentencias[0]
    assert call.nombre == "suma_hasta"
    assert len(call.argumentos) == 1
    assert call.argumentos[0].valor == 4


def test_esquema_incorrecto_rechazado():
    with pytest.raises(PuenteError):
        plano_a_programa({"syquex_flat": "1", "nodos": [], "raiz": 0})


def test_externo_estructura_no_falla():
    # H-R90-3: externo estructura (vi=1) -> DeclaracionExterna con marker
    nodos = [
        _reg(1, izq=1),
        _reg(26, vi=1, t1=_b("Vec3")),
    ]
    prog = plano_a_programa(_flat(nodos))
    ext = prog.sentencias[0]
    assert isinstance(ext, DeclaracionExterna)
    assert ext.nombre == "Vec3"
    assert ext.tipo_retorno == "__extern_struct"


def test_metodo_call_lowering_h_r90_5():
    """H-R90-5: ACCESO_CAMPO con hijo_der (method call) se lowering a
    LlamadaFuncion con self inyectado (Manual 6 §1.3: metodo decorado
    'Struct_method' recibe self como primer argumento)."""
    nodos = [
        # 0: PROGRAMA(1), hijo_izq=1
        _reg(1, izq=1),
        # 1: ESTRUCTURA(16) "Punto", hijo_izq=2 (fields), herm=3
        _reg(16, izq=2, herm=3, t1=_b("Punto")),
        # 2: PARAMETRO(15) "x" "entero", herm=0
        _reg(15, t1=_b("x"), t2=_b("entero")),
        # 3: FUNCION(2) "Punto_desplazar", hijo_izq=4 (self), der=0, herm=5
        _reg(2, izq=4, der=0, herm=5, t1=_b("Punto_desplazar")),
        # 4: PARAMETRO(15) "self", herm=0
        _reg(15, t1=_b("self")),
        # 5: FUNCION(2) "principal" ret="entero", der=6 (body), herm=0
        _reg(2, der=6, t1=_b("principal"), t2=_b("entero")),
        # 6: LET(48) "p" tipo="Punto", herm=7
        _reg(48, t1=_b("p"), t2=_b("Punto"), herm=7),
        # 7: ASIGNACION(7) p = p.desplazar(4): izq=8(Ident p), der=9(ACCESO_CAMPO)
        _reg(7, izq=8, der=9),
        # 8: IDENTIFICADOR(8) "p"
        _reg(8, t1=_b("p")),
        # 9: ACCESO_CAMPO(31) "desplazar", izq=10(obj p), der=11(arg 4)
        _reg(31, izq=10, der=11, t1=_b("desplazar")),
        # 10: IDENTIFICADOR(8) "p"
        _reg(8, t1=_b("p")),
        # 11: NUMERO(9) "4"
        _reg(9, t1=_b("4")),
    ]
    prog = plano_a_programa(_flat(nodos))
    fn = prog.sentencias[2]  # principal
    assert isinstance(fn, DefinicionFuncion)
    assert fn.nombre == "principal"
    asignacion = fn.cuerpo[1]
    assert isinstance(asignacion, AsignacionVariable)
    assert asignacion.nombre == "p"
    call = asignacion.expresion
    assert isinstance(call, LlamadaFuncion)
    assert call.nombre == "Punto_desplazar"
    assert len(call.argumentos) == 2
    assert isinstance(call.argumentos[0], Identificador)
    assert call.argumentos[0].nombre == "p"  # self inyectado
    assert isinstance(call.argumentos[1], LiteralNumero)
    assert call.argumentos[1].valor == 4


def test_metodo_call_sin_tipo_receptor_falla():
    """H-R90-5: si el tipo del receptor no es resoluble, fail-fast."""
    nodos = [
        _reg(1, izq=1),
        # ESTRUCTURA "Punto" sin metodo registrado
        _reg(16, herm=2, t1=_b("Punto")),
        # Funcion "principal" with p.metodo(4) but p has no struct type
        _reg(2, der=3, t1=_b("principal"), t2=_b("entero"), herm=0),
        # LET "p" tipo="entero" (no struct)
        _reg(34, t1=_b("p"), t2=_b("entero"), herm=4),
        # ASIGNACION p = p.metodo(4)
        _reg(7, izq=5, der=6),
        _reg(8, t1=_b("p")),
        _reg(31, izq=7, der=8, t1=_b("metodo")),
        _reg(8, t1=_b("p")),
        _reg(9, t1=_b("4")),
    ]
    with pytest.raises(PuenteError, match="tipo de receptor"):
        plano_a_programa(_flat(nodos))
