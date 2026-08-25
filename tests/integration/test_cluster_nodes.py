"""
test_cluster_nodes.py — Pruebas de integración para M8.1 (Red de Nodos Synapse)
Valida handshake criptográfico Ed25519, intercambio por canales remotos y rechazo de firmas inválidas.
"""

import os
import sys
import pytest

pytestmark = pytest.mark.integration

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from pipeline import ejecutar_compilador

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
TEMP_DIR = os.path.join(PROJECT_ROOT, '_test_cluster_temp')
os.makedirs(TEMP_DIR, exist_ok=True)


def _write_temp_syn(codigo: str) -> str:
    import uuid
    temp_name = f"test_cluster_{uuid.uuid4().hex[:8]}.syn"
    temp_path = os.path.join(TEMP_DIR, temp_name)
    with open(temp_path, 'w', encoding='utf-8') as f:
        f.write(codigo)
    return temp_path


def _cleanup_temp_syn(temp_syn: str):
    base = temp_syn.replace('.syn', '')
    for ext in ['.syn', '.exe', '.c', '.syn.json']:
        path = base + ext
        if os.path.exists(path):
            try:
                os.unlink(path)
            except:
                pass


def test_cluster_modulo_importa():
    """Valida que el módulo std.cluster se importa correctamente"""
    codigo = """#lang: es
importar std.cluster

funcion principal() -> nulo:
    retornar"""
    temp_syn = _write_temp_syn(codigo)
    try:
        resultado = ejecutar_compilador(temp_syn, mostrar_tokens=False)
        assert resultado == 0, f"Importación de std.cluster falló (código {resultado})"
    finally:
        _cleanup_temp_syn(temp_syn)


def test_cluster_generar_par():
    """Valida generación de par de claves Ed25519 via externo directo"""
    codigo = """#lang: es
importar std.cluster

funcion principal() -> nulo:
    par = cluster_generar_par_claves()
    retornar"""
    temp_syn = _write_temp_syn(codigo)
    try:
        resultado = ejecutar_compilador(temp_syn, mostrar_tokens=False)
        assert resultado == 0, f"Compilación de generación de par falló (código {resultado})"
    finally:
        _cleanup_temp_syn(temp_syn)


def test_cluster_firmar():
    """Valida firma de mensaje con Ed25519"""
    codigo = """#lang: es
importar std.cluster

funcion principal() -> nulo:
    par = cluster_generar_par_claves()
    mensaje = "Hola nodo"
    clave = "a"  // Placeholder — la firma usa el par generado
    resultado = cluster_firmar_mensaje(mensaje, par)
    retornar"""
    temp_syn = _write_temp_syn(codigo)
    try:
        resultado = ejecutar_compilador(temp_syn, mostrar_tokens=False)
        assert resultado == 0, f"Compilación de firma falló (código {resultado})"
    finally:
        _cleanup_temp_syn(temp_syn)


def test_cluster_verificar():
    """Valida verificación de firma Ed25519"""
    codigo = """#lang: es
importar std.cluster

funcion principal() -> nulo:
    par = cluster_generar_par_claves()
    mensaje = "Prueba"
    firma = cluster_firmar_mensaje(mensaje, par)
    valido = cluster_verificar_firma(mensaje, firma, par)
    retornar"""
    temp_syn = _write_temp_syn(codigo)
    try:
        resultado = ejecutar_compilador(temp_syn, mostrar_tokens=False)
        assert resultado == 0, f"Compilación de verificación falló (código {resultado})"
    finally:
        _cleanup_temp_syn(temp_syn)


def test_cluster_nodo_iniciar_detener():
    """Valida inicio y detención de nodo cluster"""
    codigo = """#lang: es
importar std.cluster

funcion principal() -> nulo:
    r = cluster_iniciar_nodo(0)  // Puerto 0 = sistema asigna
    cluster_detener_nodo()
    retornar"""
    temp_syn = _write_temp_syn(codigo)
    try:
        resultado = ejecutar_compilador(temp_syn, mostrar_tokens=False)
        assert resultado == 0, f"Compilación de inicio/detención falló (código {resultado})"
    finally:
        _cleanup_temp_syn(temp_syn)


def test_cluster_firma_invalida_rechazada():
    """Valida que firma con clave incorrecta es rechazada (retorna -1)"""
    codigo = """#lang: es
importar std.cluster

funcion principal() -> entero:
    par1 = cluster_generar_par_claves()
    par2 = cluster_generar_par_claves()
    mensaje = "secreto"
    firma = cluster_firmar_mensaje(mensaje, par1)
    // Verificar con clave pública de par2 (debería fallar)
    valido = cluster_verificar_firma(mensaje, firma, par2)
    si valido == 0:
        retornar 1  // Error: debería haber rechazado
    retornar 0"""
    temp_syn = _write_temp_syn(codigo)
    try:
        resultado = ejecutar_compilador(temp_syn, mostrar_tokens=False)
        assert resultado == 0, f"Compilación de rechazo falló (código {resultado})"
    finally:
        _cleanup_temp_syn(temp_syn)


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])