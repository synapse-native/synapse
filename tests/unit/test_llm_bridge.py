"""
Tests para F12.3: Puente de IA Local (Ollama)

Cubre:
- OllamaClient: verificar_disponible, listar_modelos
- OllamaClientMock: respuestas simuladas
- generar_completado: generacion de codigo
- explicar_codigo: explicacion de codigo
- sugerir_correccion: correccion de errores
- Integracion con server.py (aiComplete, aiExplain, aiStatus)
"""

import pytest
from synapse_lsp.llm_bridge import (
    OllamaClient,
    OllamaClientMock,
    RespuestaOllama,
    generar_completado,
    explicar_codigo,
    sugerir_correccion,
    reiniciar_cliente,
    _obtener_cliente,
)
from synapse_lsp.server import (
    _manejar_ai_complete,
    _manejar_ai_explain,
    _manejar_ai_status,
    _procesar_mensaje,
    _DOCS,
    _almacenar_documento,
)


def _simular_mensaje(metodo: str, params: dict, msg_id: int = 1) -> dict:
    return {"jsonrpc": "2.0", "id": msg_id, "method": metodo, "params": params}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def limpiar_estado():
    """Limpia el estado global entre tests."""
    reiniciar_cliente()
    _DOCS.clear()
    yield


@pytest.fixture
def mock_ollama(monkeypatch):
    """
    Reemplaza _obtener_cliente() en llm_bridge con un OllamaClientMock.
    Tambien parchea las funciones importadas en server.py para que usen
    el mismo mock.
    """
    mock = OllamaClientMock()

    # Parchear _obtener_cliente() en su modulo de origen
    monkeypatch.setattr("synapse_lsp.llm_bridge._obtener_cliente", lambda: mock)
    monkeypatch.setattr("synapse_lsp.server.generar_completado", generar_completado)
    monkeypatch.setattr("synapse_lsp.server.explicar_codigo", explicar_codigo)
    monkeypatch.setattr("synapse_lsp.server.sugerir_correccion", sugerir_correccion)

    return mock


# ---------------------------------------------------------------------------
# Tests: OllamaClient mock
# ---------------------------------------------------------------------------


def test_ollama_mock_verificar_disponible():
    """El mock debe reportarse como disponible."""
    mock = OllamaClientMock()
    assert mock.verificar_disponible() is True


def test_ollama_mock_listar_modelos():
    """El mock debe listar modelos por defecto."""
    mock = OllamaClientMock()
    modelos = mock.listar_modelos()
    assert len(modelos) > 0
    assert "phi3:mini" in modelos
    assert "llama3.2:1b" in modelos


def test_ollama_mock_generar():
    """El mock debe generar respuestas."""
    mock = OllamaClientMock()
    resp = mock.generar("contexto de prueba", "sistema de prueba")
    assert resp is not None
    assert resp.done is True
    assert len(resp.response) > 0


def test_ollama_mock_generar_error():
    """El mock debe generar respuestas de correccion para prompts de error."""
    mock = OllamaClientMock()
    resp = mock.generar("corrige este error: x no declarada")
    assert resp is not None
    assert "Corrige" in resp.response or "corrige" in resp.response


# ---------------------------------------------------------------------------
# Tests: Funciones de alto nivel
# ---------------------------------------------------------------------------


def test_generar_completado_con_mock(monkeypatch):
    """generar_completado debe funcionar con el mock."""
    monkeypatch.setattr("synapse_lsp.llm_bridge._obtener_cliente", OllamaClientMock)
    resultado = generar_completado(
        contexto="#lang: es\nfuncion main() -> nulo:\n    ",
        prompt_usuario="agrega una variable 'x' de tipo entero",
    )
    assert resultado is not None
    assert len(resultado) > 0


def test_explicar_codigo_con_mock(monkeypatch):
    """explicar_codigo debe funcionar con el mock."""
    monkeypatch.setattr("synapse_lsp.llm_bridge._obtener_cliente", OllamaClientMock)
    resultado = explicar_codigo(
        "funcion principal() -> entero:\n    retornar 0\n"
    )
    assert resultado is not None
    assert len(resultado) > 0


def test_sugerir_correccion_con_mock(monkeypatch):
    """sugerir_correccion debe funcionar con el mock."""
    monkeypatch.setattr("synapse_lsp.llm_bridge._obtener_cliente", OllamaClientMock)
    resultado = sugerir_correccion(
        error_codigo="ERR_SEM_VAR_NO_DECLARADA",
        error_mensaje="Variable 'x' no declarada",
        codigo_contexto="x = 42",
    )
    assert resultado is not None
    assert len(resultado) > 0


def test_generar_completado_sin_ollama():
    """Sin Ollama disponible, debe retornar None o tener respuesta."""
    resultado = generar_completado("contexto", "prompt")
    # Sin mock puede retornar None porque no hay Ollama real
    # o una respuesta si el real esta corriendo
    assert resultado is None or len(resultado) > 0


# ---------------------------------------------------------------------------
# Tests: Integracion con LSP server (usando mock_ollama fixture)
# ---------------------------------------------------------------------------


def test_ai_complete_con_documento(mock_ollama):
    """synapse/aiComplete debe funcionar con documento almacenado."""
    _almacenar_documento(
        "file:///test.syn",
        "#lang: es\nfuncion main() -> nulo:\n    ", None,
    )

    msg = _simular_mensaje("synapse/aiComplete", {
        "textDocument": {"uri": "file:///test.syn"},
        "prompt": "agrega una variable entera",
    })
    resultado = _manejar_ai_complete(msg)
    assert resultado is not None
    assert "ai_available" in resultado
    assert "code" in resultado
    assert resultado["ai_available"] is True
    assert len(resultado["code"]) > 0


def test_ai_explain_con_codigo(mock_ollama):
    """synapse/aiExplain debe explicar codigo proporcionado."""
    msg = _simular_mensaje("synapse/aiExplain", {
        "textDocument": {"uri": "file:///test.syn"},
        "code": "funcion main() -> entero:\n    retornar 0",
    })
    resultado = _manejar_ai_explain(msg)
    assert resultado is not None
    assert resultado.get("ai_available") is True
    assert len(resultado["explanation"]) > 0
    assert resultado["code"] is not None


def test_ai_status_con_mock(mock_ollama):
    """synapse/aiStatus debe retornar estado con mock."""
    msg = _simular_mensaje("synapse/aiStatus", {})
    resultado = _manejar_ai_status(msg)
    assert resultado is not None
    assert resultado["ai_available"] is True
    assert resultado["local_only"] is True
    assert resultado["host"] == "localhost:11434"
    assert len(resultado["modelos"]) > 0


def test_ai_status_sin_mock():
    """synapse/aiStatus sin mock debe funcionar (reportar no disponible)."""
    msg = _simular_mensaje("synapse/aiStatus", {})
    resultado = _manejar_ai_status(msg)
    assert resultado is not None
    assert "ai_available" in resultado
    assert "local_only" in resultado
    assert resultado["local_only"] is True


def test_ai_status_en_ruta_mensajes(mock_ollama):
    """El metodo synapse/aiStatus debe ser accesible via _procesar_mensaje."""
    msg = {"jsonrpc": "2.0", "id": 1, "method": "synapse/aiStatus", "params": {}}
    resultado = _procesar_mensaje(msg)
    assert resultado is not None
    assert "result" in resultado
    assert resultado["result"]["ai_available"] is True


def test_ai_complete_en_ruta_mensajes(mock_ollama):
    """El metodo synapse/aiComplete debe ser accesible via _procesar_mensaje."""
    _almacenar_documento(
        "file:///test.syn",
        "#lang: es\nfuncion main() -> nulo:\n    ", None,
    )
    msg = _simular_mensaje("synapse/aiComplete", {
        "textDocument": {"uri": "file:///test.syn"},
        "prompt": "agrega un retorno",
    })
    resultado = _procesar_mensaje(msg)
    assert resultado is not None
    assert "result" in resultado
    assert resultado["result"]["ai_available"] is True


def test_hover_con_ia_enriquecida(mock_ollama):
    """Hover en funcion debe incluir explicacion IA sin crashear."""
    _almacenar_documento(
        "file:///test.syn",
        "#lang: es\nfuncion main() -> nulo:\n    retornar\n",
        None,
    )
    msg = _simular_mensaje("textDocument/hover", {
        "textDocument": {"uri": "file:///test.syn"},
        "position": {"line": 1, "character": 5},
    })
    resultado = _procesar_mensaje(msg)
    assert resultado is not None


def test_hover_sin_documento():
    """Hover sin documento no debe crashear."""
    msg = _simular_mensaje("textDocument/hover", {
        "textDocument": {"uri": "file:///no_existe.syn"},
        "position": {"line": 0, "character": 0},
    })
    resultado = _procesar_mensaje(msg)
    assert resultado is not None


# ---------------------------------------------------------------------------
# Tests: code action IA
# ---------------------------------------------------------------------------


def test_code_action_ia_con_error(mock_ollama):
    """codeAction IA debe sugerir correccion para errores conocidos sin crash."""
    _almacenar_documento("file:///test.syn", "x = 42", None)

    msg = _simular_mensaje("textDocument/codeAction", {
        "textDocument": {"uri": "file:///test.syn"},
        "range": {"start": {"line": 0, "character": 0}, "end": {"line": 0, "character": 1}},
        "context": {
            "diagnostics": [
                {"range": {}, "code": "ERR_SEM_VAR_NO_DECLARADA", "message": "x no declarada"}
            ]
        },
    })
    resultado = _procesar_mensaje(msg)
    assert resultado is not None
    if resultado.get("result"):
        # Si hay acciones, verificar que esten bien formadas
        for action in resultado["result"]:
            assert "title" in action
            assert "kind" in action


# ---------------------------------------------------------------------------
# Tests: RespuestaOllama dataclass
# ---------------------------------------------------------------------------


def test_respuesta_ollama():
    """RespuestaOllama debe ser construible con todos los campos."""
    resp = RespuestaOllama(response="codigo", done=True, error=None)
    assert resp.response == "codigo"
    assert resp.done is True
    assert resp.error is None


def test_respuesta_ollama_con_error():
    """RespuestaOllama debe soportar errores."""
    resp = RespuestaOllama(response="", done=False, error="HTTP 500: Server Error")
    assert resp.error is not None
    assert "500" in resp.error
