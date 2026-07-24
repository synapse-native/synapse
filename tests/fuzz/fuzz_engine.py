#!/usr/bin/env python3
"""
fuzz_engine.py — Motor de fuzzing destructivo F11

Documento Maestro Parte VII:
  - Generar archivos .syn aleatorios (caracteres, llaves, Unicode corrupto)
  - El compilador NUNCA debe generar segfault
  - Todo archivo invalido debe manejarse con exit code 1
  - Zero segmentation faults bajo cualquier entrada

Modos de uso:
  python tests/fuzz/fuzz_engine.py                    # 1000 iteraciones
  python tests/fuzz/fuzz_engine.py --iterations 10000 # 10000 iteraciones
  python tests/fuzz/fuzz_engine.py --seed 42          # Semilla reproducible
  python tests/fuzz/fuzz_engine.py --native           # Probar binario nativo
  pytest tests/fuzz/test_fuzz.py -v                   # Como test unitario
"""

import os
import sys
import subprocess
import random
import string
import tempfile
import time
import logging
import traceback

PROJECT_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..'))
MAIN_PY = os.path.join(PROJECT_ROOT, 'main.py')
SYNAPSE_BOOTSTRAP = os.path.join(PROJECT_ROOT, 'synapse_bootstrap.exe')
FUZZ_DIR = os.path.join(PROJECT_ROOT, 'tests', 'fuzz')
MAX_CRASH_LOG = 100  # Limite de crashes almacenados en memoria

# ============================================================
# GENERADORES DE ENTRADA ALEATORIA
# ============================================================

IDIOMAS = ['es', 'en', 'fr', 'pt', 'de', 'it']

KEYWORDS_ES = [
    'si', 'sino', 'funcion', 'retornar', 'lanzar', 'recuperar',
    'escuchar', 'mientras', 'importar', 'estructura', 'y', 'o',
    'no', 'verdadero', 'falso', 'inseguro', 'importar_c', 'externo',
    'coincidir', 'requiere', 'garantiza', 'canal', 'asm', 'constante',
    'para', 'romper', 'siguiente'
]

TOKENS = [
    '(', ')', '{', '}', '[', ']', ':', ';', ',', '.', '->', '<-',
    '=', '==', '!=', '<', '>', '<=', '>=', '+', '-', '*', '/', '%',
    '&', '|', '!', '_'
]

# ============================================================
# ESTRATEGIAS DE GENERACION
# ============================================================

def generar_valido_simple() -> str:
    """Genera un programa Synapse sintacticamente valido minimo."""
    plantillas = [
        '#lang: es\nfuncion principal() -> entero:\n    retornar 0\n',
        '#lang: en\nfunction main() -> int:\n    return 0\n',
        '#lang: es\nfuncion suma(a: entero, b: entero) -> entero:\n    retornar a + b\n\nfuncion principal() -> entero:\n    retornar suma(1, 2)\n',
        '#lang: es\nconstante N = 42\n\nfuncion principal() -> entero:\n    retornar N\n',
    ]
    return random.choice(plantillas)


def generar_semivalido() -> str:
    """Genera codigo semi-valido con errores comunes."""
    patrones = [
        lambda: f'#lang: {random.choice(IDIOMAS)}\n' +
                'funcion main() -> entero:\n' +
                '    retornar ' + str(random.randint(-1000, 1000)) + '\n',
        lambda: f'#lang: {random.choice(IDIOMAS)}\n' +
                'funcion f(a: entero) -> entero:\n' +
                '    ' + random.choice(['si', 'mientras']) + ' ' +
                str(random.randint(0, 1)) + ' ' +
                random.choice(['==', '<', '>', '!=']) + ' ' +
                str(random.randint(0, 1)) + ':\n' +
                '        retornar ' + str(random.randint(0, 100)) + '\n' +
                '    retornar 0\n',
        lambda: f'#lang: {random.choice(IDIOMAS)}\n' +
                'estructura Punto:\n' +
                '    x: entero\n' +
                '    y: entero\n\n' +
                'funcion main() -> entero:\n' +
                '    retornar 0\n',
    ]
    return random.choice(patrones)()


def generar_aleatorio() -> str:
    """Genera contenido completamente aleatorio."""
    largo = random.randint(1, 2000)
    chars = string.printable  # Ya incluye \n \t \r etc
    if random.random() < 0.3:
        # Agregar caracteres de control y bytes nulos REALES
        control_chars = ''.join(chr(c) for c in range(32) if chr(c) not in '\n\r\t')
        chars += control_chars
        chars += chr(127)  # DEL
    # Filtrar surrogados (no encodeables)
    safe = ''.join(c for c in chars if not (0xD800 <= ord(c) <= 0xDFFF))
    return ''.join(random.choice(safe) for _ in range(largo))


def generar_cadena_malformada() -> str:
    """Genera cadenas malformadas especificas para probar el lexer."""
    src = '#lang: ' + random.choice(IDIOMAS) + '\n\n'
    casos = [
        lambda: src + 'funcion main() -> entero:\n    x = "' +
                ''.join(random.choice(string.printable) for _ in range(random.randint(1, 50))) + '\n',
        lambda: src + 'funcion main() -> entero:\n    x = "' +
                ''.join(random.choice(string.ascii_letters + '\\\\\\n\\t\\r') for _ in range(random.randint(1, 30))) + '"\n',
        lambda: src + 'funcion main() -> entero:\n' +
                '    ' + random.choice(['si', 'sino', 'mientras', 'para', 'coincidir']) + '\n',
        lambda: src + 'funcion main() -> entero:\n' +
                ''.join(random.choice(KEYWORDS_ES + TOKENS) + ' ' for _ in range(random.randint(1, 20))) + '\n',
        lambda: f'#lang: {random.choice(IDIOMAS)}\n' +
                ''.join(random.choice(KEYWORDS_ES + [str(random.randint(0, 9))]) + ':' for _ in range(random.randint(1, 10))),
    ]
    return random.choice(casos)()


def generar_indentacion_rota() -> str:
    """Genera archivos con indentacion invalida."""
    src = '#lang: ' + random.choice(IDIOMAS) + '\n'
    if random.random() < 0.5:
        src += 'funcion f() -> entero:\n'
        src += '   retornar 1\n'  # 3 spaces, not 4
    else:
        src += 'funcion f() -> entero:\n'
        src += '        retornar 1\n'  # 8 spaces (valid but deep)
        src += '       retornar 2\n'  # 7 spaces (invalid)
    return src


def generar_binario_simulado() -> bytes:
    """Genera contenido binario (no UTF-8)."""
    return bytes(random.randint(0, 255) for _ in range(random.randint(1, 500)))


def generar_unicode_corrupto() -> str:
    """Genera texto con Unicode valido pero semanticamente problematico."""
    src = ''
    if random.random() < 0.5:
        src = '#lang: ' + random.choice(IDIOMAS) + '\n'
    unicode_chars = [
        '\u0000', '\u0001', '\u0007', '\u001b',  # Control chars
        '\u200b', '\u200c', '\u200d',  # Zero-width
        '\ufeff',  # BOM
        '\ufffe',  # Non-character
        '\u0300', '\u0301',  # Combining accents
    ]
    src += ''.join(random.choice(unicode_chars) for _ in range(random.randint(1, 50)))
    return src


# ============================================================
# MOTOR DE FUZZING
# ============================================================

class ResultadoFuzz:
    def __init__(self):
        self.total = 0
        self.exit_0 = 0
        self.exit_1 = 0
        self.crash = 0
        self.timeout = 0
        self.error = 0
        self.casos_crash = []
        self.tiempo_inicio = 0
        self.tiempo_fin = 0

    def __str__(self):
        return (
            f"Total: {self.total} | exit=0: {self.exit_0} | exit=1: {self.exit_1} | "
            f"crash: {self.crash} | timeout: {self.timeout} | error: {self.error}"
        )


class FuzzEngine:
    def __init__(self, seed: int = None, use_native: bool = False):
        self.seed = seed if seed is not None else int(time.time())
        random.seed(self.seed)
        self.use_native = use_native
        self.resultado = ResultadoFuzz()

        # Estrategias de generacion con sus pesos
        self.generadores = [
            (generar_valido_simple, 10),       # 10% validos
            (generar_semivalido, 20),           # 20% semi-validos
            (generar_aleatorio, 25),            # 25% completamente aleatorios
            (generar_cadena_malformada, 20),    # 20% cadenas mal formadas
            (generar_indentacion_rota, 10),     # 10% indentacion rota
            (generar_unicode_corrupto, 10),     # 10% Unicode corrupto
            (generar_binario_simulado, 5),      # 5% binario (bytes)
        ]
        self.pesos = [p for _, p in self.generadores]
        self.total_peso = sum(self.pesos)

    def _elegir_generador(self):
        r = random.randint(1, self.total_peso)
        acum = 0
        for gen, peso in self.generadores:
            acum += peso
            if r <= acum:
                return gen
        return self.generadores[-1][0]

    def _ejecutar_compilador(self, path: str) -> subprocess.CompletedProcess:
        if self.use_native and os.path.exists(SYNAPSE_BOOTSTRAP):
            cmd = [SYNAPSE_BOOTSTRAP, path, os.devnull]
        else:
            cmd = [sys.executable, MAIN_PY, path, '-o', os.devnull]
        try:
            return subprocess.run(
                cmd, capture_output=True, text=True, timeout=10
            )
        except subprocess.TimeoutExpired:
            raise
        except Exception:
            raise

    def _registrar_crash(self, **kwargs):
        self.resultado.casos_crash.append(kwargs)
        if len(self.resultado.casos_crash) > MAX_CRASH_LOG:
            self.resultado.casos_crash.pop(0)

    def iterar(self, n: int = 1000) -> ResultadoFuzz:
        self.resultado.tiempo_inicio = time.time()
        for i in range(n):
            generador = self._elegir_generador()
            produce_bytes = generador == generar_binario_simulado
            fd = None
            try:
                fd, path = tempfile.mkstemp(suffix='.syn', dir=FUZZ_DIR)
                if produce_bytes:
                    data = generador()
                    os.write(fd, data)
                else:
                    contenido = generador()
                    # Filtrar surrogados antes de encode
                    safe = ''.join(c for c in contenido
                                   if ord(c) < 0xD800 or ord(c) > 0xDFFF)
                    os.write(fd, safe.encode('utf-8', errors='replace'))
                os.close(fd)
                fd = None
                try:
                    proc = self._ejecutar_compilador(path)
                    self.resultado.total += 1
                    rc = proc.returncode
                    if rc == 0:
                        self.resultado.exit_0 += 1
                    elif rc == 1:
                        self.resultado.exit_1 += 1
                    elif rc < 0:
                        self.resultado.crash += 1
                        self._registrar_crash(
                            tipo='signal',
                            exit=rc,
                            generador=generador.__name__,
                            stderr=proc.stderr[:300],
                        )
                        print(f"\n[FUZZ] CRASH signal={-rc} | {generador.__name__}")
                    else:
                        unhandled = 'Traceback' in proc.stderr
                        if unhandled:
                            self.resultado.error += 1
                            self._registrar_crash(
                                tipo='unhandled_error',
                                exit=rc,
                                generador=generador.__name__,
                                stderr=proc.stderr[:300],
                            )
                            print(f"\n[FUZZ] UNHANDLED exit={rc} | {generador.__name__}")
                            print(f"  {proc.stderr[:200]}")
                        else:
                            self.resultado.exit_1 += 1
                except subprocess.TimeoutExpired:
                    self.resultado.timeout += 1
                    self.resultado.total += 1
            except Exception as ex:
                self.resultado.error += 1
                self.resultado.total += 1
                print(f"\n[FUZZ] EXCEPTION: {ex}")
            finally:
                if fd is not None:
                    try:
                        os.close(fd)
                    except Exception:
                        logging.error("[FUZZ_ENGINE] Error closing fd:\n%s", traceback.format_exc())
                try:
                    os.remove(path)
                except Exception:
                    logging.error("[FUZZ_ENGINE] Error removing temp:\n%s", traceback.format_exc())
            if (i + 1) % 100 == 0:
                r = self.resultado
                print(f"[FUZZ] {i+1}/{n} iteraciones... "
                      f"(ok:{r.exit_0} err:{r.exit_1} crash:{r.crash} "
                      f"to:{r.timeout})", end='\r', file=sys.stderr)
        self.resultado.tiempo_fin = time.time()
        print(file=sys.stderr)
        return self.resultado


def mostrar_resultados(r: ResultadoFuzz, seed: int):
    duracion = r.tiempo_fin - r.tiempo_inicio
    print("\n" + "=" * 60)
    print("  RESULTADOS DE FUZZING F11")
    print("=" * 60)
    print(f"  Seed:               {seed}")
    print(f"  Duracion:           {duracion:.1f} seg")
    print(f"  Total entradas:     {r.total}")
    if duracion > 0:
        print(f"  Throughput:         {r.total/duracion:.0f} entradas/seg")
    print(f"  exit=0 (valido):    {r.exit_0}")
    print(f"  exit=1 (error):     {r.exit_1}")
    print(f"  CRASH (signal):     {r.crash}")
    print(f"  ERROR no controlado:{r.error}")
    print(f"  Timeout:            {r.timeout}")
    print()
    if r.crash > 0 or r.error > 0:
        print(f"  [FAIL] {r.crash + r.error} entradas causaron terminacion anormal")
        for caso in r.casos_crash[:5]:
            print(f"    - [{caso['generador']}] exit={caso.get('exit','?')}: "
                  f"{caso.get('stderr','')[:100]}")
    else:
        print("  [PASS] Cero crashes, cero errores no controlados")
    print("=" * 60)


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description='Motor de fuzzing F11 - Synapse/OpenSyn'
    )
    parser.add_argument('--iterations', '-n', type=int, default=1000,
                       help='Numero de iteraciones (default: 1000)')
    parser.add_argument('--seed', '-s', type=int, default=None,
                       help='Semilla para reproducibilidad')
    parser.add_argument('--native', action='store_true',
                       help='Probar binario nativo (synapse_bootstrap.exe)')
    parser.add_argument('--check-only', action='store_true',
                       help='Solo verificar funcionamiento basico')
    args = parser.parse_args()
    engine = FuzzEngine(seed=args.seed, use_native=args.native)
    print("\n[FUZZ] F11 - Fuzzing Destructivo (Documento Maestro Parte VII)")
    print(f"[FUZZ] Seed: {engine.seed} | Iteraciones: {args.iterations}")
    print(f"[FUZZ] Target: {'NATIVO' if args.native else 'PYTHON'} compiler")
    print()
    if args.check_only:
        resultado = engine.iterar(n=5)
        print(f"[FUZZ] Check: {resultado}")
        return
    resultado = engine.iterar(n=args.iterations)
    mostrar_resultados(resultado, engine.seed)
    if resultado.crash > 0 or resultado.error > 0:
        sys.exit(1)


if __name__ == '__main__':
    main()
