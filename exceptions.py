class SynapseError(Exception):
    """Excepción estructurada del compilador Synapse.
    Lleva la línea, columna y mensaje para conversión directa a Diagnostic LSP.
    """
    def __init__(self, mensaje: str, linea: int = 0, columna: int = 0):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.linea = linea
        self.columna = columna