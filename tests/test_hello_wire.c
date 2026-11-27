/*
 * test_hello_wire.c - TDD runtime para M1 (Manual 6 §5.3): HELLO binario
 * [nonce 32B][pubkey 32B][firma 64B] con prefijos "HELLO:" / "HELLO_RESP:".
 *
 * Valida en runtime que:
 *   - cluster_enviar_hello_firmado() empaqueta el buffer binario de 134 bytes
 *     (prefijo + [nonce32][pubkey32][firma64]).
 *   - el receptor (_cluster_procesar_hello_entrante via cluster_recibir_paquete)
 *     parsea el binario y responde HELLO_RESP de 139 bytes (prefijo +
 *     [nonce32][pubkey32][firma64]) con firma de servidor valida.
 */
#include <stdio.h>
#include <string.h>
#include <stdint.h>
#ifdef _WIN32
#include <winsock2.h>
#include <ws2tcpip.h>
#else
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#endif
#include "runtime/core/cluster.h"

#ifdef _WIN32
#define BAD_SOCK INVALID_SOCKET
#else
#define BAD_SOCK (-1)
#endif

static int tp = 0, tf = 0;
static void ok(const char* n, int c) {
    if (c) { tp++; printf("[PASS] %s\n", n); }
    else   { tf++; printf("[FAIL] %s\n", n); }
}

static CadenaSegura cs(const char* s) {
    CadenaSegura c; c.longitud = s ? (int)strlen(s) : 0; c.datos = s; return c;
}
static void extr(CadenaSegura o, int a, int b, char* out, int m) {
    int i, j = 0;
    for (i = a; i < b && i < o.longitud && j < m - 1; i++) out[j++] = o.datos[i];
    out[j] = '\0';
}
static void hexdec(const char* h, unsigned char* o, int n) {
    for (int i = 0; i < n; i++) { unsigned int v; sscanf(h + i * 2, "%02x", &v); o[i] = (unsigned char)v; }
}
static void hexenc(const unsigned char* in, char* o, int n) {
    for (int i = 0; i < n; i++) sprintf(o + i * 2, "%02x", in[i]);
    o[n * 2] = '\0';
}

#ifdef _WIN32
static SOCKET raw_udp(int port) {
    SOCKET s = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    if (s == INVALID_SOCKET) return INVALID_SOCKET;
    struct sockaddr_in a; memset(&a, 0, sizeof(a));
    a.sin_family = AF_INET; a.sin_addr.s_addr = INADDR_ANY; a.sin_port = htons((unsigned short)port);
    if (bind(s, (struct sockaddr*)&a, sizeof(a)) == SOCKET_ERROR) { closesocket(s); return INVALID_SOCKET; }
    return s;
}
#else
static int raw_udp(int port) {
    int s = socket(AF_INET, SOCK_DGRAM, 0);
    if (s < 0) return -1;
    struct sockaddr_in a; memset(&a, 0, sizeof(a));
    a.sin_family = AF_INET; a.sin_addr.s_addr = INADDR_ANY; a.sin_port = htons((unsigned short)port);
    if (bind(s, (struct sockaddr*)&a, sizeof(a)) < 0) { close(s); return -1; }
    return s;
}
#endif

int main(void) {
#ifdef _WIN32
    WSADATA w; if (WSAStartup(MAKEWORD(2, 2), &w) != 0) { printf("WSA fail\n"); return 2; }
#endif
    printf("=== M1 HELLO wire binario [32][32][64] (TDD runtime) ===\n");

    CadenaSegura par = cluster_generar_par_claves();
    char pub[65], priv[129];
    extr(par, 0, 64, pub, 65);
    extr(par, 65, par.longitud, priv, 129);

    CadenaSegura nonce = cluster_generar_nonce();
    char nonce_hex[65]; memcpy(nonce_hex, nonce.datos, 64); nonce_hex[64] = '\0';

    CadenaSegura firma = cluster_firmar_mensaje(cs(nonce_hex), cs(priv));
    ok("firma longitud 128", firma.longitud == 128);

    /* TEST 1: el emisor empaqueta el binario [32][32][64] */
    int recv_port = 19111, send_port = 19112;
#ifdef _WIN32
    SOCKET rx = raw_udp(recv_port);
#else
    int rx = raw_udp(recv_port);
#endif
    ok("rx socket valido", rx != BAD_SOCK);
    cluster_iniciar_nodo(send_port);
    int rc = cluster_enviar_hello_firmado("127.0.0.1", recv_port, cs("test-node"),
                                          cs(pub), cs(nonce_hex), firma);
    ok("cluster_enviar_hello_firmado rc=134 (bytes enviados)", rc == 134);
    struct sockaddr_in from; socklen_t fl = sizeof(from);
    char buf[256];
    int n = recvfrom(rx, buf, sizeof(buf) - 1, 0, (struct sockaddr*)&from, &fl);
    ok("HELLO recibido 134 bytes", n == 134);
    ok("prefijo HELLO:", n >= 6 && memcmp(buf, "HELLO:", 6) == 0);
    if (n == 134) {
        unsigned char nb[32], pb[32], fb[64];
        hexdec(nonce_hex, nb, 32); hexdec(pub, pb, 32); hexdec(firma.datos, fb, 64);
        ok("nonce binario coincide", memcmp(buf + 6, nb, 32) == 0);
        ok("pubkey binario coincide", memcmp(buf + 38, pb, 32) == 0);
        ok("firma binario coincide", memcmp(buf + 70, fb, 64) == 0);
    }
    cluster_detener_nodo();
#ifdef _WIN32
    closesocket(rx);
#else
    close(rx);
#endif

    /* TEST 2: el receptor parsea el binario y responde HELLO_RESP binario */
    int node_port = 19113;
    cluster_iniciar_nodo(node_port);
#ifdef _WIN32
    SOCKET tx = raw_udp(0);
#else
    int tx = raw_udp(0);
#endif
    ok("tx socket valido", tx != BAD_SOCK);
    char hello[140];
    memcpy(hello, "HELLO:", 6);
    hexdec(nonce_hex, (unsigned char*)hello + 6, 32);
    hexdec(pub, (unsigned char*)hello + 38, 32);
    hexdec(firma.datos, (unsigned char*)hello + 70, 64);
    struct sockaddr_in dst; memset(&dst, 0, sizeof(dst));
    dst.sin_family = AF_INET; dst.sin_addr.s_addr = inet_addr("127.0.0.1");
    dst.sin_port = htons((unsigned short)node_port);
    int sn = sendto(tx, hello, 134, 0, (struct sockaddr*)&dst, sizeof(dst));
    ok("sendto HELLO 134 bytes", sn == 134);
    CadenaSegura pkt = cluster_recibir_paquete(1500);
    (void)pkt;
    struct sockaddr_in rf; socklen_t rl = sizeof(rf);
    char rbuf[256];
    int rn = recvfrom(tx, rbuf, sizeof(rbuf) - 1, 0, (struct sockaddr*)&rf, &rl);
    ok("HELLO_RESP recibido 139 bytes", rn == 139);
    ok("prefijo HELLO_RESP:", rn >= 11 && memcmp(rbuf, "HELLO_RESP:", 11) == 0);
    if (rn == 139) {
        char dnonce[65], dpk[65], dfir[129];
        hexenc((unsigned char*)rbuf + 11, dnonce, 32);
        hexenc((unsigned char*)rbuf + 43, dpk, 32);
        hexenc((unsigned char*)rbuf + 75, dfir, 64);
        ok("HELLO_RESP firma servidor verifica (binario)",
           cluster_verificar_firma(cs(dnonce), cs(dfir), cs(dpk)) == 0);
    }
    cluster_detener_nodo();
#ifdef _WIN32
    closesocket(tx);
    WSACleanup();
#else
    close(tx);
#endif

    printf("\nPasados: %d  Fallos: %d\n", tp, tf);
    return tf == 0 ? 0 : 1;
}
