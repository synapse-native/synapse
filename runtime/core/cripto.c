// cumple Manual 6 §6: criptografía
// runtime/core/cripto.c — std.cripto: SHA-256 + Ed25519
// D-9(d) corte 8: extraído de synapse_rt.c (lines 122-182 y 523-646)
// Manual 8: std.cripto — SHA-256 (FIPS 180-4) + Ed25519 (TweetNaCl)

#include "runtime/core/cripto.h"
#include "axon/tweetnacl.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifdef _WIN32
  #include <windows.h>
  #include <wincrypt.h>
#else
  #include <unistd.h>
  #include <sys/types.h>
  #ifdef __linux__
  #include <sys/random.h>
  #endif
#endif

// --- Ed25519 Verification (via TweetNaCl) ---
// Verifica una firma Ed25519 sobre un mensaje.
// Parametros:
//   mensaje: texto plano original
//   firma: firma de 64 bytes (R || S)
//   clave_publica: clave publica de 32 bytes
// Retorna: 0 si la firma es valida, -1 si es invalida

// randombytes stub for TweetNaCl (only needed if crypto_sign_keypair is linked)
// Uses OS-provided CSPRNG instead of rand() for cryptographic security.
void randombytes(unsigned char* x, unsigned long long xlen) ;
void randombytes(unsigned char* x, unsigned long long xlen) {
    if (xlen == 0) return;
#ifdef _WIN32
    HCRYPTPROV hProv = 0;
    if (CryptAcquireContextA(&hProv, NULL, NULL, PROV_RSA_FULL,
                             CRYPT_VERIFYCONTEXT)) {
        CryptGenRandom(hProv, (DWORD)xlen, x);
        CryptReleaseContext(hProv, 0);
    } else {
        for (unsigned long long i = 0; i < xlen; i++) x[i] = 0;
    }
#else
    FILE* f = fopen("/dev/urandom", "rb");
    if (f) {
        size_t n = fread(x, 1, (size_t)xlen, f);
        fclose(f);
        for (unsigned long long i = n; i < xlen; i++) x[i] = 0;
    } else {
        #ifdef __linux__
        ssize_t ret = getrandom(x, (size_t)xlen, 0);
        if (ret < 0) {
            for (unsigned long long i = 0; i < xlen; i++) x[i] = 0;
        }
        #else
        for (unsigned long long i = 0; i < xlen; i++) x[i] = 0;
        #endif
    }
#endif
}

int _syn_ed25519_verificar(CadenaSegura mensaje, CadenaSegura firma, CadenaSegura clave_publica) {
    if (firma.longitud < 64 || clave_publica.longitud < 32) {
        return -1;
    }
    unsigned long long mlen = 0;
    unsigned char* sm = (unsigned char*)malloc((size_t)(mensaje.longitud + 64));
    if (!sm) return -1;
    memcpy(sm, firma.datos, 64);
    memcpy(sm + 64, mensaje.datos, (size_t)mensaje.longitud);
    unsigned long long smlen = (unsigned long long)(mensaje.longitud + 64);
    unsigned char* pk = (unsigned char*)clave_publica.datos;
    // Use separate buffer for output (TweetNaCl requires m != sm)
    // crypto_sign_open writes smlen (mensaje.longitud+64) bytes into m, so allocate that.
    unsigned char* m_buf = (unsigned char*)malloc((size_t)(mensaje.longitud + 64));
    if (!m_buf) { free(sm); return -1; }
    int rc = crypto_sign_open(m_buf, &mlen, sm, smlen, pk);
    free(sm);
    free(m_buf);
    return rc;
}
// ============================================================
// std.cripto — SHA-256 (FIPS 180-4) + Ed25519 (TweetNaCl)
#include "axon/tweetnacl.h"// --- SHA-256 (sin cambios) ---
// ============================================================
// (typedef SHA256_CTX movido a synapse_rt_types.h en D-9(d) corte 4:
//  lo comparten synapse_rt.c y runtime/core/cluster.c.)

static const uint32_t K[64] = {
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5,
    0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3,
    0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc,
    0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7,
    0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13,
    0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3,
    0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5,
    0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208,
    0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2
};

#define ROTR(x, n) (((x) >> (n)) | ((x) << (32 - (n))))
#define CH(x, y, z) (((x) & (y)) ^ (~(x) & (z)))
#define MAJ(x, y, z) (((x) & (y)) ^ ((x) & (z)) ^ ((y) & (z)))
#define SIG0(x) (ROTR(x, 2) ^ ROTR(x, 13) ^ ROTR(x, 22))
#define SIG1(x) (ROTR(x, 6) ^ ROTR(x, 11) ^ ROTR(x, 25))
#define sig0(x) (ROTR(x, 7) ^ ROTR(x, 18) ^ ((x) >> 3))
#define sig1(x) (ROTR(x, 17) ^ ROTR(x, 19) ^ ((x) >> 10))

static void sha256_transform(SHA256_CTX* ctx, const uint8_t* block) {
    uint32_t W[64];
    for (int i = 0; i < 16; i++) {
        W[i] = ((uint32_t)block[i*4] << 24) | ((uint32_t)block[i*4+1] << 16)
             | ((uint32_t)block[i*4+2] << 8)  | (uint32_t)block[i*4+3];
    }
    for (int i = 16; i < 64; i++) {
        W[i] = sig1(W[i-2]) + W[i-7] + sig0(W[i-15]) + W[i-16];
    }

    uint32_t a = ctx->state[0], b = ctx->state[1];
    uint32_t c = ctx->state[2], d = ctx->state[3];
    uint32_t e = ctx->state[4], f = ctx->state[5];
    uint32_t g = ctx->state[6], h = ctx->state[7];

    for (int i = 0; i < 64; i++) {
        uint32_t T1 = h + SIG1(e) + CH(e, f, g) + K[i] + W[i];
        uint32_t T2 = SIG0(a) + MAJ(a, b, c);
        h = g; g = f; f = e; e = d + T1;
        d = c; c = b; b = a; a = T1 + T2;
    }

    ctx->state[0] += a; ctx->state[1] += b;
    ctx->state[2] += c; ctx->state[3] += d;
    ctx->state[4] += e; ctx->state[5] += f;
    ctx->state[6] += g; ctx->state[7] += h;
}

void sha256_init(SHA256_CTX* ctx) {
    ctx->state[0] = 0x6a09e667; ctx->state[1] = 0xbb67ae85;
    ctx->state[2] = 0x3c6ef372; ctx->state[3] = 0xa54ff53a;
    ctx->state[4] = 0x510e527f; ctx->state[5] = 0x9b05688c;
    ctx->state[6] = 0x1f83d9ab; ctx->state[7] = 0x5be0cd19;
    ctx->bitcount = 0;
    ctx->buffer_len = 0;
}

void sha256_update(SHA256_CTX* ctx, const uint8_t* data, size_t len) {
    for (size_t i = 0; i < len; i++) {
        ctx->buffer[ctx->buffer_len++] = data[i];
        ctx->bitcount += 8;
        if (ctx->buffer_len == SHA256_BLOCK_SIZE) {
            sha256_transform(ctx, ctx->buffer);
            ctx->buffer_len = 0;
        }
    }
}

void sha256_final(SHA256_CTX* ctx, uint8_t* digest) {
    uint64_t bitcount = ctx->bitcount;
    ctx->buffer[ctx->buffer_len++] = 0x80;
    if (ctx->buffer_len > 56) {
        while (ctx->buffer_len < SHA256_BLOCK_SIZE)
            ctx->buffer[ctx->buffer_len++] = 0;
        sha256_transform(ctx, ctx->buffer);
        ctx->buffer_len = 0;
    }
    while (ctx->buffer_len < 56)
        ctx->buffer[ctx->buffer_len++] = 0;
    for (int i = 7; i >= 0; i--) {
        ctx->buffer[56 + i] = (uint8_t)(bitcount >> ((7 - i) * 8));
    }
    sha256_transform(ctx, ctx->buffer);
    for (int i = 0; i < 8; i++) {
        digest[i*4]   = (ctx->state[i] >> 24) & 0xFF;
        digest[i*4+1] = (ctx->state[i] >> 16) & 0xFF;
        digest[i*4+2] = (ctx->state[i] >> 8) & 0xFF;
        digest[i*4+3] = ctx->state[i] & 0xFF;
    }
}

CadenaSegura _syn_sha256_texto(CadenaSegura datos) {
    SHA256_CTX ctx;
    uint8_t digest[SHA256_DIGEST_SIZE];
    char hex[65];

    sha256_init(&ctx);
    sha256_update(&ctx, (const uint8_t*)datos.datos, (size_t)datos.longitud);
    sha256_final(&ctx, digest);

    for (int i = 0; i < SHA256_DIGEST_SIZE; i++) {
        sprintf(hex + i * 2, "%02x", digest[i]);
    }
    hex[64] = '\0';

    char* data = (char*)malloc(65);
    if (!data) return (CadenaSegura){ .longitud = 0, .datos = "" };
    memcpy(data, hex, 65);
    return (CadenaSegura){ .longitud = 64, .datos = data };
}
