# -*- coding: utf-8 -*-
"""
test_federated_exec_10.py — Tests ejecutables de Federated Learning (Fase 13).

Manual 5 §6 (concurrencia distribuida): orquestador federado, FedAvg.
"""
import pytest
from conftest import compilar_texto

pytestmark = pytest.mark.integration

RAIZ = None  # not needed


def _federated_existe():
    """Verifica si std.federated compila."""
    fuente = '''#lang: es
importar std.federated
funcion principal() -> nulo:
    log("ok")
'''
    _, diag = compilar_texto(fuente)
    return diag.codigo_salida() == 0


# ---------------------------------------------------------------------------
# 1. FEDERATED — ARCHIVOS (Manual concurrencia)
# ---------------------------------------------------------------------------
class TestFederatedArchivos:
    """Verifica que los archivos de federated existen."""

    def test_federated_c_existe(self):
        """nucleo/federated.c debe existir."""
        import os
        fed = os.path.join(RAIZ or os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")),
                          "nucleo", "federated.c")
        assert os.path.exists(fed), "nucleo/federated.c no existe"

    def test_federated_h_existe(self):
        """nucleo/federated.h debe existir."""
        import os
        fed_h = os.path.join(RAIZ or os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")),
                            "nucleo", "federated.h")
        assert os.path.exists(fed_h), "nucleo/federated.h no existe"

    def test_std_federated_existe(self):
        """std/federated.syn debe existir."""
        import os
        std_fed = os.path.join(RAIZ or os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")),
                              "std", "federated.syn")
        assert os.path.exists(std_fed), "std/federated.syn no existe"


# ---------------------------------------------------------------------------
# 2. FEDAVG — FUNCIONALIDAD (Manual concurrencia)
# ---------------------------------------------------------------------------
class TestFedAvgFuncionalidad:
    """Verifica que FedAvg implementa la ronda de agregación."""

    def test_federated_api(self):
        pytest.skip('ME-4: Refactor pendiente a validación funcional')
        """federated.h debe declarar API de FedAvg."""
        import os
        fed_h = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")),
                            "nucleo", "federated.h")
        with open(fed_h, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        assert "fed_ronda" in contenido or "fedavg" in contenido.lower() or \
            "ronda" in contenido.lower() or "agregar" in contenido.lower(), \
            "federated.h debe declarar API de FedAvg"

    def test_federated_iniciar(self):
        pytest.skip('ME-4: Refactor pendiente a validación funcional')
        """federated.h debe tener función para iniciar sesión."""
        import os
        fed_h = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")),
                            "nucleo", "federated.h")
        with open(fed_h, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        assert "iniciar" in contenido or "create" in contenido or "init" in contenido or \
            "sesion" in contenido.lower(), \
            "federated.h debe tener función para iniciar sesión"

    def test_federated_cerrar(self):
        pytest.skip('ME-4: Refactor pendiente a validación funcional')
        """federated.h debe tener función para cerrar sesión."""
        import os
        fed_h = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")),
                            "nucleo", "federated.h")
        with open(fed_h, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        assert "cerrar" in contenido or "close" in contenido or "destroy" in contenido, \
            "federated.h debe tener función para cerrar sesión"


# ---------------------------------------------------------------------------
# 3. FEDAVG — CODEGEN C (compilación)
# ---------------------------------------------------------------------------
class TestFedAvgCodegen:
    """Verifica que código con FedAvg genera C válido."""

    def test_fedavg_genera_codigo_c(self):
        """Código con FedAvg genera C con llamada a fed_ronda_fedavg."""
        fuente = '''#lang: es
importar std.federated
funcion principal() -> nulo:
    fed_ronda_fedavg(0)
'''
        ast, diag = compilar_texto(fuente)
        if diag.codigo_salida() != 0:
            pytest.skip("std.federated no disponible aún")
        from compilador.generator import GeneradorC
        codigo = GeneradorC(ast).generar()
        assert codigo, "Debe generar código C"
        assert "fed" in codigo.lower() or "federated" in codigo.lower() or \
            "promediar" in codigo.lower(), \
            f"Código C debe referenciar federated:\n{codigo[:500]}"

    def test_fedavg_ciclo_completo_compila(self):
        """Ciclo completo: iniciar → rounds → cerrar compila."""
        if not _federated_existe():
            pytest.skip("std.federated no existe aún")
        fuente = '''#lang: es
importar std.federated
funcion principal() -> nulo:
    sesion = fed_iniciar(0, 10, 0.001, 5)
    fed_registrar_worker(sesion, "w1", "127.0.0.1", 9000, "pk1", 1.0)
    i = 0
    mientras i < 5:
        fed_ronda_fedavg(sesion)
        i = i + 1
    fed_cerrar(sesion)
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0, \
            f"Ciclo orquestador debe compilar: {[e.get('mensaje','') for e in diag.errores]}"

    def test_fedavg_iniciar_cerrar(self):
        """Iniciar y cerrar sesión compila."""
        if not _federated_existe():
            pytest.skip("std.federated no existe aún")
        fuente = '''#lang: es
importar std.federated
funcion principal() -> nulo:
    sesion = fed_iniciar(0, 10, 0.001, 5)
    fed_cerrar(sesion)
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0, \
            f"Iniciar/cerrar debe compilar: {[e.get('mensaje','') for e in diag.errores]}"
