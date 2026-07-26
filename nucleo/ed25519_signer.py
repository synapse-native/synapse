"""
nucleo/ed25519_signer.py — Firma Ed25519 para SBOM/SLSA Level 3

Implementación pura en Python del esquema de firma Ed25519 (RFC 8032),
compatible con el ecosistema TweetNaCl/Axon existente en el proyecto.

Proporciona:
  - generar_par_claves() -> (clave_privada_hex, clave_publica_hex)
  - firmar(mensaje: bytes, clave_privada_hex: str) -> firma_hex: str
  - verificar(mensaje: bytes, firma_hex: str, clave_publica_hex: str) -> bool

Basado en el algoritmo de TweetNaCl (dominio público).
"""

import hashlib
import os
from typing import Tuple


# ================================================================
# Constantes de la curva edwards25519
# ================================================================

# Primo: 2^255 - 19
P = 2**255 - 19

# Orden del grupo: 2^252 + 27742317777372353535851937790883648493
D = -121665 * pow(121666, -1, P)  # -121665/121666 mod P

# Punto base G (x, y) — Coordenadas canónicas de edwards25519
# G_y = 4/5 mod P (constante de RFC 8032)
_G_y_val = 4 * pow(5, -1, P)  # 4/5 mod P
# G_x se calcula como la raíz cuadrada positiva de (y^2-1)/(d*y^2+1) mod P
_G_x_sq = (_G_y_val * _G_y_val - 1) * pow(D * _G_y_val * _G_y_val + 1, P - 2, P) % P
G_x = pow(_G_x_sq, (P + 3) // 8, P)
if (_G_x_sq - G_x * G_x) % P != 0:
    G_x = G_x * pow(2, (P - 1) // 4, P) % P
if G_x % 2 != 0:
    G_x = P - G_x
G_y = _G_y_val


# ================================================================
# Operaciones en el cuerpo primo
# ================================================================

def mod_inv(a: int) -> int:
    """Inverso multiplicativo módulo P."""
    return pow(a, P - 2, P)


# ================================================================
# Operaciones en la curva edwards25519 (coordenadas extendidas)
# ================================================================

def point_add(P1: Tuple[int, int, int, int], P2: Tuple[int, int, int, int]) -> Tuple[int, int, int, int]:
    """Suma de puntos en coordenadas extendidas (X, Y, Z, T)."""
    x1, y1, z1, t1 = P1
    x2, y2, z2, t2 = P2

    A = (y1 - x1) * (y2 - x2) % P
    B = (y1 + x1) * (y2 + x2) % P
    C = t1 * 2 * D * t2 % P
    DD = z1 * 2 * z2 % P
    E = B - A
    F = DD - C
    G = DD + C
    H = B + A
    x3 = E * F % P
    y3 = G * H % P
    t3 = E * H % P
    z3 = F * G % P
    return (x3, y3, z3, t3)


def point_mul(scalar: int, P: Tuple[int, int, int, int]) -> Tuple[int, int, int, int]:
    """Multiplicación escalar de punto."""
    Q = (0, 1, 1, 0)  # Punto neutro
    while scalar:
        if scalar & 1:
            Q = point_add(Q, P)
        P = point_add(P, P)
        scalar >>= 1
    return Q


def point_compress(Pt: Tuple[int, int, int, int]) -> bytes:
    """Comprime un punto a 32 bytes (coordenada y + bit de signo de x)."""
    x, y, z, _ = Pt
    zi = mod_inv(z)
    y_affine = (y * zi) % P  # P es el primo, no el punto
    x_affine = (x * zi) % P
    # El bit más significativo es el bit de paridad de x
    y_bytes = y_affine.to_bytes(32, 'little')
    if x_affine & 1:
        y_bytes = bytearray(y_bytes)
        y_bytes[31] |= 0x80
        y_bytes = bytes(y_bytes)
    return y_bytes


def point_decompress(y_bytes: bytes) -> Tuple[int, int, int, int]:
    """Descomprime 32 bytes a un punto en coordenadas extendidas."""
    y = int.from_bytes(y_bytes, 'little')
    sign = y >> 255
    y &= (1 << 255) - 1

    # Calcular x^2 = (y^2 - 1) / (d * y^2 + 1)
    y2 = y * y % P
    x_numer = (y2 - 1) % P
    x_denom = (D * y2 + 1) % P
    x_denom_inv = pow(x_denom, P - 2, P)  # inverso modular
    x_sq = (x_numer * x_denom_inv) % P
    # Raíz cuadrada: x = x_sq^((P+3)/8) mod P
    x = pow(x_sq, (P + 3) // 8, P)
    if (x * x - x_sq) % P != 0:
        x = x * pow(2, (P - 1) // 4, P) % P
    if (x * x - x_sq) % P != 0:
        raise ValueError("Punto inválido en la curva")

    if x & 1 != sign:
        x = P - x

    return (x, y, 1, x * y % P)


# ================================================================
# Funciones hash
# ================================================================

def sha512(data: bytes) -> bytes:
    """SHA-512."""
    return hashlib.sha512(data).digest()


def _decode_point(s: bytes) -> Tuple[int, int, int, int]:
    """Decodifica 32 bytes a punto en la curva."""
    return point_decompress(s)


def _encode_point(P: Tuple[int, int, int, int]) -> bytes:
    """Codifica punto a 32 bytes."""
    return point_compress(P)


# ================================================================
# API pública
# ================================================================

def generar_par_claves() -> Tuple[str, str]:
    """Genera un par de claves Ed25519.

    Returns:
        (clave_privada_hex, clave_publica_hex) como strings hex
    """
    # Semilla aleatoria de 32 bytes
    seed = os.urandom(32)

    # Hash la semilla con SHA-512
    h = sha512(seed)

    # "Clamping": ajustar los bits para cumplir con RFC 8032
    a = bytearray(h[:32])
    a[0] &= 248
    a[31] &= 127
    a[31] |= 64
    scalar = int.from_bytes(bytes(a), 'little')

    # Calcular clave pública: A = a * G
    G = (G_x, G_y, 1, G_x * G_y % P)
    A = point_mul(scalar, G)

    return seed.hex(), _encode_point(A).hex()


def _calc_public_key(seed: bytes) -> bytes:
    """Calcula clave pública a partir de una semilla."""
    h = sha512(seed)
    a = bytearray(h[:32])
    a[0] &= 248
    a[31] &= 127
    a[31] |= 64
    scalar = int.from_bytes(bytes(a), 'little')

    G = (G_x, G_y, 1, G_x * G_y % P)
    A = point_mul(scalar, G)
    return _encode_point(A)


def firmar(mensaje: bytes, clave_privada_hex: str) -> str:
    """Firma un mensaje con clave privada Ed25519.

    Args:
        mensaje: Mensaje a firmar (bytes)
        clave_privada_hex: Clave privada en hex (32 bytes → 64 chars)

    Returns:
        Firma en hex (64 bytes → 128 chars)
    """
    seed = bytes.fromhex(clave_privada_hex)

    # Hash la semilla
    h = sha512(seed)
    a_bytes = h[:32]
    prefix = h[32:]

    # Clamping
    a = bytearray(a_bytes)
    a[0] &= 248
    a[31] &= 127
    a[31] |= 64
    scalar = int.from_bytes(bytes(a), 'little')

    # Calcular r = SHA-512(prefix || mensaje) módulo l
    r_bytes = sha512(prefix + mensaje)
    r = int.from_bytes(r_bytes, 'little') % (2**252 + 27742317777372353535851937790883648493)

    # R = r * G
    G = (G_x, G_y, 1, G_x * G_y % P)
    R_point = point_mul(r, G)
    R_bytes = _encode_point(R_point)

    # S = (r + SHA-512(R || A || mensaje) * a) módulo l
    A_bytes = _calc_public_key(seed)
    hram = sha512(R_bytes + A_bytes + mensaje)
    hram_int = int.from_bytes(hram, 'little') % (2**252 + 27742317777372353535851937790883648493)
    S = (r + hram_int * scalar) % (2**252 + 27742317777372353535851937790883648493)

    return (R_bytes + S.to_bytes(32, 'little')).hex()


def verificar(mensaje: bytes, firma_hex: str, clave_publica_hex: str) -> bool:
    """Verifica una firma Ed25519.

    Args:
        mensaje: Mensaje firmado (bytes)
        firma_hex: Firma en hex (128 chars)
        clave_publica_hex: Clave pública en hex (64 chars)

    Returns:
        True si la firma es válida, False en caso contrario
    """
    try:
        firma = bytes.fromhex(firma_hex)
        public_key = bytes.fromhex(clave_publica_hex)
    except ValueError:
        return False

    if len(firma) != 64:
        return False
    if len(public_key) != 32:
        return False

    # Decodificar R y S
    R_bytes = firma[:32]
    S_bytes = firma[32:]

    # Verificar que S < l
    l = 2**252 + 27742317777372353535851937790883648493
    S_int = int.from_bytes(S_bytes, 'little')
    if S_int >= l:
        return False

    try:
        R = _decode_point(R_bytes)
        A = _decode_point(public_key)
    except ValueError:
        return False

    # Calcular h = SHA-512(R || A || mensaje)
    hram = sha512(R_bytes + public_key + mensaje)
    hram_int = int.from_bytes(hram, 'little') % l

    # Verificar: [S]G = R + [h]A
    G = (G_x, G_y, 1, G_x * G_y % P)
    SG = point_mul(S_int, G)
    hA = point_mul(hram_int, A)
    RhA = point_add(R, hA)

    return _encode_point(SG) == _encode_point(RhA)


def firmar_archivo(ruta_archivo: str, clave_privada_hex: str, ruta_firma: str = "") -> str:
    """Firma un archivo con Ed25519 y opcionalmente guarda la firma.

    Args:
        ruta_archivo: Ruta al archivo a firmar
        clave_privada_hex: Clave privada en hex
        ruta_firma: Ruta para guardar la firma (vacío = no guardar)

    Returns:
        Firma en hex
    """
    with open(ruta_archivo, 'rb') as f:
        contenido = f.read()

    firma = firmar(contenido, clave_privada_hex)

    if ruta_firma:
        with open(ruta_firma, 'w') as f:
            f.write(firma)

    return firma


def verificar_archivo(ruta_archivo: str, firma_hex: str, clave_publica_hex: str) -> bool:
    """Verifica la firma de un archivo.

    Args:
        ruta_archivo: Ruta al archivo firmado
        firma_hex: Firma en hex
        clave_publica_hex: Clave pública en hex

    Returns:
        True si la firma es válida
    """
    with open(ruta_archivo, 'rb') as f:
        contenido = f.read()
    return verificar(contenido, firma_hex, clave_publica_hex)


def _generar_clave_privada_determinista(seed: bytes) -> int:
    """Genera un escalar Ed25519 a partir de una semilla (uso interno)."""
    h = sha512(seed)
    a = bytearray(h[:32])
    a[0] &= 248
    a[31] &= 127
    a[31] |= 64
    return int.from_bytes(bytes(a), 'little')


if __name__ == '__main__':
    import sys

    if len(sys.argv) >= 2 and sys.argv[1] == 'generate':
        priv, pub = generar_par_claves()
        print(f"Clave privada: {priv}")
        print(f"Clave pública: {pub}")

    elif len(sys.argv) >= 4 and sys.argv[1] == 'sign':
        archivo = sys.argv[2]
        priv_key = sys.argv[3]
        firma = firmar_archivo(archivo, priv_key)
        print(f"Firma: {firma}")

    elif len(sys.argv) >= 5 and sys.argv[1] == 'verify':
        archivo = sys.argv[2]
        firma = sys.argv[3]
        pub_key = sys.argv[4]
        valida = verificar_archivo(archivo, firma, pub_key)
        print(f"Firma válida: {valida}")
        sys.exit(0 if valida else 1)

    else:
        print("Uso:")
        print("  python nucleo/ed25519_signer.py generate")
        print("  python nucleo/ed25519_signer.py sign <archivo> <clave_privada_hex>")
        print("  python nucleo/ed25519_signer.py verify <archivo> <firma_hex> <clave_publica_hex>")
