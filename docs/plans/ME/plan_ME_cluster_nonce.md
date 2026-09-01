# Plan ME — A1: nonce del HELLO con CSPRNG (cluster.c)

## Requisito 1: nonce aleatorio criptográfico de 32 bytes

requisito: Manual 6 §5.3 (Handshake Ed25519 Zero-Trust): "El cliente envía un
  mensaje `HELLO` con su clave pública y una firma de un **nonce aleatorio de 32
  bytes**."
texto: El nonce del HELLO debe ser generado por un CSPRNG. `rand()` es un PRNG no
  criptográfico y potencialmente predecible, lo que en un protocolo zero-trust
  permite replay/predictibilidad. El tráfico de sesión ya usa `randombytes`
  (cluster.c:164), por lo que el nonce del handshake era la única excepción.
implementacion: En `runtime/core/cluster.c`, `cluster_generar_nonce()` reemplazó el
  bucle `raw[i] = (unsigned char)(rand() % 256);` por `randombytes(raw, 32);`
  (CSPRNG declarado en cluster.c:41 y definido en cripto.c: CryptGenRandom /
  getrandom / /dev/urandom). Se mantiene la codificación hex posterior. Comentario
  grep-chequeable `cumple Manual 6 §5.3`.
oraculo: tests/unit/test_axon_crypto.py
