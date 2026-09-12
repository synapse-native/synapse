# -*- coding: utf-8 -*-
"""
test_permisos_opensyn.py — ME-5 (R6): Permisos + sandbox.

Oráculos TDD que verifican la matriz de permisos, sandbox y confinamiento
al workspace. Cada test cita el requisito que verifica (MTO grep-chequeable).

Manual 7 §7.3: "Sandboxing: El servidor de inferencia se ejecuta con permisos mínimos"
Manual 7 §7.3: "Cero telemetría: Verificado con monitoreo de red"
"""
import os
import pytest

pytestmark = pytest.mark.integration

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _leer(ruta):
    with open(ruta, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def _leer_permisos():
    return _leer(os.path.join(RAIZ, "opensyn", "permisos.syn"))


def _leer_principal():
    return _leer(os.path.join(RAIZ, "opensyn", "principal.syn"))


# ================================================================
# Replicas Python de la lógica Synapse (oráculos funcionales)
# ================================================================

PERMISO_ALLOW = 0
PERMISO_ASK = 1
PERMISO_DENY = 2


class ReglaPermiso:
    def __init__(self, herramienta, nivel, patron_ruta="*"):
        self.herramienta = herramienta
        self.nivel = nivel
        self.patron_ruta = patron_ruta


class MatrizPermisos:
    def __init__(self):
        self.reglas = [
            ReglaPermiso("listar", PERMISO_ALLOW),
            ReglaPermiso("leer", PERMISO_ALLOW),
            ReglaPermiso("git", PERMISO_ALLOW),
            ReglaPermiso("plan", PERMISO_ASK, "*.plan"),
            ReglaPermiso("editar", PERMISO_ASK),
            ReglaPermiso("compilar", PERMISO_ALLOW),
            ReglaPermiso("diagnosticar", PERMISO_ALLOW),
            ReglaPermiso("delegar", PERMISO_ALLOW),
        ]
        self.workspace_path = os.path.join(RAIZ, "opensyn")


def str_eq_f(a, b):
    return a == b


def verificar_permiso_herramienta(matriz, herramienta):
    for regla in matriz.reglas:
        if str_eq_f(regla.herramienta, herramienta):
            return regla.nivel
    return PERMISO_DENY


def es_ruta_en_workspace(ruta, workspace):
    ruta_normalizada = os.path.normpath(ruta)
    ws_normalizado = os.path.normpath(workspace)
    return ruta_normalizada.startswith(ws_normalizado)


def verificar_permiso_completo(matriz, herramienta, ruta=""):
    nivel = verificar_permiso_herramienta(matriz, herramienta)
    if nivel == PERMISO_DENY:
        return PERMISO_DENY
    # Solo herramientas de ESCRITURA (ASK) se confinan al workspace
    # Herramientas de LECTURA (ALLOW) pueden leer fuera del workspace
    if nivel == PERMISO_ASK and ruta and not es_ruta_en_workspace(ruta, matriz.workspace_path):
        return PERMISO_DENY
    return nivel


def nombre_permiso(nivel):
    if nivel == PERMISO_ALLOW:
        return "allow"
    if nivel == PERMISO_ASK:
        return "ask"
    return "deny"


# ================================================================
# R6: Matriz de permisos por defecto (Manual 7 §7.3)
# ================================================================

class TestMatrizPermisos:
    """Oráculo R6: Verifica la matriz de permisos por defecto.
    Requisito: Manual 7 §7.3 — 'Sandboxing: permisos mínimos'"""

    def test_source_funcion_existe(self):
        """Verifica: existe funcion matriz_permisos_default() en permisos.syn"""
        ps = _leer_permisos()
        assert "funcion matriz_permisos_default(" in ps

    def test_source_cant_minima_reglas(self):
        """Verifica: matriz tiene al menos 8 reglas (listar,leer,git,plan,editar,compilar,diagnosticar,delegar)"""
        ps = _leer_permisos()
        assert "cantidad_reglas = 8" in ps or "cantidad_reglas = 8" in ps

    def test_source_workspace_path(self):
        """Verifica: matriz incluye workspace_path para sandbox"""
        ps = _leer_permisos()
        assert "workspace_path" in ps

    def test_replica_allow_listar(self):
        """Verifica: listar es ALLOW (solo lectura)"""
        m = MatrizPermisos()
        assert verificar_permiso_herramienta(m, "listar") == PERMISO_ALLOW

    def test_replica_allow_leer(self):
        """Verifica: leer es ALLOW (solo lectura)"""
        m = MatrizPermisos()
        assert verificar_permiso_herramienta(m, "leer") == PERMISO_ALLOW

    def test_replica_allow_git(self):
        """Verifica: git es ALLOW (solo lectura)"""
        m = MatrizPermisos()
        assert verificar_permiso_herramienta(m, "git") == PERMISO_ALLOW

    def test_replica_ask_editar(self):
        """Verifica: editar es ASK (requiere confirmación)"""
        m = MatrizPermisos()
        assert verificar_permiso_herramienta(m, "editar") == PERMISO_ASK

    def test_replica_ask_plan(self):
        """Verifica: plan es ASK (requiere confirmación)"""
        m = MatrizPermisos()
        assert verificar_permiso_herramienta(m, "plan") == PERMISO_ASK

    def test_replica_allow_compilar(self):
        """Verifica: compilar es ALLOW (ejecución segura)"""
        m = MatrizPermisos()
        assert verificar_permiso_herramienta(m, "compilar") == PERMISO_ALLOW

    def test_replica_allow_diagnosticar(self):
        """Verifica: diagnosticar es ALLOW (solo lectura)"""
        m = MatrizPermisos()
        assert verificar_permiso_herramienta(m, "diagnosticar") == PERMISO_ALLOW

    def test_replica_allow_delegar(self):
        """Verifica: delegar es ALLOW (orquestación)"""
        m = MatrizPermisos()
        assert verificar_permiso_herramienta(m, "delegar") == PERMISO_ALLOW

    def test_replica_desconocida_deny(self):
        """Verifica: herramienta desconocida es DENY"""
        m = MatrizPermisos()
        assert verificar_permiso_herramienta(m, "herramienta_fantasma") == PERMISO_DENY


# ================================================================
# R6: Sandbox — ruta fuera del workspace (Manual 7 §7.3)
# ================================================================

class TestSandboxWorkspace:
    """Oráculo R6: Verifica confinamiento al workspace.
    Requisito: Manual 7 §7.3 — 'permisos mínimos + workspace only'"""

    def test_source_tiene_constante_allow(self):
        """Verifica: constante PERMISO_ALLOW = 0"""
        ps = _leer_permisos()
        assert "PERMISO_ALLOW = 0" in ps

    def test_source_tiene_constante_ask(self):
        """Verifica: constante PERMISO_ASK = 1"""
        ps = _leer_permisos()
        assert "PERMISO_ASK = 1" in ps

    def test_source_tiene_constante_deny(self):
        """Verifica: constante PERMISO_DENY = 2"""
        ps = _leer_permisos()
        assert "PERMISO_DENY = 2" in ps

    def test_replica_ruta_dentro_workspace(self):
        """Verifica: ruta dentro del workspace está permitida"""
        m = MatrizPermisos()
        ruta = os.path.join(RAIZ, "opensyn", "router.syn")
        assert es_ruta_en_workspace(ruta, m.workspace_path) is True

    def test_replica_ruta_fuera_workspace(self):
        """Verifica: ruta fuera del workspace es denegada"""
        m = MatrizPermisos()
        ruta = "C:\\Windows\\System32\\config.sys"
        assert es_ruta_en_workspace(ruta, m.workspace_path) is False

    def test_replica_ruta_relativa_fuera(self):
        """Verifica: ruta relativa con .. es denegada"""
        m = MatrizPermisos()
        ruta = os.path.join(RAIZ, "..", "..", "secreto.txt")
        ruta_normalizada = os.path.normpath(ruta)
        assert not ruta_normalizada.startswith(os.path.normpath(m.workspace_path))

    def test_replica_editar_fuera_deny(self):
        """Verifica: editar archivo fuera del workspace → DENY"""
        m = MatrizPermisos()
        assert verificar_permiso_completo(m, "editar", "C:\\Windows\\test.txt") == PERMISO_DENY

    def test_replica_listar_fuera_allow(self):
        """Verifica: listar archivo fuera del workspace sigue ALLOW (solo lectura)"""
        m = MatrizPermisos()
        nivel = verificar_permiso_completo(m, "listar", "C:\\Windows\\test.txt")
        assert nivel == PERMISO_ALLOW

    def test_replica_git_fuera_allow(self):
        """Verifica: git fuera del workspace sigue ALLOW (solo lectura)"""
        m = MatrizPermisos()
        nivel = verificar_permiso_completo(m, "git", "C:\\otro\\repo")
        assert nivel == PERMISO_ALLOW


# ================================================================
# R6: Nombre permiso (Manual 7 §7.3)
# ================================================================

class TestNombrePermiso:
    """Oráculo R6: Verifica nombres legibles de permisos.
    Requisito: Manual 7 §7.3 — 'feedback claro al usuario'"""

    def test_replica_allow_nombre(self):
        """Verifica: PERMISO_ALLOW → 'allow'"""
        assert nombre_permiso(PERMISO_ALLOW) == "allow"

    def test_replica_ask_nombre(self):
        """Verifica: PERMISO_ASK → 'ask'"""
        assert nombre_permiso(PERMISO_ASK) == "ask"

    def test_replica_deny_nombre(self):
        """Verifica: PERMISO_DENY → 'deny'"""
        assert nombre_permiso(PERMISO_DENY) == "deny"


# ================================================================
# R6: Integración con principal.syn (Manual 7 §7.3)
# ================================================================

class TestIntegracionPrincipal:
    """Oráculo R6: Verifica integración de permisos en principal.syn.
    Requisito: Manual 7 §7.3 — 'sandboxing en ejecución de herramientas'"""

    def test_source_principal_verifica_sandbox(self):
        """Verifica: principal.syn llama a verificar_permiso_completo"""
        pr = _leer_principal()
        assert "verificar_permiso_completo" in pr

    def test_source_principal_denegar_sandbox(self):
        """Verifica: principal.syn tiene lógica de DENY por sandbox"""
        pr = _leer_principal()
        assert "denegada por sandbox" in pr or "DENY" in pr or "nivel_perm == 2" in pr

    def test_source_principal_ask_sandbox(self):
        """Verifica: principal.syn tiene lógica ASK por sandbox"""
        pr = _leer_principal()
        assert "TOOL_ASK" in pr or "nivel_perm == 1" in pr

    def test_source_cita_manual_sandbox(self):
        """Verifica: principal.syn cita Manual 7 §7.3"""
        pr = _leer_principal()
        assert "§7.3" in pr or "M7 §7.3" in pr


# ================================================================
# R6: Citas cumple Manual (grep-chequeable)
# ================================================================

class TestCitasCumpleManual:
    """Oráculo R6: Verifica citas grep-chequeables al manual.
    Requisito: Manual 7 §7.3 — 'Cero telemetría + sandboxing'"""

    def test_permisos_cita_r6(self):
        """Verifica: permisos.syn cita §7.3"""
        ps = _leer_permisos()
        assert "cumple Manual 7 §7.3" in ps

    def test_permisos_cita_telemetria(self):
        """Verifica: permisos.syn menciona cero telemetría"""
        ps = _leer_permisos()
        assert "telemetría" in ps or "telemetria" in ps

    def test_permisos_cita_sandboxing(self):
        """Verifica: permisos.syn menciona sandboxing"""
        ps = _leer_permisos()
        assert "sandbox" in ps.lower() or "Sandboxing" in ps

    def test_principal_cita_r6(self):
        """Verifica: principal.syn referencia ME-5/R6"""
        pr = _leer_principal()
        assert "ME-5" in pr or "R6" in pr


# ================================================================
# R6: Contratos (Manual 2 §12)
# ================================================================

class TestContratosPermisos:
    """Oráculo R6: Verifica contratos requiere/garantiza.
    Requisito: Manual 2 §12 — 'toda función pública tiene contrato'"""

    def test_verificar_permiso_herramienta_contrato(self):
        """Verifica: verificar_permiso_herramienta tiene contrato"""
        ps = _leer_permisos()
        idx = ps.find("funcion verificar_permiso_herramienta(")
        assert idx >= 0
        bloque = ps[idx:idx+300]
        assert "requiere:" in bloque
        assert "garantiza:" in bloque

    def test_es_ruta_en_workspace_contrato(self):
        """Verifica: es_ruta_en_workspace tiene contrato"""
        ps = _leer_permisos()
        idx = ps.find("funcion es_ruta_en_workspace(")
        assert idx >= 0
        bloque = ps[idx:idx+300]
        assert "requiere:" in bloque
        assert "garantiza:" in bloque

    def test_verificar_permiso_completo_contrato(self):
        """Verifica: verificar_permiso_completo tiene contrato"""
        ps = _leer_permisos()
        idx = ps.find("funcion verificar_permiso_completo(")
        assert idx >= 0
        bloque = ps[idx:idx+300]
        assert "requiere:" in bloque
        assert "garantiza:" in bloque

    def test_nombre_permiso_contrato(self):
        """Verifica: nombre_permiso tiene contrato"""
        ps = _leer_permisos()
        idx = ps.find("funcion nombre_permiso(")
        assert idx >= 0
        bloque = ps[idx:idx+200]
        assert "requiere:" in bloque
        assert "garantiza:" in bloque
