#include <stdio.h>
#include <string.h>
#include <stdlib.h>

typedef struct { int longitud; char* datos; } CadenaSegura;

extern int _syn_ed25519_verificar(CadenaSegura mensaje, CadenaSegura firma, CadenaSegura clave_publica);

void randombytes(unsigned char* x, unsigned long long xlen) {
    for (unsigned long long i = 0; i < xlen; i++) x[i] = (unsigned char)(rand() & 0xFF);
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
    
    int rc = _syn_ed25519_verificar(msg, firma, pk_cs);
    printf("_syn_ed25519_verificar returned: %d\n", rc);
    return (rc == 0) ? 0 : 1;
}
