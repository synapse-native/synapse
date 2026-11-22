# -*- coding: utf-8 -*-
"""Comportamiento E2E de opensyn/memoria_persistente_cifrada.syn (r212).

Compila un driver real con `python main.py`, lo ejecuta y verifica:
- escritura y lectura cifrada de patrones, fallos y proyecto;
- persistencia entre reinicios con la passphrase correcta;
- rechazo de una passphrase incorrecta;
- no fuga de texto en claro en el archivo de memoria.

No se modifica ningun test existente.
"""
import os
import subprocess

import pytest

pytestmark = pytest.mark.integration

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PYTHON = os.path.join(RAIZ, ".venv", "Scripts", "python.exe")

DRIVER = '''#lang: es
importar std.io
importar std.texto
importar std.sistema
importar opensyn.memoria_persistente_cifrada

funcion principal() -> entero:
    let pass = obtener_env("OPENSYN_MEMORIA_PASSPHRASE")
    si longitud(pass) == 0:
        pass = "clave-r212"
    let mem0 = memoria_inicializar(pass)
    escribir_linea("INIT=" + a_texto(mem0.codigo))
    si mem0.inicializada == falso:
        retornar 0

    let mem = mem0
    let existente = memoria_consultar_proyecto(mem0, "hash123")
    si longitud(existente) == 0:
        let mem1 = memoria_guardar_patron(mem0, "usar validacion estricta", "compilar modulo rust", 0.9)
        escribir_linea("SAVE_PATRON=" + a_texto(mem1.codigo))
        let mem2 = memoria_registrar_fallo(mem1, "usar API inexistente", "no compila", "usar std.cripto")
        escribir_linea("SAVE_FALLO=" + a_texto(mem2.codigo))
        let mem3 = memoria_guardar_proyecto(mem2, "hash123", "datos del proyecto")
        escribir_linea("SAVE_PROYECTO=" + a_texto(mem3.codigo))
        mem = mem3

    let patrones = memoria_consultar_patrones(mem, "compilar modulo")
    let total_patrones = a_texto(longitud(patrones))
    escribir_linea("PATRONES=" + total_patrones)
    para p en patrones:
        let exito_txt = a_texto_decimal(p.exito_ratio)
        escribir_linea("PATRON=" + p.patron + "|" + exito_txt)

    let fallos = memoria_evitar_fallos(mem, "API inexistente")
    let total_fallos = a_texto(longitud(fallos))
    escribir_linea("FALLOS=" + total_fallos)
    para f en fallos:
        escribir_linea("FALLO=" + f.intento_fallido + "|" + f.solucion_correcta)

    let proyecto = memoria_consultar_proyecto(mem, "hash123")
    escribir_linea("PROYECTO=" + proyecto)
    let capas = memoria_capas()
    let total_capas = a_texto(longitud(capas))
    escribir_linea("CAPAS=" + total_capas)
    let mem4 = memoria_cerrar(mem)
    si mem4.inicializada == verdadero:
        escribir_linea("CERRADA=1")
    sino:
        escribir_linea("CERRADA=0")
    retornar 0
'''


def _compilar(tmp_path):
    fuente = tmp_path / "probe_memoria_cifrada.syn"
    exe = tmp_path / "probe_memoria_cifrada.exe"
    fuente.write_text(DRIVER, encoding="utf-8")
    compilacion = subprocess.run(
        [PYTHON, "main.py", str(fuente), "-o", str(exe)],
        cwd=RAIZ,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
    )
    assert compilacion.returncode == 0, (
        f"Compilacion fallo:\n{compilacion.stdout[-3000:]}\n{compilacion.stderr[-3000:]}"
    )
    assert exe.exists(), "No se genero el ejecutable"
    return exe


def _ejecutar(exe, memoria_dir, passphrase):
    env = dict(os.environ)
    env["OPENSYN_MEMORIA_DIR"] = str(memoria_dir)
    env["OPENSYN_MEMORIA_PASSPHRASE"] = passphrase
    ejecucion = subprocess.run(
        [str(exe)],
        cwd=RAIZ,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=180,
        env=env,
    )
    assert ejecucion.returncode == 0, f"Ejecucion fallo: {ejecucion.stderr[-3000:]}"
    return ejecucion.stdout


def test_memoria_cifrada_escritura_lectura_y_no_fuga(tmp_path):
    exe = _compilar(tmp_path)
    memoria_dir = tmp_path / "memoria"
    memoria_dir.mkdir()

    salida = _ejecutar(exe, memoria_dir, "clave-correcta-r212")

    assert "INIT=0" in salida, salida
    assert "SAVE_PATRON=0" in salida, salida
    assert "SAVE_FALLO=0" in salida, salida
    assert "SAVE_PROYECTO=0" in salida, salida
    assert "PATRONES=1" in salida, salida
    assert "PATRON=usar validacion estricta|0.9" in salida, salida
    assert "FALLOS=1" in salida, salida
    assert "FALLO=usar API inexistente|usar std.cripto" in salida, salida
    assert "PROYECTO=datos del proyecto" in salida, salida
    assert "CAPAS=3" in salida, salida
    assert "CERRADA=0" in salida, salida

    archivo = memoria_dir / "memoria.db"
    assert archivo.exists(), "No se creo el almacen cifrado"
    datos = archivo.read_bytes()
    assert datos, "El almacen cifrado esta vacio"

    prohibidos = [
        b"usar validacion estricta",
        b"compilar modulo rust",
        b"usar API inexistente",
        b"no compila",
        b"usar std.cripto",
        b"datos del proyecto",
        b"clave-correcta-r212",
    ]
    for texto in prohibidos:
        assert texto not in datos, f"Fuga de texto en claro: {texto!r}"

    hex_permitido = set(b"0123456789abcdefABCDEF\r\n")
    assert set(datos).issubset(hex_permitido), "El almacen contiene bytes no hexadecimales"

    lineas = [ln for ln in datos.splitlines() if ln]
    assert len(lineas) == 3, f"Se esperaban 3 entradas cifradas, hay {len(lineas)}"
    for linea in lineas:
        assert len(linea) % 2 == 0, "Blob hexadecimal con longitud impar"

    # Persistencia: un reinicio con la misma passphrase descifra lo guardado.
    salida2 = _ejecutar(exe, memoria_dir, "clave-correcta-r212")
    assert "INIT=0" in salida2, salida2
    assert "PATRONES=1" in salida2, salida2
    assert "PROYECTO=datos del proyecto" in salida2, salida2

    # Passphrase incorrecta: el almacen no es accesible.
    salida3 = _ejecutar(exe, memoria_dir, "clave-incorrecta-r212")
    assert "INIT=-1" in salida3, salida3
    assert "PATRONES=1" not in salida3, salida3
    assert "PROYECTO=datos del proyecto" not in salida3, salida3

