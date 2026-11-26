# tests/auditoria/test_oraculos_config_ruta.py
# Oraculo del ME config_ruta_absoluta — H-EOF-3 (deuda de ME eof_cierre_chat, R155).
# OBL-CFG-R1 | Manual 7 §2.1 | la config del cwd se resuelve relativa→absoluta y el
# sandbox de std.sistema funciona de verdad (antes rechazaba TODAS las rutas:
# relativas por longitud, absolutas por separador '/' vs '\') | unit | TDD
"""
Requisitos:
1. Ejecutar desde la raiz del repo: .venv/Scripts/python.exe -m pytest tests/auditoria/test_oraculos_config_ruta.py -v
2. H-EOF-3 (hallazgo de ME eof_cierre_chat): `leer_modo_config` leía
   ARCHIVO_CONFIG = ".synapse_config" RELATIVO vía std.sistema, cuyo sandbox
   `_validar_ruta_segura` lo rechazaba SIEMPRE (el comparador exige contener al
   cwd como prefijo) → la config del cwd era invisible y el modo venía de los
   fallbacks HOME/Program Files; el menú de bienvenida era inrunnable en
   instalación pre-configurada.
3. Hallazgos estructurales reparados (H-EOF-3a/b):
   a) `_syn_normalizar_ruta` emitía '/' pero el cwd de Windows trae '\' → el
      comparador por prefijo nunca matcheaba NI para absolutas: sandbox teatro
      (todo consumidor real usa bypass inseguro/asm).
   b) `_syn_ruta_en_directorio` comparaba con memcmp ciego: 'proyecto_evil'
      pasaba como hijo de 'proyecto' en POSIX; sin borde de componente.
   c) (H-CFG-2, REGISTRADO, no se repara aquí) `leer_archivo`/`existe_archivo`
      son BUILTINS del S1 Python (semantic_scope.py:53-56, decisión ratificada
      H-R153-2 citando Manual 2 §4.3) que delegan directo en el runtime SIN
      pasar por el sandbox de std.sistema; `escribir_archivo`/`eliminar_archivo`
      sí lo pasan. El probe verifica lo que el sandbox gobierna (escrituras) y
      el roundtrip con la ruta relativa del config.
4. Este oraculo ejercita el pipeline REAL: el probe .syn se compila con
   `python main.py` (pipeline Python S1; la ruta nativa stage1/stage2 hornea el
   main del compilador nucleo — producira OTRO compilador, no un probe) y
   OpenSyn se compila igual (R158). Aislamiento: cwd/USERPROFILE/HOME virtuales
   (leccion R145: el binario muta config).
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

RAIZ = Path(__file__).resolve().parents[2]
PRINCIPAL = RAIZ / "opensyn" / "principal.syn"
PROBE = RAIZ / "tests" / "fixtures" / "probe_config_ruta" / "probe_config_ruta.syn"
PYTHON = sys.executable


def _fuente() -> str:
    return PRINCIPAL.read_text(encoding="utf-8")


def _fuente_sistema() -> str:
    return (RAIZ / "std" / "sistema.syn").read_text(encoding="utf-8")


def test_estructural_sandbox_runtime_normaliza_separador_y_borde():
    """OBL-CFG-R1a (anti-sniff): el runtime emite separador de plataforma en
    _syn_normalizar_ruta y el comparador exige borde de componente."""
    c = (RAIZ / "runtime" / "core" / "sistema.c").read_text(encoding="utf-8")
    # Separador de plataforma condicionado (H-EOF-3a)
    assert "sep = '\\\\'" in c and "#ifdef _WIN32" in c, (
        "normalizador sin separador de plataforma: el sandbox sigue teatro"
    )
    # Borde de componente (H-EOF-3b): el siguiente carácter tras el prefijo
    # debe ser separador (o dir termina en separador / ruta == dir)
    assert "nx == '/' || nx == '\\\\'" in c, (
        "comparador sin borde de componente: prefijo hermano pasa como hijo"
    )
    # Punto de montaje distinto rechazado (D:\x vs C:\y)
    assert "if (a != b) return 0;" in c


def test_estructural_sistema_syn_normaliza_cwd_y_contratos():
    """OBL-CFG-R1b: std.sistema resuelve la relativa contra el cwd NORMALIZADO
    antes de comparar y la función lleva contratos requiere/garantiza."""
    f = _fuente_sistema()
    assert "_syn_normalizar_ruta(_syn_obtener_cwd())" in f, (
        "el cwd crudo ('\\' en Windows) se compara contra salida normalizada"
    )
    assert "requiere:" in f and "garantiza:" in f, (
        "contratos M2 §5.1 ausentes en _validar_ruta_segura"
    )
    # Resolucion relativa→absoluta ANTES de normalizar (el normalizador no
    # antepone el cwd por sí solo)
    assert 'concat(concat(cwd, "/"), ruta)' in f, (
        "la ruta relativa no se resuelve contra el cwd"
    )


def test_estructural_principal_ruta_config_absoluta_en_leer_y_guardar():
    """OBL-CFG-R1c: principal.syn define ruta_config_absoluta() y la usa en
    leer_modo_config Y guardar_modo_config (roundtrip coherente)."""
    f = _fuente()
    assert "funcion ruta_config_absoluta() -> texto:" in f
    assert "leer_archivo(ruta_config_absoluta())" in f, (
        "leer_modo_config sigue leyendo la ruta relativa rechazada (H-EOF-3)"
    )
    assert "escribir_archivo(ruta_config_absoluta(), linea)" in f, (
        "guardar_modo_config sigue escribiendo la ruta relativa rechazada"
    )


@pytest.fixture(scope="module")
def probe_exe():
    """Compila el probe UNA vez con el pipeline real (python main.py)."""
    out_dir = Path(tempfile.mkdtemp(prefix="cfg_ruta_probe_"))
    exe = out_dir / "probe_config_ruta.exe"
    p = subprocess.run(
        [str(PYTHON), str(RAIZ / "main.py"), str(PROBE), "-o", str(exe)],
        capture_output=True, text=True, cwd=RAIZ, timeout=900,
        encoding="utf-8", errors="replace",
    )
    assert p.returncode == 0, (
        f"Compilacion del probe fallo: {p.stdout[-2000:]} {p.stderr[-2000:]}"
    )
    assert exe.exists(), "El binario del probe no fue generado"
    yield exe
    shutil.rmtree(out_dir, ignore_errors=True)


@pytest.mark.slow
@pytest.mark.timeout(300)
def test_probe_sandbox_roundtrip_relativo_y_escape(tmp_path, probe_exe):
    """OBL-CFG-R2 (E2E del sandbox): con cwd temporal, la escritura relativa
    funciona y hace roundtrip; el escape ../.. se rechaza; la escritura
    absoluta fuera del cwd se rechaza. Antes del fix: escribir relativa
    devolvia -1 SIEMPRE (rc 1 del probe)."""
    cwd_tmp = tmp_path / "cwd"
    cwd_tmp.mkdir()
    # El probe intenta escribir FUERA del cwd via ruta absoluta cwd/../probe
    # (rc 3 = fuga del sandbox). No hay archivo pre-creado: el check es que el
    # sandbox RECHACE la escritura, no que el runtime no pueda escribirla.
    p = subprocess.run(
        [str(probe_exe)],
        capture_output=True, text=True, cwd=cwd_tmp, timeout=120,
        encoding="utf-8", errors="replace",
    )
    assert p.returncode == 0, (
        f"Probe rc={p.returncode} (1=relativa rechazada, 2=traversal abierto, "
        f"3=fuga de escritura absoluta): {p.stdout[-500:]} {p.stderr[-300:]}"
    )
    assert "[PROBE] OK" in p.stdout
    # El archivo relativo se materializo DENTRO del cwd (no en la raiz del tmp)
    assert (cwd_tmp / "probe_cfg_ruta.txt").exists(), (
        "el roundtrip relativo no se materializo en el cwd"
    )


@pytest.fixture(scope="module")
def opensyn_exe():
    """Compila OpenSyn UNA vez con su pipeline real (python main.py, R158)."""
    out_dir = Path(tempfile.mkdtemp(prefix="cfg_ruta_opensyn_"))
    exe = out_dir / "opensyn_cfg_probe.exe"
    p = subprocess.run(
        [str(PYTHON), str(RAIZ / "main.py"), str(PRINCIPAL), "-o", str(exe)],
        capture_output=True, text=True, cwd=RAIZ, timeout=900,
        encoding="utf-8", errors="replace",
    )
    assert p.returncode == 0, (
        f"Compilacion de opensyn/principal.syn fallo: {p.stdout[-2000:]} {p.stderr[-2000:]}"
    )
    assert exe.exists(), "El binario de OpenSyn no fue generado"
    yield exe
    shutil.rmtree(out_dir, ignore_errors=True)


@pytest.mark.slow
@pytest.mark.timeout(300)
def test_e2e_config_cwd_decide_el_modo(tmp_path, monkeypatch, opensyn_exe):
    """OBL-CFG-R3 (H-EOF-3 cerrado de verdad): OpenSyn con config RELATIVA en el
    cwd ('modo_oraculo=falso') debe entrar en Modo Lenguaje Puro SIN menú y sin
    tocar los fallbacks. Antes: la lectura relativa devolvia '' y el modo
    venia del fallback HOME/Program Files (menú inrunnable en instalación
    pre-configurada — skip del E2E del menú).
    Atribución válida incluso con instalación en Program Files presente: la
    config del cwd se consulta PRIMERO (leer_modo_config paso 1); si la lectura
    relativa falla, el fallback PF decide (config 'modo_oraculo=verdadero' →
    Modo Oraculo) y el assert falla — el fallback hace detectable la rotura,
    no enmascara el fix. Sin SKIP: un skip invalidaría este oráculo como
    evidencia (leccion R155: SKIP != oráculo ejecutado)."""
    exe = opensyn_exe
    cwd_tmp = tmp_path / "cwd"
    home_tmp = tmp_path / "home"
    cwd_tmp.mkdir()
    home_tmp.mkdir()
    # Config RELATIVA del cwd (sin newline: leer_modo_config compara exacto)
    (cwd_tmp / ".synapse_config").write_text(
        "modo_oraculo=falso", encoding="utf-8"
    )
    monkeypatch.setenv("USERPROFILE", str(home_tmp))
    monkeypatch.setenv("HOME", str(home_tmp))
    p = subprocess.run(
        [str(exe)],
        input="\n",
        capture_output=True, text=True, cwd=cwd_tmp, timeout=120,
        encoding="utf-8", errors="replace",
    )
    assert p.returncode == 0, f"rc={p.returncode}: {p.stdout[-500:]}"
    assert "Modo: Lenguaje Puro" in p.stdout, (
        f"H-EOF-3 regreso: la config del cwd no decidio el modo. "
        f"Salida: {p.stdout[-500:]}"
    )
    assert "Opcion" not in p.stdout, "El menu de bienvenida NO debio aparecer"
