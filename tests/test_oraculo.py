import os, sys, json, subprocess, tempfile
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

HELPER = os.path.join(os.path.dirname(__file__), '..', '_compilar_helper.py')
PYTHON = sys.executable

CODIGO_VALIDO = """#lang: es

funcion hola() -> texto:
    retornar "mundo"
"""

CODIGO_INVALIDO_SINTAXIS = """#lang: es

funcion hola() -> texto:
    esto no es valido
"""

CODIGO_INVALIDO_LANG = """funcion hola() -> texto:
    retornar "mundo"
"""


def _invocar_helper(codigo_fuente: str) -> dict:
    with tempfile.NamedTemporaryFile(
        mode='w', suffix='.syn', encoding='utf-8', delete=False
    ) as f:
        f.write(codigo_fuente)
        syn_path = f.name

    try:
        result = subprocess.run(
            [PYTHON, HELPER, syn_path],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            pytest.fail(f"Helper exited with code {result.returncode}: {result.stderr}")
        return json.loads(result.stdout)
    finally:
        os.unlink(syn_path)
        # clean up generated .c file if any
        c_path = syn_path.rsplit('.', 1)[0] + '.c'
        if os.path.exists(c_path):
            os.unlink(c_path)


class TestCompilarHelper:
    def test_codigo_valido_devuelve_exito(self):
        resultado = _invocar_helper(CODIGO_VALIDO)
        assert resultado["exito"] is True
        assert "codigo_c" in resultado
        assert len(resultado["codigo_c"]) > 0
        assert "#include" in resultado["codigo_c"]

    def test_codigo_invalido_devuelve_error(self):
        resultado = _invocar_helper(CODIGO_INVALIDO_SINTAXIS)
        assert resultado["exito"] is False
        assert "errores" in resultado
        assert len(resultado["errores"]) > 0

    def test_error_contiene_linea_columna_mensaje(self):
        resultado = _invocar_helper(CODIGO_INVALIDO_SINTAXIS)
        assert resultado["exito"] is False
        for err in resultado["errores"]:
            assert "linea" in err
            assert "columna" in err
            assert "mensaje" in err

    def test_lang_faltante_detectado(self):
        resultado = _invocar_helper(CODIGO_INVALIDO_LANG)
        assert resultado["exito"] is False
        assert len(resultado["errores"]) > 0

    def test_codigo_generado_es_c_valido(self):
        resultado = _invocar_helper(CODIGO_VALIDO)
        assert resultado["exito"] is True
        codigo_c = resultado["codigo_c"]
        assert "int main" in codigo_c or "principal" in codigo_c
        # Should contain the function definition
        assert "hola" in codigo_c

    def test_archivo_inexistente_devuelve_error(self):
        result = subprocess.run(
            [PYTHON, HELPER, "no_existe.syn"],
            capture_output=True, text=True, timeout=30
        )
        assert result.returncode != 0 or json.loads(result.stdout)["exito"] is False

    def test_sin_argumentos_devuelve_error(self):
        result = subprocess.run(
            [PYTHON, HELPER],
            capture_output=True, text=True, timeout=30
        )
        assert result.returncode != 0
        datos = json.loads(result.stdout)
        assert datos["exito"] is False


class TestOraculoExtraccionBloque:
    """Pruebas del concepto de extraccion de bloques de codigo."""

    def test_extraer_codigo_simple(self):
        texto = "Algun texto\n```\nfuncion foo() -> entero:\n    retornar 1\n```\nmas texto"
        lineas = texto.split('\n')
        dentro = False
        codigo = []
        for linea in lineas:
            if linea.startswith('```'):
                dentro = not dentro
                continue
            if dentro:
                codigo.append(linea)
        resultado = '\n'.join(codigo)
        assert "funcion foo" in resultado
        assert "retornar 1" in resultado

    def test_extraer_sin_bloques(self):
        texto = "texto sin bloques de codigo"
        lineas = texto.split('\n')
        dentro = False
        codigo = []
        for linea in lineas:
            if linea.startswith('```'):
                dentro = not dentro
                continue
            if dentro:
                codigo.append(linea)
        resultado = '\n'.join(codigo)
        assert resultado == ""

    def test_extraer_bloques_llm_tipico(self):
        texto = """Claro, aqui tienes el codigo:

```synapse
#lang: es
funcion sumar(a: entero, b: entero) -> entero:
    retornar a + b
```

Este codigo suma dos numeros."""
        lineas = texto.split('\n')
        dentro = False
        codigo = []
        for linea in lineas:
            if linea.startswith('```'):
                dentro = not dentro
                continue
            if dentro:
                codigo.append(linea)
        resultado = '\n'.join(codigo)
        assert "#lang: es" in resultado
        assert "funcion sumar" in resultado
        assert "retornar" in resultado

    def test_extraer_sin_markdown_codigo_completo(self):
        """Si no hay bloques ```, se usa la respuesta completa."""
        texto = "#lang: es\nfuncion foo() -> entero:\n    retornar 42\n"
        lineas = texto.split('\n')
        dentro = False
        codigo = []
        for linea in lineas:
            if linea.startswith('```'):
                dentro = not dentro
                continue
            if dentro:
                codigo.append(linea)
        # When no blocks found, return empty - caller should use full response
        assert len(codigo) == 0

    def test_extraer_varios_bloques(self):
        """Si hay varios bloques, devuelve todos concatenados."""
        texto = "a\n```\nbloque1\n```\nb\n```\nbloque2\n```\nc"
        lineas = texto.split('\n')
        dentro = False
        codigo = []
        for linea in lineas:
            if linea.startswith('```'):
                dentro = not dentro
                continue
            if dentro:
                codigo.append(linea)
        resultado = '\n'.join(codigo)
        assert "bloque1" in resultado
        assert "bloque2" in resultado


class TestOraculoFuncionCompleta:
    """Prueba el flujo completo del Oraculo como si fuera una funcion Python."""

    def test_flujo_completo_exitoso(self):
        """Simula el bucle del Oraculo a nivel Python: generar -> compilar -> ok."""
        # En lugar de llamar a un LLM, usamos codigo pre-escrito valido
        codigo_generado = CODIGO_VALIDO
        resultado = _invocar_helper(codigo_generado)
        assert resultado["exito"] is True

    def test_flujo_con_error_y_correccion(self):
        """Simula: intento 1 falla, intento 2 corrige."""
        codigo_mal = CODIGO_INVALIDO_SINTAXIS
        resultado1 = _invocar_helper(codigo_mal)
        assert resultado1["exito"] is False

        # Simular correccion del LLM
        codigo_bien = CODIGO_VALIDO
        resultado2 = _invocar_helper(codigo_bien)
        assert resultado2["exito"] is True

    def test_errores_contienen_informacion_util(self):
        """Verifica que los mensajes de error sean utiles para feedback."""
        resultado = _invocar_helper(CODIGO_INVALIDO_SINTAXIS)
        assert resultado["exito"] is False
        for err in resultado["errores"]:
            msg = err["mensaje"]
            assert isinstance(msg, str)
            assert len(msg) > 0  # mensaje no vacio
            assert err["linea"] >= 0
            assert err["columna"] >= 0


class TestCompilarHelperCodigoComplejo:
    """Prueba helper con codigo mas complejo."""

    CODIGO_TENSORES = """#lang: es

funcion crear_matriz(filas: entero, columnas: entero) -> tensor:
    t = crear_tensor(filas, columnas)
    retornar t

funcion principal() -> entero:
    m = crear_matriz(2, 3)
    retornar 0
"""

    def test_codigo_con_tensores(self):
        resultado = _invocar_helper(self.CODIGO_TENSORES)
        assert resultado["exito"] is True
        assert "crear_tensor" in resultado["codigo_c"]

    CODIGO_ESTR_LEN = """#lang: es

funcion longitud(s: texto) -> entero:
    retornar contar(s)

funcion principal() -> entero:
    s = "hola"
    escribir_linea(entero_a_texto(longitud(s)))
    retornar 0
"""

    def test_codigo_con_funciones_anidadas(self):
        resultado = _invocar_helper(self.CODIGO_ESTR_LEN)
        assert resultado["exito"] is True
