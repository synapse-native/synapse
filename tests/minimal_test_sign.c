#include <stdio.h>
#include <string.h>
#include <stdlib.h>

typedef unsigned char u8;
typedef unsigned long long u64;

void randombytes(u8 *x, u64 xlen) {
    for (u64 i = 0; i < xlen; i++) x[i] = (u8)(rand() & 0xFF);
}

extern int crypto_sign_ed25519_tweet_open(u8 *m, u64 *mlen, const u8 *sm, u64 n, const u8 *pk);

int main() {
    u8 pk[32];
    u8 sig[64];
    
    const char* pk_hex = "d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a";
    const char* sig_hex = "e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e065224901555fb8821590a33bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b";
    
    for (int i = 0; i < 32; i++) { unsigned int b; char h[3]={pk_hex[i*2],pk_hex[i*2+1],0}; sscanf(h,"%x",&b); pk[i]=(u8)b; }
    for (int i = 0; i < 64; i++) { unsigned int b; char h[3]={sig_hex[i*2],sig_hex[i*2+1],0}; sscanf(h,"%x",&b); sig[i]=(u8)b; }
    
    printf("Testing crypto_sign_ed25519_tweet_open with RFC 8032 test vector...\n");
    
    u8 sm[64];
    memcpy(sm, sig, 64);
    u64 mlen = 0;
    u8 m[64];
    int rc = crypto_sign_ed25519_tweet_open(m, &mlen, sm, 64, pk);
    
    printf("Return code: %d\n", rc);
    if (rc == 0) {
        printf("SUCCESS! Signature verified.\n");
        return 0;
    } else {
        printf("FAILED! rc=%d\n", rc);
        return 1;
    }
}
