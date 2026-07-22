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
    u8 pk[32], sig[64];
    const char* pk_hex = "d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a";
    const char* sig_hex = "e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e065224901555fb8821590a33bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b";
    for (int i = 0; i < 32; i++) { unsigned int b; char h[3]={pk_hex[i*2],pk_hex[i*2+1],0}; sscanf(h,"%x",&b); pk[i]=(u8)b; }
    for (int i = 0; i < 64; i++) { unsigned int b; char h[3]={sig_hex[i*2],sig_hex[i*2+1],0}; sscanf(h,"%x",&b); sig[i]=(u8)b; }
    
    // TEST 1: Different buffers (like minimal test)
    printf("TEST 1: Different buffers... ");
    u8 sm1[64]; memcpy(sm1, sig, 64);
    u8 m1[64];
    u64 mlen1 = 0;
    int rc1 = crypto_sign_ed25519_tweet_open(m1, &mlen1, sm1, 64, pk);
    printf("rc=%d, mlen=%llu %s\n", rc1, mlen1, rc1 == 0 ? "PASS" : "FAIL");
    
    // TEST 2: Same buffer (like wrapper)
    printf("TEST 2: Same buffer... ");
    u8 buf[64]; memcpy(buf, sig, 64);
    u64 mlen2 = 0;
    int rc2 = crypto_sign_ed25519_tweet_open(buf, &mlen2, buf, 64, pk);
    printf("rc=%d, mlen=%llu %s\n", rc2, mlen2, rc2 == 0 ? "PASS" : "FAIL");
    
    // TEST 3: Heap allocated same buffer (like wrapper)
    printf("TEST 3: Heap same buffer... ");
    u8* hbuf = (u8*)malloc(64);
    memcpy(hbuf, sig, 64);
    u64 mlen3 = 0;
    int rc3 = crypto_sign_ed25519_tweet_open(hbuf, &mlen3, hbuf, 64, pk);
    printf("rc=%d, mlen=%llu %s\n", rc3, mlen3, rc3 == 0 ? "PASS" : "FAIL");
    free(hbuf);
    
    return (rc1 == 0 && rc2 == 0 && rc3 == 0) ? 0 : 1;
}
