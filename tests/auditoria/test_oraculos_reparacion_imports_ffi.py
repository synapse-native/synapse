# Oráculos del ME reparacion_imports_ffi (H-CFG-4/H-CFG-5 + MTO re-anclado)
# cumple Manual 1 §3.1: pipeline con resolución de imports (fallback a raíz).
# cumple Manual 6 §3.1: FFI de colecciones con handle entero ↔ void* del lado C.
# cumple Manual 7 §4.2: flujo de validación — el MTO se re-ancla a secciones reales.
# OBL-M1-02: sintaxis core parsea y compila (R1).
"""Oráculos de comportamiento del ME reparacion_imports_ffi.

R1: resolución de imports con fallback a la raíz del workspace
    (compilador/resolvedor_axon.py + pipeline.py).
R3: el MTO re-anclado no reporta citas muertas (auditar_calidad_tests --solo-mto).
El oráculo de R2 vive en tests/unit/test_puente_ffi_lista_mapa.py (12 GREEN).
"""
import os
import subprocess
import sys

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from pipeline import compilar_desde_texto
from compilador.generator import GeneradorC


def _compilar_en(dir_tmp, nombre, contenido):
    """Escribe un fuente en dir_tmp y lo compila con el pipeline real.
    dependencias=None: sin manifiesto axon.toml — la resolución de imports
    es por búsqueda en disco (Manual 1 §3.1), no por manifiesto."""
    ruta = os.path.join(str(dir_tmp), nombre)
    with open(ruta, 'w', encoding='utf-8') as f:
        f.write(contenido)
    return compilar_desde_texto(ruta, set(), os.path.dirname(ruta),
                                False, None, None)


def test_import_desde_subdirectorio_cae_en_raiz(tmp_path):
    """H-CFG-4a: un fuente en subdirectorio temporal resuelve
    `importar opensyn` contra la RAÍZ del repo (opensyn/principal.syn) —
    pre-fix era E-603 según la carpeta del fuente (repro de test_ia_adv_10)."""
    ast, diag = _compilar_en(
        tmp_path, '_drv_raiz.syn',
        '#lang: es\nimportar opensyn\nfuncion principal() -> nulo:\n'
        '    log("hola")\n')
    assert diag.codigo_salida() == 0, \
        f"el import debe resolver contra la raiz: " \
        f"{[e.get('mensaje', '') for e in diag.errores]}"


def test_import_encadenado_resuelve_contra_directorio_del_modulo(tmp_path):
    """H-CFG-4b: los imports ENCADENADOS se resuelven contra el directorio del
    MÓDULO importado, no del fuente raíz (Manual 1 §3.1). sub/satelita.syn
    importa 'permiso' que vive en sub/ — aunque exista otro permiso.syn en
    tmp/ (el del módulo gana: retorna 777, no 111)."""
    sub = tmp_path / 'sub'
    sub.mkdir()
    (tmp_path / 'permiso.syn').write_text(
        '#lang: es\nfuncion dar_permiso() -> entero:\n    retornar 111\n',
        encoding='utf-8')
    (sub / 'permiso.syn').write_text(
        '#lang: es\nfuncion dar_permiso() -> entero:\n    retornar 777\n',
        encoding='utf-8')
    (sub / 'satelita.syn').write_text(
        '#lang: es\nimportar permiso\nfuncion valor_satelite() -> entero:\n'
        '    retornar dar_permiso()\n', encoding='utf-8')
    ast, diag = _compilar_en(
        tmp_path, 'raiz.syn',
        '#lang: es\nimportar sub.satelita\nfuncion principal() -> entero:\n'
        '    retornar valor_satelite()\n')
    assert diag.codigo_salida() == 0, \
        f"la cadena de imports debe resolver: " \
        f"{[e.get('mensaje', '') for e in diag.errores]}"
    c = GeneradorC(ast).generar()
    assert '777' in c, "debe enlazar el permiso del DIRECTORIO del modulo (sub/)"
    assert '111' not in c, "no debe tomar el permiso del dir del fuente raiz"


def test_principal_del_usuario_gana_sobre_importado(tmp_path):
    """H-CFG-4c: si el archivo del usuario define `principal`, el principal
    IMPORTADO se descarta (el ejecutable es del usuario, Manual 1 §3.1)."""
    paq = tmp_path / 'paq'
    paq.mkdir()
    (paq / 'principal.syn').write_text(
        '#lang: es\nfuncion principal() -> entero:\n    retornar 222\n',
        encoding='utf-8')
    ast, diag = _compilar_en(
        tmp_path, 'usuario.syn',
        '#lang: es\nimportar paq\nfuncion principal() -> entero:\n'
        '    retornar 333\n')
    assert diag.codigo_salida() == 0, \
        f"sin redefinicion de principal: " \
        f"{[e.get('mensaje', '') for e in diag.errores]}"
    c = GeneradorC(ast).generar()
    assert '333' in c, "el principal del USUARIO debe ganar"
    assert '222' not in c, "el principal IMPORTADO debe descartarse"


def test_r2_ffi_emite_casts_de_handle_y_firma_unica(tmp_path):
    """H-CFG-5 (Manual 6 §3.1): el C emitido castea los handles
    entero↔void* y declara _syn_lista_crear UNA sola vez (header canónico)."""
    ast, diag = _compilar_en(
        tmp_path, '_drv_ffi.syn',
        '#lang: es\nfuncion principal() -> entero:\n'
        '    let l = lista_crear()\n'
        '    lista_agregar(l, 42)\n'
        '    let n = lista_longitud(l)\n'
        '    lista_liberar(l)\n'
        '    retornar n\n')
    assert diag.codigo_salida() == 0, \
        f"{[e.get('mensaje', '') for e in diag.errores]}"
    c = GeneradorC(ast).generar()
    assert c.count('extern void* _syn_lista_crear') == 1, \
        "UNA sola declaracion canonica de crear (H-CFG-5: fin de conflicting types)"
    assert '(intptr_t)_syn_lista_crear()' in c, \
        "el creador castea a handle entero (M6 §3.1)"
    assert '(void*)(intptr_t)(' in c, \
        "los handles viajan casteados a void* del lado C"


def test_r2_for_en_sobre_lista_emite_cast_seguro(tmp_path):
    """H-CFG-5 + Manual 3 §3: el for-en sobre Lista<T> declara su temporal
    con cast (void*)(intptr_t)(...) — sin conversión implícita int↔puntero."""
    ast, diag = _compilar_en(
        tmp_path, '_drv_foren.syn',
        '#lang: es\nfuncion principal() -> entero:\n'
        '    let l = lista_crear()\n'
        '    l.agregar(7)\n'
        '    let suma = 0\n'
        '    para v en l:\n'
        '        suma = suma + v\n'
        '    l.liberar()\n'
        '    retornar suma\n')
    assert diag.codigo_salida() == 0, \
        f"for-en sobre handle entero debe compilar: " \
        f"{[e.get('mensaje', '') for e in diag.errores]}"
    c = GeneradorC(ast).generar()
    assert '(void*)(intptr_t)(' in c, \
        "cast explícito al borde del for-en (M6 §3.1)"


def test_mto_reanclado_sin_citas_muertas():
    """R3: el MTO re-anclado pasa su propia validación (Manual 7 §4.2)."""
    r = subprocess.run(
        [sys.executable, 'auditoria/auditar_calidad_tests.py', '--solo-mto'],
        cwd=RAIZ, capture_output=True, text=True, encoding='utf-8',
        errors='replace', timeout=300)
    assert r.returncode == 0, \
        f"MTO invalido:\n{r.stdout[-600:]}\n{r.stderr[-300:]}"
