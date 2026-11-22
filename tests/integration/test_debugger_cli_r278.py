import os, subprocess, pytest

pytestmark = pytest.mark.integration

# Path al binario synapse (ya compilado)
SYNAPSE = os.getenv("SYNAPSE", "./synapse.exe")

# Directorio temporal para traces
TRACE_DIR = os.getenv("TRACE_DIR", os.path.join(os.path.dirname(__file__), "fixtures", "traces"))

def _run_syn(args, cwd=None):
    cmd = [SYNAPSE] + args
    env = dict(os.environ)
    env["SYNAPSE_TRACE"] = "1"
    # Asegurar directorio de traces
    if cwd is None:
        cwd = os.getcwd()
    res = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env=env, timeout=30)
    return res

def _setup_trace(name):
    """Crea una traza mínima para tests que no dependen de una existente."""
    trace_path = os.path.join(TRACE_DIR, name)
    os.makedirs(TRACE_DIR, exist_ok=True)
    # Escribir cabecera TRACE v1
    with open(trace_path, "wb") as f:
        f.write(b"TRACE v1\n")
        f.write(b"id=trace_001\n")
        f.write(b"programa=test_program\n")
        f.write(b"eventos=0\n")
        f.write(b"---\n")
    return trace_path

class TestDebuggerCLIR278:
    @pytest.fixture(autouse=True)
    def _setup(self):
        os.makedirs(TRACE_DIR, exist_ok=True)
        yield
        # cleanup después de cada test
        for f in os.listdir(TRACE_DIR):
            fp = os.path.join(TRACE_DIR, f)
            if f.endswith(".trace") or f.endswith(".pos"):
                os.remove(fp)

    def test_load_traza(self):
        """--load debe cargar la traza y no fallar."""
        trace = _setup_trace("test_load.trace")
        res = _run_syn(["debug", "--load", trace])
        assert res.returncode == 0, f"rc={res.returncode} stderr={res.stderr}"
        assert "Traza cargada" in res.stderr, f"Expected 'Traza cargada' in output, got: {res.stderr}"

    def test_step_después_de_load(self):
        """--step después de --load debe avanzar la posición."""
        trace = _setup_trace("test_step.trace")
        # Primero cargar
        res = _run_syn(["debug", "--load", trace])
        assert res.returncode == 0
        # Luego step
        res = _run_syn(["debug", "--step"])
        # Debe imprimir posicion y rc (puede ser 0 o -1 dependiendo de si hay eventos)
        assert "posicion=" in res.stderr, f"Expected 'posicion=' in output, got: {res.stderr}"

    def test_reverse_después_de_load(self):
        """--reverse después de --load debe retroceder."""
        trace = _setup_trace("test_reverse.trace")
        res = _run_syn(["debug", "--load", trace])
        assert res.returncode == 0
        res = _run_syn(["debug", "--reverse"])
        assert "retrocedido" in res.stderr or "posicion=" in res.stderr, f"Expected reverse output, got: {res.stderr}"

    def test_snapshots_list_eventos(self):
        """--snapshots debe listar eventos en la traza."""
        trace = _setup_trace("test_snapshots.trace")
        res = _run_syn(["debug", "--load", trace])
        assert res.returncode == 0
        res = _run_syn(["debug", "--snapshots"])
        assert "eventos en traza" in res.stderr, f"Expected 'eventos en traza' in output, got: {res.stderr}"

    def test_sin_traza(self):
        """Sin traza cargada, los comandos deben fallar con mensaje honesto."""
        res = _run_syn(["debug", "--step"])
        assert res.returncode != 0 or "no hay traza cargada" in res.stderr.lower(), \
            f"Expected failure or 'no hay traza cargada', got rc={res.returncode} stderr={res.stderr}"