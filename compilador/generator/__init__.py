# Re-exportaciones de la API pública del generador de código C.
# La implementación vive en generator.py y los submódulos de dominio.

from .context import GeneratorContext, MAPA_TIPOS_C  # noqa: F401
from .generator import GeneradorC, visitar  # noqa: F401
