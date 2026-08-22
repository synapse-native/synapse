/*
 * test_cluster_kx.c — R78: Derivación de clave de sesión crypto_kx-equivalente
 *
 * Manual 5 §6.2 paso 3 / Manual 6 §5.3 paso 4 (clave de sesión para cifrar tráfico).
 * Construcción sobre primitivas TweetNaCl exclusivamente (regla 8):
 *   q     = X25519(sk_local, kx_pk_remota)
 *   h     = SHA-512(q || kxpk_cliente || kxpk_servidor)   (orden por ROL)
 *   clave = h[0..31]
 *
 * Modo "test" (default):      pruebas unitarias in-process (4 casos)
 * Modo "server <puerto>":     nodo real: HELLO->HELLO_RESP + KX_INIT->derivación;
 *                             imprime "KX_KEY:<hex>" cuando la sesión queda activa
 * Modo "client <ip> <puerto>": flujo completo del cliente (HELLO firmado ->
 *                             HELLO_RESP -> KX_INIT firmado -> KX_RESP ->
 *                             derivación rol cliente); imprime "KX_KEY:<hex>"
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#ifdef _WIN32
#include <winsock2.h>
#include <ws2tcpip.h>
#else
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#define SOCKET int
#endif

typedef struct { int longitud; const char* datos; } CadenaSegura;

/* API del runtime bajo prueba */
extern int cluster_kx_secreto_compartido(const unsigned char* sk_local,
                                          const unsigned char* pk_local,
                                          const char* kx_pk_remota_hex,
                                          int rol_cliente,
                                          unsigned char* clave_out32);
extern int cluster_kx_par(char* pk_hex_out65, unsigned char* sk_out32);
extern CadenaSegura cluster_kx_generar_par(void);
extern int cluster_kx_derivar(const char* kx_pk_remota_hex, int rol_cliente);
extern CadenaSegura cluster_clave_sesion_hex(void);
extern int cluster_enviar_kx_init(const char* ip, int puerto,
                                   CadenaSegura kx_pk_hex, CadenaSegura firma_hex);
extern CadenaSegura cluster_generar_par_claves(void);
extern CadenaSegura cluster_firmar_mensaje(CadenaSegura mensaje, CadenaSegura clave_privada_hex);
extern int cluster_verificar_firma(CadenaSegura mensaje, CadenaSegura firma_hex,
                                    CadenaSegura clave_publica_hex);
extern int cluster_iniciar_nodo(int puerto);
extern int cluster_detener_nodo(void);
extern CadenaSegura cluster_generar_nonce(void);
extern int cluster_enviar_hello_firmado(const char* ip, int puerto, CadenaSegura id_origen,
                                         CadenaSegura pubkey_hex, CadenaSegura nonce_hex,
                                         CadenaSegura firma_hex);
extern CadenaSegura cluster_recibir_paquete(int timeout_ms);
extern int cluster_canal_remoto_enviar(const char* ip, int puerto,
                                        const char* datos, int lon, int chan_id);

static int tests_passed = 0, tests_failed = 0;

static void check(int cond, const char* nombre) {
    if (cond) { printf("[PASS] %s\n", nombre); tests_passed++; }
    else      { printf("[FAIL] %s\n", nombre); tests_failed++; }
}

/* Extrae el campo idx de una cadena separada por ':' */
static int campo(const char* src, int idx, char* out, int max_out) {
    int i = 0, actual = 0, j = 0;
    while (src[i] && actual < idx) { if (src[i] == ':') actual++; i++; }
    while (src[i] && src[i] != ':' && j < max_out - 1) out[j++] = src[i++];
    out[j] = '\0';
    return j > 0;
}

static void hex_a_str(const char* datos, int lon, char* out, int max_out) {
    int j = 0;
    for (int i = 0; i < lon && j < max_out - 1; i++) out[j++] = datos[i];
    out[j] = '\0';
}

/* ===== MODO TEST (unitario) ===== */

static void hex_dec(const char* hex, unsigned char* out32) {
    for (int i = 0; i < 32; i++) {
        unsigned int b;
        sscanf(hex + i * 2, "%2x", &b);
        out32[i] = (unsigned char)b;
    }
}

static void modo_test(void) {
    char pkA[65], pkB[65], pkC[65];
    unsigned char skA[32], skB[32], skC[32];
    unsigned char pkA_raw[32], pkB_raw[32], pkC_raw[32];
    unsigned char claveA[32], claveB[32], claveC[32];

    check(cluster_kx_par(pkA, skA) == 0, "U1 generar par A");
    check(cluster_kx_par(pkB, skB) == 0, "U2 generar par B");
    hex_dec(pkA, pkA_raw);
    hex_dec(pkB, pkB_raw);

    /* A es cliente (rol 1), B es servidor (rol 0): mismas entradas -> misma clave */
    check(cluster_kx_secreto_compartido(skA, pkA_raw, pkB, 1, claveA) == 0,
          "U3 ECDH lado cliente");
    check(cluster_kx_secreto_compartido(skB, pkB_raw, pkA, 0, claveB) == 0,
          "U4 ECDH lado servidor");
    check(memcmp(claveA, claveB, 32) == 0, "U5 claves identicas cliente/servidor");

    /* Un intruso con su propio par deriva una clave DIFERENTE */
    check(cluster_kx_par(pkC, skC) == 0, "U6 generar par C (intruso)");
    hex_dec(pkC, pkC_raw);
    check(cluster_kx_secreto_compartido(skC, pkC_raw, pkB, 1, claveC) == 0,
          "U7 intruso completa su ECDH");
    check(memcmp(claveC, claveA, 32) != 0, "U8 clave intrusa distinta de la sesion");

    /* Entradas invalidas rechazadas */
    check(cluster_kx_secreto_compartido(skA, pkA_raw, "zz", 1, claveA) != 0,
          "U9 hex malformado rechazado");
    check(cluster_kx_secreto_compartido(skA, NULL, pkB, 1, claveA) != 0,
          "U10 pk_local nula rechazada");

    printf("RESUMEN: Exitos: %d Fallos: %d\n", tests_passed, tests_failed);
    printf(tests_failed == 0 ? "[PASS] 0 fallos\n" : "[FAIL] hay fallos\n");
}

/* ===== MODO SERVER ===== */
static int modo_server(int puerto) {
    if (cluster_iniciar_nodo(puerto) < 0) {
        fprintf(stderr, "server: no se pudo iniciar en puerto %d\n", puerto);
        return 1;
    }
    int sesion = 0;
    for (int i = 0; i < 160; i++) {           /* ~80 s máximo */
        CadenaSegura p = cluster_recibir_paquete(500); /* HELLO_RESP/KX_INIT automáticos */
        CadenaSegura k = cluster_clave_sesion_hex();
        if (!sesion && k.longitud == 64) {
            sesion = 1;
            printf("KX_KEY:%.*s\n", 64, k.datos);
            fflush(stdout);
        }
        /* Criterio Manual 5 §9: envío/recepción — primer payload descifrado */
        if (sesion && p.longitud > 0) {
            printf("DATA_OK:%.*s\n", p.longitud, p.datos);
            fflush(stdout);
            cluster_detener_nodo();
            return 0;
        }
    }
    fprintf(stderr, "server: timeout esperando KX_INIT/DATA\n");
    return 2;
}

/* ===== MODO CLIENT ===== */
static int modo_client(const char* ip, int puerto) {
    CadenaSegura par = cluster_generar_par_claves();
    if (par.longitud != 193) { fprintf(stderr, "client: par invalido\n"); return 1; }

    if (cluster_iniciar_nodo(0) < 0) { fprintf(stderr, "client: nodo\n"); return 1; }

    CadenaSegura nonce = cluster_generar_nonce();
    char nonce_hex[65]; hex_a_str(nonce.datos, nonce.longitud, nonce_hex, 65);

    CadenaSegura mensaje = { .longitud = 64, .datos = nonce_hex };
    CadenaSegura firma = cluster_firmar_mensaje(mensaje, par);
    if (firma.longitud != 128) { fprintf(stderr, "client: firma\n"); return 1; }

    CadenaSegura pk_cli = { .longitud = 64, .datos = par.datos };
    if (cluster_enviar_hello_firmado(ip, puerto, (CadenaSegura){12, "synapse-node"},
                                      pk_cli, nonce, firma) < 0) {
        fprintf(stderr, "client: enviar HELLO\n"); return 1;
    }

    /* Esperar HELLO_RESP */
    char resp_buf[1024] = {0};
    for (int i = 0; i < 20; i++) {
        CadenaSegura p = cluster_recibir_paquete(500);
        if (p.longitud > 11 && strncmp(p.datos, "HELLO_RESP:", 11) == 0) {
            hex_a_str(p.datos, p.longitud, resp_buf, 1024);
            break;
        }
    }
    if (!resp_buf[0]) { fprintf(stderr, "client: timeout HELLO_RESP\n"); return 2; }

    char id_s[128], nonce_s[65], pk_s[65], fir_s[129];
    if (!campo(resp_buf + 11, 0, id_s, 128) || !campo(resp_buf + 11, 1, nonce_s, 65) ||
        !campo(resp_buf + 11, 2, pk_s, 65) || !campo(resp_buf + 11, 3, fir_s, 129)) {
        fprintf(stderr, "client: HELLO_RESP malformado\n"); return 2;
    }
    CadenaSegura m_ns = { .longitud = 64, .datos = nonce_s };
    CadenaSegura f_ns = { .longitud = 128, .datos = fir_s };
    CadenaSegura pk_srv = { .longitud = 64, .datos = pk_s };
    if (cluster_verificar_firma(m_ns, f_ns, pk_srv) != 0) {
        fprintf(stderr, "client: firma servidor invalida\n"); return 3;
    }

    /* Fase KX: par efímero propio + KX_INIT firmado */
    CadenaSegura kxl = cluster_kx_generar_par();
    if (kxl.longitud != 64) { fprintf(stderr, "client: kx par\n"); return 1; }
    char kxl_hex[65]; hex_a_str(kxl.datos, 64, kxl_hex, 65);
    char msg_kx[160];
    snprintf(msg_kx, sizeof(msg_kx), "%s:%s", kxl_hex, nonce_hex);
    CadenaSegura m_kx = { .longitud = (int)strlen(msg_kx), .datos = msg_kx };
    CadenaSegura f_kx = cluster_firmar_mensaje(m_kx, par);
    if (f_kx.longitud != 128) { fprintf(stderr, "client: firma kx\n"); return 1; }
    if (cluster_enviar_kx_init(ip, puerto, kxl, f_kx) < 0) {
        fprintf(stderr, "client: enviar KX_INIT\n"); return 1;
    }

    /* Esperar KX_RESP */
    char kxr_buf[512] = {0};
    for (int i = 0; i < 20; i++) {
        CadenaSegura p = cluster_recibir_paquete(500);
        if (p.longitud > 8 && strncmp(p.datos, "KX_RESP:", 8) == 0) {
            hex_a_str(p.datos, p.longitud, kxr_buf, 512);
            break;
        }
    }
    if (!kxr_buf[0]) { fprintf(stderr, "client: timeout KX_RESP\n"); return 2; }

    char kxs_hex[65], fir_kxs[129];
    if (!campo(kxr_buf + 8, 0, kxs_hex, 65) || !campo(kxr_buf + 8, 1, fir_kxs, 129)) {
        fprintf(stderr, "client: KX_RESP malformado\n"); return 2;
    }
    char msg_kxs[160];
    snprintf(msg_kxs, sizeof(msg_kxs), "%s:%s", kxs_hex, nonce_s);
    CadenaSegura m_kxs = { .longitud = (int)strlen(msg_kxs), .datos = msg_kxs };
    CadenaSegura f_kxs = { .longitud = 128, .datos = fir_kxs };
    if (cluster_verificar_firma(m_kxs, f_kxs, pk_srv) != 0) {
        fprintf(stderr, "client: firma KX_RESP invalida\n"); return 3;
    }

    if (cluster_kx_derivar(kxs_hex, 1) != 0) {
        fprintf(stderr, "client: derivacion\n"); return 4;
    }
    CadenaSegura k = cluster_clave_sesion_hex();
    if (k.longitud != 64) { fprintf(stderr, "client: sesion inactiva\n"); return 4; }
    printf("KX_KEY:%.*s\n", 64, k.datos);
    fflush(stdout);

    /* Criterio Manual 5 §9: envío/recepción sobre el canal cifrado */
    const char* payload = "kx-payload-42";
    if (cluster_canal_remoto_enviar(ip, puerto, payload,
                                     (int)strlen(payload), 1) < 0) {
        fprintf(stderr, "client: enviar DATA\n"); return 5;
    }
    return 0;
}

int main(int argc, char** argv) {
#ifdef _WIN32
    WSADATA wsa; WSAStartup(MAKEWORD(2, 2), &wsa);
#endif
    int rc;
    if (argc >= 3 && strcmp(argv[1], "server") == 0)
        rc = modo_server(atoi(argv[2]));
    else if (argc >= 4 && strcmp(argv[1], "client") == 0)
        rc = modo_client(argv[2], atoi(argv[3]));
    else
        modo_test(), rc = (tests_failed == 0) ? 0 : 1;
#ifdef _WIN32
    WSACleanup();
#endif
    return rc;
}
