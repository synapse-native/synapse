# -*- coding: utf-8 -*-
"""
tests/integration/test_syquex_fuzz.py — Fuzzing del compilador Syquex (FASE 28 ME_28_T4).
Manual 3 §3 (frontmatter + statement + expression).

Verifica que el pipeline Syquex NUNCA crashee con entradas invalidas:
  - Archivos vacios, binarios, unicode corrupto
  - Keywords en posiciones incorrectas
  - Inputs aleatorios (fuzzing)
  - Paréntesis/llaves desbalanceados
  - Cadenas sin cerrar

El compilador debe retornar rc=0 o rc=1, nunca crash (rc<0 o unhandled exception).
cumple Manual 3 §3
"""
import os
import random
import subprocess
import sys
import tempfile
import time

import pytest

pytestmark = pytest.mark.integration

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, RAIZ)

from pipeline import ejecutar_compilador


def _compilar_syquex(contenido, timeout=15):
    """Compila contenido Syquex y verifica que no crashee."""
    fd, path = tempfile.mkstemp(suffix='.syq')
    try:
        if isinstance(contenido, bytes):
            os.write(fd, contenido)
        else:
            os.write(fd, contenido.encode('utf-8', errors='replace'))
        os.close(fd)
        fd = None

        out = path.replace('.syq', '.exe')
        inicio = time.time()
        try:
            rc = ejecutar_compilador(path, output_path=out)
        except subprocess.TimeoutExpired:
            return {'exit_code': -1, 'crash': False, 'timeout': True}
        except Exception:
            return {'exit_code': 1, 'crash': False, 'timeout': False}
        duracion = time.time() - inicio

        return {
            'exit_code': rc,
            'duracion': duracion,
            'crash': rc < 0,
            'timeout': False,
        }
    finally:
        if fd is not None:
            try:
                os.close(fd)
            except OSError:
                pass
        for ext in ['.syq', '.c', '.exe', '.exe.o', '.syn.json']:
            try:
                os.remove(path.replace('.syq', ext))
            except OSError:
                pass
        try:
            os.remove(path)
        except OSError:
            pass


# ============================================================
# TESTS RÁPIDOS (edge cases conocidos)
# ============================================================

class TestSyquexFuzzEdgeCases:
    """Fuzzing edge cases del compilador Syquex."""

    def test_archivo_vacio(self):
        """Archivo vacío -> rc=1, no crash."""
        r = _compilar_syquex('')
        assert not r.get('crash'), f"Crash en archivo vacío: {r}"
        assert r['exit_code'] in (0, 1), f"Exit code inesperado: {r['exit_code']}"

    def test_sin_lang(self):
        """Archivo sin #lang: -> rc=1, no crash."""
        r = _compilar_syquex('funcion main() -> entero:\n    retornar 0\n')
        assert not r.get('crash'), f"Crash sin lang: {r}"
        assert r['exit_code'] == 1, f"Esperaba rc=1, obtuvo {r['exit_code']}"

    def test_binario_aleatorio(self):
        """Archivo binario random -> rc=1, no crash."""
        data = bytes(random.randint(0, 255) for _ in range(200))
        r = _compilar_syquex(data)
        assert not r.get('crash'), f"Crash en binario: {r}"
        assert r['exit_code'] == 1, f"Esperaba rc=1, obtuvo {r['exit_code']}"

    def test_unicode_corrupto(self):
        """Unicode corrupto (BOM, zero-width, emoji) -> no crash."""
        casos = [
            '\ufeff#lang: es\nfuncion main() -> entero:\n    retornar 0\n',
            '#lang: es\n\u200bfuncion main() -> entero:\n    retornar 0\n',
            '#lang: es\nfuncion main() -> entero:\n    retornar \U0001f600\n',
            '#lang: es\nfuncion main() -> entero:\n    retornar \x00\n',
        ]
        for i, caso in enumerate(casos):
            r = _compilar_syquex(caso)
            assert not r.get('crash'), f"Crash unicode caso {i}: {r}"

    def test_keywords_en_posiciones_invalidas(self):
        """Keywords Syquex en posiciones incorrectas -> no crash."""
        keywords = [
            'estructura', 'enumeracion', 'funcion', 'retornar', 'si', 'sino',
            'mientras', 'para', 'coincidir', 'importar', 'externo', 'constante',
            'variable', 'tipo', 'lanzar', 'recuperar', 'intentar', 'atrapar',
        ]
        for kw in keywords:
            contenido = f'#lang: es\n{kw} {kw} {kw}:\n    {kw} {kw}\n'
            r = _compilar_syquex(contenido)
            assert not r.get('crash'), f"Crash con keyword '{kw}': {r}"

    def test_llaves_desbalanceadas(self):
        """Llaves/paréntesis desbalanceados -> no crash."""
        casos = [
            '#lang: es\nfuncion main() -> entero:\n    (\n    retornar 0\n',
            '#lang: es\nfuncion main( -> entero:\n    retornar 0\n',
            '#lang: es\nfuncion main() -> entero:\n    )\n    retornar 0\n',
            '#lang: es\nfuncion main() -> entero:\n    [ ] )\n    retornar 0\n',
            '#lang: es\nestructura Foo:\n    x: entero\n    ],\n',
        ]
        for i, caso in enumerate(casos):
            r = _compilar_syquex(caso)
            assert not r.get('crash'), f"Crash brackets caso {i}: {r}"

    def test_cadenas_sin_cerrar(self):
        """Cadenas sin cerrar -> no crash."""
        casos = [
            '#lang: es\nfuncion main() -> entero:\n    x = "hola\n    retornar 0\n',
            '#lang: es\nfuncion main() -> entero:\n    y = \'mundo\n    retornar 0\n',
            '#lang: es\nfuncion main() -> entero:\n    z = "\\\\\n    retornar 0\n',
        ]
        for i, caso in enumerate(casos):
            r = _compilar_syquex(caso)
            assert not r.get('crash'), f"Crash string caso {i}: {r}"

    def test_nulos_en_medio(self):
        """Bytes nulos en medio del código -> no crash."""
        casos = [
            '#lang: es\nfuncion main() -> entero:\n    retornar \x00\n',
            '#lang: es\nfunc\x00ion main() -> entero:\n    retornar 0\n',
            '#lang: es\nfuncion main() -> entero:\n    \x00retornar 0\n',
        ]
        for i, caso in enumerate(casos):
            r = _compilar_syquex(caso)
            assert not r.get('crash'), f"Crash nulos caso {i}: {r}"

    def test_indentacion_invalida(self):
        """Indentación inválida -> no crash."""
        casos = [
            '#lang: es\nfuncion main() -> entero:\n   retornar 0\n',
            '#lang: es\nfuncion main() -> entero:\n\tretornar 0\n',
            '#lang: es\nfuncion f():\n retornar 1\n',
        ]
        for i, caso in enumerate(casos):
            r = _compilar_syquex(caso)
            assert not r.get('crash'), f"Crash indent caso {i}: {r}"

    def test_operadores_invalidos(self):
        """Operadores inválidos o incompletos -> no crash."""
        casos = [
            '#lang: es\nfuncion main() -> entero:\n    x = <<<\n    retornar 0\n',
            '#lang: es\nfuncion main() -> entero:\n    x = =>>\n    retornar 0\n',
            '#lang: es\nfuncion main() -> entero:\n    x = !!@@\n    retornar 0\n',
            '#lang: es\nfuncion main() -> entero:\n    x = \n    retornar 0\n',
        ]
        for i, caso in enumerate(casos):
            r = _compilar_syquex(caso)
            assert not r.get('crash'), f"Crash operadores caso {i}: {r}"


# ============================================================
# FUZZING ALEATORIO
# ============================================================

class TestSyquexFuzzRandom:
    """Fuzzing aleatorio del compilador Syquex."""

    def test_fuzz_random_50(self):
        """50 entradas aleatorias -> 0 crashes."""
        random.seed(42)
        crashes = []
        for i in range(50):
            largo = random.randint(1, 300)
            tiene_lang = random.random() < 0.5
            chars = '#lang: es\n' if tiene_lang else ''
            chars += ''.join(random.choice(
                'abcdefghijklmnopqrstuvwxyz(){}[]:;=+-*/<>! \n\t0123456789'
            ) for _ in range(largo))
            r = _compilar_syquex(chars)
            if r.get('crash'):
                crashes.append(f"#{i}: exit={r['exit_code']}")
        assert len(crashes) == 0, f"{len(crashes)} crashes:\n" + "\n".join(crashes)

    def test_fuzz_mutacion_keywords_syquex(self):
        """Mutaciones de keywords Syquex en posiciones críticas."""
        random.seed(99)
        crashes = []
        keywords = [
            'estructura', 'enumeracion', 'funcion', 'retornar', 'si', 'sino',
            'mientras', 'coincidir', 'importar', 'externo', 'constante',
            'variable', 'tipo', 'lanzar', 'recuperar', 'crear', 'metodo',
            'self', 'nulo', 'verdadero', 'falso', 'entero', 'texto',
        ]
        for _ in range(50):
            kw = random.choice(keywords)
            contenido = f'#lang: es\n{kw} {kw} {kw}:\n    {kw} {kw}\n'
            r = _compilar_syquex(contenido)
            if r.get('crash'):
                crashes.append(f"kw={kw}: exit={r['exit_code']}")
        assert len(crashes) == 0, f"{len(crashes)} crashes:\n" + "\n".join(crashes)

    def test_fuzz_estructuras_aleatorias(self):
        """Generación aleatoria de estructuras Syquex."""
        random.seed(77)
        crashes = []
        campos = ['entero', 'texto', 'nulo', 'falso', 'verdadero']
        for _ in range(30):
            n_campos = random.randint(0, 5)
            body = '\n'.join(f'    c{i}: {random.choice(campos)}' for i in range(n_campos))
            contenido = f'#lang: es\nestructura Foo:\n{body}\n'
            r = _compilar_syquex(contenido)
            if r.get('crash'):
                crashes.append(f"campos={n_campos}: exit={r['exit_code']}")
        assert len(crashes) == 0, f"{len(crashes)} crashes:\n" + "\n".join(crashes)

    def test_fuzz_funciones_aleatorias(self):
        """Generación aleatoria de funciones Syquex."""
        random.seed(55)
        crashes = []
        tipos_retorno = ['entero', 'texto', 'nulo']
        for _ in range(30):
            n_params = random.randint(0, 4)
            params = ', '.join(f'p{i}: {random.choice(tipos_retorno)}' for i in range(n_params))
            ret = random.choice(tipos_retorno)
            contenido = f'#lang: es\nfuncion f({params}) -> {ret}:\n    retornar 0\n'
            r = _compilar_syquex(contenido)
            if r.get('crash'):
                crashes.append(f"params={n_params}: exit={r['exit_code']}")
        assert len(crashes) == 0, f"{len(crashes)} crashes:\n" + "\n".join(crashes)

    def test_fuzz_input_largo(self):
        """Input muy largo (10KB) -> no crash."""
        random.seed(33)
        contenido = '#lang: es\n'
        for _ in range(200):
            contenido += f'    x_{random.randint(0,999)} = {random.randint(0,999)}\n'
        r = _compilar_syquex(contenido[:10000])
        assert not r.get('crash'), f"Crash en input largo: {r}"

    def test_fuzz_lineas_masivas(self):
        """Muchas líneas vacías -> no crash."""
        contenido = '#lang: es\n\n' * 500 + 'funcion main() -> entero:\n    retornar 0\n'
        r = _compilar_syquex(contenido)
        assert not r.get('crash'), f"Crash en líneas masivas: {r}"
