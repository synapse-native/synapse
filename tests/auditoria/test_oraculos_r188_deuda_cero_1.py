"""
Oraculos del ME r188_deuda_cero_1 (2026-10-15) — mandato: cero deuda sin excepcion.

Frentes verificados (plan docs/plan_ME_r188_deuda_cero_1.md):
  R1 (Manual 5 §3.6, H-R184-1): la forma canonica `coincidir co ->:` compila
     rc=0 y EJECUTA ambas ramas (ok: valor recibido; err: canal cerrado tras
     cerrar). La forma historica `coincidir r:` sobre ADT sigue verde.
  R2 (Manual 8 §4.1, H-R187-1): una firma malformada con '(' abierto NO
     destruye la estructura del resto del archivo — rc=1 con el error en la
     LINEA de la firma (sin cascada). La continuacion multilínea sana de
     r153 sigue compilando rc=0.

Anti-fabricacion (Manual 7 §2.3): compila/executa con el pipeline real
(main.py), nada mira solo texto.
"""
import re
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent.parent
PY = sys.executable


@pytest.fixture(scope="module")
def tmp_probe(tmp_path_factory):
    return tmp_path_factory.mktemp("r188_deuda_cero_1")


def _compilar(fuente: str, tmp, nombre: str, capturar=False):
    """Compila con main.py (pipeline S1 completo). Devuelve (rc, ruta, salida)."""
    path = tmp / nombre
    path.write_text(fuente, encoding="utf-8")
    if capturar:
        proc = subprocess.run(
            [PY, str(RAIZ / "main.py"), str(path), "-o", str(tmp / "out.exe")],
            cwd=str(RAIZ), capture_output=True,
        )
        salida = (proc.stdout + proc.stderr).decode("utf-8", errors="replace")
        return proc.returncode, path, salida
    rc = subprocess.call(
        [PY, str(RAIZ / "main.py"), str(path), "-o", str(tmp / (nombre + ".exe"))],
        cwd=str(RAIZ), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    return rc, path, ""


class TestR1CoincidirFlecha:
    """Manual 5 §3.6: `coincidir c ->:` forma canonica (H-R184-1)."""

    def test_forma_flecha_compila_y_ejecuta_ambas_ramas(self, tmp_probe):
        fuente = """#lang: es
funcion principal() -> entero:
    let co = canal(entero, 2)
    co <- 7
    coincidir co ->:
        ok(v) => escribir(entero_a_texto(v))
        err(_) => escribir("cerrado-1")
    cerrar(co)
    coincidir co ->:
        ok(_) => escribir("ok-2")
        err(_) => escribir("cerrado-2")
    retornar 0
"""
        rc, _, _ = _compilar(fuente, tmp_probe, "flecha.syn")
        assert rc == 0, "la forma canonica M5 §3.6 `coincidir co ->:` debe compilar rc=0"
        proc = subprocess.run(
            [str(tmp_probe / "flecha.syn.exe")], capture_output=True, timeout=120,
        )
        salida = proc.stdout.decode("utf-8", errors="replace")
        assert "7" in salida, "ok(v) recibio el valor enviado (7)"
        assert "cerrado-2" in salida, "err(_) tras cerrar(co) — M5 §3.6 cierre de canal"
        assert "ok-2" not in salida, "la rama err debe ganar tras cerrar(co)"

    def test_forma_historica_sigue_verde(self, tmp_probe):
        """Regression: `coincidir r:` sin flecha sigue siendo valido."""
        fuente = """#lang: es
tipo Res = ok(entero) | err(texto)
funcion hago(b: booleano) -> Res:
    si b:
        retornar ok(6)
    retornar err("x")
funcion principal() -> entero:
    let r = hago(verdadero)
    coincidir r:
        ok(v) => escribir("ok")
        err(e) => escribir("err")
    retornar 0
"""
        rc, _, _ = _compilar(fuente, tmp_probe, "historica.syn")
        assert rc == 0, "la forma historica `coincidir r:` no debe registrar regresion"


class TestR2ContinuacionAcotada:
    """Manual 8 §4.1 (H-R187-1): '(' abierta NO destruye el RESTO del archivo."""

    def test_firma_malformada_error_en_su_linea_no_cascada(self, tmp_probe):
        fuente = """#lang: es
funcion rotura(c: entero) -> entero:
    retornar c

funcion roto(a:
funcion principal() -> entero:
    let x = rotura(2)
    escribir(entero_a_texto(x))
    retornar x
"""
        rc, _, salida = _compilar(fuente, tmp_probe, "malformada.syn", capturar=True)
        assert rc != 0, "la firma malformada debe rechazarse (rc=1)"
        lineas = [int(g.group(1)) for g in re.finditer(r":([0-9]+):[0-9]+ - ", salida)]
        assert lineas and min(lineas) == 5, \
            f"rc=1 con el error en la LINEA de la firma (5); salida: {salida[:300]}"

    def test_llamada_multilinea_sana_sigue_compilando(self, tmp_probe):
        """Regression r153: llamada partida entre lineas (continuacion sana)
        sigue verde — el guard solo corta lineas que terminan en ':'. """
        fuente = """#lang: es
funcion suma(a: entero, b: entero) -> entero:
    retornar a + b
funcion principal() -> entero:
    let r = suma(3,
        4)
    escribir(entero_a_texto(r))
    retornar 0
"""
        rc, _, _ = _compilar(fuente, tmp_probe, "multilinea.syn")
        assert rc == 0, "la continuacion multilinea sana de r153 sigue verde"
        salida = subprocess.run(
            [str(tmp_probe / "multilinea.syn.exe")], capture_output=True, timeout=120,
        ).stdout.decode("utf-8", errors="replace")
        assert "7" in salida
