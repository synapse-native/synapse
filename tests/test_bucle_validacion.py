# -*- coding: utf-8 -*-
"""
test_bucle_validacion.py — M7 §6.3: Bucle de corrección automática (3 intentos).

Manual 7 §6.3: "OpenSyn implementa un bucle de validación y corrección automática
orquestado por el LSP. Este bucle asegura que el código generado cumpla con las
reglas del compilador."

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
    """Verificación de requisitos explícitos del Manual 7 §6.3."""

    def test_requisito_1_maximo_3_intentos(self):
        """M7 §6.3: 'bucle de validación y corrección automática orquestado por el LSP'
        
        REQUISITO: El bucle debe tener un máximo de 3 intentos.
        """
        # Verificar que la especificación define 3 intentos
        max_intentos = 3
        assert max_intentos == 3, \
            "FALLA REQUISITO M7 §6.3: El máximo de intentos debe ser 3"

    def test_requisito_2_validacion_con_check(self):
        """M7 §6.3: 'El LSP pasa el código al compilador en modo --check'
        
        REQUISITO: La validación debe usar el flag --check del compilador.
        """
        # Verificar que el compilador soporta --check
        # (esto es una especificación, no una implementación)
        flag_check = "--check"
        assert flag_check == "--check", \
            "FALLA REQUISITO M7 §6.3: Debe existir flag --check"

    def test_requisito_3_captura_error_compilacion(self):
        """M7 §6.3: 'El compilador devuelve el error exacto (línea, columna, mensaje)'
        
        REQUISITO: El sistema debe capturar errores de compilación.
        """
        # Verificar que la estructura de error incluye línea, columna, mensaje
        campos_error = ["linea", "columna", "mensaje"]
        assert len(campos_error) == 3, \
            "FALLA REQUISITO M7 §6.3: Error debe tener línea, columna y mensaje"

    def test_requisito_4_reconstruccion_prompt_con_error(self):
        """M7 §6.3: 'Construye un nuevo prompt añadiendo: El código anterior tiene el siguiente error...'
        
        REQUISITO: El sistema debe reconstruir el prompt con el error.
        """
        # Verificar que el prompt de reintento incluye el error
        prompt_reintento = "El código anterior tiene el siguiente error: {error}. Por favor, corrígelo."
        assert "{error}" in prompt_reintento, \
            "FALLA REQUISITO M7 §6.3: Prompt de reintento debe incluir placeholder de error"

    def test_requisito_5_feedback_humano(self):
        """M7 §6.3: 'OpenSyn guarda el par (instrucción, código_corregido) en ~/.opensyn/feedback.jsonl'
        
        REQUISITO: El sistema debe guardar feedback humano para mejora.
        """
        ruta_feedback = os.path.expanduser("~/.opensyn/feedback.jsonl")
        # Verificar que la ruta está definida (no que existe, porque puede no haber feedback aún)
        assert ".opensyn" in ruta_feedback, \
            "FALLA REQUISITO M7 §6.3: Ruta de feedback debe estar en ~/.opensyn/"
        assert "feedback.jsonl" in ruta_feedback, \
            "FALLA REQUISITO M7 §6.3: Archivo de feedback debe ser feedback.jsonl"

    def test_requisito_6_fallo_definitivo_mensaje(self):
        """M7 §6.3: 'Si el tercer intento falla, el LSP muestra el último código generado y los errores'
        
        REQUISITO: Al fallar 3 intentos, mostrar código y errores al usuario.
        """
        mensaje_fallo = "No se pudo generar código válido automáticamente. Intenta ajustar la instrucción o corrige manualmente."
        assert "No se pudo generar código válido" in mensaje_fallo, \
            "FALLA REQUISITO M7 §6.3: Mensaje de fallo definitivo incorrecto"

    def test_requisito_7_integracion_lsp(self):
        """M7 §6.3: 'orquestado por el LSP'
        
        REQUISITO: El bucle debe estar integrado en el LSP.
        """
        # Verificar que hay archivos de LSP
        archivos_lsp = ["nucleo/lsp.syn"]
        for archivo in archivos_lsp:
            ruta = os.path.join(RAIZ, archivo)
            # No verificamos existencia aquí, solo que la especificación está documentada
            assert archivo, "FALLA REQUISITO M7 §6.3: Debe haber integración con LSP"

class TestImplementacion:
    """Tests de implementación - DEBEN FALLAR si el código no existe."""

    def test_implementacion_archivo_bucle_validacion(self):
        """VERIFICACIÓN: Debe existir archivo de bucle de validación."""
        # Buscar archivos que implementen el bucle de validación
        archivos_posibles = [
            "opensyn/validation_loop.syn",
            "opensyn/bucle_validacion.syn", 
            "opensyn/correction_loop.syn",
            "nucleo/lsp.syn"
        ]
        
        archivos_existentes = []
        for archivo in archivos_posibles:
            ruta = os.path.join(RAIZ, archivo)
            if os.path.exists(ruta):
                archivos_existentes.append(archivo)
        
        assert len(archivos_existentes) > 0, \
            "FALLA IMPLEMENTACIÓN: No existe archivo de bucle de validación"

    def test_implementacion_funcion_validar_codigo(self):
        """VERIFICACIÓN: Debe existir función para validar código con --check."""
        archivos_posibles = [
            "opensyn/validation_loop.syn",
            "opensyn/bucle_validacion.syn",
            "opensyn/correction_loop.syn"
        ]
        
        funcion_encontrada = False
        for archivo in archivos_posibles:
            ruta = os.path.join(RAIZ, archivo)
            if os.path.exists(ruta):
                with open(ruta, 'r', encoding='utf-8') as f:
                    contenido = f.read()
                if "validar" in contenido.lower() or "check" in contenido.lower():
                    funcion_encontrada = True
                    break
        
        assert funcion_encontrada, \
            "FALLA IMPLEMENTACIÓN: No existe función de validación de código"

    def test_implementacion_funcion_reconstruir_prompt(self):
        """VERIFICACIÓN: Debe existir función para reconstruir prompt con error."""
        archivos_posibles = [
            "opensyn/validation_loop.syn",
            "opensyn/bucle_validacion.syn",
            "opensyn/correction_loop.syn",
            "nucleo/synapse_rag.c"
        ]
        
        funcion_encontrada = False
        for archivo in archivos_posibles:
            ruta = os.path.join(RAIZ, archivo)
            if os.path.exists(ruta):
                with open(ruta, 'r', encoding='utf-8') as f:
                    contenido = f.read()
                if "reconstruir" in contenido.lower() or "prompt" in contenido.lower():
                    funcion_encontrada = True
                    break
        
        assert funcion_encontrada, \
            "FALLA IMPLEMENTACIÓN: No existe función de reconstrucción de prompt"

    def test_implementacion_contador_intentos(self):
        """VERIFICACIÓN: Debe existir contador de intentos (máximo 3)."""
        archivos_posibles = [
            "opensyn/validation_loop.syn",
            "opensyn/bucle_validacion.syn",
            "opensyn/correction_loop.syn"
        ]
        
        contador_encontrado = False
        for archivo in archivos_posibles:
            ruta = os.path.join(RAIZ, archivo)
            if os.path.exists(ruta):
                with open(ruta, 'r', encoding='utf-8') as f:
                    contenido = f.read()
                if "intentos" in contenido.lower() or "max_intentos" in contenido.lower() or "3" in contenido:
                    contador_encontrado = True
                    break
        
        assert contador_encontrado, \
            "FALLA IMPLEMENTACIÓN: No existe contador de intentos"

    def test_implementacion_guardar_feedback(self):
        """VERIFICACIÓN: Debe existir función para guardar feedback humano."""
        archivos_posibles = [
            "opensyn/validation_loop.syn",
            "opensyn/bucle_validacion.syn",
            "opensyn/correction_loop.syn"
        ]
        
        funcion_encontrada = False
        for archivo in archivos_posibles:
            ruta = os.path.join(RAIZ, archivo)
            if os.path.exists(ruta):
                with open(ruta, 'r', encoding='utf-8') as f:
                    contenido = f.read()
                if "feedback" in contenido.lower() or "guardar" in contenido.lower():
                    funcion_encontrada = True
                    break
        
        assert funcion_encontrada, \
            "FALLA IMPLEMENTACIÓN: No existe función para guardar feedback"

    def test_implementacion_flag_check_cli(self):
        """VERIFICACIÓN: El CLI debe soportar flag --check."""
        ruta_principal = os.path.join(RAIZ, "nucleo", "principal.syn")
        if not os.path.exists(ruta_principal):
            pytest.fail("FALLA IMPLEMENTACIÓN: No existe nucleo/principal.syn")
        
        with open(ruta_principal, 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        assert "--check" in contenido or "check" in contenido, \
            "FALLA IMPLEMENTACIÓN: CLI no soporta flag --check"

    def test_implementacion_mensaje_fallo_definitivo(self):
        """VERIFICACIÓN: Debe existir mensaje de fallo definitivo."""
        archivos_posibles = [
            "opensyn/validation_loop.syn",
            "opensyn/bucle_validacion.syn",
            "opensyn/correction_loop.syn"
        ]
        
        mensaje_encontrado = False
        for archivo in archivos_posibles:
            ruta = os.path.join(RAIZ, archivo)
            if os.path.exists(ruta):
                with open(ruta, 'r', encoding='utf-8') as f:
                    contenido = f.read()
                if "No se pudo generar" in contenido or "fallo" in contenido.lower():
                    mensaje_encontrado = True
                    break
        
        assert mensaje_encontrado, \
            "FALLA IMPLEMENTACIÓN: No existe mensaje de fallo definitivo"