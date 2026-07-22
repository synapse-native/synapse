// Test de intrusion: validacion Ed25519 con vectores de prueba conocidos (RFC 8032)
// Compilar: gcc -include tweetnacl.h -o tests/test_ed25519_axon.exe tests/test_ed25519_axon.c synapse_rt.c tweetnacl.c -lm -lpthread -lws2_32
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct { int longitud; char* datos; } CadenaSegura;

// Variables for comparing expected vs actual results
static int passed = 0, failed = 0;

// Wrap _syn_ed25519_verificar for direct testing (bypasses file I/O)
extern int _syn_ed25519_verificar(CadenaSegura mensaje, CadenaSegura firma, CadenaSegura clave_publica);
extern int _syn_axon_verificar_firma(const char* tar_ruta, const char* sig_ruta, const char* clave_publica_hex);

extern int crypto_sign_keypair(unsigned char* pk, unsigned char* sk);

void test_direct(const char* nombre, CadenaSegura msg, CadenaSegura sig, CadenaSegura pk, int esperado) {
    int rc = _syn_ed25519_verificar(msg, sig, pk);
    if ((rc == 0 && esperado == 0) || (rc != 0 && esperado != 0)) {
        printf("  PASS (rc=%d)\n", rc);
        passed++;
    } else {
        printf("  FAIL (rc=%d, esperado=%d)\n", rc, esperado);
        failed++;
    }
}

void test_file_io(const char* nombre, const char* tar_ruta, const char* sig_ruta, const char* pk_hex, int esperado) {
    int rc = _syn_axon_verificar_firma(tar_ruta, sig_ruta, pk_hex);
    if ((rc == 0 && esperado == 0) || (rc != 0 && esperado != 0)) {
        printf("  PASS (rc=%d)\n", rc);
        passed++;
    } else {
        printf("  FAIL (rc=%d, esperado=%d)\n", rc, esperado);
        failed++;
    }
}

int main() {
    system("mkdir .axon_cache 2>nul");
    printf("=== TEST ED25519 AXON (Intrusion) ===\n\n");

    // ===== VECTOR DE PRUEBA 1: RFC 8032 Section 7.1 =====
    // Mensaje: "" (empty string)
    // Clave publica: d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a
    // Firma: e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e065224901555fb8821590a33bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b

    printf("[TEST 1a] RFC8032 vector firmado (directo)...\n");
    unsigned char pk1[32], sig1[64];
    const char* pk1_hex = "d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a";
    for (int i = 0; i < 32; i++) {
        unsigned int b; char h[3] = { pk1_hex[i*2], pk1_hex[i*2+1], 0 };
        sscanf(h, "%x", &b); pk1[i] = (unsigned char)b;
    }
    const char* sig1_hex = "e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e065224901555fb8821590a33bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b";
    for (int i = 0; i < 64; i++) {
        unsigned int b; char h[3] = { sig1_hex[i*2], sig1_hex[i*2+1], 0 };
        sscanf(h, "%x", &b); sig1[i] = (unsigned char)b;
    }
    CadenaSegura msg_empty = { .longitud = 0, .datos = "" };
    CadenaSegura sig_cs = { .longitud = 64, .datos = (char*)sig1 };
    CadenaSegura pk_cs = { .longitud = 32, .datos = (char*)pk1 };
    test_direct("RFC8032 empty msg", msg_empty, sig_cs, pk_cs, 0);

    // ===== VECTOR DE PRUEBA 2: File I/O path =====
    printf("[TEST 1b] RFC8032 vector via archivos...\n");
    // Write message (empty)
    FILE* f = fopen(".axon_cache/rfc_test.tar", "wb");
    fputc(0, f); fclose(f);  // write one null byte as empty message marker
    f = fopen(".axon_cache/rfc_test.tar", "wb");
    fclose(f);  // truly empty file
    // Write signature
    f = fopen(".axon_cache/rfc_test.tar.sig", "wb");
    fwrite(sig1, 1, 64, f);
    fclose(f);
    test_file_io("RFC8032 via file I/O", ".axon_cache/rfc_test.tar", ".axon_cache/rfc_test.tar.sig", pk1_hex, 0);

    // ===== PRUEBA 3: Firma corrupta debe fallar =====
    printf("[TEST 2] Firma corrupta (rechazada)...\n");
    f = fopen(".axon_cache/rfc_test.tar.sig", "r+b");
    if (f) { fputc(0xFF, f); fclose(f); }
    test_file_io("sig corrupta", ".axon_cache/rfc_test.tar", ".axon_cache/rfc_test.tar.sig", pk1_hex, -1);

    // ===== PRUEBA 4: Mensaje corrupto debe fallar =====
    printf("[TEST 3] Mensaje corrupto (rechazado)...\n");
    // Restore correct sig
    f = fopen(".axon_cache/rfc_test.tar.sig", "wb");
    if (f) { fwrite(sig1, 1, 64, f); fclose(f); }
    // Write wrong message
    f = fopen(".axon_cache/rfc_test.tar", "wb");
    if (f) { fputs("WRONG", f); fclose(f); }
    test_file_io("tar corrupto", ".axon_cache/rfc_test.tar", ".axon_cache/rfc_test.tar.sig", pk1_hex, -1);

    // ===== PRUEBA 5: Clave incorrecta debe fallar =====
    printf("[TEST 4] Clave publica incorrecta (rechazado)...\n");
    // Use a different known public key
    const char* wrong_pk_hex = "0000000000000000000000000000000000000000000000000000000000000000";
    // Restore correct files
    f = fopen(".axon_cache/rfc_test.tar", "wb"); fclose(f);
    f = fopen(".axon_cache/rfc_test.tar.sig", "wb");
    if (f) { fwrite(sig1, 1, 64, f); fclose(f); }
    test_file_io("wrong key", ".axon_cache/rfc_test.tar", ".axon_cache/rfc_test.tar.sig", wrong_pk_hex, -1);

    // ===== PRUEBA 6: Signature file demasiado corto =====
    printf("[TEST 5] Firma corta (rechazado)...\n");
    f = fopen(".axon_cache/rfc_test.tar.sig", "wb");
    if (f) { fwrite(sig1, 1, 32, f); fclose(f); }  // only 32 bytes
    test_file_io("sig corta", ".axon_cache/rfc_test.tar", ".axon_cache/rfc_test.tar.sig", pk1_hex, -1);

    // ===== PRUEBA 7: Hex clave invalido =====
    printf("[TEST 6] Hex clave invalido (rechazado)...\n");
    f = fopen(".axon_cache/rfc_test.tar.sig", "wb");
    if (f) { fwrite(sig1, 1, 64, f); fclose(f); }
    test_file_io("hex invalido", ".axon_cache/rfc_test.tar", ".axon_cache/rfc_test.tar.sig", "xyz", -1);

    // Summary
    printf("\n=== RESULTADOS: %d passed, %d failed, %d total ===\n", passed, failed, passed+failed);
    if (failed == 0) printf("TODOS LOS TEST PASARON\n");
    return failed > 0 ? 1 : 0;
}
