# tests/auditoria/test_r301_generator_reconciliacion.py
# cumple Manual 2 §8.2: oráculo del ME r301_generator_reconciliacion (H-R300-1).
"""`nucleo/generator.syn` debe ser EXACTAMENTE lo que producen los submódulos.

Antes de este ME el archivo versionado tenía correcciones manuales (contratos y
bloques H-R275-1 de indexado de texto) que `_rebuild_generator.py` descartaba:
regenerar era perder semántica. Ahora las correcciones viven en
`nucleo/generador/*.syn` y la regeneración es idempotente.
"""

import importlib.util
import os
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
SCRIPT = RAIZ / "nucleo" / "_rebuild_generator.py"
GENERADO = RAIZ / "nucleo" / "generator.syn"


def _modulo_rebuild():
    spec = importlib.util.spec_from_file_location("_rebuild_generator", SCRIPT)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def test_generator_es_la_salida_de_los_submodulos():
    modulo = _modulo_rebuild()
    with tempfile.TemporaryDirectory() as tmp:
        destino = os.path.join(tmp, "generator.syn")
        modulo.SALIDA = destino
        assert modulo.reconstruir() == 0
        reconstruido = Path(destino).read_text(encoding="utf-8")
    versionado = GENERADO.read_text(encoding="utf-8")
    assert reconstruido == versionado, (
        "nucleo/generator.syn NO es la salida de nucleo/generador/*.syn: "
        "corré `python nucleo/_rebuild_generator.py` y no edites el combinado")


def test_correcciones_H_R275_1_viven_en_los_submodulos():
    marcadores = {
        "expr_eval.syn": "((CadenaSegura){1, &((%s).datos[(int)(%s)])})",
        "nodos_flujo.syn": "declara CadenaSegura",
        "funciones.syn": "antes el hoisting",
        "orquestador.syn": "el indexado de texto infiere texto",
    }
    for archivo, marcador in marcadores.items():
        texto = (RAIZ / "nucleo" / "generador" / archivo).read_text(encoding="utf-8")
        assert marcador in texto, f"{archivo}: falta el bloque H-R275-1"


def test_contratos_publicos_en_el_generador_combinado():
    texto = GENERADO.read_text(encoding="utf-8")
    for firma in (
        "funcion traducir_tipo_c_campo(",
        "funcion traducir_tipo_retorno(",
        "funcion gen_emitir_linea(",
        "funcion gen_emitir_str(",
        "funcion gen_emitir_nueva_linea(",
    ):
        pos = texto.index(firma) + len(firma)
        cuerpo = texto[pos:pos + 200]
        assert "requiere:" in cuerpo and "garantiza:" in cuerpo, (
            f"{firma} sin contratos (Manual 2 §12/§5.1)")


def test_sin_citas_invalidas_cumplé():
    for ruta in [GENERADO] + sorted((RAIZ / "nucleo" / "generador").glob("*.syn")):
        texto = ruta.read_text(encoding="utf-8")
        assert "cumplé Manual" not in texto, f"{ruta}: cita inválida 'cumplé'"
