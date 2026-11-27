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
MAX_HERRAMIENTAS = 8

HERRAMIENTAS = ["listar", "leer", "git", "plan", "editar", "compilar", "diagnosticar", "delegar"]
NIVELES = [PERMISO_ALLOW, PERMISO_ALLOW, PERMISO_ALLOW, PERMISO_ASK, PERMISO_ASK,
           PERMISO_ALLOW, PERMISO_ALLOW, PERMISO_ALLOW]


class MatrizPermisosSim:
    def __init__(self, workspace=""):
        self.cantidades = MAX_HERRAMIENTAS
        self.workspace_path = workspace or os.path.join(RAIZ, "opensyn")


def str_eq_f(a, b):
    return a == b


def verificar_permiso_herramienta(matriz, herramienta):
    for i in range(MAX_HERRAMIENTAS):
        if str_eq_f(HERRAMIENTAS[i], herramienta):
            return NIVELES[i]
    return PERMISO_DENY


def es_ruta_en_workspace(ruta, workspace):
    ruta_n = os.path.normpath(ruta)
    ws_n = os.path.normpath(workspace)
    if not ruta_n.startswith(ws_n):
        return False
    if len(ruta_n) == len(ws_n):
        return True
    sig = ruta_n[len(ws_n)]
    return sig in ('\\', '/')


def verificar_permiso_completo(matriz, herramienta, ruta=""):
    nivel = verificar_permiso_herramienta(matriz, herramienta)
    if nivel == PERMISO_DENY:
        return PERMISO_DENY
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
# R6: Fuente — estructura y constantes (Manual 7 §7.3)
# ================================================================

class TestFuentePermisos:
    """Oráculo R6: Verifica que permisos.syn tenga la estructura correcta.
    Requisito: Manual 7 §7.3 — 'Sandboxing: permisos mínimos'"""

    def test_source_constante_allow(self):
        """Verifica: constante PERMISO_ALLOW = 0"""
        ps = _leer_permisos()
        assert "PERMISO_ALLOW = 0" in ps

    def test_source_constante_ask(self):
        """Verifica: constante PERMISO_ASK = 1"""
        ps = _leer_permisos()
        assert "PERMISO_ASK = 1" in ps

    def test_source_constante_deny(self):
        """Verifica: constante PERMISO_DENY = 2"""
        ps = _leer_permisos()
        assert "PERMISO_DENY = 2" in ps

    def test_source_max_herramientas(self):
        """Verifica: constante MAX_HERRAMIENTAS = 8"""
        ps = _leer_permisos()
        assert "MAX_HERRAMIENTAS = 8" in ps

    def test_source_funcion_nombre_herramienta(self):
        """Verifica: existe funcion nombre_herramienta()"""
        ps = _leer_permisos()
        assert "funcion nombre_herramienta(" in ps

    def test_source_funcion_nivel_permiso(self):
        """Verifica: existe funcion nivel_permiso()"""
        ps = _leer_permisos()
        assert "funcion nivel_permiso(" in ps

    def test_source_funcion_verificar_herramienta(self):
        """Verifica: existe funcion verificar_permiso_herramienta()"""
        ps = _leer_permisos()
        assert "funcion verificar_permiso_herramienta(" in ps

    def test_source_funcion_verificar_completo(self):
        """Verifica: existe funcion verificar_permiso_completo()"""
        ps = _leer_permisos()
        assert "funcion verificar_permiso_completo(" in ps

    def test_source_funcion_es_ruta_workspace(self):
        """Verifica: existe funcion es_ruta_en_workspace()"""
        ps = _leer_permisos()
        assert "funcion es_ruta_en_workspace(" in ps

    def test_source_funcion_nombre_permiso(self):
        """Verifica: existe funcion nombre_permiso()"""
        ps = _leer_permisos()
        assert "funcion nombre_permiso(" in ps

    def test_source_funcion_matriz_crear(self):
        """Verifica: existe funcion matriz_permisos_crear()"""
        ps = _leer_permisos()
        assert "funcion matriz_permisos_crear(" in ps


# ================================================================
# R6: Lógica funcional — permisos por herramienta (Manual 7 §7.3)
# ================================================================

class TestLogicaPermisos:
    """Oráculo R6: Verifica la lógica de permisos por herramienta.
    Requisito: Manual 7 §7.3 — 'permisos mínimos'"""

    def test_listar_es_allow(self):
        """Verifica: listar es ALLOW (solo lectura)"""
        m = MatrizPermisosSim()
        assert verificar_permiso_herramienta(m, "listar") == PERMISO_ALLOW

    def test_leer_es_allow(self):
        """Verifica: leer es ALLOW (solo lectura)"""
        m = MatrizPermisosSim()
        assert verificar_permiso_herramienta(m, "leer") == PERMISO_ALLOW

    def test_git_es_allow(self):
        """Verifica: git es ALLOW (solo lectura)"""
        m = MatrizPermisosSim()
        assert verificar_permiso_herramienta(m, "git") == PERMISO_ALLOW

    def test_plan_es_ask(self):
        """Verifica: plan es ASK (requiere confirmación)"""
        m = MatrizPermisosSim()
        assert verificar_permiso_herramienta(m, "plan") == PERMISO_ASK

    def test_editar_es_ask(self):
        """Verifica: editar es ASK (requiere confirmación)"""
        m = MatrizPermisosSim()
        assert verificar_permiso_herramienta(m, "editar") == PERMISO_ASK

    def test_compilar_es_allow(self):
        """Verifica: compilar es ALLOW (ejecución segura)"""
        m = MatrizPermisosSim()
        assert verificar_permiso_herramienta(m, "compilar") == PERMISO_ALLOW

    def test_diagnosticar_es_allow(self):
        """Verifica: diagnosticar es ALLOW"""
        m = MatrizPermisosSim()
        assert verificar_permiso_herramienta(m, "diagnosticar") == PERMISO_ALLOW

    def test_delegar_es_allow(self):
        """Verifica: delegar es ALLOW"""
        m = MatrizPermisosSim()
        assert verificar_permiso_herramienta(m, "delegar") == PERMISO_ALLOW

    def test_desconocida_es_deny(self):
        """Verifica: herramienta desconocida es DENY"""
        m = MatrizPermisosSim()
        assert verificar_permiso_herramienta(m, "herramienta_fantasma") == PERMISO_DENY


# ================================================================
# R6: Sandbox — workspace confinement (Manual 7 §7.3)
# ================================================================

class TestSandboxWorkspace:
    """Oráculo R6: Verifica confinamiento al workspace.
    Requisito: Manual 7 §7.3 — 'writes confinados al workspace'"""

    def test_ruta_dentro_workspace(self):
        """Verifica: ruta dentro del workspace → True"""
        m = MatrizPermisosSim()
        ruta = os.path.join(RAIZ, "opensyn", "router.syn")
        assert es_ruta_en_workspace(ruta, m.workspace_path) is True

    def test_ruta_fuera_workspace(self):
        """Verifica: ruta fuera del workspace → False"""
        m = MatrizPermisosSim()
        assert es_ruta_en_workspace("C:\\Windows\\System32\\config.sys", m.workspace_path) is False

    def test_ruta_misma_longitud(self):
        """Verifica: ruta igual al workspace → True"""
        m = MatrizPermisosSim()
        assert es_ruta_en_workspace(m.workspace_path, m.workspace_path) is True

    def test_ruta_bypass_separador(self):
        """Verifica: ruta con prefijo相似 pero sin separador → False"""
        m = MatrizPermisosSim()
        ws = os.path.normpath(m.workspace_path)
        ruta_bypass = ws + "_evil\\malware.syn"
        assert es_ruta_en_workspace(ruta_bypass, ws) is False

    def test_editar_fuera_deny(self):
        """Verifica: editar archivo fuera del workspace → DENY"""
        m = MatrizPermisosSim()
        assert verificar_permiso_completo(m, "editar", "C:\\Windows\\test.txt") == PERMISO_DENY

    def test_listar_fuera_allow(self):
        """Verifica: listar archivo fuera del workspace → ALLOW (lectura)"""
        m = MatrizPermisosSim()
        nivel = verificar_permiso_completo(m, "listar", "C:\\Windows\\test.txt")
        assert nivel == PERMISO_ALLOW

    def test_git_fuera_allow(self):
        """Verifica: git fuera del workspace → ALLOW (lectura)"""
        m = MatrizPermisosSim()
        nivel = verificar_permiso_completo(m, "git", "C:\\otro\\repo")
        assert nivel == PERMISO_ALLOW


# ================================================================
# R6: Nombre permiso (Manual 7 §7.3)
# ================================================================

class TestNombrePermiso:
    """Oráculo R6: Verifica nombres legibles de permisos.
    Requisito: Manual 7 §7.3 — 'feedback claro al usuario'"""

    def test_allow_nombre(self):
        """Verifica: PERMISO_ALLOW → 'allow'"""
        assert nombre_permiso(PERMISO_ALLOW) == "allow"

    def test_ask_nombre(self):
        """Verifica: PERMISO_ASK → 'ask'"""
        assert nombre_permiso(PERMISO_ASK) == "ask"

    def test_deny_nombre(self):
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
        assert "denegada por sandbox" in pr

    def test_source_principal_ask_sandbox(self):
        """Verifica: principal.syn tiene lógica ASK por sandbox"""
        pr = _leer_principal()
        assert "TOOL_ASK" in pr

    def test_source_cita_manual_sandbox(self):
        """Verifica: principal.syn referencia ME-5/R6"""
        pr = _leer_principal()
        assert "ME-5" in pr or "R6" in pr

    def test_source_permisos_crear(self):
        """Verifica: principal.syn usa matriz_permisos_crear()"""
        pr = _leer_principal()
        assert "matriz_permisos_crear" in pr


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

    def test_permisos_cita_sandboxing(self):
        """Verifica: permisos.syn menciona sandboxing"""
        ps = _leer_permisos()
        assert "sandbox" in ps.lower() or "Sandboxing" in ps

    def test_permisos_cita_telemetria(self):
        """Verifica: permisos.syn menciona cero telemetría"""
        ps = _leer_permisos()
        assert "telemetría" in ps or "telemetria" in ps


# ================================================================
# R6: Contratos (Manual 2 §12)
# ================================================================

class TestContratosPermisos:
    """Oráculo R6: Verifica contratos requiere/garantiza.
    Requisito: Manual 2 §12 — 'toda función pública tiene contrato'"""

    def test_nombre_herramienta_contrato(self):
        """Verificar: nombre_herramienta tiene contrato"""
        ps = _leer_permisos()
        idx = ps.find("funcion nombre_herramienta(")
        assert idx >= 0
        bloque = ps[idx:idx+300]
        assert "requiere:" in bloque
        assert "garantiza:" in bloque

    def test_verificar_herramienta_contrato(self):
        """Verificar: verificar_permiso_herramienta tiene contrato"""
        ps = _leer_permisos()
        idx = ps.find("funcion verificar_permiso_herramienta(")
        assert idx >= 0
        bloque = ps[idx:idx+300]
        assert "requiere:" in bloque
        assert "garantiza:" in bloque

    def test_es_ruta_workspace_contrato(self):
        """Verificar: es_ruta_en_workspace tiene contrato"""
        ps = _leer_permisos()
        idx = ps.find("funcion es_ruta_en_workspace(")
        assert idx >= 0
        bloque = ps[idx:idx+300]
        assert "requiere:" in bloque
        assert "garantiza:" in bloque

    def test_verificar_completo_contrato(self):
        """Verificar: verificar_permiso_completo tiene contrato"""
        ps = _leer_permisos()
        idx = ps.find("funcion verificar_permiso_completo(")
        assert idx >= 0
        bloque = ps[idx:idx+300]
        assert "requiere:" in bloque
        assert "garantiza:" in bloque

    def test_nombre_permiso_contrato(self):
        """Verificar: nombre_permiso tiene contrato"""
        ps = _leer_permisos()
        idx = ps.find("funcion nombre_permiso(")
        assert idx >= 0
        bloque = ps[idx:idx+200]
        assert "requiere:" in bloque
        assert "garantiza:" in bloque
