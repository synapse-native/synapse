/* test_detect_hardware.c — Integration test for hardware detection (M4.1)
 * Tests: simulated 8GB vs 32GB profiles produce distinct model/config selections
 * Compile: gcc -I. -o tests/test_detect_hardware.exe tests/test_detect_hardware.c nucleo/detect_hardware.c -lm -lgdi32
 * Run:    tests/test_detect_hardware.exe
 */

#include "nucleo/detect_hardware.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

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

/* --- Test helpers --- */

static void assert_tier(HwProfile* p, HwTier expected) {
    TEST("Tier correcto", p->tier == expected, "got %d, exp %d", p->tier, expected);
}

static void assert_modelo_contains(HwProfile* p, const char* substr) {
    int ok = strstr(p->modelo_sugerido, substr) != NULL;
    TEST("Modelo contiene substring", ok, "modelo=%s, esperado contiene=%s", p->modelo_sugerido, substr);
}

static void assert_ctx_between(HwProfile* p, int lo, int hi) {
    TEST("ctx-size en rango", p->ctx_size_sugerido >= lo && p->ctx_size_sugerido <= hi,
         "ctx=%d, esperado [%d,%d]", p->ctx_size_sugerido, lo, hi);
}

static void assert_threads_positive(HwProfile* p) {
    TEST("threads > 0", p->threads_sugeridos > 0, "threads=%d", p->threads_sugeridos);
}

static void assert_ngl_zero(HwProfile* p) {
    TEST("ngl == 0 (sin VRAM)", p->ngl_sugerido == 0, "ngl=%d", p->ngl_sugerido);
}

/* --- Simulated profile tests --- */

static void test_8gb_profile() {
    fprintf(stderr, "\n=== PERFIL: 8 GB RAM, 2 cores, sin VRAM ===\n");
    HwProfile p;
    memset(&p, 0, sizeof(p));
    p.total_ram_gb = 8.0;
    p.cpu_logicos = 4;
    p.cpu_fisicos = 2;
    p.vram_gb = 0.0;
    synapse_hw_sugerir_config(&p);

    assert_tier(&p, HW_TIER_1B);
    assert_modelo_contains(&p, "1B");
    assert_ctx_between(&p, 2048, 8192);
    assert_threads_positive(&p);
    assert_ngl_zero(&p);
}

static void test_32gb_profile() {
    fprintf(stderr, "\n=== PERFIL: 32 GB RAM, 8 cores, VRAM 6 GB ===\n");
    HwProfile p;
    memset(&p, 0, sizeof(p));
    p.total_ram_gb = 32.0;
    p.cpu_logicos = 16;
    p.cpu_fisicos = 8;
    p.vram_gb = 6.0;
    synapse_hw_sugerir_config(&p);

    assert_tier(&p, HW_TIER_7B);
    assert_modelo_contains(&p, "7B");
    assert_ctx_between(&p, 4096, 16384);
    assert_threads_positive(&p);
    TEST("ngl > 0 (con VRAM)", p.ngl_sugerido > 0, "ngl=%d", p.ngl_sugerido);
    TEST("ngl >= 20", p.ngl_sugerido >= 20, "ngl=%d", p.ngl_sugerido);
}

static void test_64gb_profile() {
    fprintf(stderr, "\n=== PERFIL: 64 GB RAM, 16 cores, VRAM 12 GB ===\n");
    HwProfile p;
    memset(&p, 0, sizeof(p));
    p.total_ram_gb = 64.0;
    p.cpu_logicos = 32;
    p.cpu_fisicos = 16;
    p.vram_gb = 12.0;
    synapse_hw_sugerir_config(&p);

    assert_tier(&p, HW_TIER_70B);
    assert_modelo_contains(&p, "70B");
    assert_ctx_between(&p, 4096, 16384);
    assert_threads_positive(&p);
    TEST("ngl == 999 (VRAM >= 6GB)", p.ngl_sugerido == 999, "ngl=%d", p.ngl_sugerido);
}

static void test_4gb_profile() {
    fprintf(stderr, "\n=== PERFIL: 4 GB RAM (insuficiente) ===\n");
    HwProfile p;
    memset(&p, 0, sizeof(p));
    p.total_ram_gb = 4.0;
    p.cpu_logicos = 2;
    p.cpu_fisicos = 1;
    p.vram_gb = 0.0;
    synapse_hw_sugerir_config(&p);

    assert_tier(&p, HW_TIER_INSUFICIENTE);
    assert_modelo_contains(&p, "desconocido");
    assert_ctx_between(&p, 1024, 4096);
    assert_threads_positive(&p);
    assert_ngl_zero(&p);
}

static void test_16gb_vram_4gb_profile() {
    fprintf(stderr, "\n=== PERFIL: 16 GB RAM, VRAM 4 GB (mid-range GPU) ===\n");
    HwProfile p;
    memset(&p, 0, sizeof(p));
    p.total_ram_gb = 16.0;
    p.cpu_logicos = 8;
    p.cpu_fisicos = 4;
    p.vram_gb = 4.0;
    synapse_hw_sugerir_config(&p);

    assert_tier(&p, HW_TIER_1B);
    TEST("ngl entre 8 y 30 (VRAM 4GB)", p.ngl_sugerido > 0 && p.ngl_sugerido < 999,
         "ngl=%d", p.ngl_sugerido);
    TEST("ngl == 20 (VRAM exactamente 4GB)", p.ngl_sugerido == 20, "ngl=%d", p.ngl_sugerido);
}

/* --- Real hardware detection test --- */
static void test_real_hw_detection() {
    fprintf(stderr, "\n=== PERFIL REAL (maquina actual) ===\n");
    HwProfile p;
    int rc = synapse_detectar_hardware(&p);
    TEST("Deteccion real exitosa", rc == 0, "rc=%d", rc);
    TEST("RAM > 0", p.total_ram_gb > 0.0, "ram=%.1f", p.total_ram_gb);
    TEST("CPUs fisicos > 0", p.cpu_fisicos > 0, "cores=%d", p.cpu_fisicos);
    TEST("CPUs logicos > 0", p.cpu_logicos > 0, "logicos=%d", p.cpu_logicos);
    TEST("CPUs logicos >= fisicos", p.cpu_logicos >= p.cpu_fisicos, "log=%d fis=%d",
         p.cpu_logicos, p.cpu_fisicos);
    TEST("modelo sugerido no vacio", strlen(p.modelo_sugerido) > 0, "");
    TEST("ctx-size sugerido > 0", p.ctx_size_sugerido > 0, "ctx=%d", p.ctx_size_sugerido);
    TEST("threads sugeridos > 0", p.threads_sugeridos > 0, "threads=%d", p.threads_sugeridos);
}

/* --- JSON serialization test --- */
static void test_json_output() {
    fprintf(stderr, "\n=== SERIALIZACION JSON ===\n");
    HwProfile p;
    memset(&p, 0, sizeof(p));
    p.total_ram_gb = 16.0;
    p.vram_gb = 2.0;
    p.cpu_logicos = 8;
    p.cpu_fisicos = 4;
    p.tier = HW_TIER_1B;
    strncpy(p.modelo_sugerido, "Llama-3.2-1B-Instruct-Q4_K_M.gguf", sizeof(p.modelo_sugerido));
    p.ctx_size_sugerido = 4096;
    p.threads_sugeridos = 3;
    p.ngl_sugerido = 8;

    char buf[512];
    int rc = synapse_hw_to_json(&p, buf, sizeof(buf));
    TEST("JSON serializado", rc == 0, "rc=%d", rc);
    TEST("JSON contiene ram_gb", strstr(buf, "ram_gb") != NULL, "");
    TEST("JSON contiene modelo", strstr(buf, "modelo") != NULL, "");
    TEST("JSON contiene ctx_size", strstr(buf, "ctx_size") != NULL, "");
    TEST("JSON contiene threads", strstr(buf, "threads") != NULL, "");
    TEST("JSON contiene ngl", strstr(buf, "ngl") != NULL, "");
    TEST("JSON parseable como float", strstr(buf, "16.0") != NULL, "");
}

/* --- Diff test: 8GB vs 32GB produce different configs --- */
static void test_config_diff() {
    fprintf(stderr, "\n=== DIFERENCIACION: 8GB vs 32GB ===\n");
    HwProfile p8, p32;
    memset(&p8, 0, sizeof(p8)); p8.total_ram_gb = 8.0; p8.cpu_fisicos = 2; p8.cpu_logicos = 4;
    memset(&p32, 0, sizeof(p32)); p32.total_ram_gb = 32.0; p32.cpu_fisicos = 8; p32.cpu_logicos = 16;
    synapse_hw_sugerir_config(&p8);
    synapse_hw_sugerir_config(&p32);

    TEST("Tiers distintos", p8.tier != p32.tier, "8GB=%d 32GB=%d", p8.tier, p32.tier);
    TEST("Modelos distintos", strcmp(p8.modelo_sugerido, p32.modelo_sugerido) != 0,
         "8GB=%s 32GB=%s", p8.modelo_sugerido, p32.modelo_sugerido);
    TEST("ctx-size distintos", p8.ctx_size_sugerido != p32.ctx_size_sugerido,
         "8GB=%d 32GB=%d", p8.ctx_size_sugerido, p32.ctx_size_sugerido);
    TEST("threads distintos", p8.threads_sugeridos != p32.threads_sugeridos,
         "8GB=%d 32GB=%d", p8.threads_sugeridos, p32.threads_sugeridos);
}

int main() {
    fprintf(stderr, "============================================================\n");
    fprintf(stderr, "  AXON HARDWARE DETECTION TEST SUITE (M4.1)\n");
    fprintf(stderr, "============================================================\n");

    test_8gb_profile();
    test_32gb_profile();
    test_64gb_profile();
    test_4gb_profile();
    test_16gb_vram_4gb_profile();
    test_real_hw_detection();
    test_json_output();
    test_config_diff();

    fprintf(stderr, "\n============================================================\n");
    fprintf(stderr, "  RESULTADOS: %d passed, %d failed, %d total\n",
            g_passed, g_failed, g_passed + g_failed);
    fprintf(stderr, "============================================================\n");

    if (g_failed == 0) {
        fprintf(stderr, "\n  [OK] TODOS LOS TESTS DE HARDWARE PASARON\n");
        fprintf(stderr, "  [OK] M4.1 --detect-hardware: deteccion + diferenciacion validada\n\n");
        return 0;
    }
    fprintf(stderr, "\n  [FAIL] %d TESTS FALLARON\n\n", g_failed);
    return 1;
}
