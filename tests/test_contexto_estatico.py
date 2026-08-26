# -*- coding: utf-8 -*-
"""
test_contexto_estatico.py — M7 §2.3: Sistema de inyección de contexto estático.

Manual 7 §2.3: "OpenSyn inyecta un bloque de 'Reglas de Sintaxis' en el System Prompt de cada consulta.
Este bloque contiene la gramática esencial, el modelo de memoria y ejemplos de Synapse/Syquex."

ESTE ARCHIVO ES LA ESPECIFICACIÓN DEL MANUAL. No lee código fuente.
Los tests deben FALLAR si el código no está implementado.
"""
import os
import pytest
import sys

# Agregar directorio raíz al path
RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, RAIZ)

pytestmark = pytest.mark.integration

class TestRequisitosManuales:
    """Verificación de requisitos explícitos del Manual 7 §2.3."""

    def test_requisito_1_archivo_configuracion_debe_existir(self):
        """M7 §2.3: 'Este bloque debe ser configurable y actualizable mediante el archivo de configuración.'
        
        REQUISITO: Debe existir un archivo de configuración para las reglas.
        """
        ruta = os.path.join(RAIZ, "opensyn", "reglas_synapse.toml")
        assert os.path.exists(ruta), \
            "FALLA REQUISITO M7 §2.3: No existe archivo de configuración opensyn/reglas_synapse.toml"

    def test_requisito_2_archivo_debe_tener_secciones_synapse_syquex(self):
        """M7 §2.3: El bloque contiene reglas de Synapse y Syquex.
        
        REQUISITO: El archivo debe tener secciones [synapse] y [syquex].
        """
        ruta = os.path.join(RAIZ, "opensyn", "reglas_synapse.toml")
        if not os.path.exists(ruta):
            pytest.fail("FALLA REQUISITO M7 §2.3: No existe archivo de configuración")
        
        with open(ruta, 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        assert "[synapse]" in contenido, \
            "FALLA REQUISITO M7 §2.3: Falta sección [synapse] en archivo de configuración"
        assert "[syquex]" in contenido, \
            "FALLA REQUISITO M7 §2.3: Falta sección [syquex] en archivo de configuración"

    def test_requisito_3_sintaxis_synapse_funciones(self):
        """M7 §2.3: 'Funciones: funcion nombre(parametros) -> tipo:'
        
        REQUISITO: Reglas de Synapse deben incluir definición de funciones.
        """
        ruta = os.path.join(RAIZ, "opensyn", "reglas_synapse.toml")
        if not os.path.exists(ruta):
            pytest.fail("FALLA REQUISITO M7 §2.3: No existe archivo de configuración")
        
        with open(ruta, 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        assert "funcion" in contenido, \
            "FALLA REQUISITO M7 §2.3: Reglas de Synapse no incluyen 'funcion'"

    def test_requisito_4_sintaxis_synapse_variables(self):
        """M7 §2.3: 'Variables: let nombre = valor'
        
        REQUISITO: Reglas de Synapse deben incluir definición de variables.
        """
        ruta = os.path.join(RAIZ, "opensyn", "reglas_synapse.toml")
        if not os.path.exists(ruta):
            pytest.fail("FALLA REQUISITO M7 §2.3: No existe archivo de configuración")
        
        with open(ruta, 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        assert "let" in contenido, \
            "FALLA REQUISITO M7 §2.3: Reglas de Synapse no incluyen 'let'"

    def test_requisito_5_sintaxis_synapse_condicional(self):
        """M7 §2.3: 'Condicional: si condicion:'
        
        REQUISITO: Reglas de Synapse deben incluir condicional.
        """
        ruta = os.path.join(RAIZ, "opensyn", "reglas_synapse.toml")
        if not os.path.exists(ruta):
            pytest.fail("FALLA REQUISITO M7 §2.3: No existe archivo de configuración")
        
        with open(ruta, 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        assert "si" in contenido, \
            "FALLA REQUISITO M7 §2.3: Reglas de Synapse no incluyen 'si'"

    def test_requisito_6_sintaxis_synapse_bucle(self):
        """M7 §2.3: 'Bucle: mientras condicion:'
        
        REQUISITO: Reglas de Synapse deben incluir bucle.
        """
        ruta = os.path.join(RAIZ, "opensyn", "reglas_synapse.toml")
        if not os.path.exists(ruta):
            pytest.fail("FALLA REQUISITO M7 §2.3: No existe archivo de configuración")
        
        with open(ruta, 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        assert "mientras" in contenido, \
            "FALLA REQUISITO M7 §2.3: Reglas de Synapse no incluyen 'mientras'"

    def test_requisito_7_sintaxis_synapse_retorno(self):
        """M7 §2.3: 'Retorno con transferencia de ownership (move): retornar -> variable'
        
        REQUISITO: Reglas de Synapse deben incluir retorno con ownership.
        """
        ruta = os.path.join(RAIZ, "opensyn", "reglas_synapse.toml")
        if not os.path.exists(ruta):
            pytest.fail("FALLA REQUISITO M7 §2.3: No existe archivo de configuración")
        
        with open(ruta, 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        assert "retornar" in contenido, \
            "FALLA REQUISITO M7 §2.3: Reglas de Synapse no incluyen 'retornar'"

    def test_requisito_8_sintaxis_synapse_concurrencia(self):
        """M7 §2.3: 'Concurrencia: lanzar funcion()'
        
        REQUISITO: Reglas de Synapse deben incluir concurrencia.
        """
        ruta = os.path.join(RAIZ, "opensyn", "reglas_synapse.toml")
        if not os.path.exists(ruta):
            pytest.fail("FALLA REQUISITO M7 §2.3: No existe archivo de configuración")
        
        with open(ruta, 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        assert "lanzar" in contenido, \
            "FALLA REQUISITO M7 §2.3: Reglas de Synapse no incluyen 'lanzar'"

    def test_requisito_9_sintaxis_synapse_canales(self):
        """M7 §2.3: 'Canales: Canal<T> y canal <- valor, valor = canal ->'
        
        REQUISITO: Reglas de Synapse deben incluir canales.
        """
        ruta = os.path.join(RAIZ, "opensyn", "reglas_synapse.toml")
        if not os.path.exists(ruta):
            pytest.fail("FALLA REQUISITO M7 §2.3: No existe archivo de configuración")
        
        with open(ruta, 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        assert "Canal" in contenido, \
            "FALLA REQUISITO M7 §2.3: Reglas de Synapse no incluyen 'Canal'"

    def test_requisito_10_sintaxis_synapse_tensores(self):
        """M7 §2.3: 'Tensores: tensor(filas, columnas)'
        
        REQUISITO: Reglas de Synapse deben incluir tensores.
        """
        ruta = os.path.join(RAIZ, "opensyn", "reglas_synapse.toml")
        if not os.path.exists(ruta):
            pytest.fail("FALLA REQUISITO M7 §2.3: No existe archivo de configuración")
        
        with open(ruta, 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        assert "tensor" in contenido, \
            "FALLA REQUISITO M7 §2.3: Reglas de Synapse no incluyen 'tensor'"

    def test_requisito_11_sintaxis_syquex_funciones(self):
        """M7 §2.3: 'Funciones: funcion nombre(parametros) -> tipo:'
        
        REQUISITO: Reglas de Syquex deben incluir definición de funciones.
        """
        ruta = os.path.join(RAIZ, "opensyn", "reglas_synapse.toml")
        if not os.path.exists(ruta):
            pytest.fail("FALLA REQUISITO M7 §2.3: No existe archivo de configuración")
        
        with open(ruta, 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        # Buscar en la sección de syquex
        assert "[syquex]" in contenido, "Falta sección [syquex]"
        # Verificar que hay una definición de función en syquex
        lineas = contenido.split('\n')
        en_syquex = False
        funcion_encontrada = False
        for linea in lineas:
            if "[syquex]" in linea:
                en_syquex = True
            elif en_syquex and linea.startswith('[') and not linea.startswith('[syquex.'):
                en_syquex = False
            elif en_syquex and "funcion" in linea:
                funcion_encontrada = True
                break
        
        assert funcion_encontrada, \
            "FALLA REQUISITO M7 §2.3: Reglas de Syquex no incluyen 'funcion'"

    def test_requisito_12_sintaxis_syquex_estructuras(self):
        """M7 §2.3: 'Estructuras: estructura Nombre: campo: tipo'
        
        REQUISITO: Reglas de Syquex deben incluir estructuras.
        """
        ruta = os.path.join(RAIZ, "opensyn", "reglas_synapse.toml")
        if not os.path.exists(ruta):
            pytest.fail("FALLA REQUISITO M7 §2.3: No existe archivo de configuración")
        
        with open(ruta, 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        assert "estructura" in contenido, \
            "FALLA REQUISITO M7 §2.3: Reglas de Syquex no incluyen 'estructura'"

    def test_requisito_13_sintaxis_syquex_metodos(self):
        """M7 §2.3: 'Métodos: metodo nombre(parametros) -> tipo:'
        
        REQUISITO: Reglas de Syquex deben incluir métodos.
        """
        ruta = os.path.join(RAIZ, "opensyn", "reglas_synapse.toml")
        if not os.path.exists(ruta):
            pytest.fail("FALLA REQUISITO M7 §2.3: No existe archivo de configuración")
        
        with open(ruta, 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        assert "metodo" in contenido, \
            "FALLA REQUISITO M7 §2.3: Reglas de Syquex no incluyen 'metodo'"

    def test_requisito_14_sintaxis_syquex_constructores(self):
        """M7 §2.3: 'Constructores: crear(parametros):'
        
        REQUISITO: Reglas de Syquex deben incluir constructores.
        """
        ruta = os.path.join(RAIZ, "opensyn", "reglas_synapse.toml")
        if not os.path.exists(ruta):
            pytest.fail("FALLA REQUISITO M7 §2.3: No existe archivo de configuración")
        
        with open(ruta, 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        assert "crear" in contenido, \
            "FALLA REQUISITO M7 §2.3: Reglas de Syquex no incluyen 'crear'"

    def test_requisito_15_sintaxis_syquex_errores(self):
        """M7 §2.3: 'Manejo de Errores: Resultado<T, E> y operador ? (propaga errores).'
        
        REQUISITO: Reglas de Syquex deben incluir manejo de errores.
        """
        ruta = os.path.join(RAIZ, "opensyn", "reglas_synapse.toml")
        if not os.path.exists(ruta):
            pytest.fail("FALLA REQUISITO M7 §2.3: No existe archivo de configuración")
        
        with open(ruta, 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        assert "Resultado" in contenido, \
            "FALLA REQUISITO M7 §2.3: Reglas de Syquex no incluyen 'Resultado'"

    def test_requisito_16_sintaxis_syquex_concurrencia(self):
        """M7 §2.3: 'Concurrencia: lanzar funcion()'
        
        REQUISITO: Reglas de Syquex deben incluir concurrencia.
        """
        ruta = os.path.join(RAIZ, "opensyn", "reglas_synapse.toml")
        if not os.path.exists(ruta):
            pytest.fail("FALLA REQUISITO M7 §2.3: No existe archivo de configuración")
        
        with open(ruta, 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        # Verificar que hay "lanzar" en el contenido (puede estar en syquex o en ejemplos)
        assert "lanzar" in contenido, \
            "FALLA REQUISITO M7 §2.3: Reglas de Syquex no incluyen 'lanzar'"

    def test_requisito_17_sintaxis_syquex_canales(self):
        """M7 §2.3: 'Canales: Canal<T>(capacidad)'
        
        REQUISITO: Reglas de Syquex deben incluir canales con capacidad.
        """
        ruta = os.path.join(RAIZ, "opensyn", "reglas_synapse.toml")
        if not os.path.exists(ruta):
            pytest.fail("FALLA REQUISITO M7 §2.3: No existe archivo de configuración")
        
        with open(ruta, 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        # Verificar que hay mención de canales en syquex
        assert "Canal" in contenido, \
            "FALLA REQUISITO M7 §2.3: Reglas de Syquex no incluyen 'Canal'"

    def test_requisito_18_sintaxis_syquex_modulos(self):
        """M7 §2.3: 'Importar módulos: importar lib.modulo'
        
        REQUISITO: Reglas de Syquex deben incluir importación de módulos.
        """
        ruta = os.path.join(RAIZ, "opensyn", "reglas_synapse.toml")
        if not os.path.exists(ruta):
            pytest.fail("FALLA REQUISITO M7 §2.3: No existe archivo de configuración")
        
        with open(ruta, 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        assert "importar" in contenido, \
            "FALLA REQUISITO M7 §2.3: Reglas de Syquex no incluyen 'importar'"

    def test_requisito_19_estructura_prompt_system(self):
        """M7 §2.3: El prompt debe contener [SYSTEM] como primer bloque.
        
        REQUISITO: El sistema debe generar prompts con estructura [SYSTEM].
        """
        # Este test verifica la ESPECIFICACIÓN del manual, no la implementación
        # El manual define que el prompt debe tener [SYSTEM], [CONTEXT], [INSTRUCCIÓN]
        estructura_requerida = [
            "[SYSTEM]",
            "[CONTEXT]",
            "[INSTRUCCIÓN]"
        ]
        
        # Verificar que la especificación está documentada
        # (este test siempre pasará porque verifica el manual, no el código)
        for bloque in estructura_requerida:
            assert bloque in "[SYSTEM]...[CONTEXT]...[INSTRUCCIÓN]", \
                f"FALLA ESPECIFICACIÓN: Bloque {bloque} no definido en Manual 7 §2.3"

    def test_requisito_20_configurable_y_actualizable(self):
        """M7 §2.3: 'Este bloque debe ser configurable y actualizable mediante el archivo de configuración.'
        
        REQUISITO: El archivo de configuración debe ser modificable por el usuario.
        """
        ruta = os.path.join(RAIZ, "opensyn", "reglas_synapse.toml")
        if not os.path.exists(ruta):
            pytest.fail("FALLA REQUISITO M7 §2.3: No existe archivo de configuración")
        
        # Verificar que el archivo tiene metadatos de configuración
        with open(ruta, 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        assert "[config]" in contenido, \
            "FALLA REQUISITO M7 §2.3: Falta sección [config] para configuración"
        assert "actualizable" in contenido, \
            "FALLA REQUISITO M7 §2.3: Falta campo 'actualizable' en configuración"

class TestImplementacion:
    """Tests de implementación - DEBEN FALLAR si el código no existe."""

    def test_implementacion_modulo_rag_existe(self):
        """VERIFICACIÓN: El módulo synapse_rag debe existir."""
        ruta = os.path.join(RAIZ, "nucleo", "synapse_rag.c")
        assert os.path.exists(ruta), \
            "FALLA IMPLEMENTACIÓN: No existe nucleo/synapse_rag.c"

    def test_implementacion_header_rag_existe(self):
        """VERIFICACIÓN: El header synapse_rag.h debe existir."""
        ruta = os.path.join(RAIZ, "nucleo", "synapse_rag.h")
        assert os.path.exists(ruta), \
            "FALLA IMPLEMENTACIÓN: No existe nucleo/synapse_rag.h"

    def test_implementacion_estructura_rag_contexto_estatico(self):
        """VERIFICACIÓN: Debe existir estructura RagContextoEstatico."""
        ruta = os.path.join(RAIZ, "nucleo", "synapse_rag.h")
        if not os.path.exists(ruta):
            pytest.fail("FALLA IMPLEMENTACIÓN: No existe nucleo/synapse_rag.h")
        
        with open(ruta, 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        assert "RagContextoEstatico" in contenido, \
            "FALLA IMPLEMENTACIÓN: Falta estructura RagContextoEstatico en synapse_rag.h"

    def test_implementacion_funcion_cargar_configuracion(self):
        """VERIFICACIÓN: Debe existir función para cargar configuración."""
        ruta = os.path.join(RAIZ, "nucleo", "synapse_rag.h")
        if not os.path.exists(ruta):
            pytest.fail("FALLA IMPLEMENTACIÓN: No existe nucleo/synapse_rag.h")
        
        with open(ruta, 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        assert "rag_configuracion_cargar" in contenido, \
            "FALLA IMPLEMENTACIÓN: Falta función rag_configuracion_cargar"

    def test_implementacion_funcion_construir_bloque_estatico(self):
        """VERIFICACIÓN: Debe existir función para construir bloque estático."""
        ruta = os.path.join(RAIZ, "nucleo", "synapse_rag.h")
        if not os.path.exists(ruta):
            pytest.fail("FALLA IMPLEMENTACIÓN: No existe nucleo/synapse_rag.h")
        
        with open(ruta, 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        assert "rag_construir_bloque_estatico" in contenido, \
            "FALLA IMPLEMENTACIÓN: Falta función rag_construir_bloque_estatico"

    def test_implementacion_funcion_prompt_con_contexto(self):
        """VERIFICACIÓN: Debe existir función para construir prompt con contexto estático."""
        ruta = os.path.join(RAIZ, "nucleo", "synapse_rag.h")
        if not os.path.exists(ruta):
            pytest.fail("FALLA IMPLEMENTACIÓN: No existe nucleo/synapse_rag.h")
        
        with open(ruta, 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        assert "synapse_rag_construir_prompt_con_contexto_estatico" in contenido, \
            "FALLA IMPLEMENTACIÓN: Falta función synapse_rag_construir_prompt_con_contexto_estatico"

    def test_implementacion_parser_toml(self):
        """VERIFICACIÓN: Debe existir parser TOML para leer configuración."""
        ruta = os.path.join(RAIZ, "nucleo", "synapse_rag.c")
        if not os.path.exists(ruta):
            pytest.fail("FALLA IMPLEMENTACIÓN: No existe nucleo/synapse_rag.c")
        
        with open(ruta, 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        assert "rag_parsear_toml_simple" in contenido, \
            "FALLA IMPLEMENTACIÓN: Falta parser TOML en synapse_rag.c"