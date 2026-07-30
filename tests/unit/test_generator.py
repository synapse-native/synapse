import pytest
from ast_nodes import Programa
from generator import GeneradorC


class TestGeneradorCUnit:

    def test_generador_crea_codigo(self):
        prog = Programa()
        generador = GeneradorC(prog)
        codigo = generador.generar()
        assert codigo is not None
        assert len(codigo) > 0

    def test_encabezado_incluye_include(self):
        prog = Programa()
        generador = GeneradorC(prog)
        codigo = generador.generar()
        assert "#include" in codigo

    def test_codigo_incluye_runtime(self):
        prog = Programa()
        generador = GeneradorC(prog)
        codigo = generador.generar()
        assert "salir(int" in codigo or "void salir" in codigo

    def test_generador_no_es_nulo(self):
        prog = Programa()
        generador = GeneradorC(prog)
        assert generador is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])