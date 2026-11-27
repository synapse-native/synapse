#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// Forward declarations from synapse_rt.c
int _syn_tar_extraer(const char* tar_ruta, const char* salida_dir);
int _syn_axon_buscar_local(const char* paquete, const char* version,
                           char* tar_path, int tar_sz,
                           char* extract_dir, int ext_sz);

int main() {
    int passed = 0;
    int failed = 0;
    
    printf("=== Test: Path Traversal Protection ===\n\n");
    
    // Test 1: Regular file - should succeed
    printf("Test 1: Archivo normal... ");
    fflush(stdout);
    system("mkdir -p .axon_cache/tar_test_out");
    int rc = _syn_tar_extraer("tests/fixtures/malicious.tar", ".axon_cache/tar_test_out");
    if (rc == 0) {
        // Check if test_normal.txt was extracted
        FILE* f = fopen(".axon_cache/tar_test_out/test_normal.txt", "rb");
        if (f) {
            printf("PASS (archivo extraido correctamente)\n");
            fclose(f);
            passed++;
        } else {
            printf("FAIL (archivo no extraido)\n");
            failed++;
        }
    } else {
        printf("FAIL (return code %d)\n", rc);
        failed++;
    }
    
    // Test 2: Check that malicious files were NOT extracted
    printf("Test 2: Path traversal bloqueado... ");
    fflush(stdout);
    FILE* f = fopen(".axon_cache/tar_test_out/../../etc/passwd", "rb");
    if (f) {
        printf("FAIL (archivo malicioso extraido!)\n");
        fclose(f);
        failed++;
    } else {
        // Also check if it escaped the output dir
        f = fopen(".axon_cache/tar_test_out/../../tmp/escaped_test", "rb");
        if (!f) {
            printf("PASS (path traversal bloqueado)\n");
            passed++;
        } else {
            printf("WARN (archivo en tmp, posible escape)\n");
            fclose(f);
            failed++;
        }
    }
    
    // Test 3: Check that /etc/shadow was NOT extracted
    printf("Test 3: Ruta absoluta bloqueada... ");
    fflush(stdout);
    f = fopen(".axon_cache/tar_test_out/etc/shadow", "rb");
    if (f) {
        printf("FAIL (ruta absoluta extraida!)\n");
        fclose(f);
        failed++;
    } else {
        printf("PASS (ruta absoluta bloqueada)\n");
        passed++;
    }
    
    // Cleanup
    system("rm -rf .axon_cache/tar_test_out");
    
    printf("\n=== Resultados: %d passed, %d failed ===\n", passed, failed);
    return failed > 0 ? 1 : 0;
}
