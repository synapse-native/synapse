/* gen_axon_test_fixtures.c — Generates Ed25519 test fixtures for E2E tests
 * Compile: gcc -I. -o tests/gen_axon_test_fixtures.exe tests/gen_axon_test_fixtures.c tweetnacl.c -lm
 * Usage: tests/gen_axon_test_fixtures.exe <tar_path> <sig_path> <pk_hex_out> <sk_hex_out>
 *
 * Generates an Ed25519 keypair, signs the tar file at <tar_path>,
 * writes 64-byte raw signature to <sig_path>,
 * writes hex public key to <pk_hex_out> and hex secret key to <sk_hex_out>.
 *
 * NOTE: randombytes() is called by crypto_sign_keypair in tweetnacl.c.
 * We provide a deterministic stub for reproducible test fixtures.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "tweetnacl.h"

/* Deterministic randombytes stub for reproducible test fixtures */
static unsigned char _rnd_buf[256];
static int _rnd_pos = 0;

void randombytes(unsigned char *x, unsigned long long xlen) {
    for (unsigned long long i = 0; i < xlen; i++) {
        if (_rnd_pos >= 256) _rnd_pos = 0;
        x[i] = _rnd_buf[_rnd_pos++];
    }
}

static void bin_to_hex(const unsigned char *bin, int len, char *hex) {
    for (int i = 0; i < len; i++)
        sprintf(hex + i * 2, "%02x", bin[i]);
    hex[len * 2] = 0;
}

int main(int argc, char **argv) {
    if (argc != 5) {
        fprintf(stderr, "Usage: %s <tar_path> <sig_path> <pk_hex_out> <sk_hex_out>\n", argv[0]);
        return 1;
    }

    const char *tar_path = argv[1];
    const char *sig_path = argv[2];
    const char *pk_out   = argv[3];
    const char *sk_out   = argv[4];

    /* Initialize deterministic random buffer */
    for (int i = 0; i < 256; i++)
        _rnd_buf[i] = (unsigned char)(i * 17 + 42);

    /* Generate Ed25519 keypair */
    unsigned char pk[crypto_sign_PUBLICKEYBYTES];
    unsigned char sk[crypto_sign_SECRETKEYBYTES];
    crypto_sign_keypair(pk, sk);

    /* Read tar file */
    FILE *f = fopen(tar_path, "rb");
    if (!f) { fprintf(stderr, "ERROR: Cannot open %s\n", tar_path); return 1; }
    fseek(f, 0, SEEK_END);
    long fsz = ftell(f);
    fseek(f, 0, SEEK_SET);
    unsigned char *msg = (unsigned char*)malloc((size_t)fsz + 1);
    if (!msg) { fclose(f); fprintf(stderr, "ERROR: malloc failed\n"); return 1; }
    size_t nread = fread(msg, 1, (size_t)fsz, f);
    fclose(f);
    if ((long)nread != fsz) { free(msg); fprintf(stderr, "ERROR: read failed\n"); return 1; }

    /* Sign the message (crypto_sign prepends 64-byte signature) */
    unsigned char *sm = (unsigned char*)malloc((size_t)fsz + crypto_sign_BYTES);
    unsigned long long smlen;
    if (crypto_sign(sm, &smlen, msg, (unsigned long long)fsz, sk) != 0) {
        free(msg); free(sm);
        fprintf(stderr, "ERROR: crypto_sign failed\n");
        return 1;
    }

    /* Write just the 64-byte signature to sig_path */
    f = fopen(sig_path, "wb");
    if (!f) { free(msg); free(sm); fprintf(stderr, "ERROR: Cannot open %s\n", sig_path); return 1; }
    fwrite(sm, 1, crypto_sign_BYTES, f);
    fclose(f);

    /* Write hex public key to pk_out */
    char pk_hex[crypto_sign_PUBLICKEYBYTES * 2 + 1];
    bin_to_hex(pk, crypto_sign_PUBLICKEYBYTES, pk_hex);
    f = fopen(pk_out, "w");
    if (!f) { free(msg); free(sm); fprintf(stderr, "ERROR: Cannot open %s\n", pk_out); return 1; }
    fprintf(f, "%s\n", pk_hex);
    fclose(f);
    printf("[gen] PK: %s\n", pk_hex);

    /* Write hex secret key to sk_out */
    char sk_hex[crypto_sign_SECRETKEYBYTES * 2 + 1];
    bin_to_hex(sk, crypto_sign_SECRETKEYBYTES, sk_hex);
    f = fopen(sk_out, "w");
    if (!f) { free(msg); free(sm); fprintf(stderr, "ERROR: Cannot open %s\n", sk_out); return 1; }
    fprintf(f, "%s\n", sk_hex);
    fclose(f);
    printf("[gen] SK: %s\n", sk_hex);

    printf("[gen] Signature written to %s\n", sig_path);

    free(msg);
    free(sm);
    return 0;
}
