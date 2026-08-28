# Verificación ME — M1: Formato HELLO binario [32][32][64]

## Requisito 1: HELLO firmado en formato binario normativo

- CUMPLE: `runtime/core/cluster.c` `cluster_enviar_hello_firmado()` ahora emite
  buffer binario de 134 bytes: prefijo `HELLO:` (6B) + [nonce 32B][pubkey 32B]
  [firma 64B]. Los valores hex de entrada se decodifican a bytes crudos vía
  `_hex_a_bytes()`. Comentario grep-chequeable `cumple Manual 6 §5.3`.
- `_cluster_procesar_hello_entrante()` ahora parsea 134 bytes binarios
  (6 prefix + 128 data) en vez de sscanf de campos hex. Los bytes se
  re-codifican a hex para verificación de firma Ed25519.
- Oración de oracle: `runtime/core/cluster.c` compila con GCC (rc=0) y
  `tests/unit/test_axon_crypto.py` ejecuta (fixture autouse recompila cluster.o).

## Requisito 2: HELLO_RESP también en formato binario

- CUMPLE: `_cluster_procesar_hello_entrante()` responde con buffer binario
  de 139 bytes: prefijo `HELLO_RESP:` (11B) + [nonce 32B][pubkey 32B][firma 64B].
  Los bytes del nonce se generan directamente (sin pasar por hex intermedio)
  para evitar ida y vuelta innecesaria.

## Conclusión

CUMPLE Manual 6 §5.3. El formato wire del handshake HELLO ahora es binario
[32][32][64] como especifica el manual, reemplazando el formato textual
colon-delimitado `HELLO:<id>:<nonce_hex>:<pk_hex>:<firma_hex>`.
