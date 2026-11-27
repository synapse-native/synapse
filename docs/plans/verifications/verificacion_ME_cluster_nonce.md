# Verificación ME — A1: nonce del HELLO con CSPRNG (cluster.c)

## Requisito 1: nonce aleatorio criptográfico de 32 bytes

- CUMPLE: `runtime/core/cluster.c` `cluster_generar_nonce()` usa `randombytes(raw, 32)`
  (CSPRNG) en lugar de `rand() % 256`, con comentario `cumple Manual 6 §5.3`.
- Oración de oracle: `runtime/core/cluster.c` compila con GCC (rc=0) y
  `tests/unit/test_axon_crypto.py` ejecuta (el fixture autouse de conftest recompila
  cluster.o como parte del runtime; los tests de cripto/clúster pasan). El nonce ahora
  es no predecible, alineado con §5.3.
