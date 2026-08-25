import os, glob, time
import pytest

from conftest import DIR_INVALID, compilar_texto
from compilador.diagnostics import ErrorCodes


# Mapa: nombre del fixture → códigos de error esperados (al menos uno debe aparecer)
ERRORES_ESPERADOS: dict[str, set[ErrorCodes]] = {
    'arrow_faltante': {ErrorCodes.ERR_SYNTAX_EXPECTED_TOKEN},
    'expr_inesperada': {ErrorCodes.ERR_SYNTAX_UNEXPECTED_EXPR},
    'indent_invalido': {ErrorCodes.ERR_INDENT_INVALID},
    'lang_faltante': {ErrorCodes.ERR_LANG_MISSING},
    'token_inesperado': {ErrorCodes.ERR_LEX_CHAR_UNEXPECTED},
    'tortura_shadowing': {ErrorCodes.ERR_SEM_REDEFINICION},
    'tortura_tipos': {ErrorCodes.ERR_SEM_TIPO_INCOMPATIBLE},
    'tortura_alcance': {ErrorCodes.ERR_SEM_VAR_NO_DECLARADA},
    'tortura_recursividad': {ErrorCodes.ERR_SEM_FUNC_NO_DEFINIDA},
}


def _listar_fixtures_invalidas():
    return sorted(glob.glob(os.path.join(DIR_INVALID, '*.syn')))


@pytest.mark.parametrize('ruta_syn', _listar_fixtures_invalidas())
def test_diagnostico_captura_error(ruta_syn):
    base = os.path.splitext(os.path.basename(ruta_syn))[0]

    with open(ruta_syn, 'r', encoding='utf-8') as f:
        fuente = f.read()

    inicio = time.time()
    ast, diag = compilar_texto(fuente)
    duracion = time.time() - inicio

    assert duracion < 5.0, (
        f"Posible bucle infinito — la compilación tardó {duracion:.2f}s "
        f"en {base}.syn"
    )

    assert diag.hay_errores(), (
        f"Se esperaban errores en {base}.syn, pero no se reportó ninguno"
    )

    codigos_obtenidos = {e['codigo'] for e in diag.errores}
    esperados = ERRORES_ESPERADOS.get(base)

    if esperados:
        assert codigos_obtenidos & esperados, (
            f"{base}.syn: se esperaba uno de {[e.name for e in esperados]}, "
            f"se obtuvieron {[e.name for e in codigos_obtenidos]}"
        )
