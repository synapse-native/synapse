# Plan ME — M1: Formato HELLO binario [32][32][64]

## Requisito 1: HELLO firmado en formato binario normativo

requisito: Manual 6 §5.3 (Handshake Ed25519 Zero-Trust): "Estructura del
  mensaje HELLO: [nonce (32 bytes)] [clave_publica (32 bytes)] [firma (64 bytes)]."
texto: El código actual (`cluster_enviar_hello_firmado`) emite texto
  `HELLO:<id>:<nonce_hex>:<pubkey_hex>:<firma_hex>` (delimitado por `:`,
  con campo `id` adicional no especificado). El receptor
  (`_cluster_procesar_hello_entrante`) parsea este formato textual.
  El manual exige layout binario de 128 bytes sin delimitadores.
implementacion:
  1. `cluster_enviar_hello_firmado`: decodifica hex→bytes, emite buffer
     binario de 128 bytes: [nonce 32B][pubkey 32B][firma 64B]. Se añade
     prefijo `HELLO:` (6 bytes) para que el receptor lo identifique.
  2. `_cluster_procesar_hello_entrante`: tras detectar prefijo `HELLO:`,
     parsea 128 bytes binarios en vez de sscanf de campos hex.
  3. HELLO_RESP: también binario [32][32][64] con prefijo `HELLO_RESP:`.
  4. `cluster_enviar_hello` (no firmado, discovery): se mantiene textual
     (no especificado en manual como binario).
oraculo: tests/test_cluster_handshake_e2e.c compila y ejecuta (rc=0);
  tests/integration/test_cluster_adv_10.py verifica presencia de
  cluster_enviar_hello_firmado.

## Requisito 2: HELLO_RESP también en formato binario

requisito: Manual 6 §5.3 — el servidor responde con la misma estructura:
  [nonce (32 bytes)] [clave_publica (32 bytes)] [firma (64 bytes)].
texto: `_cluster_procesar_hello_entrante` envía HELLO_RESP como texto
  `HELLO_RESP:<id>:<nonce_hex>:<pk_hex>:<firma_hex>`. Debe cambiarse
  a binario para alinearse con la especificación.
implementacion: el response se construye como buffer binario 128 bytes
  con prefijo `HELLO_RESP:` (11 bytes). El parser del cliente (si existe)
  debe adaptarse. Por ahora el parser del servidor es el único receiver
  documentado.
oraculo: tests/test_cluster_handshake_e2e.c — test 7 (Envio HELLO) pasa.
