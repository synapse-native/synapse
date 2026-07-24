from typing import Optional

_MAX_DOCS = 100
_DOCS: dict[str, dict] = {}


def _almacenar_documento(uri: str, texto: str, ast=None, version: int = 1, analizador=None) -> None:
    if len(_DOCS) >= _MAX_DOCS:
        _DOCS.pop(next(iter(_DOCS)))
    _DOCS[uri] = {"texto": texto, "ast": ast, "version": version, "analizador": analizador}


def _eliminar_documento(uri: str) -> None:
    _DOCS.pop(uri, None)


def _obtener_documento(uri: str) -> Optional[dict]:
    return _DOCS.get(uri)
