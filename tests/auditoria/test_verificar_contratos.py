# cumple Manual 2 §5.1 — los contratos `requiere`/`garantiza` se declaran y se
# evalúan en el cuerpo de la función; una función pública sin ellos es deuda.
# cumple Manual 2 §12 — la auditoría tiene que poder fallar (ratchet), no sólo
# imprimir un informe.
"""Regresión de `auditoria/verificar_contratos.py`.

Construye árboles sintéticos para comprobar ambos lados del gate: verde con
contratos completos o con deuda registrada en el baseline, y rojo cuando
aparece una función pública nueva sin `requiere` y `garantiza` o cuando se pide
`--estricto`.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
GATE = RAIZ / "auditoria" / "verificar_contratos.py"


def _cargar_gate():
    spec = importlib.util.spec_from_file_location("verificar_contratos", GATE)
    modulo = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(modulo)
    return modulo


def _arbol(tmp_path: Path, fuente: str, archivo: str = "std/prueba.syn") -> Path:
    raiz = tmp_path / "repo"
    destino = raiz / archivo
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(fuente, encoding="utf-8")
    return raiz


def test_passa_con_ambos_contratos(tmp_path, capsys):
    raiz = _arbol(tmp_path, "funcion sumar(a: entero, b: entero) -> entero:\n"
                            "    requiere: a >= 0\n"
                            "    garantiza: _resultado_ >= a\n"
                            "    retornar a + b\n")
    codigo = _cargar_gate().main(["--raiz", str(raiz)])
    salida = capsys.readouterr().out
    assert codigo == 0, salida
    assert salida.startswith("OK: contratos")


def test_falla_con_contrato_incompleto(tmp_path, capsys):
    raiz = _arbol(tmp_path, "funcion restar(a: entero, b: entero) -> entero:\n"
                            "    requiere: verdadero\n"
                            "    retornar a - b\n")
    codigo = _cargar_gate().main(["--raiz", str(raiz)])
    salida = capsys.readouterr().out
    assert codigo == 1
    assert "restar" in salida and "garantiza:" in salida


def test_baseline_registra_la_deuda(tmp_path, capsys):
    raiz = _arbol(tmp_path, "funcion heredada() -> nulo:\n"
                            "    retornar\n")
    gate = _cargar_gate()
    assert gate.main(["--raiz", str(raiz), "--baseline"]) == 0
    capsys.readouterr()
    codigo = gate.main(["--raiz", str(raiz)])
    salida = capsys.readouterr().out
    assert codigo == 0, salida
    assert "0 nuevas" in salida
    # Y --estricto sigue exigiendo deuda cero.
    assert gate.main(["--raiz", str(raiz), "--estricto"]) == 1


def test_exentos_ffi_y_privadas(tmp_path, capsys):
    raiz = _arbol(tmp_path, "externo funcion _syn_ffi(x: entero) -> entero\n"
                            "\n"
                            "funcion _privada() -> nulo:\n"
                            "    retornar\n")
    codigo = _cargar_gate().main(["--raiz", str(raiz)])
    salida = capsys.readouterr().out
    assert codigo == 0, salida
    assert "1 FFI exentas" in salida
