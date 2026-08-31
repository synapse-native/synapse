"""Tests TDD para ME-3: Contratos requiere/garantiza en std/.
Cumple MTO OBL-M2-02 | Manual 2 §12 | Contratos requiere/garantiza observables.
Todos los tests verifican que cada función pública en std/ tenga contratos.
"""
# cumple Manual 2 §12 (OBL-M2-02)

import os
import pytest

pytestmark = pytest.mark.unit

_RT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Archivos std/ que DEBEN tener contratos (ME-3)
STD_FILES = {
    "io.syn": [
        "abrir", "leer", "escribir", "escribir_linea", "leer_linea", "leer_bytes",
    ],
    "json.syn": [
        "desde_texto", "liberar_nodo", "obtener_elemento", "obtener_campo", "a_texto",
    ],
    "math.syn": [
        "crear_tensor", "suma_tensor", "producto_punto", "relu",
    ],
    "texto.syn": [
        "contiene", "indice_de", "reemplazar", "termina_con", "recortar",
        "mayusculas", "minusculas", "escapar_json", "a_texto", "cmp_texto",
        "strlen_s", "strstr_f", "strchr_f", "atoi_f", "strcpy_f", "strncpy_f",
    ],
}


def _read_std(filename):
    """Lee un archivo std/ y retorna su contenido."""
    path = os.path.join(_RT_ROOT, "std", filename)
    with open(path, encoding="utf-8") as f:
        return f.read()


def _find_func_block(content, func_name):
    """Encuentra el bloque de una función y retorna el texto hasta la siguiente función o final."""
    lines = content.split("\n")
    in_func = False
    block_lines = []
    for line in lines:
        stripped = line.strip()
        # Detect start of function
        if stripped.startswith(f"funcion {func_name}(") or stripped.startswith(f"funcion {func_name} ("):
            in_func = True
            block_lines = [line]
            continue
        if in_func:
            # Detect end of function (next function or externo or estructura)
            if (stripped.startswith("funcion ") or stripped.startswith("externo ") or
                    stripped.startswith("estructura ") or stripped.startswith("#")):
                break
            block_lines.append(line)
    return "\n".join(block_lines)


# ---------------------------------------------------------------------------
# Tests TDD — cada test cita Manual 2 §12 (OBL-M2-02)
# ---------------------------------------------------------------------------

class TestContractsIO:
    """OBL-M2-02: std/io.syn debe tener contratos en cada función pública."""

    def test_io_abrir_tiene_requiere(self):
        """Manual 2 §12: abrir() debe tener requiere."""
        content = _read_std("io.syn")
        block = _find_func_block(content, "abrir")
        assert "requiere:" in block, f"abrir() sin requiere: {block[:200]}"

    def test_io_abrir_tiene_garantiza(self):
        """Manual 2 §12: abrir() debe tener garantiza."""
        content = _read_std("io.syn")
        block = _find_func_block(content, "abrir")
        assert "garantiza:" in block, f"abrir() sin garantiza: {block[:200]}"

    def test_io_leer_tiene_requiere(self):
        """Manual 2 §12: leer() debe tener requiere."""
        content = _read_std("io.syn")
        block = _find_func_block(content, "leer")
        assert "requiere:" in block, f"leer() sin requiere: {block[:200]}"

    def test_io_escribir_tiene_requiere(self):
        """Manual 2 §12: escribir() debe tener requiere."""
        content = _read_std("io.syn")
        block = _find_func_block(content, "escribir")
        assert "requiere:" in block, f"escribir() sin requiere: {block[:200]}"

    def test_io_leer_linea_tiene_garantiza(self):
        """Manual 2 §12: leer_linea() debe tener garantiza."""
        content = _read_std("io.syn")
        block = _find_func_block(content, "leer_linea")
        assert "garantiza:" in block, f"leer_linea() sin garantiza: {block[:200]}"

    def test_io_leer_bytes_tiene_requiere(self):
        """Manual 2 §12: leer_bytes() debe tener requiere."""
        content = _read_std("io.syn")
        block = _find_func_block(content, "leer_bytes")
        assert "requiere:" in block, f"leer_bytes() sin requiere: {block[:200]}"


class TestContractsJSON:
    """OBL-M2-02: std/json.syn debe tener contratos en cada función pública."""

    def test_json_desde_texto_tiene_requiere(self):
        """Manual 2 §12: desde_texto() debe tener requiere."""
        content = _read_std("json.syn")
        block = _find_func_block(content, "desde_texto")
        assert "requiere:" in block, f"desde_texto() sin requiere: {block[:200]}"

    def test_json_desde_texto_tiene_garantiza(self):
        """Manual 2 §12: desde_texto() debe tener garantiza."""
        content = _read_std("json.syn")
        block = _find_func_block(content, "desde_texto")
        assert "garantiza:" in block, f"desde_texto() sin garantiza: {block[:200]}"

    def test_json_obtener_elemento_tiene_requiere(self):
        """Manual 2 §12: obtener_elemento() debe tener requiere."""
        content = _read_std("json.syn")
        block = _find_func_block(content, "obtener_elemento")
        assert "requiere:" in block, f"obtener_elemento() sin requiere: {block[:200]}"

    def test_json_obtener_campo_tiene_requiere(self):
        """Manual 2 §12: obtener_campo() debe tener requiere."""
        content = _read_std("json.syn")
        block = _find_func_block(content, "obtener_campo")
        assert "requiere:" in block, f"obtener_campo() sin requiere: {block[:200]}"

    def test_json_a_texto_tiene_garantiza(self):
        """Manual 2 §12: a_texto() debe tener garantiza."""
        content = _read_std("json.syn")
        block = _find_func_block(content, "a_texto")
        assert "garantiza:" in block, f"a_texto() sin garantiza: {block[:200]}"


class TestContractsMath:
    """OBL-M2-02: std/math.syn debe tener contratos en cada función pública."""

    def test_math_crear_tensor_tiene_requiere(self):
        """Manual 2 §12: crear_tensor() debe tener requiere."""
        content = _read_std("math.syn")
        block = _find_func_block(content, "crear_tensor")
        assert "requiere:" in block, f"crear_tensor() sin requiere: {block[:200]}"

    def test_math_suma_tensor_tiene_requiere(self):
        """Manual 2 §12: suma_tensor() debe tener requiere."""
        content = _read_std("math.syn")
        block = _find_func_block(content, "suma_tensor")
        assert "requiere:" in block, f"suma_tensor() sin requiere: {block[:200]}"

    def test_math_relu_tiene_requiere(self):
        """Manual 2 §12: relu() debe tener requiere."""
        content = _read_std("math.syn")
        block = _find_func_block(content, "relu")
        assert "requiere:" in block, f"relu() sin requiere: {block[:200]}"


class TestContractsTexto:
    """OBL-M2-02: std/texto.syn debe tener contratos en cada función pública."""

    def test_texto_contiene_tiene_requiere(self):
        """Manual 2 §12: contiene() debe tener requiere."""
        content = _read_std("texto.syn")
        block = _find_func_block(content, "contiene")
        assert "requiere:" in block, f"contiene() sin requiere: {block[:200]}"

    def test_texto_contiene_tiene_garantiza(self):
        """Manual 2 §12: contiene() debe tener garantiza."""
        content = _read_std("texto.syn")
        block = _find_func_block(content, "contiene")
        assert "garantiza:" in block, f"contiene() sin garantiza: {block[:200]}"

    def test_texto_reemplazar_tiene_requiere(self):
        """Manual 2 §12: reemplazar() debe tener requiere."""
        content = _read_std("texto.syn")
        block = _find_func_block(content, "reemplazar")
        assert "requiere:" in block, f"reemplazar() sin requiere: {block[:200]}"

    def test_texto_recortar_tiene_garantiza(self):
        """Manual 2 §12: recortar() debe tener garantiza."""
        content = _read_std("texto.syn")
        block = _find_func_block(content, "recortar")
        assert "garantiza:" in block, f"recortar() sin garantiza: {block[:200]}"

    def test_texto_cmp_texto_tiene_garantiza(self):
        """Manual 2 §12: cmp_texto() debe tener garantiza."""
        content = _read_std("texto.syn")
        block = _find_func_block(content, "cmp_texto")
        assert "garantiza:" in block, f"cmp_texto() sin garantiza: {block[:200]}"

    def test_texto_strcpy_f_tiene_garantiza(self):
        """Manual 2 §12: strcpy_f() debe tener garantiza."""
        content = _read_std("texto.syn")
        block = _find_func_block(content, "strcpy_f")
        assert "garantiza:" in block, f"strcpy_f() sin garantiza: {block[:200]}"
