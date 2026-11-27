# -*- coding: utf-8 -*-
"""test_compilacion_fase32_s2.py — gate S2 de compilación de Fase 32.

Manual 9 §6.2: "La suite de tests completa en cada target."
Manual 8 §4.2: el modo de validación (`synapse check`) debe reportar la causa.

Este gate cierra el target **S2 (compilador nativo, `synapse.exe`)** para los
mismos módulos que ya cubre S1 en `test_compilacion_fase32.py`:

- los 14 módulos de producción `opensyn/*.syn` y `nucleo/grafo_conocimiento.syn`
  compilan con el binario nativo (`synapse check`) con rc=0;
- los fuentes cumplen Manual 2 §1.2 (UTF-8 sin BOM) y Manual 2 §1.1 (`#lang`
  en la línea 1);
- un error léxico/sintáctico emite línea y columna accionables y rc≠0;
- el lexer nativo tolera un BOM inicial (paridad con S1, que también lo acepta);
- `Resultado`/`Opcion` (Manual 2 §4.2) resuelven como tipos del prelude;
- un `importar` relativo se resuelve contra el directorio del módulo importador.
"""
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration

RAIZ = Path(__file__).resolve().parents[2]
GRAFO = RAIZ / "nucleo" / "grafo_conocimiento.syn"
BOM = b"\xef\xbb\xbf"


def _binario():
    """Binario nativo (S2). Sin binario el gate FALLA: no se salta."""
    for cand in (RAIZ / "dist" / "bin" / "synapse.exe",
                 RAIZ / "synapse.exe",
                 RAIZ / "synapse_bootstrap.exe"):
        if cand.exists():
            return cand
    return None


def _check(ruta):
    """Ejecuta `synapse check <ruta>` en el binario nativo."""
    bin_ = _binario()
    assert bin_ is not None, "no se encontro binario nativo (S2)"
    p = subprocess.run([str(bin_), "check", str(ruta)], capture_output=True,
                       text=True, cwd=str(RAIZ), timeout=300,
                       encoding="utf-8", errors="replace")
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def _modulos_produccion():
    modulos = sorted((RAIZ / "opensyn").glob("*.syn"))
    if GRAFO.exists():
        modulos.append(GRAFO)
    return modulos


def _escribir(ruta, contenido, bom=False):
    datos = contenido.encode("utf-8")
    ruta.write_bytes((BOM + datos) if bom else datos)
    return ruta


def test_binario_nativo_disponible():
    assert _binario() is not None, (
        "falta el binario nativo (S2); compilar con `python main.py nucleo/principal.syn`"
    )


@pytest.mark.slow
@pytest.mark.timeout(900)
def test_s2_modulos_fase32_compilan():
    """Todos los módulos de producción de Fase 32 compilan con S2."""
    errores = []
    for ruta in _modulos_produccion():
        rc, salida = _check(ruta)
        if rc != 0:
            rel = ruta.relative_to(RAIZ).as_posix()
            errores.append(f"{rel} (rc={rc}):\n{salida[-1200:]}")
    assert not errores, "modulos que no compilan en S2:\n\n" + "\n\n".join(errores)


def test_s2_fuentes_sin_bom_y_lang_en_linea_1():
    """Manual 2 §1.2 (sin BOM) y §1.1 (`#lang` en la línea 1)."""
    for ruta in _modulos_produccion():
        datos = ruta.read_bytes()
        rel = ruta.relative_to(RAIZ).as_posix()
        assert not datos.startswith(BOM), f"{rel} tiene BOM UTF-8 (Manual 2 §1.2)"
        primera = datos.split(b"\n", 1)[0].decode("utf-8", "replace").strip()
        assert primera.startswith("#lang"), f"{rel} no abre con #lang (Manual 2 §1.1)"


def test_s2_error_lexico_reporta_linea_y_columna(tmp_path):
    """Manual 8 §4.2: el fallo léxico se reporta con ubicación y rc≠0."""
    fuente = "#lang: es\nfuncion principal() -> entero:\n    retornar 0 @\n"
    ruta = _escribir(tmp_path / "lexico.syn", fuente)
    rc, salida = _check(ruta)
    assert rc != 0, salida
    assert "Error lexico" in salida, salida
    assert "linea 3" in salida and "columna" in salida, salida
    assert "fallo lexico" in salida, salida


def test_s2_error_sintaxis_reporta_linea_y_columna(tmp_path):
    """Manual 8 §4.2: el fallo sintáctico se reporta con ubicación y rc≠0."""
    fuente = "#lang: es\nfuncion principal() -> entero:\n    retornar )\n"
    ruta = _escribir(tmp_path / "sintaxis.syn", fuente)
    rc, salida = _check(ruta)
    assert rc != 0, salida
    assert "Error de sintaxis" in salida, salida
    assert "linea 3" in salida and "columna" in salida, salida
    assert "error de sintaxis" in salida, salida


def test_s2_bom_inicial_tolerado_paridad_s1(tmp_path):
    """Paridad S1/S2: un BOM inicial no impide detectar `#lang` (S1 lo acepta)."""
    ruta = _escribir(tmp_path / "bom.syn",
                     "#lang: es\nfuncion principal() -> entero:\n    retornar 0\n",
                     bom=True)
    rc, salida = _check(ruta)
    assert rc == 0, salida


def test_s2_tipos_algebraicos_del_prelude(tmp_path):
    """Manual 2 §4.2: `Resultado<T,E>` y `Opcion<T>` son tipos válidos."""
    fuente = ("#lang: es\n"
              "funcion procesar(r: Resultado<entero, texto>) -> entero:\n"
              "    retornar 0\n"
              "funcion obtener(o: Opcion<entero>) -> entero:\n"
              "    retornar 0\n"
              "funcion principal() -> entero:\n"
              "    retornar 0\n")
    ruta = _escribir(tmp_path / "prelude.syn", fuente)
    rc, salida = _check(ruta)
    assert rc == 0, salida


def test_s2_import_relativo_al_modulo_importador(tmp_path):
    """`importar` se resuelve contra el directorio del módulo que importa."""
    paquete = tmp_path / "paquete"
    paquete.mkdir()
    _escribir(paquete / "dependencia.syn",
              "#lang: es\nfuncion valor() -> entero:\n    retornar 7\n")
    _escribir(paquete / "principal.syn",
              "#lang: es\nimportar dependencia\n"
              "funcion principal() -> entero:\n    retornar dependencia.valor()\n")
    rc, salida = _check(paquete / "principal.syn")
    assert rc == 0, salida
