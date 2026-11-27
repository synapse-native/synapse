# -*- coding: utf-8 -*-
"""test_opensyn_e2e_local.py — r275: E2E real y benchmark local de OpenSyn.

cumple Manual 7 §7.2, §7.3, §8; Manual 9 §5.5.

Opt-in: `OPENSYN_E2E=1`. Resuelve `llama-server` y un GGUF locales; si faltan,
hace skip con causa explícita (CI sin modelo no finge verde). Con ellos:

1. Levanta `llama-server` en loopback y ejecuta un chat real
   (`/v1/chat/completions`), midiendo latencia, tokens/s y VRAM.
2. Valida código generado con el compilador real (`synapse check --no-emit`).
3. Ejecuta una sonda compilada contra `opensyn/permisos.syn` para probar el
   sandbox de herramientas: editar dentro = ASK, editar fuera = DENY,
   leer dentro = ALLOW.
4. Monitorea las conexiones de `opensyn.exe doctor` y exige solo loopback.

El binario nativo S2 no compila hoy la sonda de `permisos.syn` (str_eq sobre
texto indexado); la sonda se compila con S1 (`main.py`) y se registra el
hallazgo. La validación de código sí usa el binario nativo real.
"""
import json
import os
import platform
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
PYTHON = sys.executable

pytestmark = [pytest.mark.integration, pytest.mark.e2e, pytest.mark.opensyn]


def _activo():
    return os.environ.get("OPENSYN_E2E", "").strip().lower() in ("1", "true", "yes", "si")


def _resolver_llama():
    candidatos = []
    if os.environ.get("OPENSYN_LLAMA_SERVER"):
        candidatos.append(Path(os.environ["OPENSYN_LLAMA_SERVER"]))
    candidatos += [
        RAIZ / "dist" / "opensyn" / "ia" / "llama-server.exe",
        RAIZ / "dist" / "ia" / "llama-server.exe",
        Path.home() / ".opensyn" / "ia" / "llama-server.exe",
        RAIZ / "dist" / "opensyn" / "ia" / "llama-server",
        RAIZ / "dist" / "ia" / "llama-server",
        Path.home() / ".opensyn" / "ia" / "llama-server",
    ]
    for ruta in candidatos:
        if ruta.is_file():
            return ruta
    return None


def _resolver_gguf():
    if os.environ.get("OPENSYN_GGUF"):
        ruta = Path(os.environ["OPENSYN_GGUF"])
        if ruta.is_file():
            return ruta
    for directorio in (
        Path.home() / ".opensyn" / "models",
        RAIZ / "dist" / "opensyn" / "models",
        RAIZ / "dist" / "ia",
        RAIZ / "models",
    ):
        if directorio.is_dir():
            for ruta in sorted(directorio.glob("*.gguf")):
                return ruta
    return None


def _puerto_libre():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _esperar_servidor(base, proc, timeout=180):
    limite = time.time() + timeout
    while time.time() < limite:
        if proc.poll() is not None:
            salida = proc.stdout.read() if proc.stdout else ""
            pytest.fail(f"llama-server terminó antes de responder:\n{salida[-2000:]}")
        for ruta in ("/health", "/v1/models"):
            try:
                with urllib.request.urlopen(base + ruta, timeout=2) as resp:
                    if resp.status == 200:
                        return
            except (urllib.error.URLError, ConnectionError, TimeoutError):
                pass
        time.sleep(0.5)
    proc.kill()
    pytest.fail(f"llama-server no respondió en {timeout}s en {base}")


def _vram_mb():
    try:
        salida = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=10,
        )
        if salida.returncode == 0:
            return int(salida.stdout.strip().splitlines()[0])
    except (OSError, ValueError, subprocess.TimeoutExpired):
        pass
    return None


@pytest.fixture(scope="module")
def llama_local():
    if not _activo():
        pytest.skip("E2E real opt-in: exporta OPENSYN_E2E=1 y define el GGUF local")
    servidor = _resolver_llama()
    modelo = _resolver_gguf()
    if servidor is None:
        pytest.skip("llama-server no encontrado (OPENSYN_LLAMA_SERVER / dist/opensyn/ia)")
    if modelo is None:
        pytest.skip("GGUF no encontrado (OPENSYN_GGUF / ~/.opensyn/models/*.gguf)")

    puerto = _puerto_libre()
    comando = [
        str(servidor), "-m", str(modelo),
        "--host", "127.0.0.1", "--port", str(puerto),
        "--ctx-size", "2048", "--n-gpu-layers", "0", "--threads", "4",
    ]
    proc = subprocess.Popen(
        comando, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, encoding="utf-8", errors="replace",
    )
    base = f"http://127.0.0.1:{puerto}"
    _esperar_servidor(base, proc)
    yield {"base": base, "puerto": puerto, "modelo": modelo, "servidor": servidor}
    proc.terminate()
    try:
        proc.wait(timeout=15)
    except subprocess.TimeoutExpired:
        proc.kill()


def _chat(base, prompt, max_tokens=32):
    cuerpo = json.dumps({
        "model": "default",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.0,
    }).encode("utf-8")
    req = urllib.request.Request(
        base + "/v1/chat/completions", data=cuerpo,
        headers={"Content-Type": "application/json"}, method="POST",
    )
    inicio = time.perf_counter()
    with urllib.request.urlopen(req, timeout=120) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    return payload, time.perf_counter() - inicio


def test_chat_real_y_metricas(llama_local):
    """Manual 7 §7.2 + Manual 9 §5.5: consulta simple real y benchmark medido."""
    payload, latencia = _chat(llama_local["base"], "Di 'Hola' en español.")
    eleccion = (payload.get("choices") or [{}])[0]
    contenido = (eleccion.get("message") or {}).get("content", "")
    assert isinstance(contenido, str) and contenido.strip(), (
        f"respuesta vacía del servidor real: {payload!r}"
    )

    timings = payload.get("timings") or {}
    tokens = timings.get("predicted_n")
    if not tokens:
        tokens = (payload.get("usage") or {}).get("completion_tokens")
    tps = timings.get("predicted_per_second")
    if tps is None and tokens:
        tps = tokens / latencia if latencia > 0 else 0.0

    metricas = {
        "fecha": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "maquina": platform.node(),
        "plataforma": platform.platform(),
        "cpu": platform.processor(),
        "modelo": llama_local["modelo"].name,
        "servidor": str(llama_local["servidor"]),
        "puerto": llama_local["puerto"],
        "latencia_s": round(latencia, 3),
        "tokens_generados": tokens,
        "tokens_por_segundo": round(tps, 2) if tps else None,
        "vram_mb": _vram_mb(),
        "respuesta": contenido.strip()[:200],
    }
    print("[R275] " + json.dumps(metricas, ensure_ascii=False))
    # El umbral <1 s de Manual 7 §7.2 es para 7B en GPU; esta máquina corre
    # CPU con un modelo pequeño. Se mide y se reporta, no se falsifica.
    assert latencia < 120.0, f"latencia anómala {latencia:.1f}s (servidor vivo)"


def _synapse_nativo():
    for ruta in (RAIZ / "dist" / "bin" / "synapse.exe", RAIZ / "synapse.exe"):
        if ruta.is_file():
            return ruta
    return None


def test_validacion_check_no_emit(tmp_path):
    """Manual 7 §8: el código generado se valida con `synapse check --no-emit`."""
    if not _activo():
        pytest.skip("E2E real opt-in: exporta OPENSYN_E2E=1")
    exe = _synapse_nativo()
    if exe is None:
        pytest.skip("synapse nativo ausente: no hay `check --no-emit` que validar")

    valido = tmp_path / "valido.syn"
    valido.write_text(
        "#lang: es\n"
        "funcion sumar(a: entero, b: entero) -> entero:\n"
        "    requiere:\n"
        "        verdadero\n"
        "    garantiza:\n"
        "        verdadero\n"
        "    retornar a + b\n",
        encoding="utf-8",
    )
    r = subprocess.run(
        [str(exe), "check", "--no-emit", str(valido)],
        cwd=str(RAIZ), capture_output=True, text=True, timeout=120,
        encoding="utf-8", errors="replace",
    )
    assert r.returncode == 0, f"código válido rechazado:\n{r.stdout}\n{r.stderr}"

    invalido = tmp_path / "invalido.syn"
    invalido.write_text("#lang: es\nfuncion roto( -> entero:\n", encoding="utf-8")
    r2 = subprocess.run(
        [str(exe), "check", "--no-emit", str(invalido)],
        cwd=str(RAIZ), capture_output=True, text=True, timeout=120,
        encoding="utf-8", errors="replace",
    )
    assert r2.returncode != 0, "código inválido aceptado por check --no-emit"


def _compilar_sonda(tmp_path):
    fuera = "C:\\\\Windows\\\\System32\\\\x.txt" if os.name == "nt" else "/etc/passwd"
    sonda = tmp_path / "sonda_permisos.syn"
    sonda.write_text(
        "#lang: es\n"
        "// cumple Manual 7 §7.3: sonda E2E del sandbox de herramientas\n"
        "importar opensyn.permisos\n"
        "importar std.io\n"
        "\n"
        "funcion principal() -> entero:\n"
        "    let m = matriz_permisos_crear()\n"
        '    let dentro_ruta = concat(_syn_obtener_cwd(), "\\\\r275_workspace\\\\x.txt")\n'
        '    let dentro = verificar_permiso_completo(m, "editar", dentro_ruta)\n'
        f'    let fuera = verificar_permiso_completo(m, "editar", "{fuera}")\n'
        '    let lectura = verificar_permiso_completo(m, "leer", dentro_ruta)\n'
        '    escribir_linea(concat("editar_dentro=", entero_a_texto(dentro)))\n'
        '    escribir_linea(concat("editar_fuera=", entero_a_texto(fuera)))\n'
        '    escribir_linea(concat("leer_dentro=", entero_a_texto(lectura)))\n'
        "    retornar 0\n",
        encoding="utf-8",
    )

    nativo = _synapse_nativo()
    if nativo is not None:
        r = subprocess.run(
            [str(nativo), str(sonda), "-o", "sonda.exe"],
            cwd=str(tmp_path), capture_output=True, text=True, timeout=180,
            encoding="utf-8", errors="replace",
        )
        if r.returncode == 0:
            return tmp_path / "sonda.exe", "S2"

    main_py = RAIZ / "main.py"
    r = subprocess.run(
        [PYTHON, str(main_py), "sonda_permisos.syn", "-o", "sonda.exe"],
        cwd=str(tmp_path), capture_output=True, text=True, timeout=300,
        encoding="utf-8", errors="replace",
    )
    assert r.returncode == 0, (
        "la sonda de permisos no compiló ni con S2 ni con S1:\n"
        + (r.stdout or "")[-2000:] + "\n" + (r.stderr or "")[-2000:]
    )
    return tmp_path / "sonda.exe", "S1"


def test_tool_con_aprobacion_y_sandbox(tmp_path):
    """Manual 7 §7.3: ASK dentro del workspace, DENY fuera, ALLOW de lectura."""
    if not _activo():
        pytest.skip("E2E real opt-in: exporta OPENSYN_E2E=1")
    exe, compilador = _compilar_sonda(tmp_path)
    r = subprocess.run(
        [str(exe)], cwd=str(tmp_path), capture_output=True, text=True,
        timeout=30, encoding="utf-8", errors="replace",
    )
    assert r.returncode == 0, f"sonda falló:\n{r.stdout}\n{r.stderr}"
    valores = {}
    for linea in (r.stdout or "").splitlines():
        if "=" in linea:
            clave, valor = linea.split("=", 1)
            if valor.strip().lstrip("-").isdigit():
                valores[clave.strip()] = int(valor)
    assert valores.get("editar_dentro") == 1, (
        f"editar dentro debe ser ASK(1), obtuvo {valores} (compilador {compilador})"
    )
    assert valores.get("editar_fuera") == 2, (
        f"editar fuera debe ser DENY(2), obtuvo {valores} (compilador {compilador})"
    )
    assert valores.get("leer_dentro") == 0, (
        f"leer dentro debe ser ALLOW(0), obtuvo {valores} (compilador {compilador})"
    )
    if compilador == "S1":
        print("[R275][WARN] sonda compilada con S1: S2 no emite permisos.syn "
              "(hallazgo H-R275-1)")


def _conexiones_del_pid(pid):
    """Remote addresses de las conexiones TCP del PID (Windows netstat)."""
    try:
        r = subprocess.run(["netstat", "-ano"], capture_output=True, text=True,
                           timeout=10, encoding="utf-8", errors="replace")
    except (OSError, subprocess.TimeoutExpired):
        return None
    remotos = []
    for linea in (r.stdout or "").splitlines():
        campos = linea.split()
        if len(campos) >= 5 and campos[-1] == str(pid):
            remotos.append(campos[2])
    return remotos


def test_doctor_sin_conexiones_salientes():
    """Manual 7 §7.3: monitoreo real de red; solo loopback."""
    if not _activo():
        pytest.skip("E2E real opt-in: exporta OPENSYN_E2E=1")
    if os.name != "nt":
        pytest.skip("monitoreo netstat implementado para Windows")
    exe = RAIZ / "dist" / "bin" / "opensyn.exe"
    if not exe.is_file():
        pytest.skip("dist/bin/opensyn.exe ausente")
    if _conexiones_del_pid(os.getpid()) is None:
        pytest.skip("netstat no disponible para monitoreo")

    proc = subprocess.Popen(
        [str(exe), "doctor"], cwd=str(RAIZ),
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    remotas = set()
    limite = time.time() + 60
    while proc.poll() is None and time.time() < limite:
        for remoto in _conexiones_del_pid(proc.pid) or []:
            remotas.add(remoto)
        time.sleep(0.2)
    proc.wait(timeout=10)

    def _loopback(remoto):
        return (
            remoto.startswith("127.")
            or remoto.startswith("[::1]")
            or remoto.startswith("0.0.0.0")
            or remoto.startswith("[::]")
            or remoto in ("*:*", "")
        )

    externas = sorted(r for r in remotas if not _loopback(r))
    assert not externas, f"opensyn doctor abrió conexiones no locales: {externas}"
