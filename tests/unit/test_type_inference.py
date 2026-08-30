# -*- coding: utf-8 -*-
"""tests/unit/test_type_inference.py — Manual 2 §12 (test obligatorio).

Cubre la brecha 2.4 P0 (Hindley-Milner, Manual 2 §8.2) implementada con la
representación estructurada `TipoKind` (Opción B del Arquitecto, Fase 2):

  1. Representación estructurada de tipos (compilador/tipos.py)
  2. Unificación Hindley-Milner con *occurs check* (algoritmo W)
  3. Validación de aridad de ADT y argumentos de tipo conocidos
  4. ERR_SEM_TYPE_AMBIGUOUS para TVar sin resolver (Manual 2 §8.2)
"""
from pathlib import Path

from compilador.lexer import Lexer
from compilador.parser import Parser
from compilador.analizador_semantico import AnalizadorSemantico
from compilador.diagnostics import DiagnosticManager, ErrorCodes
import pytest

pytestmark = pytest.mark.unit
from compilador.tipos import (
    ContadorTVar, Tipo, TipoKind, UnificadorHM,
    tipo_desde_cadena, tipo_a_cadena, es_tipo_conocido,
)


# ---------------------------------------------------------------------------
# 1. Representación estructurada TipoKind (Manual 2 §8.2)
# ---------------------------------------------------------------------------

class TestTipoKind:
    def test_primitivo_normalizado(self):
        t = tipo_desde_cadena('entero')
        assert t.kind == TipoKind.PRIMITIVO
        assert t.nombre == 'int'

    def test_primitivo_aliases(self):
        assert tipo_desde_cadena('int64_t').nombre == 'int'
        assert tipo_desde_cadena('double').nombre == 'float'
        assert tipo_desde_cadena('CadenaSegura').nombre == 'texto'

    def test_adt_concreto(self):
        t = tipo_desde_cadena('Resultado<entero,texto>')
        assert t.kind == TipoKind.ALGEBRAICO
        assert t.nombre == 'Resultado'
        assert len(t.argumentos) == 2
        assert t.argumentos[0].nombre == 'int'
        assert t.argumentos[1].nombre == 'texto'

    def test_adt_anidado(self):
        t = tipo_desde_cadena('Resultado<Resultado<entero,texto>,decimal>')
        assert t.kind == TipoKind.ALGEBRAICO
        inner = t.argumentos[0]
        assert inner.kind == TipoKind.ALGEBRAICO
        assert inner.argumentos[1].nombre == 'texto'
        assert t.argumentos[1].nombre == 'float'

    def test_tvar(self):
        c = ContadorTVar()
        t = tipo_desde_cadena('T', c, {'T'})
        assert t.kind == TipoKind.VARIABLE
        assert t.var_id == c.n

    def test_puntero(self):
        t = tipo_desde_cadena('entero*')
        assert t.kind == TipoKind.PUNTERO
        assert t.tipo_base.nombre == 'int'

    def test_referencia_mut(self):
        r = tipo_desde_cadena('&mut texto')
        assert r.kind == TipoKind.REFERENCIA
        assert r.es_mut
        assert r.tipo_base.nombre == 'texto'

    def test_redondeo_a_cadena(self):
        t = tipo_desde_cadena('Resultado<entero,texto>')
        assert tipo_a_cadena(t) == 'Resultado<int,texto>'

    def test_struct_mayuscula_no_es_tvar(self):
        # Con estructuras_conocidas, 'Persona' (struct de usuario) es
        # ESTRUCTURA, NUNCA un TVar (revisión code-reviewer 2.4).
        t = tipo_desde_cadena('Persona', estructuras_conocidas={'Persona'})
        assert t.kind == TipoKind.ESTRUCTURA
        assert t.nombre == 'Persona'


# ---------------------------------------------------------------------------
# 2. Unificación Hindley-Milner con occurs check (Manual 2 §8.2)
# ---------------------------------------------------------------------------

class TestUnificadorHM:
    def test_tvar_con_concreto(self):
        uf = UnificadorHM()
        t = Tipo(TipoKind.VARIABLE, var_id=1)
        assert uf.unificar(t, tipo_desde_cadena('entero'))
        assert uf.resolver(t).nombre == 'int'

    def test_tvar_compartido_consistente(self):
        # id(x): T -> T ; x:int => el TVar queda unificado a int
        uf = UnificadorHM()
        tv = Tipo(TipoKind.VARIABLE, var_id=1)
        assert uf.unificar(tv, tipo_desde_cadena('int'))
        r = uf.instanciar(tv)
        assert r.kind == TipoKind.PRIMITIVO
        assert r.nombre == 'int'

    def test_occurs_check_rechaza_tipo_recursivo(self):
        # T = T* prohibido por el occurs check (Manual 2 §8.2)
        uf = UnificadorHM()
        t = Tipo(TipoKind.VARIABLE, var_id=1)
        ptr = Tipo(TipoKind.PUNTERO, tipo_base=t)
        assert not uf.unificar(t, ptr)

    def test_primitivos_incompatibles(self):
        assert not UnificadorHM().unificar(
            tipo_desde_cadena('entero'), tipo_desde_cadena('texto'))

    def test_adt_misma_base_y_aridad(self):
        uf = UnificadorHM()
        assert uf.unificar(tipo_desde_cadena('Resultado<entero,texto>'),
                           tipo_desde_cadena('Resultado<int,texto>'))

    def test_adt_aridad_distinta_no_unifica(self):
        assert not UnificadorHM().unificar(
            tipo_desde_cadena('Resultado<entero,texto>'),
            tipo_desde_cadena('Resultado<int>'))

    def test_adt_argumento_incompatible(self):
        assert not UnificadorHM().unificar(
            tipo_desde_cadena('Resultado<entero,texto>'),
            tipo_desde_cadena('Resultado<int,decimal>'))


# ---------------------------------------------------------------------------
# 3. Argumentos de tipo conocidos y aridad de ADT (es_tipo_conocido)
# ---------------------------------------------------------------------------

class TestArgumentosConocidos:
    def test_aridad_correcta(self):
        assert es_tipo_conocido('Resultado<entero,texto>',
                                {'Resultado'}, {'Resultado': 2})

    def test_aridad_incorrecta(self):
        assert not es_tipo_conocido('Resultado<entero>',
                                    {'Resultado'}, {'Resultado': 2})

    def test_anidado(self):
        assert es_tipo_conocido('Resultado<Resultado<entero,texto>,decimal>',
                                {'Resultado'}, {'Resultado': 2})

    def test_tipo_desconocido(self):
        assert not es_tipo_conocido('Resultado<entero,NoExiste>',
                                    {'Resultado'}, {'Resultado': 2})

    def test_puntero_y_referencia(self):
        assert es_tipo_conocido('entero*')
        assert es_tipo_conocido('&mut texto')
        assert es_tipo_conocido('texto')


# ---------------------------------------------------------------------------
# 4. Integración en el checker: firma con ADT genérico y llamadas polimórficas
# ---------------------------------------------------------------------------

def _analizar(fuente):
    lexer = Lexer(fuente)
    tokens = lexer.tokenizar()
    diag = DiagnosticManager()
    parser = Parser(tokens, diag)
    prog = parser.parsear()
    analizador = AnalizadorSemantico(prog, diag)
    analizador.analizar()
    return diag


class TestChecadorHindleyMilner:
    def test_firma_adt_valida(self):
        diag = _analizar(
            "#lang: es\n"
            "tipo Resultado<T, E> = ok(T) | err(E)\n"
            "funcion crear() -> Resultado<entero, texto>:\n"
            "    retornar ok(5)\n"
        )
        assert not diag.hay_errores(), [e for e in diag.errores]

    def test_firma_aridad_incorrecta(self):
        diag = _analizar(
            "#lang: es\n"
            "tipo Resultado<T, E> = ok(T) | err(E)\n"
            "funcion crear() -> Resultado<entero>:\n"
            "    retornar ok(5)\n"
        )
        assert diag.hay_errores()
        assert any(e['codigo'] == ErrorCodes.ERR_SEM_TIPO_INCOMPATIBLE
                   for e in diag.errores)

    def test_firma_argumento_desconocido(self):
        diag = _analizar(
            "#lang: es\n"
            "tipo Resultado<T, E> = ok(T) | err(E)\n"
            "funcion crear() -> Resultado<entero, NoExiste>:\n"
            "    retornar ok(5)\n"
        )
        assert diag.hay_errores()
        assert any(e['codigo'] == ErrorCodes.ERR_SEM_TIPO_INCOMPATIBLE
                   for e in diag.errores)

    def test_llamada_generica_unifica(self):
        # id(x: T) -> T: el TVar se infiere de la llamada (id(5) -> int)
        diag = _analizar(
            "#lang: es\n"
            "funcion identidad(x: T) -> T:\n"
            "    retornar x\n"
            "funcion principal() -> nulo:\n"
            "    z = identidad(5)\n"
        )
        assert not diag.hay_errores(), [e for e in diag.errores]

    def test_tipo_ambiguo_tvar_sin_resolver(self):
        # T declarado solo en el retorno: no se puede inferir -> AMBIGUOUS
        diag = _analizar(
            "#lang: es\n"
            "funcion generar() -> T:\n"
            "    retornar 5\n"
            "funcion principal() -> nulo:\n"
            "    z = generar()\n"
        )
        assert diag.hay_errores()
        assert any(e['codigo'] == ErrorCodes.ERR_SEM_TYPE_AMBIGUOUS
                   for e in diag.errores)

    def test_struct_mayuscula_en_funcion_generica(self):
        # 'Persona' (struct en mayúscula) NO es un TVar en una función
        # genérica: no debe unificar con T ni provocar AMBIGUOUS (revisión
        # code-reviewer 2.4: uppercase -> TVar habría unificado erróneamente).
        diag = _analizar(
            "#lang: es\n"
            "estructura Persona:\n"
            "    nombre: texto\n"
            "funcion empaquetar(x: T, p: Persona) -> T:\n"
            "    retornar x\n"
            "funcion principal() -> nulo:\n"
            "    z = empaquetar(5, Persona())\n"
        )
        assert not diag.hay_errores(), [e for e in diag.errores]

    def test_firma_base_desconocida(self):
        # Typo en la base de la instanciación: 'Resultados' no existe (revisión
        # code-reviewer 2.4: la base desconocida pasaba silenciosa).
        diag = _analizar(
            "#lang: es\n"
            "tipo Resultado<T, E> = ok(T) | err(E)\n"
            "funcion crear() -> Resultados<entero, texto>:\n"
            "    retornar ok(5)\n"
        )
        assert diag.hay_errores()
        assert any(e['codigo'] == ErrorCodes.ERR_SEM_TIPO_INCOMPATIBLE
                   for e in diag.errores)

    def test_integracion_fixture_d2(self):
        # Prioridad 3 del Arquitecto: el sistema de tipos 2.4 debe integrarse
        # con la instanciación genérica (D-2: Resultado<T,E> -> Resultado<entero,
        # texto>), los constructores ok/err, el operador '?' (D-6) y el acceso
        # .tag sin romper programas reales del fixture D-2.
        ruta = Path(__file__).resolve().parent.parent / 'fixtures' \
            / 'test_d2_genericos.syn'
        diag = _analizar(ruta.read_text(encoding='utf-8'))
        assert not diag.hay_errores(), [e for e in diag.errores]

    def test_integracion_fixture_d6(self):
        # Prioridad 3 del Arquitecto: el ADT concreto del fixture D-6
        # (Resultado = ok(entero) | err(texto), sin genéricos) con '?' y
        # coincidir implícito también debe pasar la validación 2.4.
        ruta = Path(__file__).resolve().parent.parent / 'fixtures' \
            / 'test_d6_propagar.syn'
        diag = _analizar(ruta.read_text(encoding='utf-8'))
        assert not diag.hay_errores(), [e for e in diag.errores]

    # R23 (paridad nativo): la REDEFINICION del archivo del usuario debe ser
    # observable en el S1 — el unity merge ya no deduplica los duplicados del
    # propio archivo (hallazgo R21; Manual 3 §3.1, diagnóstico Manual 2 §10.1).
    def test_redefinicion_adt_observable(self):
        diag = _analizar(
            "#lang: es\n"
            "tipo Color = rojo | azul\n"
            "tipo Color = verde | amarillo\n"
            "funcion principal() -> nulo:\n"
            "    retornar\n"
        )
        assert diag.hay_errores()
        assert any(e['codigo'] == ErrorCodes.ERR_SEM_REDEFINICION
                   for e in diag.errores)

    def test_redefinicion_variable_local_observable(self):
        diag = _analizar(
            "#lang: es\n"
            "funcion f() -> entero:\n"
            "    let x = 1\n"
            "    let x = 2\n"
            "    retornar x\n"
            "funcion principal() -> nulo:\n"
            "    retornar\n"
        )
        assert diag.hay_errores()
        assert any(e['codigo'] == ErrorCodes.ERR_SEM_REDEFINICION
                   for e in diag.errores)

    def test_shadowing_ambito_anidado_ok(self):
        # El shadowing en un ambito anidado NO es REDEFINICION (declarar
        # retorna True en el scope nuevo; solo el mismo ambito es error).
        diag = _analizar(
            "#lang: es\n"
            "funcion f(x: entero) -> entero:\n"
            "    si x > 0:\n"
            "        let x = 99\n"
            "        retornar x\n"
            "    retornar x\n"
            "funcion principal() -> nulo:\n"
            "    retornar\n"
        )
        assert not diag.hay_errores(), [e for e in diag.errores]
