#!/usr/bin/env python3
"""
fuzz_engine.py — Motor de fuzzing destructivo F11 (M10.3 — Continuo 24/7)

Documento Maestro Parte VII:
  - Generar archivos .syn aleatorios (caracteres, llaves, Unicode corrupto)
  - El compilador NUNCA debe generar segfault
  - Todo archivo invalido debe manejarse con exit code 1
  - Zero segmentation faults bajo cualquier entrada

Modos de uso:
  python tests/fuzz/fuzz_engine.py                              # 1000 iteraciones
  python tests/fuzz/fuzz_engine.py --iterations 10000           # 10000 iteraciones
  python tests/fuzz/fuzz_engine.py --sanitize                   # Probar con ASan/UBSan
  python tests/fuzz/fuzz_engine.py --247                        # Modo continuo 24/7
  python tests/fuzz/fuzz_engine.py --corpus ./corpus            # Usar corpus semilla
  python tests/fuzz/fuzz_engine.py --native                     # Probar binario nativo
  pytest tests/fuzz/test_fuzz.py -v                             # Como test unitario
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
import hashlib
import signal
import json
from pathlib import Path
from typing import List, Optional, Callable, Tuple

PROJECT_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..'))
MAIN_PY = os.path.join(PROJECT_ROOT, 'main.py')
SYNAPSE_BOOTSTRAP = os.path.join(PROJECT_ROOT, 'synapse_bootstrap.exe')
FUZZ_DIR = os.path.join(PROJECT_ROOT, 'tests', 'fuzz')
CORPUS_DIR = os.path.join(FUZZ_DIR, 'corpus')
CRASHES_DIR = os.path.join(FUZZ_DIR, 'crashes')
MAX_CRASH_LOG = 200  # Limite de crashes almacenados en memoria

# ============================================================
# GENERADORES DE ENTRADA ALEATORIA
# ============================================================

IDIOMAS = ['es', 'en', 'fr', 'pt', 'de', 'it']

KEYWORDS_ES = [
    'si', 'sino', 'funcion', 'retornar', 'lanzar', 'recuperar',
    'escuchar', 'mientras', 'importar', 'estructura', 'y', 'o',
    'no', 'verdadero', 'falso', 'inseguro', 'importar_c', 'externo',
    'coincidir', 'requiere', 'garantiza', 'canal', 'asm', 'constante',
    'para', 'romper', 'siguiente', 'tipo', 'enum', 'trazar', 'puro'
]

TOKENS = [
    '(', ')', '{', '}', '[', ']', ':', ';', ',', '.', '->', '<-',
    '=', '==', '!=', '<', '>', '<=', '>=', '+', '-', '*', '/', '%',
    '&', '|', '!', '_', '@', '#', '$', '~', '`', '^'
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
        '#lang: es\ntipo ResultadoEntero = Resultado<entero, texto>\n\nfuncion principal() -> entero:\n    retornar 0\n',
    ]
    return random.choice(plantillas)


def generar_semivalido() -> str:
    """Genera codigo semi-valido con errores comunes."""
    patrones = [
        lambda: f'#lang: {random.choice(IDIOMAS)}\n'
                'funcion main() -> entero:\n'
                '    retornar ' + str(random.randint(-1000, 1000)) + '\n',
        lambda: f'#lang: {random.choice(IDIOMAS)}\n'
                'funcion f(a: entero) -> entero:\n'
                '    ' + random.choice(['si', 'mientras']) + ' '
                + str(random.randint(0, 1)) + ' '
                + random.choice(['==', '<', '>', '!=']) + ' '
                + str(random.randint(0, 1)) + ':\n'
                '        retornar ' + str(random.randint(0, 100)) + '\n'
                '    retornar 0\n',
        lambda: f'#lang: {random.choice(IDIOMAS)}\n'
                'estructura Punto:\n'
                '    x: entero\n'
                '    y: entero\n\n'
                'funcion main() -> entero:\n'
                '    retornar 0\n',
        lambda: f'#lang: {random.choice(IDIOMAS)}\n'
                'funcion recursiva(n: entero) -> entero:\n'
                '    si n <= 0:\n'
                '        retornar 0\n'
                '    retornar recursiva(n - 1)\n\n'
                'funcion main() -> entero:\n'
                '    retornar recursiva(10)\n',
        lambda: f'#lang: {random.choice(IDIOMAS)}\n'
                'estructura Nodo:\n'
                '    valor: entero\n'
                '    siguiente: &Nodo\n\n'
                'funcion main() -> entero:\n'
                '    let n = Nodo{valor: 1, siguiente: ninguno}\n'
                '    retornar 0\n',
    ]
    return random.choice(patrones)()


def generar_aleatorio() -> str:
    """Genera contenido completamente aleatorio."""
    largo = random.randint(1, 3000)
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
        lambda: src + 'funcion main() -> entero:\n'
                '    ' + random.choice(['si', 'sino', 'mientras', 'para', 'coincidir']) + '\n',
        lambda: src + 'funcion main() -> entero:\n'
                + ''.join(random.choice(KEYWORDS_ES + TOKENS) + ' ' for _ in range(random.randint(1, 20))) + '\n',
        lambda: f'#lang: {random.choice(IDIOMAS)}\n'
                + ''.join(random.choice(KEYWORDS_ES + [str(random.randint(0, 9))]) + ':' for _ in range(random.randint(1, 10))),
    ]
    return random.choice(casos)()


def generar_indentacion_rota() -> str:
    """Genera archivos con indentacion invalida."""
    src = '#lang: ' + random.choice(IDIOMAS) + '\n'
    variantes = [
        lambda s: s + 'funcion f() -> entero:\n'
                      '   retornar 1\n',  # 3 spaces
        lambda s: s + 'funcion f() -> entero:\n'
                      '        retornar 1\n'
                      '       retornar 2\n',  # 7 spaces
        lambda s: s + 'funcion f():\n'
                      '    si verdadero:\n'
                      '           retornar 1\n',  # 11 spaces
        lambda s: s + 'funcion f() -> entero:\n'
                      '\tretornar 1\n',  # tab
        lambda s: s + 'funcion f() -> entero:\n'
                      '    retornar 0\n'
                      '  ',  # trailing
        lambda s: s + 'funcion a():\n'
                      '    funcion b():\n'
                      '         retornar 0\n',  # inconsistent nesting
    ]
    return random.choice(variantes)(src)


def generar_binario_simulado() -> bytes:
    """Genera contenido binario (no UTF-8)."""
    return bytes(random.randint(0, 255) for _ in range(random.randint(1, 1000)))


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
        '\u0300', '\u0301', '\u0302',  # Combining accents
        '\U0001f600', '\U0001f601',  # Emoji
    ]
    src += ''.join(random.choice(unicode_chars) for _ in range(random.randint(1, 100)))
    return src


def generar_mutacion_ast() -> str:
    """Genera mutaciones a nivel de AST: tipos, estructuras, funciones anidadas."""
    templates = [
        '#lang: es\n'
        'funcion f<T>(x: T) -> T:\n'
        '    retornar x\n'
        '\nfuncion main() -> entero:\n'
        '    retornar 0\n',
        '#lang: es\n'
        'funcion main() -> entero:\n'
        '    let x = si verdadero:\n'
        '        1\n'
        '    si no:\n'
        '        0\n'
        '    retornar x\n',
        '#lang: es\n'
        'externo funcion printf(formato: &texto) -> entero\n'
        '\nfuncion main() -> entero:\n'
        '    retornar 0\n',
        '#lang: es\n'
        'funcion main() -> entero:\n'
        '    let r = coincidir 1:\n'
        '        0 => 42\n'
        '        1 => 0\n'
        '    retornar r\n',
        '#lang: es\n'
        'funcion main() -> entero:\n'
        '    let mut x = 0\n'
        '    mientras x < 10:\n'
        '        x = x + 1\n'
        '    retornar x\n',
        '#lang: es\n'
        'funcion main() -> entero:\n'
        '    let mut v = []\n'
        '    v = [1, 2, 3]\n'
        '    retornar 0\n',
    ]
    base = random.choice(templates)
    if random.random() < 0.3:
        # Add random garbage at the end
        base += '\n' + ''.join(random.choice(string.printable) for _ in range(random.randint(1, 50)))
    return base


def generar_combinatoria() -> str:
    """Genera combinaciones complejas de caracteristicas del lenguaje."""
    # Combinar keyword + indent + token en secuencias
    src = '#lang: ' + random.choice(IDIOMAS) + '\n\n'
    num_blocks = random.randint(1, 5)
    for _ in range(num_blocks):
        kw = random.choice(KEYWORDS_ES)
        indent = '    ' * random.randint(0, 3)
        src += f'{indent}{kw} '
        if random.random() < 0.5:
            src += random.choice(TOKENS) + ' '
        src += ':\n'
        inner = '    ' * (random.randint(1, 3))
        src += f'{inner}retornar {random.randint(0, 100)}\n'
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
        self.casos_crash: List[dict] = []
        self.hashes_crash: set = set()
        self.tiempo_inicio = 0
        self.tiempo_fin = 0

    def __str__(self):
        return (
            f"Total: {self.total} | exit=0: {self.exit_0} | exit=1: {self.exit_1} | "
            f"crash: {self.crash} | timeout: {self.timeout} | error: {self.error}"
        )


class FuzzEngine:
    def __init__(self, seed: Optional[int] = None, use_native: bool = False,
                 use_sanitize: bool = False, corpus_dir: Optional[str] = None):
        self.seed = seed if seed is not None else int(time.time())
        random.seed(self.seed)
        self.use_native = use_native
        self.use_sanitize = use_sanitize
        self.corpus_dir = corpus_dir
        self.resultado = ResultadoFuzz()
        self._signal_caught = False
        self._old_signal_handler = None

        # Estrategias de generacion con sus pesos
        self.generadores: List[Tuple[Callable, int]] = [
            (generar_valido_simple, 8),         # 8% validos
            (generar_semivalido, 15),            # 15% semi-validos
            (generar_aleatorio, 20),             # 20% completamente aleatorios
            (generar_cadena_malformada, 15),     # 15% cadenas mal formadas
            (generar_indentacion_rota, 10),      # 10% indentacion rota
            (generar_unicode_corrupto, 10),      # 10% Unicode corrupto
            (generar_binario_simulado, 5),       # 5% binario (bytes)
            (generar_mutacion_ast, 10),          # 10% mutacion AST (NUEVO)
            (generar_combinatoria, 7),           # 7% combinatoria (NUEVO)
        ]
        self.pesos = [p for _, p in self.generadores]
        self.total_peso = sum(self.pesos)

        # Asegurar directorios
        os.makedirs(CRASHES_DIR, exist_ok=True)
        if corpus_dir:
            os.makedirs(corpus_dir, exist_ok=True)

    def _signal_handler(self, signum, frame):
        """Maneja Ctrl+C para mostrar resultados parciales."""
        self._signal_caught = True
        print("\n[FUZZ] Interrupcion detectada. Finalizando...")

    def _elegir_generador(self) -> Callable:
        r = random.randint(1, self.total_peso)
        acum = 0
        for gen, peso in self.generadores:
            acum += peso
            if r <= acum:
                return gen
        return self.generadores[-1][0]

    def _cargar_corpus(self) -> List[str]:
        """Carga entradas del corpus semilla."""
        entradas = []
        if not self.corpus_dir or not os.path.isdir(self.corpus_dir):
            return entradas
        for fname in os.listdir(self.corpus_dir):
            if fname.endswith('.syn') or fname.endswith('.txt'):
                fpath = os.path.join(self.corpus_dir, fname)
                try:
                    with open(fpath, 'rb') as f:
                        data = f.read()
                    entradas.append(data.decode('utf-8', errors='replace'))
                except Exception:
                    pass
        return entradas

    def _guardar_en_corpus(self, contenido: str, exit_code: int):
        """Guarda entrada interesante en el corpus (exit=0 valido o exit=1 interesante)."""
        if not self.corpus_dir:
            return
        # Solo guardar exit=0 (validos) para retroalimentacion positiva
        if exit_code != 0:
            return
        h = hashlib.sha256(contenido.encode()).hexdigest()[:16]
        fname = f'corpus_{h}_{int(time.time())}.syn'
        fpath = os.path.join(self.corpus_dir, fname)
        try:
            with open(fpath, 'w', encoding='utf-8') as f:
                f.write(contenido)
        except Exception:
            pass

    def _purgar_crashes_viejos(self, max_archivos: int = 500):
        """Mantiene un maximo de archivos de crash en disco."""
        try:
            archivos = sorted(
                [f for f in os.listdir(CRASHES_DIR) if f.startswith('crash_')],
                key=lambda f: os.path.getmtime(os.path.join(CRASHES_DIR, f))
            )
            while len(archivos) > max_archivos:
                viejo = archivos.pop(0)
                try:
                    os.remove(os.path.join(CRASHES_DIR, viejo))
                except Exception:
                    pass
        except Exception:
            pass

    def _guardar_crash(self, contenido: str, generador: str, resultado: dict):
        """Guarda un caso de crash a disco para analisis."""
        # Purgar antes de guardar para limitar el crecimiento
        self._purgar_crashes_viejos(500)
        h = hashlib.sha256(contenido.encode() if isinstance(contenido, str) else contenido).hexdigest()[:16]
        ts = int(time.time())
        fname = f'crash_{h}_{generador}_{ts}.syn'
        fpath = os.path.join(CRASHES_DIR, fname)
        meta_name = f'crash_{h}_{generador}_{ts}.meta.json'
        meta_path = os.path.join(CRASHES_DIR, meta_name)
        try:
            if isinstance(contenido, bytes):
                with open(fpath, 'wb') as f:
                    f.write(contenido)
            else:
                with open(fpath, 'w', encoding='utf-8') as f:
                    f.write(contenido)
            # Guardar metadatos del crash
            meta = {
                'timestamp': ts,
                'generador': generador,
                'seed': self.seed,
                'exit_code': resultado.get('exit_code', -1),
                'stderr': resultado.get('stderr', '')[:2000],
                'hash': h,
            }
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(meta, f, indent=2)
        except Exception:
            pass

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

    def _compilar_con_sanitizers(self, ruta_c: str, ruta_exe: str) -> bool:
        """Compila codigo C generado con sanitizers (ASan + UBSan)."""
        try:
            compiler = os.environ.get('CC', None) or os.environ.get('SYNAPSE_GCC', None) or 'gcc'
            flags = '-O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer'
            link_flags = '-fsanitize=address,undefined'
            thread_flag = '-lpthread' if sys.platform != 'win32' else ''
            net_flag = '-lws2_32' if sys.platform == 'win32' else ''

            # Buscar objetos runtime
            rt_obj = os.path.join(PROJECT_ROOT, 'synapse_rt.o')
            rt_mem_obj = os.path.join(PROJECT_ROOT, 'synapse_rt_memory.o')
            rt_conc_obj = os.path.join(PROJECT_ROOT, 'synapse_rt_concurrency.o')
            tn_obj = os.path.join(PROJECT_ROOT, 'tweetnacl.o')

            # Build command components list to avoid f-string quote escaping issues
            cmd_parts = [compiler, flags, '-I.', f'"{ruta_c}"']
            if os.path.exists(rt_obj):
                cmd_parts.append(f'"{rt_obj}"')
            if os.path.exists(rt_mem_obj):
                cmd_parts.append(f'"{rt_mem_obj}"')
            if os.path.exists(rt_conc_obj):
                cmd_parts.append(f'"{rt_conc_obj}"')
            if os.path.exists(tn_obj):
                cmd_parts.append(f'"{tn_obj}"')
            cmd_parts.extend([f'-o "{ruta_exe}"', thread_flag, '-lm', net_flag, link_flags])
            cmd = ' '.join(c for c in cmd_parts if c)
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            return result.returncode == 0
        except Exception as e:
            print(f"[SANITIZE] Error compilando con sanitizers: {e}")
            return False

    def _registrar_crash(self, **kwargs):
        self.resultado.casos_crash.append(kwargs)
        if len(self.resultado.casos_crash) > MAX_CRASH_LOG:
            self.resultado.casos_crash.pop(0)

    def iterar(self, n: int = 1000) -> ResultadoFuzz:
        self.resultado.tiempo_inicio = time.time()
        corpus = self._cargar_corpus()

        # Registrar handler para Ctrl+C solo durante la iteracion
        old_handler = signal.signal(signal.SIGINT, self._signal_handler)

        for i in range(n):
            if self._signal_caught:
                break

            generador = self._elegir_generador()
            produce_bytes = generador == generar_binario_simulado
            fd = None
            path = None

            # Ocasionalmente mutar una entrada del corpus
            usar_corpus = corpus and random.random() < 0.1
            if usar_corpus:
                contenido_base = random.choice(corpus)
                # Mutar: cambiar caracteres aleatorios
                contenido = list(contenido_base)
                num_mutaciones = random.randint(1, min(5, len(contenido)))
                for _ in range(num_mutaciones):
                    idx = random.randint(0, len(contenido) - 1)
                    contenido[idx] = random.choice(string.printable)
                contenido_str = ''.join(contenido)
                produce_bytes = False
            else:
                contenido_str = None

            try:
                fd, path = tempfile.mkstemp(suffix='.syn', dir=FUZZ_DIR)
                if produce_bytes:
                    data = generador()
                    os.write(fd, data)
                    contenido_guardar = data
                elif usar_corpus:
                    safe = ''.join(c for c in contenido_str
                                   if ord(c) < 0xD800 or ord(c) > 0xDFFF)
                    os.write(fd, safe.encode('utf-8', errors='replace'))
                    contenido_guardar = safe
                else:
                    contenido = generador()
                    safe = ''.join(c for c in contenido
                                   if ord(c) < 0xD800 or ord(c) > 0xDFFF)
                    os.write(fd, safe.encode('utf-8', errors='replace'))
                    contenido_guardar = safe
                os.close(fd)
                fd = None

                # --- FASE 1: Compilar con el pipeline principal ---
                try:
                    proc = self._ejecutar_compilador(path)
                    self.resultado.total += 1
                    rc = proc.returncode

                    crash_hash = hashlib.sha256(
                        (proc.stderr or '').encode() + str(rc).encode()
                    ).hexdigest()[:16]

                    if rc == 0:
                        self.resultado.exit_0 += 1
                        # Guardar entrada valida en corpus
                        self._guardar_en_corpus(
                            contenido_guardar if isinstance(contenido_guardar, str) else '',
                            rc
                        )
                    elif rc == 1:
                        self.resultado.exit_1 += 1
                    elif rc < 0:
                        # Crash por señal (segfault, abort, etc.)
                        if crash_hash not in self.resultado.hashes_crash:
                            self.resultado.hashes_crash.add(crash_hash)
                            self.resultado.crash += 1
                            self._registrar_crash(
                                tipo='signal',
                                exit=rc,
                                generador=generador.__name__,
                                stderr=proc.stderr[:500],
                                seed=self.seed,
                            )
                            self._guardar_crash(contenido_guardar, generador.__name__, {
                                'exit_code': rc, 'stderr': proc.stderr
                            })
                            print(f"\n[FUZZ] CRASH signal={-rc} | {generador.__name__} | hash={crash_hash}")
                    else:
                        unhandled = 'Traceback' in proc.stderr or 'Exception' in proc.stderr
                        if unhandled:
                            if crash_hash not in self.resultado.hashes_crash:
                                self.resultado.hashes_crash.add(crash_hash)
                                self.resultado.error += 1
                                self._registrar_crash(
                                    tipo='unhandled_error',
                                    exit=rc,
                                    generador=generador.__name__,
                                    stderr=proc.stderr[:500],
                                    seed=self.seed,
                                )
                                self._guardar_crash(contenido_guardar, generador.__name__, {
                                    'exit_code': rc, 'stderr': proc.stderr
                                })
                                print(f"\n[FUZZ] UNHANDLED exit={rc} | {generador.__name__} | hash={crash_hash}")
                                print(f"  {proc.stderr[:200]}")
                        else:
                            self.resultado.exit_1 += 1

                    # --- FASE 2: Si hay sanitizers activos, compilar C generado ---
                    if self.use_sanitize and rc == 0:
                        # El pipeline genera synapse_unity.c en el directorio actual
                        ruta_c_local = os.path.join(PROJECT_ROOT, 'synapse_unity.c')
                        if os.path.exists(ruta_c_local):
                            exe_san_path = path + '.san.exe'
                            ok = self._compilar_con_sanitizers(ruta_c_local, exe_san_path)
                            if ok:
                                # Ejecutar el binario sanitizado
                                try:
                                    san_proc = subprocess.run(
                                        [exe_san_path],
                                        capture_output=True, text=True, timeout=5
                                    )
                                    if san_proc.returncode != 0:
                                        # Posible sanitizer detecto algo
                                        san_err = san_proc.stderr
                                        if 'Sanitizer' in san_err or 'ERROR:' in san_err:
                                            crash_hash_san = hashlib.sha256(
                                                san_err.encode()
                                            ).hexdigest()[:16]
                                            if crash_hash_san not in self.resultado.hashes_crash:
                                                self.resultado.hashes_crash.add(crash_hash_san)
                                                self.resultado.crash += 1
                                                self._registrar_crash(
                                                    tipo='sanitizer',
                                                    exit=san_proc.returncode,
                                                    generador=generador.__name__,
                                                    stderr=san_err[:1000],
                                                    seed=self.seed,
                                                )
                                                print(f"\n[FUZZ-SAN] SANITIZER exit={san_proc.returncode} | {generador.__name__}")
                                                print(f"  {san_err[:300]}")
                                except subprocess.TimeoutExpired:
                                    pass
                                finally:
                                    try:
                                        os.remove(exe_san_path)
                                    except Exception:
                                        pass

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
                if path is not None:
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
        # Restaurar handler original de SIGINT
        signal.signal(signal.SIGINT, old_handler)
        return self.resultado


def mostrar_resultados(r: ResultadoFuzz, seed: int):
    duracion = r.tiempo_fin - r.tiempo_inicio
    print("\n" + "=" * 60)
    print("  RESULTADOS DE FUZZING F11 \u2014 M10.3")
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
    print(f"  Crashes unicos:     {len(r.hashes_crash)}")
    print()

    # Contar crashes guardados
    crash_files = [f for f in os.listdir(CRASHES_DIR) if f.startswith('crash_')]
    print(f"  Crashes en disco:   {len(crash_files)} (en {CRASHES_DIR})")

    if r.crash > 0 or r.error > 0:
        print(f"\n  [FAIL] {r.crash + r.error} entradas causaron terminacion anormal")
        for caso in r.casos_crash[:5]:
            print(f"    - [{caso['generador']}] exit={caso.get('exit','?')}: "
                  f"{caso.get('stderr','')[:100]}")
    else:
        print("  [PASS] Cero crashes, cero errores no controlados")
    print("=" * 60)


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description='Motor de fuzzing F11 — M10.3 (Continuo 24/7)'
    )
    parser.add_argument('--iterations', '-n', type=int, default=1000,
                       help='Numero de iteraciones (default: 1000)')
    parser.add_argument('--seed', '-s', type=int, default=None,
                       help='Semilla para reproducibilidad')
    parser.add_argument('--native', action='store_true',
                       help='Probar binario nativo (synapse_bootstrap.exe)')
    parser.add_argument('--sanitize', action='store_true',
                       help='Compilar C con -fsanitize=address,undefined')
    parser.add_argument('--corpus', type=str, default=None,
                       help='Directorio de corpus semilla')
    parser.add_argument('--247', dest='mode_247', action='store_true',
                       help='Modo continuo 24/7 (se ejecuta hasta Ctrl+C)')
    parser.add_argument('--check-only', action='store_true',
                       help='Solo verificar funcionamiento basico')

    args = parser.parse_args()

    engine = FuzzEngine(
        seed=args.seed,
        use_native=args.native,
        use_sanitize=args.sanitize,
        corpus_dir=args.corpus or CORPUS_DIR,
    )

    print("\n[FUZZ] F11 - Fuzzing Destructivo (M10.3 — Continuo 24/7)")
    print(f"[FUZZ] Seed: {engine.seed}")
    if args.mode_247:
        print("[FUZZ] Modo: CONTINUO 24/7 (Ctrl+C para detener)")
        args.iterations = 10_000_000  # Efectivamente infinito
    else:
        print(f"[FUZZ] Iteraciones: {args.iterations}")
    print(f"[FUZZ] Target: {'NATIVO' if args.native else 'PYTHON'} compiler")
    if args.sanitize:
        print("[FUZZ] Sanitizers: ASan + UBSan activados")
    if args.corpus or CORPUS_DIR:
        corpus_dir = args.corpus or CORPUS_DIR
        n_corpus = len([f for f in os.listdir(corpus_dir) if os.path.isfile(os.path.join(corpus_dir, f))]) if os.path.isdir(corpus_dir) else 0
        print(f"[FUZZ] Corpus: {corpus_dir} ({n_corpus} entradas)")
    print()

    if args.check_only:
        resultado = engine.iterar(n=5)
        print(f"[FUZZ] Check: {resultado}")
        return

    resultado = engine.iterar(n=args.iterations)
    mostrar_resultados(resultado, engine.seed)

    if resultado.crash > 0 or resultado.error > 0:
        print(f"\n⚠️  {resultado.crash + resultado.error} fallos detectados. "
              f"Revisar {CRASHES_DIR}/ para detalles.")
        sys.exit(1)

    print("\n[OK] Fuzzing completado sin fallos.")


if __name__ == '__main__':
    main()
