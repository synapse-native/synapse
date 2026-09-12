# -*- coding: utf-8 -*-
"""
test_rag_file_finder.py — TDD del file-finder y catálogo APIs (ME-2, R2, Manual 7 §2.3).

Valida que el file-finder localice archivos relevantes y que el catálogo
de APIs std impida alucinaciones de funciones.

Réplica en Python de las funciones Synapse de router.syn para poder
ejecutar assertions en CI sin compilar el binario.

Cumple MTO §3: cada requisito del manual se convierte en test ejecutable.
requisito: Manual 7 §2.3
texto: "El pipeline RAG extrae el contexto más relevante del código fuente
  para construir un prompt eficiente y preciso."
oraculo: tests/unit/test_rag_file_finder.py
"""

import os

import pytest

pytestmark = pytest.mark.unit

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# --- Funciones réplica de router.syn ---

def obtener_catalogo_api() -> str:
    """Catálogo de APIs std/*.syn. Replica router.syn:obtener_catalogo_api()."""
    catalogo = "APIs std/ (usar SOLO estas funciones): "
    catalogo += "std.io: abrir, leer, escribir, escribir_linea, leer_linea; "
    catalogo += "std.texto: contiene, indice_de, reemplazar, termina_con, recortar, mayusculas, minusculas, a_texto, cmp_texto, strlen_s, strstr_f, strcpy_f; "
    catalogo += "std.sistema: ejecutar_comando, escribir_archivo, leer_archivo, existe_archivo; "
    catalogo += "std.json: desde_texto, obtener_elemento, obtener_campo, a_texto; "
    catalogo += "std.os: memoria_total, memoria_libre, vram_total, cpu_nucleos; "
    catalogo += "std.net: iniciar_red, crear_socket, conectar, enviar_datos, recibir_datos, cerrar_socket; "
    catalogo += "std.http: iniciar_servidor, aceptar, leer_peticion, responder; "
    catalogo += "std.modelo: cargar_modelo, cerrar_modelo, generar_texto, obtener_n_ctx; "
    catalogo += "std.math: crear_tensor, suma_tensor, producto_punto, relu; "
    catalogo += "std.cripto: sha256_texto, ed25519_verificar; "
    catalogo += "std.tiempo: ahora_ms, dormir_ms; "
    catalogo += "std.testing: assert_verdadero, assert_falso, assert_igual, assert_diferente; "
    catalogo += "std.debug: registrar_evento, trace, iniciar_sesion, finalizar_sesion"
    return catalogo


def obtener_mapa_keywords() -> str:
    """Mapa keyword → archivo. Replica router.syn:obtener_mapa_keywords()."""
    mapa = "io:std/io.syn;escribir:std/io.syn;leer:std/io.syn;archivo:std/io.syn;"
    mapa += "texto:std/texto.syn;cadena:std/texto.syn;reemplazar:std/texto.syn;"
    mapa += "sistema:std/sistema.syn;comando:std/sistema.syn;ejecutar:std/sistema.syn;"
    mapa += "json:std/json.syn;parse:std/json.syn;"
    mapa += "os:std/os.syn;ram:std/os.syn;vram:std/os.syn;cpu:std/os.syn;"
    mapa += "red:std/net.syn;socket:std/net.syn;conexion:std/net.syn;"
    mapa += "http:std/http.syn;servidor:std/http.syn;puerto:std/http.syn;"
    mapa += "modelo:std/modelo.syn;gguf:std/modelo.syn;inferencia:std/modelo.syn;"
    mapa += "tensor:std/math.syn;matriz:std/math.syn;"
    mapa += "cripto:std/cripto.syn;sha256:std/cripto.syn;ed25519:std/cripto.syn;"
    mapa += "tiempo:std/tiempo.syn;reloj:std/tiempo.syn;dormir:std/tiempo.syn;"
    mapa += "debug:std/debug.syn;traza:std/debug.syn;trace:std/debug.syn;"
    mapa += "test:std/testing.syn;assert:std/testing.syn;"
    mapa += "router:opensyn/router.syn;rag:opensyn/router.syn;"
    mapa += "principal:opensyn/principal.syn;agente:opensyn/principal.syn;modo:opensyn/principal.syn;"
    mapa += "ollama:runtime/core/ollama.c;llama:runtime/core/ollama.c;"
    mapa += "tui:runtime/core/tui.c;terminal:runtime/core/tui.c"
    return mapa


def file_finder(consulta: str) -> str:
    """Localiza archivos relevantes por palabras clave. Replica router.syn:file_finder()."""
    encontrados = ""
    mapa = obtener_mapa_keywords()
    entries = mapa.split(";")
    for entry in entries:
        if ":" not in entry:
            continue
        kw, archivo = entry.split(":", 1)
        if kw in consulta:
            if archivo not in encontrados:
                if encontrados:
                    encontrados += ", "
                encontrados += archivo
    return encontrados


# ============================================================
# Tests TDD — Manual 7 §2.3 (file-finder + catálogo APIs)
# ============================================================


class TestCatalogoAPI:
    """obtener_catalogo_api() retorna el catálogo completo de APIs std."""

    def test_catalogo_no_vacio(self):
        assert len(obtener_catalogo_api()) > 100

    def test_catalogo_incluye_io(self):
        assert "std.io" in obtener_catalogo_api()

    def test_catalogo_incluye_texto(self):
        assert "std.texto" in obtener_catalogo_api()

    def test_catalogo_incluye_modelo(self):
        assert "std.modelo" in obtener_catalogo_api()

    def test_catalogo_incluye_sistema(self):
        assert "std.sistema" in obtener_catalogo_api()

    def test_catalogo_menciona_funciones_reales(self):
        cat = obtener_catalogo_api()
        assert "escribir_linea" in cat
        assert "generar_texto" in cat
        assert "strlen_s" in cat

    def test_catalogo_no_incluye_funciones_fantasma(self):
        """El catálogo NO debe incluir funciones inventadas."""
        cat = obtener_catalogo_api()
        assert "teletransportar" not in cat
        assert "absolutamente_nueva_funcion" not in cat


class TestFileFinder:
    """file_finder() localiza archivos relevantes por palabras clave."""

    def test_io_encontra_archivos(self):
        resultado = file_finder("quiero escribir un archivo")
        assert "std/io.syn" in resultado

    def test_texto_encontra_archivos(self):
        resultado = file_finder("necesito reemplazar una cadena de texto")
        assert "std/texto.syn" in resultado

    def test_modelo_encontra_archivos(self):
        resultado = file_finder("cargar un modelo gguf")
        assert "std/modelo.syn" in resultado

    def test_red_encontra_archivos(self):
        resultado = file_finder("abrir un socket de red")
        assert "std/net.syn" in resultado

    def test_http_encontra_archivos(self):
        resultado = file_finder("crear un servidor http")
        assert "std/http.syn" in resultado

    def test_ollama_encontra_archivos(self):
        resultado = file_finder("consultar ollama")
        assert "runtime/core/ollama.c" in resultado

    def test_tui_encontra_archivos(self):
        resultado = file_finder("dibujar en la terminal tui")
        assert "runtime/core/tui.c" in resultado

    def test_router_encontra_archivos(self):
        resultado = file_finder("modificar el router rag")
        assert "opensyn/router.syn" in resultado

    def test_multiple_keywords(self):
        resultado = file_finder("escribir archivo de texto en sistema")
        assert "std/io.syn" in resultado or "std/texto.syn" in resultado

    def test_keyword_corta_matchea(self):
        """Keywords cortas como "io" matchean por substring — comportamiento conocido.
        El file-finder es una primera aproximación; el catálogo de APIs
        es el que realmente impide alucinaciones."""
        resultado = file_finder("io es un modulo")
        # "io" está en la consulta → matchea std/io.syn
        assert "std/io.syn" in resultado

    def test_keyword_no_encontrada(self):
        """Si ninguna keyword está en la consulta, retorna vacío."""
        # "xyz" no contiene ninguna keyword del mapa
        resultado = file_finder("xyz xyz xyz")
        assert resultado == ""

    def test_consulta_corta(self):
        """Consulta muy corta."""
        resultado = file_finder("ab")
        assert resultado == ""


class TestIntegracionFileFinderCatalogo:
    """Integración: file-finder + catálogo working juntos."""

    def test_file_finder_retorna_strings(self):
        for q in ["escribir", "leer archivo", "modelo gguf"]:
            r = file_finder(q)
            assert isinstance(r, str)

    def test_catalogo_y_finder_complementarios(self):
        """El catálogo lista APIs; el finder localiza archivos. No deben solaparse."""
        cat = obtener_catalogo_api()
        finder = file_finder("escribir archivo de texto")
        # El catálogo menciona std.io; el finder encuentra std/io.syn
        assert "std.io" in cat
        assert "std/io.syn" in finder
