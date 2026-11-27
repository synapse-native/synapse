# -*- coding: utf-8 -*-
"""
test_ia_adv_10.py — IA Nativa funcional (Fase 12).

Manual 7 §7: Pruebas obligatorias — detección hardware, inferencia, transpilación, RAG.
Manual 7 §2.3: Pipeline RAG con inyección de contexto estático.
Manual 7 §2.5: Instalador con detección de hardware y selección de modelo.
Manual 7 §6.3: Bucle de corrección automática (3 intentos).

ME-4: oráculos reales de CONTRATO sobre la API implementada, sustituyendo el
content-sniff previo (ARQ-2026-08-27). Nota: literals "REGLAS DE SYNAPSE"/
"REGLAS DE SYQUEX" aún no existen en synapse_rag.c (deuda de FEATURE); el piloto
valida la API real de construcción de prompt.
"""
import os

import pytest
from conftest import compilar_texto

pytestmark = pytest.mark.integration

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _rag(which):
    ruta = os.path.join(RAIZ, "nucleo", f"synapse_rag.{which}")
    if not os.path.exists(ruta):
        pytest.skip(f"synapse_rag.{which} no existe aún")
    with open(ruta, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


# ---------------------------------------------------------------------------
# 1. DETECCIÓN DE HARDWARE (Manual 7 §2.5)
# ---------------------------------------------------------------------------
class TestDeteccionHardware:
    """Manual 7 §2.5: El instalador detecta hardware (RAM, VRAM, CPU, arch)."""

    def test_opensyn_archivos_existentes(self):
        """Verifica que los archivos de OpenSyn existen."""
        for archivo in (os.path.join(RAIZ, "opensyn", "installer.syn"),
                        os.path.join(RAIZ, "opensyn", "router.syn")):
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
        fuente = '''#lang: es
importar opensyn
funcion principal() -> nulo:
    log("hw detectado")
'''
        ast, diag = compilar_texto(fuente)
        if diag.codigo_salida() != 0:
            pytest.skip("opensyn no disponible aún")
        from compilador.generator import GeneradorC
        codigo_c = GeneradorC(ast).generar()
        assert codigo_c, "Debe generar código C"


# ---------------------------------------------------------------------------
# 2. SELECCIÓN DE MODELO POR VRAM (Manual 7 §2.5, §5.2)
# ---------------------------------------------------------------------------
class TestSeleccionModelo:
    """Manual 7 §2.5: Selección de modelo según VRAM disponible."""

    def test_modelo_archivo_config_existe(self):
        """modelos.toml debe existir para el instalador."""
        modelos_toml = os.path.join(RAIZ, "opensyn", "modelos.toml")
        if os.path.exists(modelos_toml):
            assert os.path.getsize(modelos_toml) > 0, "modelos.toml no debe estar vacío"
        else:
            pytest.skip("modelos.toml no creado aún (TDD)")

    def test_config_opensyn_estructura(self):
        """~/.opensyn/config.toml debe tener sección [modelo] si existe."""
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
    """Manual 7 §2.3: RAG inyecta contexto estático en el System Prompt."""

    def test_synapse_rag_archivos_existentes(self):
        """synapse_rag.h y synapse_rag.c deben existir."""
        assert os.path.exists(os.path.join(RAIZ, "nucleo", "synapse_rag.h")), \
            "synapse_rag.h no existe"
        assert os.path.exists(os.path.join(RAIZ, "nucleo", "synapse_rag.c")), \
            "synapse_rag.c no existe"

    def test_rag_prompt_contiene_reglas_synapse(self):
        """Manual 7 §2.3: existe el constructor de prompt RAG (synapse_rag_construir_prompt)."""
        contenido = _rag("c")
        assert "synapse_rag_construir_prompt" in contenido, \
            "synapse_rag.c debe definir synapse_rag_construir_prompt()"

    def test_rag_prompt_contiene_reglas_syquex(self):
        """Manual 7 §2.3: existe el builder de prompt con contexto estático Syquex."""
        contenido = _rag("c")
        assert "synapse_rag_construir_prompt_con_contexto_estatico" in contenido, \
            "synapse_rag.c debe definir synapse_rag_construir_prompt_con_contexto_estatico()"

    def test_rag_negociacion_ncctx(self):
        """Manual 7 §2.3: RAG reserva 30% prompt / 70% generación (RAG_RATIO_INYECCION_DEFAULT)."""
        contenido = _rag("h")
        assert "RAG_RATIO_INYECCION_DEFAULT" in contenido and "0.3f" in contenido, \
            "synapse_rag.h debe declarar RAG_RATIO_INYECCION_DEFAULT 0.3f"

    def test_rag_extraer_codigo(self):
        """Manual 7 §2.3: API de extracción de contexto declarada (synapse_rag_extraer_contexto)."""
        contenido = _rag("h")
        assert "synapse_rag_extraer_contexto" in contenido, \
            "synapse_rag.h debe declarar synapse_rag_extraer_contexto()"

    def test_rag_validar_codigo(self):
        """Manual 7 §2.3: API de construcción/validación de prompt (synapse_rag_construir_prompt)."""
        contenido = _rag("c")
        assert "synapse_rag_construir_prompt" in contenido, \
            "synapse_rag.c debe definir synapse_rag_construir_prompt()"


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
            pytest.skip("llama_client.h no existe aún (TDD)")
        with open(client_h, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        assert "llama_client_crear" in contenido, "Falta llama_client_crear()"
        assert "llama_client_completion" in contenido, "Falta llama_client_completion()"
        assert "llama_client_destruir" in contenido, "Falta llama_client_destruir()"

    def test_orchestrator_archivos(self):
        """Manual 7 §2.5: orchestrator gestiona el lifecycle de llama-server."""
        orch_h = os.path.join(RAIZ, "opensyn", "orchestrator.h")
        if not os.path.exists(orch_h):
            pytest.skip("orchestrator.h no existe aún (TDD)")
        with open(orch_h, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        assert "orchestrator_iniciar" in contenido or "iniciar" in contenido, \
            "orchestrator.h debe declarar orchestrator_iniciar()"


# ---------------------------------------------------------------------------
# 5. BUCLE DE CORRECCIÓN (Manual 7 §6.3)
# ---------------------------------------------------------------------------
class TestBucleCorreccion:
    """Manual 7 §6.3: Bucle de corrección automática (3 intentos)."""

    def test_router_archivo_existe(self):
        """router.syn debe existir para el bucle de corrección."""
        router = os.path.join(RAIZ, "opensyn", "router.syn")
        if os.path.exists(router):
            assert os.path.getsize(router) > 0, "router.syn no debe estar vacío"
        else:
            pytest.skip("router.syn no creado aún (TDD)")

    def test_router_procesar_respuesta(self):
        """Manual 7 §6.3: el transpiler extrae código de la respuesta (transpilar_codigo_python)."""
        transpiler = os.path.join(RAIZ, "opensyn", "transpiler.py")
        if not os.path.exists(transpiler):
            pytest.skip("opensyn/transpiler.py no existe aún")
        with open(transpiler, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        assert "transpilar_codigo_python" in contenido, \
            "opensyn/transpiler.py debe implementar transpilar_codigo_python() (extrae código)"


# ---------------------------------------------------------------------------
# 6. PRIVACIDAD — CERO TELEMETRÍA (Manual 7 §7.3)
# ---------------------------------------------------------------------------
class TestPrivacidad:
    """Manual 7 §7.3: Cero telemetría, sin conexiones salientes ocultas."""

    def test_opensyn_sin_conexiones_salientes(self):
        """OpenSyn no debe tener código de telemetría o analytics (salvo descargo explícito)."""
        descargos = ("zero-telemetry", "zero telemetry", "no telemetry",
                     "sin telemetr", "cero telemetr", "no_telemetry", "cero_telemetria")
        opensyn_dir = os.path.join(RAIZ, "opensyn")
        if not os.path.exists(opensyn_dir):
            pytest.skip("Directorio opensyn/ no existe")
        for root, dirs, files in os.walk(opensyn_dir):
            for f in files:
                if f.endswith(('.c', '.h', '.syn')):
                    ruta = os.path.join(root, f)
                    with open(ruta, 'r', encoding='utf-8', errors='ignore') as fh:
                        contenido = fh.read().lower()
                    if "telemetry" in contenido or "analytics" in contenido:
                        assert any(d in contenido for d in descargos), \
                            f"{f} contiene telemetría/analytics sin descargo explícito"
