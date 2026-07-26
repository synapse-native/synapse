// Test: key generation, sign, and verify
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

typedef struct { int longitud; const char* datos; } CadenaSegura;

extern void pool_init(uint32_t total_blocks, uint32_t block_size);
extern void* pool_alloc(size_t size);
extern CadenaSegura cluster_generar_par_claves(void);
extern CadenaSegura cluster_firmar_mensaje(CadenaSegura mensaje, CadenaSegura clave_privada_hex);
extern int cluster_verificar_firma(CadenaSegura mensaje, CadenaSegura firma_hex, CadenaSegura clave_publica_hex);

int main() {
    pool_init(64, 4096);
    
    CadenaSegura par = cluster_generar_par_claves();
    printf("par (%d): %.*s\n", par.longitud, par.longitud, par.datos);
    
    // par is "pubkey_hex:privkey_hex" where pubkey=64 chars, privkey=128 chars
    CadenaSegura pubkey_hex = { .longitud = 64, .datos = par.datos };
    CadenaSegura privkey_hex = { .longitud = 128, .datos = par.datos + 65 }; // skip pubkey + ':'
    
    CadenaSegura mensaje = { .longitud = 15, .datos = "Prueba de firma" };
    
    CadenaSegura firma = cluster_firmar_mensaje(mensaje, privkey_hex);
    printf("sig (%d): %.*s\n", firma.longitud, firma.longitud, firma.datos);
    
    int valido = cluster_verificar_firma(mensaje, firma, pubkey_hex);
    printf("verify with correct pubkey: %d (expect 0)\n", valido);
    
    // Generate wrong pubkey for negative test
    CadenaSegura par2 = cluster_generar_par_claves();
    CadenaSegura pubkey2_hex = { .longitud = 64, .datos = par2.datos };
    int invalido = cluster_verificar_firma(mensaje, firma, pubkey2_hex);
    printf("verify with wrong pubkey: %d (expect non-zero)\n", invalido);
    
    return (valido != 0 || invalido == 0) ? 1 : 0;
}