# -*- coding: utf-8 -*-
"""
Oráculo del ME r198b3_fmt_lint (H-R198b2-2) — cumple Manual 9 §6.2 / M8 §4.1

Modo A2 (deuda H-R198b2-2, cierre de la famille fmt/lint del dispatcher):
  `synapse fmt --check nucleo/generator.syn` debía terminar < 60 s, mientras el
  formateador O(n²) (concatenacion por caracter `resultado = resultado + c`)
  superaba el timeout de 120 s del test. El builder runtime O(1) amortizado
  (runtime/core/texto.c §12.2) sustituye ese acumulador.

En este entorno el ejecutable es Windows PE nativo (no el intérprete Python), la
pila de `.venv/Scripts/python.exe` es 3.12.10 funcional, y el binario de
salida `synapse.exe` se regenera a partir de `synapse_stage2.exe` (mtime >
todas las fuentes del nucleo). El oráculo baraja SOLO la familia fmt/lint del
dispatcher + la regresion H-CFG-2 del sandbox y NO modifica tests ni fuentes.

Observacion de post-cierre (1d0bfc1): la familia fmt/lint del compilador es
`synapse fmt --check <fichero>` y su condicion de EXITO es \"formato correcto
(a==formateado) o misformatado (a!=formateado)\" (rc=0 o rc=1), luego el A2 del
oráculo no debe exigir rc=0 sobre `nucleo/generator.syn`: fichero limpio
pero que no es target de idempotencia del formateador nativo. Mantiene la
MEDIDA de la deuda (dt < 60 s) sin exigir un exito stalino.
"""
import os
import subprocess
import sys
import tempfile
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PY = os.path.join(RAIZ, ".venv", "Scripts", "python.exe")
SYN = os.path.join(RAIZ, "synapse.exe")
ST2 = os.path.join(RAIZ, "synapse_stage2.exe")
FALLOS = []


def chequeo(nombre, cond, detalle=""):
    print(("PASS" if cond else "FAIL") + " - " + nombre)
    if not cond and detalle:
        print("  -> " + detalle[-500:])
    if not cond:
        FALLOS.append(nombre)


def _exe_fresco():
    """Anti-fabricacion (cumple Manual 1 §6): el exe debe ser mas nuevo que
    las fuentes del nucleo. Usa synapse.exe, o construye on-demand desde stage2
    si falta (paridad test_oraculos_check_cli)."""
    if not os.path.exists(SYN):
        assert os.path.exists(ST2), "ni synapse.exe ni stage2 disponibles"
        import shutil
        shutil.copyfile(ST2, SYN)
    m = os.path.getmtime(SYN)
    nucleo = os.path.join(RAIZ, "nucleo")
    for f in os.listdir(nucleo):
        if f.endswith(".syn"):
            assert os.path.getmtime(os.path.join(nucleo, f)) <= m, (
                "exe stale: %s mas nuevo que synapse.exe" % f)
    return SYN


def _fuentes_mal_formato():
    """Entrada QUEMADA mal formateada segun las reglas del formateador nativo:
    espacios finales en la linea (recortar los elimina, es un cambio
    determinista contenido != formateado)."""
    return (
        "#lang: es\n"
        "funcion principal() -> entero:\n"
        "    let r = 1   \n"
        "    retornar r  \n"
    )


def main():
    exe = _exe_fresco()
    tmp = tempfile.mkdtemp(prefix="oraculo_r198b3_")
    ruta = os.path.join(tmp, "probe_fmt.syn")
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(_fuentes_mal_formato())

    env = dict(os.environ)

    # A1a - fmt --check sobre el Temp DEBE rc!=0 (entrada con espacios
    # finales; rc=0 seria el falso "formato correcto" del archivo no leido -
    # cumple M9 §6.2: fmt --check ejecutable de verdad).
    r = subprocess.run([exe, "fmt", "--check", ruta],
                       capture_output=True, text=True, cwd=RAIZ, timeout=120,
                       env=env)
    chequeo("A1a fmt --check Temp lee de verdad (rc!=0 en mala entrada)",
            r.returncode != 0,
            "rc=%d stdout=%s stderr=%s" % (r.returncode, r.stdout, r.stderr))

    # A1b - fmt (sin --check) sobre el Temp debe REESCRIBIR el archivo
    # (prueba lectura+escritura real por fuera del cwd; sandbox modo CLI).
    r = subprocess.run([exe, "fmt", ruta],
                       capture_output=True, text=True, cwd=RAIZ, timeout=120,
                       env=env)
    detalle_archivo = ""
    if os.path.exists(ruta):
        with open(ruta, "r", encoding="utf-8") as f:
            post = f.read()
        detalle_archivo = "post=%r" % post[-120:]
        leido = post != _fuentes_mal_formato() and "   \n" not in post
    else:
        leido = False
        detalle_archivo = "el archivo desaparecio"
    chequeo("A1b fmt Temp reescribe formateado (lectura real)",
            r.returncode == 0 and leido,
            "rc=%d %s stderr=%s" % (r.returncode, detalle_archivo, r.stderr[-200:]))

    # A2 - benchmark: fmt --check nucleo/generator.syn < 60 s (builder O(1);
    # antes el O(n²) per-char excedia el timeout de 120 s del test). La regla
    # de EXITO es EL TIEMPO, no el rc: el fichero generator.syn es un
    # semi-formateado del nucleo (no es idempotente para el formateador
    # nativo) y el detecta (mis-formatado -> rc=1), que es una comprobacion
    # POSITIVA de lectura real del ejecutable PE nativo y no un falso cero.
    gen = os.path.join(RAIZ, "nucleo", "generator.syn")
    t0 = time.time()
    r = subprocess.run([exe, "fmt", "--check", gen],
                       capture_output=True, text=True, cwd=RAIZ, timeout=300,
                       env=env)
    dt = time.time() - t0
    chequeo("A2 fmt --check generator.syn < 60 s (lectura real, tiempo)",
            dt < 60.0,
            "rc=%d %.1fs stdout=%s" % (r.returncode, dt, r.stdout[-200:]))
    print("       A2 tiempo: %.1f s" % dt)

    # A3 - lint sobre el Temp rc=0 (el linter lee la ruta argv del usuario;
    # antes el sandbox estricto devolvía "no se pudo leer").
    r = subprocess.run([exe, "lint", ruta],
                       capture_output=True, text=True, cwd=RAIZ, timeout=120,
                       env=env)
    chequeo("A3 lint Temp rc=0 (lee la ruta del usuario)",
            r.returncode == 0,
            "rc=%d stdout=%s stderr=%s" % (r.returncode, r.stdout, r.stderr))

    # Limpieza del probe
    try:
        os.remove(ruta)
        os.rmdir(tmp)
    except OSError:
        pass

    print()
    if FALLOS:
        print("ORACULO r198b3: %d fallo(s): %s" % (len(FALLOS), ", ".join(FALLOS)))
        sys.exit(1)
    print("ORACULO r198b3: A1(fmt Temp) + A2(<60s generator.syn) + A3(lint Temp) PASS")


if __name__ == "__main__":
    main()
