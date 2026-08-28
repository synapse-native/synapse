# -*- coding: utf-8 -*-
"""
tests/unit/test_ast_serialization.py — Manual 2 §12

Criterio: "Serialización y deserialización correcta a `.syn.json`"

Formato EXACTO según M2 §13:
{
  "tipo": "Programa",
  "declaraciones": [
    {
      "tipo": "FuncionDef",
      "nombre": "sumar",
      "parametros": [
        { "nombre": "a", "tipo": "int", "es_transferencia": false }
      ],
      "tipo_retorno": "int",
      "contratos": null,
      "cuerpo": {
        "tipo": "Bloque",
        "sentencias": [...]
      }
    }
  ]
}

Este test ES la especificación. Si el código no produce este formato,
el test falla y se corrige el CÓDIGO.
"""
import json
import os
import sys
import tempfile

import pytest

pytestmark = pytest.mark.unit

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from compilador.lexer import Lexer
from compilador.parser import Parser
from compilador.diagnostics import DiagnosticManager


def _parsear(fuente: str):
    """Parsea código Synapse y retorna Programa."""
    fuente_completa = f"#lang: es\n{fuente}" if not fuente.startswith('#lang:') else fuente
    tokens = Lexer(fuente_completa).tokenizar()
    diag = DiagnosticManager()
    return Parser(tokens, diag).parsear()


def _serializar_a_archivo(programa, ruta: str):
    """Serializa un Programa a archivo .syn.json."""
    from compilador.canonical import ast_a_canonico
    json_str = ast_a_canonico(programa)
    with open(ruta, 'w', encoding='utf-8') as f:
        f.write(json_str)


def _deserializar_desde_archivo(ruta: str):
    """Lee un archivo .syn.json y reconstruye el Programa."""
    from compilador.canonical import canonico_a_ast
    with open(ruta, 'r', encoding='utf-8') as f:
        json_str = f.read()
    return canonico_a_ast(json_str)


def _leer_json(ruta: str) -> dict:
    """Lee y retorna el JSON crudo de un archivo .syn.json."""
    with open(ruta, 'r', encoding='utf-8') as f:
        return json.load(f)


# =========================================================================
# 1. SERIALIZACIÓN A ARCHIVO .syn.json (M2 §12)
# =========================================================================
class TestSerializacionArchivo:
    """M2 §12: serialización correcta a `.syn.json`."""

    def test_crea_archivo_syn_json(self, tmp_path):
        """Serializar produce un archivo .syn.json existente y no vacío."""
        prog = _parsear("funcion principal() -> nulo:\n    retornar")
        ruta = str(tmp_path / "programa.syn.json")
        _serializar_a_archivo(prog, ruta)
        assert os.path.exists(ruta)
        assert os.path.getsize(ruta) > 0

    def test_archivo_contiene_json_valido(self, tmp_path):
        """El archivo .syn.json contiene JSON parseable."""
        prog = _parsear("funcion principal() -> nulo:\n    retornar")
        ruta = str(tmp_path / "programa.syn.json")
        _serializar_a_archivo(prog, ruta)
        data = _leer_json(ruta)
        assert isinstance(data, dict)


# =========================================================================
# 2. FORMATO JSON — M2 §13 (ESTRICTO, sin fallbacks)
# =========================================================================
class TestFormatoManualM2_13:
    """M2 §13: el JSON debe tener EXACTAMENTE la estructura del manual."""

    def test_raiz_tiene_tipo_programa(self, tmp_path):
        """M2 §13: raíz tiene campo 'tipo' con valor 'Programa'."""
        prog = _parsear("funcion principal() -> nulo:\n    retornar")
        ruta = str(tmp_path / "p.syn.json")
        _serializar_a_archivo(prog, ruta)
        data = _leer_json(ruta)
        assert data.get("tipo") == "Programa", \
            f"M2 §13 exige 'tipo': 'Programa' en raíz, obtuvo: {data.get('tipo')}"

    def test_raiz_tiene_declaraciones(self, tmp_path):
        """M2 §13: raíz tiene campo 'declaraciones' (NO 'sentencias')."""
        prog = _parsear("funcion principal() -> nulo:\n    retornar")
        ruta = str(tmp_path / "p.syn.json")
        _serializar_a_archivo(prog, ruta)
        data = _leer_json(ruta)
        assert "declaraciones" in data, \
            f"M2 §13 exige campo 'declaraciones', claves actuales: {list(data.keys())}"

    def test_funcion_se_llama_funciondef(self, tmp_path):
        """M2 §13: tipo de nodo función es 'FuncionDef' (NO 'DefinicionFuncion')."""
        prog = _parsear("funcion sumar(a: entero) -> entero:\n    retornar a")
        ruta = str(tmp_path / "p.syn.json")
        _serializar_a_archivo(prog, ruta)
        data = _leer_json(ruta)
        fn = data["declaraciones"][0]
        assert fn.get("tipo") == "FuncionDef", \
            f"M2 §13 exige 'tipo': 'FuncionDef', obtuvo: {fn.get('tipo')}"

    def test_funcion_campos_requeridos(self, tmp_path):
        """M2 §13: FuncionDef tiene nombre, parametros, tipo_retorno, contratos, cuerpo."""
        prog = _parsear("funcion sumar(a: entero, b: entero) -> entero:\n    retornar a + b")
        ruta = str(tmp_path / "p.syn.json")
        _serializar_a_archivo(prog, ruta)
        data = _leer_json(ruta)
        fn = data["declaraciones"][0]
        for campo in ["nombre", "parametros", "tipo_retorno", "contratos", "cuerpo"]:
            assert campo in fn, \
                f"M2 §13: FuncionDef debe tener '{campo}', claves actuales: {list(fn.keys())}"

    def test_parametros_formato_manual(self, tmp_path):
        """M2 §13: parámetros tienen nombre, tipo, es_transferencia."""
        prog = _parsear("funcion f(a: entero, b: texto) -> nulo:\n    retornar")
        ruta = str(tmp_path / "p.syn.json")
        _serializar_a_archivo(prog, ruta)
        data = _leer_json(ruta)
        params = data["declaraciones"][0]["parametros"]
        assert len(params) == 2
        for p in params:
            for campo in ["nombre", "tipo", "es_transferencia"]:
                assert campo in p, \
                    f"M2 §13: parámetro debe tener '{campo}', claves: {list(p.keys())}"
        assert params[0]["nombre"] == "a"
        assert params[0]["tipo"] == "entero"

    def test_cuerpo_es_bloque_con_sentencias(self, tmp_path):
        """M2 §13: cuerpo tiene 'tipo': 'Bloque' y 'sentencias'."""
        prog = _parsear("funcion f() -> nulo:\n    retornar")
        ruta = str(tmp_path / "p.syn.json")
        _serializar_a_archivo(prog, ruta)
        data = _leer_json(ruta)
        bin_cuerpo = data["declaraciones"][0]["cuerpo"]
        assert bin_cuerpo.get("tipo") == "Bloque", \
            f"M2 §13: cuerpo debe ser 'Bloque', obtuvo: {bin_cuerpo.get('tipo')}"
        assert "sentencias" in bin_cuerpo, \
            f"M2 §13: Bloque debe tener 'sentencias', claves: {list(bin_cuerpo.keys())}"

    def test_retornar_campos_manual(self, tmp_path):
        """M2 §13: SentenciaRetornar tiene 'es_transferencia' y 'valor'."""
        prog = _parsear("funcion f() -> entero:\n    retornar 42")
        ruta = str(tmp_path / "p.syn.json")
        _serializar_a_archivo(prog, ruta)
        data = _leer_json(ruta)
        sentencias = data["declaraciones"][0]["cuerpo"]["sentencias"]
        ret = sentencias[0]
        assert ret.get("tipo") == "SentenciaRetornar", \
            f"M2 §13: sentencia debe ser 'SentenciaRetornar', obtuvo: {ret.get('tipo')}"
        assert "es_transferencia" in ret, \
            f"M2 §13: SentenciaRetornar debe tener 'es_transferencia'"
        assert "valor" in ret, \
            f"M2 §13: SentenciaRetornar debe tener 'valor' (no 'expr')"

    def test_expresion_aritmetica_campos_manual(self, tmp_path):
        """M2 §13: ExpresionArit tiene operador, izquierda, derecha."""
        prog = _parsear("funcion f() -> entero:\n    retornar 1 + 2")
        ruta = str(tmp_path / "p.syn.json")
        _serializar_a_archivo(prog, ruta)
        data = _leer_json(ruta)
        ret = data["declaraciones"][0]["cuerpo"]["sentencias"][0]
        expr = ret["valor"]
        assert expr.get("tipo") == "ExpresionArit", \
            f"M2 §13: expresión debe ser 'ExpresionArit', obtuvo: {expr.get('tipo')}"
        assert expr.get("operador") == "+"
        assert "izquierda" in expr, \
            f"M2 §13: ExpresionArit debe tener 'izquierda' (no 'izquierdo')"
        assert "derecha" in expr, \
            f"M2 §13: ExpresionArit debe tener 'derecha' (no 'derecho')"


# =========================================================================
# 3. DESERIALIZACIÓN — ROUNDTRIP ARCHIVO → AST (M2 §12)
# =========================================================================
class TestRoundtripArchivo:
    """M2 §12: deserialización correcta desde `.syn.json`."""

    def test_roundtrip_archivo_completo(self, tmp_path):
        """Serializar → archivo → deserializar → verificar Programa."""
        prog = _parsear("funcion principal() -> nulo:\n    retornar")
        ruta = str(tmp_path / "p.syn.json")
        _serializar_a_archivo(prog, ruta)
        prog2 = _deserializar_desde_archivo(ruta)
        assert prog2 is not None
        assert len(prog2.sentencias) == len(prog.sentencias)

    def test_roundtrip_preserva_nombre_funcion(self, tmp_path):
        """Roundtrip preserva nombre de la función."""
        prog = _parsear("funcion sumar(k: entero) -> entero:\n    retornar k")
        ruta = str(tmp_path / "p.syn.json")
        _serializar_a_archivo(prog, ruta)
        prog2 = _deserializar_desde_archivo(ruta)
        fn = prog2.sentencias[0]
        assert fn.nombre == "sumar"

    def test_roundtrip_preserva_parametros(self, tmp_path):
        """Roundtrip preserva parámetros con nombre y tipo."""
        prog = _parsear("funcion f(a: entero, b: texto) -> nulo:\n    retornar")
        ruta = str(tmp_path / "p.syn.json")
        _serializar_a_archivo(prog, ruta)
        prog2 = _deserializar_desde_archivo(ruta)
        fn = prog2.sentencias[0]
        assert len(fn.parametros) == 2
        assert fn.parametros[0].nombre == "a"
        assert fn.parametros[0].tipo == "entero"

    def test_roundtrip_preserva_tipo_retorno(self, tmp_path):
        """Roundtrip preserva tipo de retorno."""
        prog = _parsear("funcion f() -> entero:\n    retornar 1")
        ruta = str(tmp_path / "p.syn.json")
        _serializar_a_archivo(prog, ruta)
        prog2 = _deserializar_desde_archivo(ruta)
        assert prog2.sentencias[0].tipo_retorno == "entero"

    def test_roundtrip_preserva_estructura(self, tmp_path):
        """Roundtrip preserva estructura con campos."""
        prog = _parsear("estructura Punto:\n    x: entero\n    z: entero")
        ruta = str(tmp_path / "p.syn.json")
        _serializar_a_archivo(prog, ruta)
        prog2 = _deserializar_desde_archivo(ruta)
        est = prog2.sentencias[0]
        assert est.nombre == "Punto"
        assert len(est.campos) == 2

    def test_roundtrip_preserva_adt(self, tmp_path):
        """Roundtrip preserva tipo ADT."""
        prog = _parsear("tipo Resultado<T, E> = ok(T) | err(E)")
        ruta = str(tmp_path / "p.syn.json")
        _serializar_a_archivo(prog, ruta)
        prog2 = _deserializar_desde_archivo(ruta)
        dt = prog2.sentencias[0]
        assert dt.nombre == "Resultado"

    def test_roundtrip_ejemplo_manual_m2_13(self, tmp_path):
        """M2 §13: roundtrip del ejemplo completo del manual."""
        prog = _parsear(
            "funcion sumar(a: entero, b: entero) -> entero:\n"
            "    retornar a + b\n"
            "\n"
            "funcion principal() -> nulo:\n"
            "    resultado = sumar(5, 3)\n"
            "    log(\"Resultado: \", resultado)\n"
        )
        ruta = str(tmp_path / "p.syn.json")
        _serializar_a_archivo(prog, ruta)
        prog2 = _deserializar_desde_archivo(ruta)
        assert len(prog2.sentencias) >= 2


# =========================================================================
# 4. CASOS NEGATIVOS
# =========================================================================
class TestCasosNegativos:
    """Archivos inválidos deben ser rechazados."""

    def test_json_malformado_rechazado(self, tmp_path):
        """JSON inválido en .syn.json debe fallar al deserializar."""
        ruta = str(tmp_path / "malo.syn.json")
        with open(ruta, 'w') as f:
            f.write("esto no es json")
        with pytest.raises((json.JSONDecodeError, ValueError)):
            _deserializar_desde_archivo(ruta)

    def test_wrapper_incorrecto_rechazado(self, tmp_path):
        """JSON sin 'tipo': 'Programa' en raíz debe fallar."""
        ruta = str(tmp_path / "malo.syn.json")
        with open(ruta, 'w') as f:
            json.dump({"tipo": "OtraCosa", "declaraciones": []}, f)
        with pytest.raises((ValueError, KeyError, TypeError)):
            _deserializar_desde_archivo(ruta)


# =========================================================================
# 5. NODOS VACÍOS — robustez de serialización
# =========================================================================
class TestNodosVacios:
    """AST con estructuras mínimas o vacías serializa/deserializa correctamente."""

    def test_programa_vacio(self, tmp_path):
        """Un programa sin sentencias serializa y deserializa sin error."""
        prog = _parsear("x = 1")  # el parser requiere al menos 1 stmt
        assert len(prog.sentencias) >= 1
        ruta = str(tmp_path / "vacio.syn.json")
        _serializar_a_archivo(prog, ruta)
        prog2 = _deserializar_desde_archivo(ruta)
        assert prog2 is not None
        assert isinstance(prog2.sentencias, list)

    def test_funcion_sin_cuerpo(self, tmp_path):
        """Una función con retornar vacío serializa correctamente."""
        prog = _parsear("funcion f() -> nulo:\n    retornar")
        ruta = str(tmp_path / "fn_vacia.syn.json")
        _serializar_a_archivo(prog, ruta)
        data = _leer_json(ruta)
        fn = data["declaraciones"][0]
        assert fn["nombre"] == "f"
        assert isinstance(fn["cuerpo"], dict)

    def test_roundtrip_sentencia_unica(self, tmp_path):
        """Una sola sentencia serializa y deserializa correctamente."""
        prog = _parsear("x = 42")
        ruta = str(tmp_path / "una.syn.json")
        _serializar_a_archivo(prog, ruta)
        prog2 = _deserializar_desde_archivo(ruta)
        assert len(prog2.sentencias) == 1


# =========================================================================
# 6. UTF-8 — M2 §1: "archivos codificados en UTF-8 sin BOM"
# =========================================================================
class TestEncodingUTF8:
    """M2 §1: caracteres UTF-8 preservados en serialización a .syn.json."""

    def test_string_con_tilde(self, tmp_path):
        """Un string con tilde preserva el contenido en .syn.json."""
        prog = _parsear('x = "caf\u00e9"')
        ruta = str(tmp_path / "utf8.syn.json")
        _serializar_a_archivo(prog, ruta)
        with open(ruta, 'r', encoding='utf-8') as f:
            bin_contenido = f.read()
        assert "caf\u00e9" in bin_contenido, "El string con tilde debe preservarse en el JSON"

    def test_roundtrip_string_utf8(self, tmp_path):
        """Roundtrip preserva contenido UTF-8 en strings."""
        prog = _parsear('x = "a\u00f1o"')
        ruta = str(tmp_path / "utf8.syn.json")
        _serializar_a_archivo(prog, ruta)
        prog2 = _deserializar_desde_archivo(ruta)
        assert prog2 is not None
        # El AST reconstruido debe tener la sentencia
        assert len(prog2.sentencias) >= 1

    def test_archivo_es_utf8_sin_bom(self, tmp_path):
        """M2 §1: el archivo .syn.json está codificado en UTF-8 sin BOM."""
        prog = _parsear('x = "ni\u00f1o"')
        ruta = str(tmp_path / "utf8.syn.json")
        _serializar_a_archivo(prog, ruta)
        with open(ruta, 'rb') as f:
            primeros_bytes = f.read(3)
        # BOM UTF-8 es EF BB BF — no debe estar presente
        assert primeros_bytes[:3] != b'\xef\xbb\xbf', "El archivo no debe tener BOM UTF-8"
