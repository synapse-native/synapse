// Simple test of cluster key generation via direct C
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

typedef struct { int longitud; const char* datos; } CadenaSegura;

extern void pool_init(uint32_t total_blocks, uint32_t block_size);
extern void* pool_alloc(size_t size);
extern int crypto_sign_keypair(unsigned char *pk, unsigned char *sk);
extern CadenaSegura cluster_generar_par_claves(void);

int main() {
    pool_init(64, 4096);
    CadenaSegura par = cluster_generar_par_claves();
    printf("par: %.*s\n", par.longitud, par.datos);
    printf("len: %d\n", par.longitud);
    return 0;
}