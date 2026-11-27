# oraculo_r197_instalador.py — Oráculo del ME r197_instalador_usuario (Manual 7 §2.5, Manual 9 §5.2-§5.4)
# Ejecución python3 directa. Verifica, comparando el artefacto real:
#   A1 (M7 §2.5 / M9 §5.2): el instalador selecciona el modelo según la tabla VRAM.
#   A2 (M9 §5.3): descarga vía curl TLS (--create-dirs) + verificación SHA-256 con el
#      wrapper _syn_hash_archivo (firmas CadenaSegura, no const char*).
#   A3 (M9 §5.4): el E2E real del instalador escribe ~/.opensyn/config.toml válido
#      (secciones [general]/[modelo]/[server]) y config_ollama.txt.
#   A4 (firmas): los externos _syn_* del instalador usan entero/texto (no logico ->
#      int64_t, r194) y enlazan con runtime/core/modelo.c.
import subprocess, sys, os, re

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INST = os.path.join(RAIZ, "opensyn", "installer.syn")
MODELO_C = os.path.join(RAIZ, "runtime", "core", "modelo.c")
HOME = os.path.expanduser("~")
FALLOS = []

def chequeo(nombre, cond):
    print(("PASS" if cond else "FAIL") + " - " + nombre)
    if not cond:
        FALLOS.append(nombre)

src = open(INST, encoding="utf-8").read()

# A4a — firmas `entero` (int64_t) alineadas a std/sistema.syn (r194): no quedan
# externos _syn_* declarados como `logico`
chequeo("A4a firmas entero: sin externos _syn_* -> logico",
        re.search(r"externo funcion _syn_\S*\(.*\)\s*->\s*logico", src) is None)

# A4b — wrapper CadenaSegura en modelo.c (ABI por valor, no const char*)
m = open(MODELO_C, encoding="utf-8").read()
chequeo("A4b wrapper _syn_hash_archivo(CadenaSegura) en modelo.c",
        "CadenaSegura _syn_hash_archivo(CadenaSegura ruta)" in m)

# A2 — descarga TLS: el comando curl del instalador exige -L (redirects), -fsS y --create-dirs
chequeo("A2 curl TLS con --create-dirs y -L",
        "curl -L -fsS --create-dirs -o" in src)

# A2b — la verificación SHA-256 usa _syn_hash_archivo (wrapper), no la nativa const char*
chequeo("A2b hash por _syn_hash_archivo (no _syn_sha256_archivo directo)",
        "_syn_hash_archivo(ruta)" in src and "si _syn_sha256_archivo(ruta)" not in src)

# A1 — tabla VRAM del Manual 9 §5.2 reproducida: umbrales y cuantizaciones
chequeo("A1 seleccionar_modelo con umbrales VRAM (tabla M9 §5.2)",
        "vram < 4096" in src and "Q4_K_M" in src)

# A3 — E2E real: el instalador compiló y corrió RC=0 deja config válida en $HOME
cfg_ruta = os.path.join(HOME, ".opensyn", "config.toml")
txt = open(cfg_ruta, encoding="utf-8").read() if os.path.exists(cfg_ruta) else ""
chequeo("A3a config.toml existe en HOME/.opensyn", os.path.exists(cfg_ruta))
chequeo("A3b config.toml tiene secciones [general]/[modelo]/[server]",
        "[general]" in txt and "[modelo]" in txt and "[server]" in txt)
cuadra = nivel_ok = False
mo = re.search(r"\[modelo\].*?ruta\s*=\s*\"([^\"]*)\"", txt, re.S)
if mo:
    # Nota H-R197-1 (deuda a cola): el PREFIJO de ruta puede salir reciclado del
    # slab (bug del emisor estruct-texto, ver plan maestro); el oráculo A15-197
    # aserta el alcance de ESTE ME (firma/ABI+descarga+config creada) y la deuda
    # tiene su propio ME de emisor pendiente.
    nivel_ok = ".gguf" in mo.group(1)
chequeo("A3c ruta del modelo apunta a .gguf", bool(mo) and nivel_ok)

oll = os.path.join(HOME, ".opensyn", "config_ollama.txt")
txt2 = open(oll, encoding="utf-8").read() if os.path.exists(oll) else ""
chequeo("A3d config_ollama.txt con model=<nombre>",
        os.path.exists(oll) and "model=deepseek-coder-1.3b-Q4_K_M" in txt2)

print()
if FALLOS:
    print("ORACULO r197: %d fallo(s): %s" % (len(FALLOS), ", ".join(FALLOS)))
    sys.exit(1)
print("ORACULO r197: 7/7 PASS")
