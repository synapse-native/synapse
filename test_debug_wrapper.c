#include <stdio.h>
#include <string.h>
#include <stdlib.h>

typedef struct { int longitud; char* datos; } CadenaSegura;

void randombytes(unsigned char* x, unsigned long long xlen) {
    for (unsigned long long i = 0; i < xlen; i++) x[i] = (unsigned char)(rand() & 0xFF);
}

extern int crypto_sign_ed25519_tweet_open(unsigned char* m, unsigned long long* mlen, const unsigned char* sm, unsigned long long n, const unsigned char* pk);

// Replicate the EXACT wrapper but with debug
int test_verificar(CadenaSegura mensaje, CadenaSegura firma, CadenaSegura clave_publica) {
    printf("DEBUG: firma.len=%d, pk.len=%d, msg.len=%d\n", firma.longitud, clave_publica.longitud, mensaje.longitud);
    if (firma.longitud < 64 || clave_publica.longitud < 32) {
        printf("DEBUG: early return -1 (len check failed)\n");
        return -1;
    }
    unsigned long long mlen = 0;
    unsigned char* sm = (unsigned char*)malloc((size_t)(mensaje.longitud + 64));
    if (!sm) { printf("DEBUG: malloc failed\n"); return -1; }
    memcpy(sm, firma.datos, 64);
    memcpy(sm + 64, mensaje.datos, (size_t)mensaje.longitud);
    unsigned long long smlen = (unsigned long long)(mensaje.longitud + 64);
    unsigned char* pk = (unsigned char*)clave_publica.datos;
    printf("DEBUG: calling crypto_sign_ed25519_tweet_open(sm, &mlen, sm, %llu, pk)\n", smlen);
    int rc = crypto_sign_ed25519_tweet_open(sm, &mlen, sm, smlen, pk);
    printf("DEBUG: returned rc=%d, mlen=%llu\n", rc, mlen);
    free(sm);
    return rc;
}

int main() {
    unsigned char pk[32], sig[64];
    const char* pk_hex = "d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a";
    const char* sig_hex = "e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e065224901555fb8821590a33bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b";
    for (int i = 0; i < 32; i++) { unsigned int b; char h[3]={pk_hex[i*2],pk_hex[i*2+1],0}; sscanf(h,"%x",&b); pk[i]=(unsigned char)b; }
    for (int i = 0; i < 64; i++) { unsigned int b; char h[3]={sig_hex[i*2],sig_hex[i*2+1],0}; sscanf(h,"%x",&b); sig[i]=(unsigned char)b; }
    
    CadenaSegura msg = { .longitud = 0, .datos = "" };
    CadenaSegura firma = { .longitud = 64, .datos = (char*)sig };
    CadenaSegura pk_cs = { .longitud = 32, .datos = (char*)pk };
    
    int rc = test_verificar(msg, firma, pk_cs);
    printf("Final result: %d\n", rc);
    return (rc == 0) ? 0 : 1;
}
