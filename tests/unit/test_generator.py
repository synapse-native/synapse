# cumple Manual 2 §4
import pytest
from compilador.ast_nodes import Programa
from compilador.generator import GeneradorC

pytestmark = pytest.mark.unit


class TestGeneradorCUnit:

    def test_generador_crea_codigo(self):
        prog = Programa()
        generador = GeneradorC(prog)
        bin_codigo = generador.generar()
        assert bin_codigo is not None
        assert len(bin_codigo) > 0

    def test_encabezado_incluye_include(self):
        prog = Programa()
        generador = GeneradorC(prog)
        bin_codigo = generador.generar()
        assert "#include" in bin_codigo

    def test_codigo_incluye_runtime(self):
        prog = Programa()
        generador = GeneradorC(prog)
        bin_codigo = generador.generar()
        assert "salir(int" in bin_codigo or "void salir" in bin_codigo

    def test_generador_no_es_nulo(self):
        prog = Programa()
        generador = GeneradorC(prog)
        assert generador is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])