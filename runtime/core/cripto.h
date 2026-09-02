// cumple Manual 6 6: criptografía
// runtime/core/cripto.h — std.cripto: SHA-256 + Ed25519 API
// D-9(d) corte 8: extraído de synapse_rt.c (SHA-256 core + Ed25519 + randombytes stub)
// Manual 8: std.cripto — SHA-256 (FIPS 180-4) + Ed25519 (TweetNaCl)
#ifndef CRIPTO_H
#define CRIPTO_H

#include "synapse_rt_types.h"

// Public API — same signatures as the original (defined in synapse_rt.c)
void sha256_init(SHA256_CTX* ctx);
void sha256_update(SHA256_CTX* ctx, const uint8_t* data, size_t len);
void sha256_final(SHA256_CTX* ctx, uint8_t* digest);

CadenaSegura _syn_sha256_texto(CadenaSegura datos);
int _syn_ed25519_verificar(CadenaSegura mensaje, CadenaSegura firma, CadenaSegura clave_publica);

#endif /* CRIPTO_H */
