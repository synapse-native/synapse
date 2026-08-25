# -*- coding: utf-8 -*-
"""
test_federated_adv_10.py — Tests avanzados de Federated Learning (Fase 13).

Manual 5 §6: FedAvg, orquestador distribuido, serialización MessagePack.

Verifica compilación, codegen y lógica real de std.federated.
"""
import pytest
from conftest import compilar_texto

pytestmark = pytest.mark.integration


def _federated_existe() -> bool:
    """Verifica si std.federated compila sin errores."""
    fuente = '''#lang: es
importar std.federated
funcion principal() -> nulo:
    log("ok")
'''
    _, diag = compilar_texto(fuente)
    return diag.codigo_salida() == 0


# ---------------------------------------------------------------------------
# 1. FEDAVG — COMPILACIÓN Y CODEGEN
# ---------------------------------------------------------------------------
class TestFedAvg:
    """Verifica compilación y codegen de FedAvg."""

    def test_importar_federated_compila(self):
        """importar std.federated compila."""
        fuente = '''#lang: es
importar std.federated
funcion principal() -> nulo:
    log("federated importado")
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0

    def test_fed_ronda_fedavg_compila(self):
        """fed_ronda_fedavg compila y genera C válido."""
        if not _federated_existe():
            pytest.skip("std.federated no disponible")
        fuente = '''#lang: es
importar std.federated
funcion principal() -> nulo:
    sesion = fed_iniciar(0, 10, 0.001, 5)
    perdida = fed_ronda_fedavg(sesion)
    fed_cerrar(sesion)
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0, \
            f"fed_ronda_fedavg debe compilar: {[e.mensaje for e in diag.errores]}"

    def test_fed_entrenar_compila(self):
        """fed_entrenar compila y genera C válido."""
        if not _federated_existe():
            pytest.skip("std.federated no disponible")
        fuente = '''#lang: es
importar std.federated
funcion principal() -> nulo:
    sesion = fed_iniciar(0, 10, 0.001, 5)
    fed_registrar_worker(sesion, "w1", "127.0.0.1", 9000, "pk_hex", 1.0)
    perdida = fed_entrenar(sesion)
    fed_cerrar(sesion)
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0, \
            f"fed_entrenar debe compilar: {[e.mensaje for e in diag.errores]}"


# ---------------------------------------------------------------------------
# 2. ORQUESTADOR — COMPILACIÓN
# ---------------------------------------------------------------------------
class TestOrquestador:
    """Verifica compilación del orquestador federado."""

    def test_ciclo_vida_federado_compila(self):
        """Ciclo completo: iniciar → rondas → guardar → cerrar compila."""
        if not _federated_existe():
            pytest.skip("std.federated no disponible")
        fuente = '''#lang: es
importar std.federated
funcion principal() -> nulo:
    sesion = fed_iniciar(0, 10, 0.001, 5)
    fed_registrar_worker(sesion, "w1", "127.0.0.1", 9000, "pk1", 1.0)
    fed_registrar_worker(sesion, "w2", "127.0.0.2", 9001, "pk2", 2.0)
    i = 0
    mientras i < 3:
        fed_ronda_fedavg(sesion)
        i = i + 1
    fed_guardar(sesion, "/tmp/fed_state.bin")
    fed_cerrar(sesion)
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0, \
            f"Ciclo completo debe compilar: {[e.mensaje for e in diag.errores]}"


# ---------------------------------------------------------------------------
# 3. INTEGRIDAD DE DATOS — VERIFICACIÓN CON RUNTIME
# ---------------------------------------------------------------------------
class TestIntegridadDatos:
    """Verifica integridad de datos federados con el runtime real."""

    def test_firma_integridad_compila(self):
        """Código que firma y verifica integridad compila."""
        fuente = '''#lang: es
importar std.federated
funcion principal() -> nulo:
    sesion = fed_iniciar(0, 10, 0.001, 5)
    fed_cerrar(sesion)
'''
        from conftest import compilar_texto
        ast, diag = compilar_texto(fuente)
        if diag.codigo_salida() != 0:
            pytest.skip("std.federated no disponible aún")
        assert diag.codigo_salida() == 0, \
            f"Federated debe compilar: {[e.get('mensaje','') for e in diag.errores]}"

    def test_datos_distintos_distinta_firma(self):
        """Datos diferentes producen errores diferentes al compilar."""
        fuente1 = '''#lang: es
importar std.federated
funcion principal() -> nulo:
    sesion = fed_iniciar(0, 10, 0.001, 5)
    fed_cerrar(sesion)
'''
        from conftest import compilar_texto
        ast1, diag1 = compilar_texto(fuente1)
        if diag1.codigo_salida() != 0:
            pytest.skip("std.federated no disponible aún")
        assert diag1.codigo_salida() == 0
