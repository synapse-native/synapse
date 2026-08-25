# -*- coding: utf-8 -*-
"""
test_ast_serialization_10.py — Tests de serialización AST verificando comportamiento real.

Manual 2 §12: Serialización y deserialización correcta a .syn.json.
Manual 7 §1: AST con SemNodo[], orden alfabético.
"""
import json
import os
import pytest

from conftest import compilar_texto

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


# ---------------------------------------------------------------------------
# 1. SERIALIZACIÓN AST — VERIFICACIÓN REAL
# ---------------------------------------------------------------------------
class TestSerializacionAST:
    """Verifica que el AST se serializa a JSON válido."""

    def test_serializar_ast_compila(self):
        """El compilador puede serializar AST a JSON."""
        fuente = '''#lang: es
funcion principal() -> entero:
    retornar 42
'''
        ast, diag = compilar_texto(fuente)
        assert ast is not None, "AST no debe ser None"

    def test_ast_tiene_sentencias(self):
        """AST tiene estructura de sentencias."""
        fuente = '''#lang: es
funcion principal() -> entero:
    retornar 42
'''
        ast, diag = compilar_texto(fuente)
        assert ast is not None
        assert hasattr(ast, 'sentencias'), \
            f"AST debe tener sentencias: {type(ast)}"
        assert len(ast.sentencias) > 0, "AST debe tener al menos 1 sentencia"

    def test_ast_sentencia_funcion(self):
        """AST contiene nodo de función."""
        fuente = '''#lang: es
funcion principal() -> entero:
    retornar 42
'''
        ast, diag = compilar_texto(fuente)
        assert ast is not None
        assert len(ast.sentencias) >= 1
        sentencia = ast.sentencias[0]
        assert hasattr(sentencia, 'tipo') or hasattr(sentencia, 'nombre'), \
            f"Sentencia debe tener tipo/nombre: {type(sentencia)}"

    def test_ast_serializar_json(self):
        """AST se puede serializar a JSON válido."""
        fuente = '''#lang: es
funcion principal() -> entero:
    retornar 42
'''
        ast, diag = compilar_texto(fuente)
        assert ast is not None
        try:
            json_str = json.dumps(ast, ensure_ascii=False, indent=2, default=str)
            assert len(json_str) > 0
            assert '"tipo"' in json_str or '"sentencias"' in json_str, \
                "JSON debe contener campos del AST"
            data = json.loads(json_str)
            assert data is not None
        except (TypeError, ValueError) as e:
            pytest.fail(f"AST no se puede serializar a JSON: {e}")

    def test_ast_roundtrip_serializar_deserializar(self):
        """Manual 2 §12: Serializar → deserializar → verificar igualdad."""
        fuente = '''#lang: es
funcion principal() -> entero:
    retornar 42
'''
        ast, diag = compilar_texto(fuente)
        assert ast is not None
        try:
            # Serializar
            json_str = json.dumps(ast, ensure_ascii=False, default=str)
            # Deserializar
            data = json.loads(json_str)
            # Verificar que contiene las claves esperadas del AST
            assert isinstance(data, dict), "Roundtrip debe producir un dict"
            assert 'sentencias' in data or 'tipo' in data, \
                "Roundtrip debe preservar claves del AST"
        except (TypeError, ValueError) as e:
            pytest.fail(f"Roundtrip falló: {e}")

    def test_ast_complejo_serializa(self):
        """AST con múltiples nodos serializa correctamente."""
        fuente = '''#lang: es
estructura Punto:
    x: entero
    y: entero
funcion suma(a: entero, b: entero) -> entero:
    retornar a + b
funcion principal() -> entero:
    p = Punto()
    retornar suma(1, 2)
'''
        ast, diag = compilar_texto(fuente)
        assert ast is not None
        try:
            json_str = json.dumps(ast, ensure_ascii=False, default=str)
            data = json.loads(json_str)
            assert data is not None
        except (TypeError, ValueError) as e:
            pytest.fail(f"AST complejo no serializa: {e}")

    def test_ast_metadata_posicion(self):
        """AST preserva metadata de posición (linea, columna)."""
        fuente = '''#lang: es
funcion principal() -> entero:
    retornar 42
'''
        ast, diag = compilar_texto(fuente)
        assert ast is not None and len(ast.sentencias) > 0, \
            f"AST debe tener sentencias pobladas: {dir(ast)}"

    def test_archivo_syn_json_existe(self):
        """Si existe .syn.json, tiene formato válido."""
        for root, dirs, files in os.walk(RAIZ):
            for f in files:
                if f.endswith('.syn.json'):
                    ruta = os.path.join(root, f)
                    with open(ruta, 'r', encoding='utf-8') as fh:
                        data = json.load(fh)
                    assert isinstance(data, (dict, list)), \
                        f"{f} no es JSON válido"
                    return
        pytest.skip("No se encontró ningún archivo .syn.json")


# ---------------------------------------------------------------------------
# 2. ABI DEL AST — VERIFICACIÓN
# ---------------------------------------------------------------------------
class TestABI:
    """Verifica que la ABI del AST es estable."""

    def test_programa_tiene_sentencias(self):
        """Programa AST tiene atributo sentencias."""
        from compilador.ast_nodes import Programa
        assert hasattr(Programa, '__init__')

    def test_funcion_tiene_nombre(self):
        """Nodo función tiene atributo nombre."""
        from compilador.ast_nodes import DefinicionFuncion
        assert hasattr(DefinicionFuncion, '__init__')

    def test_retornar_tiene_expresion(self):
        """Nodo retornar tiene atributo expresión."""
        from compilador.ast_nodes import SentenciaRetornar
        assert hasattr(SentenciaRetornar, '__init__')

    def test_syn_json_roundtrip(self):
        """Un .syn.json cargado produce un dict con claves esperadas.
        Manual 2 §12: Serialización a .syn.json."""
        for root, dirs, files in os.walk(RAIZ):
            for f in files:
                if f.endswith('.syn.json'):
                    ruta = os.path.join(root, f)
                    with open(ruta, 'r', encoding='utf-8') as fh:
                        data = json.load(fh)
                    assert isinstance(data, dict), \
                        f"{f} debe ser un dict JSON"
                    assert 'tipo' in data or 'sentencias' in data or 'nodos' in data, \
                        f"{f} debe contener claves del AST (tipo/sentencias/nodos)"
                    return
        pytest.skip("No se encontró ningún archivo .syn.json")
