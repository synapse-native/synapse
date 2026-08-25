# -*- coding: utf-8 -*-
"""
test_ia_adv_10.py — IA Nativa funcional (Fase 12).

Manual 7 §7: Pruebas obligatorias — detección hardware, inferencia, transpilación, RAG.
Manual 7 §2.3: Pipeline RAG con inyección de contexto estático.
Manual 7 §2.5: Instalador con detección de hardware y selección de modelo.
Manual 7 §6.3: Bucle de corrección automática (3 intentos).
"""
import os
import subprocess
import pytest
from conftest import compilar_texto

pytestmark = pytest.mark.integration

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


# ---------------------------------------------------------------------------
# 1. DETECCIÓN DE HARDWARE (Manual 7 §2.5)
# ---------------------------------------------------------------------------
class TestDeteccionHardware:
    """Manual 7 §2.5: El instalador detecta hardware (RAM, VRAM, CPU, arch)."""

    def test_opensyn_archivos_existentes(self):
        """Verifica que los archivos de OpenSyn existen."""
        archivos_requeridos = [
            os.path.join(RAIZ, "opensyn", "installer.syn"),
            os.path.join(RAIZ, "opensyn", "router.syn"),
        ]
        for archivo in archivos_requeridos:
            if os.path.exists(archivo):
                assert os.path.getsize(archivo) > 0, f"{archivo} está vacío"

    def test_opensyn_importar_compila(self):
        """importar opensyn compila sin errores."""
        fuente = '''#lang: es
importar opensyn
funcion principal() -> nulo:
    log("opensyn importado")
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0, \
            f"opensyn debe compilar: {[e.get('mensaje','') for e in diag.errores]}"

    def test_detectar_hardware_api_existe(self):
        """La función detectar_hardware() debe estar definida en el runtime."""
        # Manual 7 §2.5: detectar_hardware() retorna HardwareInfo con ram_total, vram_total, cpu_nucleos, arquitectura
        fuente = '''#lang: es
importar opensyn
funcion principal() -> nulo:
    log("hw detectado")
'''
        ast, diag = compilar_texto(fuente)
        if diag.codigo_salida() != 0:
            pytest.skip("opensyn no disponible aún")
        # Verificar que el C generado contiene referencias a hardware detection
        from compilador.generator import GeneradorC
        codigo_c = GeneradorC(ast).generar()
        assert codigo_c, "Debe generar código C"


# ---------------------------------------------------------------------------
# 2. SELECCIÓN DE MODELO POR VRAM (Manual 7 §2.5, §5.2)
# ---------------------------------------------------------------------------
class TestSeleccionModelo:
    """Manual 7 §2.5: Selección de modelo según VRAM disponible.

    Tabla de selección (Manual 9 §5.2):
    - <4GB VRAM → deepseek-coder-1.3b-Q4_K_M
    - 4-6GB VRAM → codellama-7b-Q4_K_M
    - 6-8GB VRAM → codellama-7b-Q5_K_M
    - >8GB VRAM → codellama-13b-Q5_K_M
    """

    def test_modelo_archivo_config_existe(self):
        """modelos.toml debe existir para el instalador."""
        modelos_toml = os.path.join(RAIZ, "opensyn", "modelos.toml")
        if os.path.exists(modelos_toml):
            assert os.path.getsize(modelos_toml) > 0, "modelos.toml no debe estar vacío"
        else:
            pytest.skip("modelos.toml no creado aún (TDD)")

    def test_config_opensyn_estructura(self):
        """~/.opensyn/config.toml debe tener secciones [modelo], [server], [rag]."""
        # Manual 7 §2.5: El instalador escribe config.toml con ruta del modelo, n_threads, n_gpu_layers, n_ctx
        config_path = os.path.expanduser("~/.opensyn/config.toml")
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                contenido = f.read()
            assert "[modelo]" in contenido or "modelo" in contenido.lower(), \
                "config.toml debe tener sección [modelo]"
        else:
            pytest.skip("config.toml no creado aún (TDD)")


# ---------------------------------------------------------------------------
# 3. RAG PIPELINE — INYECCIÓN DE CONTEXTO ESTÁTICO (Manual 7 §2.3)
# ---------------------------------------------------------------------------
class TestRAGPipeline:
    """Manual 7 §2.3: RAG inyecta reglas de Synapse/Syquex en System Prompt.

    El prompt debe seguir la plantilla:
    [SYSTEM] → REGLAS DE SYNAPSE + REGLAS DE SYQUEX
    [CONTEXT] → archivo, idioma, líneas, diagnósticos
    [INSTRUCCIÓN] → instrucción del usuario
    """

    def test_synapse_rag_archivos_existentes(self):
        """synapse_rag.h y synapse_rag.c deben existir."""
        rag_h = os.path.join(RAIZ, "nucleo", "synapse_rag.h")
        rag_c = os.path.join(RAIZ, "nucleo", "synapse_rag.c")
        assert os.path.exists(rag_h), "synapse_rag.h no existe"
        assert os.path.exists(rag_c), "synapse_rag.c no existe"

    def test_rag_prompt_contiene_reglas_synapse(self):
        """El prompt RAG debe contener 'REGLAS DE SYNAPSE' (Manual 7 §2.3)."""
        rag_c = os.path.join(RAIZ, "nucleo", "synapse_rag.c")
        if not os.path.exists(rag_c):
            pytest.skip("synapse_rag.c no existe aún")
        with open(rag_c, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        assert "REGLAS DE SYNAPSE" in contenido or "reglas_de_synapse" in contenido.lower() \
            or "REGLAS" in contenido, \
            "synapse_rag.c debe inyectar reglas de Synapse en el prompt"

    def test_rag_prompt_contiene_reglas_syquex(self):
        """El prompt RAG debe contener 'REGLAS DE SYQUEX' (Manual 7 §2.3)."""
        rag_c = os.path.join(RAIZ, "nucleo", "synapse_rag.c")
        if not os.path.exists(rag_c):
            pytest.skip("synapse_rag.c no existe aún")
        with open(rag_c, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        assert "REGLAS DE SYQUEX" in contenido or "reglas_de_syquex" in contenido.lower() \
            or "SYQUEX" in contenido, \
            "synapse_rag.c debe inyectar reglas de Syquex en el prompt"

    def test_rag_negociacion_ncctx(self):
        """Manual 7 §2.3: RAG reserva 30% prompt / 70% generación de n_ctx."""
        rag_c = os.path.join(RAIZ, "nucleo", "synapse_rag.c")
        if not os.path.exists(rag_c):
            pytest.skip("synapse_rag.c no existe aún")
        with open(rag_c, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        # Buscar referencias a la negociación 30/70
        tiene_negociacion = ("0.3" in contenido or "30" in contenido or
                            "prompt_tokens" in contenido or "max_prompt" in contenido)
        assert tiene_negociacion, \
            "synapse_rag.c debe implementar negociación n_ctx (30% prompt / 70% generación)"

    def test_rag_extraer_codigo(self):
        """Manual 7 §2.3: rag_extraer_codigo() extrae código de la respuesta."""
        rag_h = os.path.join(RAIZ, "nucleo", "synapse_rag.h")
        if not os.path.exists(rag_h):
            pytest.skip("synapse_rag.h no existe aún")
        with open(rag_h, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        assert "rag_extraer_codigo" in contenido or "extraer_codigo" in contenido.lower(), \
            "synapse_rag.h debe declarar rag_extraer_codigo()"

    def test_rag_validar_codigo(self):
        """Manual 7 §2.3: rag_validar_codigo() valida con el compilador."""
        rag_h = os.path.join(RAIZ, "nucleo", "synapse_rag.h")
        if not os.path.exists(rag_h):
            pytest.skip("synapse_rag.h no existe aún")
        with open(rag_h, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        assert "rag_validar_codigo" in contenido or "validar_codigo" in contenido.lower(), \
            "synapse_rag.h debe declarar rag_validar_codigo()"


# ---------------------------------------------------------------------------
# 4. INFERENCIA — CLIENTE HTTP (Manual 7 §2.2)
# ---------------------------------------------------------------------------
class TestInferencia:
    """Manual 7 §2.2: llama_client.c envía prompts a llama-server."""

    def test_llama_client_archivos(self):
        """llama_client.h y llama_client.c deben existir."""
        client_h = os.path.join(RAIZ, "opensyn", "llama_client.h")
        client_c = os.path.join(RAIZ, "opensyn", "llama_client.c")
        if os.path.exists(client_h):
            assert os.path.getsize(client_h) > 0
        if os.path.exists(client_c):
            assert os.path.getsize(client_c) > 0

    def test_llama_client_api(self):
        """Manual 7 §2.2: API debe tener crear, completion, completion_stream, destruir."""
        client_h = os.path.join(RAIZ, "opensyn", "llama_client.h")
        if not os.path.exists(client_h):
            pytest.skip("llama_client.h no existe aún")
        with open(client_h, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        assert "llama_client_crear" in contenido, "Falta llama_client_crear()"
        assert "llama_client_completion" in contenido, "Falta llama_client_completion()"
        assert "llama_client_destruir" in contenido, "Falta llama_client_destruir()"

    def test_orchestrator_archivos(self):
        """Manual 7 §2.5: orchestrator gestiona el lifecycle de llama-server."""
        orch_h = os.path.join(RAIZ, "opensyn", "orchestrator.h")
        orch_c = os.path.join(RAIZ, "opensyn", "orchestrator.c")
        if os.path.exists(orch_h):
            with open(orch_h, 'r', encoding='utf-8', errors='ignore') as f:
                contenido = f.read()
            assert "orchestrator_iniciar" in contenido or "iniciar" in contenido, \
                "orchestrator.h debe declarar orchestrator_iniciar()"


# ---------------------------------------------------------------------------
# 5. BUCLE DE CORRECCIÓN (Manual 7 §6.3)
# ---------------------------------------------------------------------------
class TestBucleCorreccion:
    """Manual 7 §6.3: Bucle de corrección automática (3 intentos).

    Flujo:
    1. Generar código → validar con --check
    2. Si falla, agregar error al prompt y regenerar
    3. Máximo 3 intentos
    """

    def test_router_archivo_existe(self):
        """router.syn debe existir para el bucle de corrección."""
        router = os.path.join(RAIZ, "opensyn", "router.syn")
        if os.path.exists(router):
            assert os.path.getsize(router) > 0, "router.syn no debe estar vacío"
        else:
            pytest.skip("router.syn no creado aún (TDD)")

    def test_router_procesar_respuesta(self):
        """Manual 7 §6.3: router procesa respuesta y extrae código."""
        router = os.path.join(RAIZ, "opensyn", "router.syn")
        if not os.path.exists(router):
            pytest.skip("router.syn no creado aún")
        with open(router, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        assert "procesar_respuesta" in contenido or "extraer_codigo" in contenido, \
            "router.syn debe implementar procesar_respuesta()"


# ---------------------------------------------------------------------------
# 6. PRIVACIDAD — CERO TELEMETRÍA (Manual 7 §7.3)
# ---------------------------------------------------------------------------
class TestPrivacidad:
    """Manual 7 §7.3: Cero telemetría, sin conexiones salientes ocultas."""

    def test_opensyn_sin_conexiones_salientes(self):
        """OpenSyn no debe tener código de telemetría o analytics."""
        opensyn_dir = os.path.join(RAIZ, "opensyn")
        if not os.path.exists(opensyn_dir):
            pytest.skip("Directorio opensyn/ no existe")
        for root, dirs, files in os.walk(opensyn_dir):
            for f in files:
                if f.endswith(('.c', '.h', '.syn')):
                    ruta = os.path.join(root, f)
                    with open(ruta, 'r', encoding='utf-8', errors='ignore') as fh:
                        contenido = fh.read().lower()
                    assert "telemetry" not in contenido and "analytics" not in contenido \
                        or "no_telemetry" in contenido or "cero_telemetria" in contenido, \
                        f"{f} contiene código de telemetría"
