import sys
import json
from typing import Optional, Any


def _leer_mensaje() -> Optional[dict]:
    content_length: Optional[int] = None
    buf = b""

    while True:
        byte = sys.stdin.buffer.read(1)
        if not byte:
            return None
        buf += byte

        if buf.endswith(b"\r\n\r\n"):
            header_section = buf[:-4].decode("utf-8", errors="replace")
            for line in header_section.split("\r\n"):
                if line.lower().startswith("content-length:"):
                    raw_value = line.split(":", 1)[1].strip()
                    try:
                        content_length = int(raw_value)
                    except ValueError:
                        content_length = 0
                    break

            if content_length is None:
                content_length = 0

            body_bytes = sys.stdin.buffer.read(content_length)
            if len(body_bytes) != content_length:
                return None

            try:
                return json.loads(body_bytes.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                return None

        if len(buf) > 4096:
            return None


def _enviar_respuesta(respuesta: dict) -> None:
    cuerpo = json.dumps(respuesta, ensure_ascii=False)
    cuerpo_bytes = cuerpo.encode("utf-8")
    raw = f"Content-Length: {len(cuerpo_bytes)}\r\n\r\n".encode("utf-8") + cuerpo_bytes
    sys.stdout.buffer.write(raw)
    sys.stdout.buffer.flush()


def _enviar_notificacion(metodo: str, params: Any) -> None:
    _enviar_respuesta({"jsonrpc": "2.0", "method": metodo, "params": params})
