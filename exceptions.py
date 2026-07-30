class SynapseError(SyntaxError):
    """Excepción estructurada del compilador Synapse.
    Lleva la línea, columna y mensaje para conversión directa a Diagnostic LSP.
    Hereda de SyntaxError para compatibilidad con pytest.raises(SyntaxError).
    """
    def __init__(self, mensaje: str, linea: int = 0, columna: int = 0):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.linea = linea
        self.columna = columna