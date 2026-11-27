# Verificacion de la logica del gate de lectura previa (auditoria/registrar_lectura.py).
# Manual 2 §12 (contratos y trazabilidad) + gobernanza regla 1 (lectura previa obligatoria).
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "auditoria"))
import registrar_lectura as rl


def test_cubre_seccion_explicita_por_subseccion():
    # Leer §11.2 cubre el requisito §11 (semantica jerarquica).
    leidas = {("2", "11.2")}
    assert rl.cubre("2", "11", leidas) is True


def test_cubre_seccion_exacta():
    leidas = {("6", "5.3")}
    assert rl.cubre("6", "5.3", leidas) is True


def test_cubre_falla_si_seccion_no_leida():
    leidas = {("6", "5.3")}
    assert rl.cubre("6", "1.3", leidas) is False
    assert rl.cubre("3", "5.3", leidas) is False


def test_cubre_manual_entero_exige_seccion_concreta():
    # Anti-no-op: requisito "Manual 1" (sin §) NO se satisface registrando
    # el manual sin seccion; exige al menos una seccion concreta leida.
    leidas_solo_manual = {("1", "")}
    assert rl.cubre("1", "", leidas_solo_manual) is False
    leidas_con_seccion = {("1", "4")}
    assert rl.cubre("1", "", leidas_con_seccion) is True


def test_cubre_manual_entero_distinto_no_cubre():
    leidas = {("2", "8")}
    assert rl.cubre("1", "", leidas) is False
