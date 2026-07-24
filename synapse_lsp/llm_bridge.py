"""
synapse_lsp/llm_bridge.py — Puente de IA Local (F12.3)

Segun Documento Maestro Parte VI:
"El LSP de Synapse debe estar preparado para interactuar con modelos locales
(ej. Ollama, Phi-3). Toda telemetría y contexto debe procesarse exclusivamente
en la máquina host (localhost)."

Este modulo implementa el puente con Ollama (API REST en localhost:11434)
usando exclusivamente la biblioteca estandar de Python (urllib).
NO utiliza requests, NO llama a APIs de nube.

Arquitectura:
- OllamaClient: Cliente HTTP para la API REST de Ollama
- generar_completado: Genera codigo Synapse a partir de contexto
- explicar_codigo: Explica codigo Synapse en lenguaje natural
- sugerir_accion: Sugiere acciones correctivas para errores
- Todas las funciones son tolerantes a fallos (Ollama puede no estar corriendo)
"""

import json
import urllib.request
import urllib.error
import logging
import traceback
from typing import Optional
from dataclasses import dataclass

logger = logging.getLogger("synapse-lsp.llm")

# ---------------------------------------------------------------------------
# Configuracion
# ---------------------------------------------------------------------------

OLLAMA_HOST = "http://localhost:11434"
DEFAULT_MODEL = "phi3:mini"  # Modelo ligero recomendado
FALLBACK_MODEL = "llama3.2:1b"  # Alternativa si phi3 no esta disponible
TIMEOUT_SECS = 15  # Timeout generoso para modelos locales

# ---------------------------------------------------------------------------
# Modelos de datos para la API de Ollama
# ---------------------------------------------------------------------------


@dataclass
class RespuestaOllama:
    """Respuesta tipada de /api/generate."""
    response: str
    done: bool
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Cliente Ollama
# ---------------------------------------------------------------------------


class OllamaClient:
    """Cliente HTTP para la API REST de Ollama (localhost)."""

    def __init__(
        self,
        host: str = OLLAMA_HOST,
        model: str = DEFAULT_MODEL,
        timeout: int = TIMEOUT_SECS,
    ):
        self.host = host.rstrip("/")
        self.model = model
        self.timeout = timeout
        self._disponible: Optional[bool] = None

    # ------------------------------------------------------------------
    # Metodos de estado
    # ------------------------------------------------------------------

    def verificar_disponible(self) -> bool:
        """Verifica si Ollama esta corriendo en localhost."""
        if self._disponible is not None:
            return self._disponible
        try:
            req = urllib.request.Request(
                f"{self.host}/api/tags",
                method="GET",
            )
            with urllib.request.urlopen(req, timeout=3) as resp:
                self._disponible = resp.status == 200
                return self._disponible
        except (urllib.error.URLError, ConnectionRefusedError, OSError):
            self._disponible = False
            return False

    def listar_modelos(self) -> list[str]:
        """Lista los modelos disponibles en Ollama."""
        try:
            req = urllib.request.Request(
                f"{self.host}/api/tags",
                method="GET",
            )
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                modelos = data.get("models", [])
                return [m.get("name", "?") for m in modelos]
        except Exception:
            logging.error("[LSP] Error listando modelos Ollama:\n%s", traceback.format_exc())
            return []

    def modelo_disponible(self, modelo: Optional[str] = None) -> bool:
        """Verifica si un modelo especifico esta disponible."""
        modelo = modelo or self.model
        return modelo in self.listar_modelos()

    # ------------------------------------------------------------------
    # API /api/generate (completions)
    # ------------------------------------------------------------------

    def generar(
        self,
        prompt: str,
        sistema: str = "",
        modelo: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 512,
    ) -> Optional[RespuestaOllama]:
        """
        Envia una solicitud de generacion a /api/generate.

        Args:
            prompt: El texto de entrada para el modelo.
            sistema: Instrucciones de sistema (contexto).
            modelo: Nombre del modelo (default: self.model).
            temperature: Control de creatividad (0.0 - 1.0).
            max_tokens: Maximo de tokens a generar.

        Returns:
            RespuestaOllama o None si hay error.
        """
        if not self.verificar_disponible():
            logger.warning("Ollama no esta disponible en %s", self.host)
            return None

        modelo = modelo or self.model
        payload = {
            "model": modelo,
            "prompt": prompt,
            "system": sistema,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                f"{self.host}/api/generate",
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                body = json.loads(resp.read().decode("utf-8"))
                return RespuestaOllama(
                    response=body.get("response", ""),
                    done=body.get("done", False),
                    error=body.get("error"),
                )
        except urllib.error.HTTPError as e:
            logger.error("Ollama HTTP error: %d %s", e.code, e.reason)
            return RespuestaOllama(
                response="", done=False,
                error=f"HTTP {e.code}: {e.reason}",
            )
        except urllib.error.URLError as e:
            logger.error("Ollama connection error: %s", e.reason)
            return None
        except Exception as e:
            logger.error("Ollama error inesperado: %s", e)
            return None

    # Nota: El endpoint /api/chat (conversacional) esta disponible via
    # self.chat() pero no se expone en la API publica del LSP por ahora.
    # Se agregara cuando se necesiten capacidades conversacionales.
    # Referencia: Reservado para expansion futura de F12.3.


# ---------------------------------------------------------------------------
# Funciones de alto nivel para el LSP
# ---------------------------------------------------------------------------

# Cliente global (singleton perezoso)
_client: Optional[OllamaClient] = None


def _obtener_cliente() -> OllamaClient:
    """Retorna o crea el cliente global."""
    global _client
    if _client is None:
        _client = OllamaClient()
    return _client


def reiniciar_cliente() -> None:
    """Fuerza reinicio del cliente (util en tests)."""
    global _client
    _client = None


# ---------------------------------------------------------------------------
# Sistema de prompts para Synapse
# ---------------------------------------------------------------------------

_SISTEMA_CODIGO = """Eres un asistente de codigo para el lenguaje Synapse.
Synapse es un lenguaje de sistemas con sintaxis en espanol.
Caracteristicas clave:
- Tipado estatico con sintaxis 'nombre: Tipo'
- Ownership/RAII para seguridad de memoria
- Canales tipados para concurrencia (Canal<T>)
- Contratos logicos: requiere / garantiza
- Compilacion a C nativo

Reglas:
1. Genera SOLO codigo Synapse valido, sin explicaciones.
2. Usa indentacion de 4 espacios.
3. Las funciones se definen con 'funcion nombre(params) -> Tipo:'
4. Las variables se declaran con 'nombre: Tipo = valor' o 'nombre = valor'
5. Los comentarios son con '//'
6. Usa '#lang: es' al inicio del archivo.
7. NO incluyas bloques ```synapse``` en la respuesta."""

_SISTEMA_EXPLICACION = """Eres un tutor de programacion para el lenguaje Synapse.
Explica el codigo de forma clara y concisa en espanol.
Synapse es un lenguaje de sistemas con sintaxis en espanol,
tipado estatico, ownership, y concurrencia por canales."""


def generar_completado(
    contexto: str,
    prompt_usuario: str,
    modelo: Optional[str] = None,
) -> Optional[str]:
    """
    Genera codigo Synapse usando IA local.

    Args:
        contexto: Codigo existente en el buffer del editor.
        prompt_usuario: Descripcion de lo que se quiere generar.
        modelo: Modelo Ollama a usar.

    Returns:
        Codigo generado o None si no esta disponible.
    """
    cliente = _obtener_cliente()
    if not cliente.verificar_disponible():
        return None

    prompt = f"Contexto actual del codigo:\n{contexto}\n\n---\n\n{prompt_usuario}"

    resp = cliente.generar(
        prompt=prompt,
        sistema=_SISTEMA_CODIGO,
        modelo=modelo,
        temperature=0.3,
        max_tokens=512,
    )

    if resp and not resp.error and resp.response:
        return resp.response.strip()
    return None


def explicar_codigo(
    codigo: str,
    modelo: Optional[str] = None,
) -> Optional[str]:
    """
    Explica codigo Synapse usando IA local.

    Args:
        codigo: Codigo a explicar.
        modelo: Modelo Ollama a usar.

    Returns:
        Explicacion o None si no esta disponible.
    """
    cliente = _obtener_cliente()
    if not cliente.verificar_disponible():
        return None

    resp = cliente.generar(
        prompt=f"Explica este codigo Synapse:\n\n{codigo}",
        sistema=_SISTEMA_EXPLICACION,
        modelo=modelo,
        temperature=0.5,
        max_tokens=512,
    )

    if resp and not resp.error and resp.response:
        return resp.response.strip()
    return None


def sugerir_correccion(
    error_codigo: str,
    error_mensaje: str,
    codigo_contexto: str,
    modelo: Optional[str] = None,
) -> Optional[str]:
    """
    Sugiere una correccion para un error de compilacion.

    Args:
        error_codigo: Codigo del error (ej. ERR_SEM_VAR_NO_DECLARADA).
        error_mensaje: Mensaje del error.
        codigo_contexto: Codigo alrededor del error.
        modelo: Modelo Ollama a usar.

    Returns:
        Sugerencia de correccion o None si no esta disponible.
    """
    cliente = _obtener_cliente()
    if not cliente.verificar_disponible():
        return None

    prompt = (
        f"Error de compilacion Synapse: [{error_codigo}] {error_mensaje}\n\n"
        f"Codigo:\n{codigo_contexto}\n\n"
        "Sugiere una correccion especifica (solo codigo):"
    )

    resp = cliente.generar(
        prompt=prompt,
        sistema=_SISTEMA_CODIGO,
        modelo=modelo,
        temperature=0.2,
        max_tokens=256,
    )

    if resp and not resp.error and resp.response:
        return resp.response.strip()
    return None


# ---------------------------------------------------------------------------
# Cliente mock para pruebas sin Ollama
# ---------------------------------------------------------------------------


class OllamaClientMock(OllamaClient):
    """
    Cliente mock que NO conecta a Ollama.
    Util para tests y cuando Ollama no esta instalado.
    """

    def __init__(self):
        super().__init__()
        self._disponible = True  # Simula estar disponible
        self._modelos_mock = ["phi3:mini", "llama3.2:1b"]

    def verificar_disponible(self) -> bool:
        return True

    def listar_modelos(self) -> list[str]:
        return list(self._modelos_mock)

    def modelo_disponible(self, modelo: Optional[str] = None) -> bool:
        return True

    def generar(
        self,
        prompt: str,
        sistema: str = "",
        modelo: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 512,
    ) -> Optional[RespuestaOllama]:
        # Retorna respuestas simuladas segun el prompt
        prompt_lower = prompt.lower()
        response = ""

        if "error" in prompt_lower or "correccion" in prompt_lower:
            response = "// Corrige la variable 'x' declarandola con 'x: entero = 0'"
        elif "explica" in prompt_lower or prompt_lower.startswith("explica"):
            response = (
                "Este codigo define una funcion 'principal' que retorna un entero. "
                "Usa '#lang: es' para establecer el idioma."
            )
        elif "contexto" in prompt_lower:
            response = "funcion auxiliar() -> entero:\n    retornar 42\n"
        else:
            response = (
                "funcion respuesta_ia() -> texto:\n"
                '    retornar "Generado por IA local"'
            )

        return RespuestaOllama(response=response, done=True)
