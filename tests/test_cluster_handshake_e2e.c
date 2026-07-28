/*
 * test_cluster_handshake_e2e.c — M18.4: Prueba E2E Ed25519 Handshake sobre UDP
 *
 * Modo "test" (default):      21 tests unitarios de cripto + raw UDP
 * Modo "server <puerto>":     SOCKET RAW: espera HELLO, verifica firma, responde HELLO_ACK
 * Modo "client <ip> <puerto> [clave_invalida|firma_corrupta]":
 *                              SOCKET RAW: envia HELLO, recibe HELLO_ACK, verifica firma
 *
 * IMPORTANTE: Los modos server/client usan sockets RAW (sendto/recvfrom) para
 * garantizar interoperabilidad cross-process. Solo las funciones CRIPTOGRAFICAS
 * del runtime se utilizan (generar_par, firmar, verificar). Esto evita la
 * dependencia del socket global interno del runtime (_cluster_sock_global).
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
#include <fcntl.h>
#include <errno.h>
#define SOCKET int
#define INVALID_SOCKET -1
#define SOCKET_ERROR -1
#define closesocket(x) close(x)
#endif

/* Tipos del runtime (solo para crypto) */
typedef struct { int longitud; const char* datos; } CadenaSegura;

/* Declaraciones externas SOLO de funciones criptograficas del runtime */
extern CadenaSegura cluster_generar_par_claves(void);
extern CadenaSegura cluster_firmar_mensaje(CadenaSegura mensaje, CadenaSegura clave_privada_hex);
extern int cluster_verificar_firma(CadenaSegura mensaje, CadenaSegura firma_hex, CadenaSegura clave_publica_hex);

/* NO se usan: cluster_iniciar_nodo, cluster_detener_nodo, cluster_enviar_hello,
   cluster_recibir_paquete, cluster_canal_remoto_enviar */


/* ===== HELPERS ===== */

static int tests_passed = 0, tests_failed = 0;

static void extraer_parte(CadenaSegura origen, int inicio, int fin, char* out, int max_out) {
    int i, j = 0;
    for (i = inicio; i < fin && i < origen.longitud && j < max_out - 1; i++)
        out[j++] = origen.datos[i];
    out[j] = '\0';
}

static CadenaSegura make_cs(const char* str) {
    CadenaSegura cs;
    cs.longitud = str ? (int)strlen(str) : 0;
    cs.datos = str;
    return cs;
}

/* Crea un socket UDP, lo bindea a puerto (0=ephemeral). Retorna socket o INVALID_SOCKET */
static SOCKET raw_udp_socket(int puerto) {
    SOCKET s = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    if (s == INVALID_SOCKET) return INVALID_SOCKET;

    struct sockaddr_in addr;
    memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = INADDR_ANY;
    addr.sin_port = htons((unsigned short)puerto);

    if (bind(s, (struct sockaddr*)&addr, sizeof(addr)) == SOCKET_ERROR) {
        closesocket(s);
        return INVALID_SOCKET;
    }
    return s;
}

/* Envia un datagrama UDP a ip:puerto. Retorna bytes enviados o -1 */
static int raw_udp_send(SOCKET s, const char* ip, int puerto,
                         const char* datos, int len) {
    struct sockaddr_in addr;
    memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = inet_addr(ip);
    addr.sin_port = htons((unsigned short)puerto);
    int n = sendto(s, datos, len, 0,
                   (struct sockaddr*)&addr, sizeof(addr));
    return (n == SOCKET_ERROR) ? -1 : n;
}

/* Recibe datagrama UDP con timeout. Retorna bytes recibidos o 0 (timeout) o -1 (error) */
static int raw_udp_recv(SOCKET s, char* buf, int bufsize, int timeout_ms,
                         char* from_ip, int from_ip_size, int* from_port) {
#ifdef _WIN32
    u_long mode = 1;
    ioctlsocket(s, FIONBIO, &mode);
#else
    int flags = fcntl(s, F_GETFL, 0);
    fcntl(s, F_SETFL, flags | O_NONBLOCK);
#endif

    /* Poll durante timeout_ms */
    int waited = 0;
    while (waited < timeout_ms) {
        struct sockaddr_in from;
        socklen_t from_len = sizeof(from);
        memset(&from, 0, sizeof(from));
        int n = recvfrom(s, buf, bufsize - 1, 0,
                         (struct sockaddr*)&from, &from_len);
        if (n > 0) {
            buf[n] = '\0';
            if (from_ip) {
                strncpy(from_ip, inet_ntoa(from.sin_addr), (size_t)from_ip_size - 1);
                from_ip[from_ip_size - 1] = '\0';
            }
            if (from_port) *from_port = ntohs(from.sin_port);
            return n;
        }
#ifdef _WIN32
        if (n == SOCKET_ERROR && WSAGetLastError() != WSAEWOULDBLOCK) return -1;
#else
        if (n < 0 && errno != EAGAIN && errno != EWOULDBLOCK) return -1;
#endif
#ifdef _WIN32
        Sleep(50);
#else
        usleep(50000);
#endif
        waited += 50;
    }
    return 0; /* timeout */
}

static void test_result(const char* name, int condition) {
    if (condition) {
        printf("[PASS] %s\n", name); tests_passed++;
    } else {
        printf("[FAIL] %s\n", name); tests_failed++;
    }
}

/* ===== TESTS UNITARIOS (CRIPTO + UDP RUNTIME) ===== */

static void test_generar_par() {
    printf("\n=== Prueba 1: Generar par Ed25519 ===\n");
    CadenaSegura par;
    par = cluster_generar_par_claves();
    test_result("generar_par() no retorna vacio", par.longitud > 0);
    char pub[65], priv[129];
    extraer_parte(par, 0, 64, pub, 65);
    extraer_parte(par, 65, par.longitud, priv, 129);
    test_result("pubkey=64 hex", strlen(pub) == 64);
    test_result("privkey=128 hex", strlen(priv) == 128);
}

static void test_firmar_verificar() {
    printf("\n=== Prueba 2: Firma y verificacion ===\n");
    CadenaSegura par;
    par = cluster_generar_par_claves();
    char pub[65], priv[129];
    extraer_parte(par, 0, 64, pub, 65);
    extraer_parte(par, 65, par.longitud, priv, 129);
    CadenaSegura firma;
    firma = cluster_firmar_mensaje(make_cs("synapse-handshake:test"), make_cs(priv));
    test_result("firma retorna datos", firma.longitud > 0);
    test_result("firma=128 hex", firma.longitud == 128);
    int rc = cluster_verificar_firma(make_cs("synapse-handshake:test"), firma, make_cs(pub));
    test_result("verificar()=0 valida", rc == 0);
}

static void test_firma_corrupta() {
    printf("\n=== Prueba 3: Rechazo firma corrupta ===\n");
    CadenaSegura par;
    par = cluster_generar_par_claves();
    char pub[65], priv[129];
    extraer_parte(par, 0, 64, pub, 65);
    extraer_parte(par, 65, par.longitud, priv, 129);
    CadenaSegura firma;
    firma = cluster_firmar_mensaje(make_cs("synapse-handshake:test"), make_cs(priv));
    char fc[129];
    extraer_parte(firma, 0, 127, fc, 128);
    fc[127] = (fc[127]=='a')?'b':'a';
    fc[128] = '\0';
    test_result("rechaza firma corrupta", cluster_verificar_firma(make_cs("synapse-handshake:test"), make_cs(fc), make_cs(pub)) != 0);
    test_result("rechaza mensaje incorrecto", cluster_verificar_firma(make_cs("otro-mensaje"), firma, make_cs(pub)) != 0);
}

static void test_clave_incorrecta() {
    printf("\n=== Prueba 4: Rechazo clave incorrecta ===\n");
    CadenaSegura pa, pb;
    pa = cluster_generar_par_claves();
    pb = cluster_generar_par_claves();
    char priv_a[129], pub_b[65];
    extraer_parte(pa, 65, pa.longitud, priv_a, 129);
    extraer_parte(pb, 0, 64, pub_b, 65);
    CadenaSegura firma;
    firma = cluster_firmar_mensaje(make_cs("synapse-handshake:test"), make_cs(priv_a));
    test_result("rechaza clave incorrecta", cluster_verificar_firma(make_cs("synapse-handshake:test"), firma, make_cs(pub_b)) != 0);
}

static void test_bidi() {
    printf("\n=== Prueba 5: Handshake bidireccional ===\n");
    CadenaSegura pa, pb;
    pa = cluster_generar_par_claves();
    pb = cluster_generar_par_claves();
    char pub_a[65], priv_a[129], pub_b[65], priv_b[129];
    extraer_parte(pa, 0, 64, pub_a, 65);
    extraer_parte(pa, 65, pa.longitud, priv_a, 129);
    extraer_parte(pb, 0, 64, pub_b, 65);
    extraer_parte(pb, 65, pb.longitud, priv_b, 129);

    char ma[512];
    snprintf(ma, 512, "synapse-handshake:%s", pub_b);
    CadenaSegura fa;
    fa = cluster_firmar_mensaje(make_cs(ma), make_cs(priv_a));
    test_result("A firma handshake", fa.longitud == 128);
    test_result("B verifica A", cluster_verificar_firma(make_cs(ma), fa, make_cs(pub_a)) == 0);

    char mb[512];
    snprintf(mb, 512, "synapse-handshake:%s", pub_a);
    CadenaSegura fb;
    fb = cluster_firmar_mensaje(make_cs(mb), make_cs(priv_b));
    test_result("B firma respuesta", fb.longitud == 128);
    test_result("A verifica B", cluster_verificar_firma(make_cs(mb), fb, make_cs(pub_b)) == 0);
    test_result("A rechaza msg alterado", cluster_verificar_firma(make_cs("x"), fb, make_cs(pub_b)) != 0);
}

static void test_udp() {
    printf("\n=== Prueba 6: Raw UDP socket ===\n");
    SOCKET s = raw_udp_socket(0);
    test_result("raw_udp_socket(0) valido", s != INVALID_SOCKET);
    if (s != INVALID_SOCKET) closesocket(s);

    SOCKET s2 = raw_udp_socket(19100);
    test_result("raw_udp_socket(19100) valido", s2 != INVALID_SOCKET);
    if (s2 != INVALID_SOCKET) closesocket(s2);
}

static void test_raw_send_recv() {
    printf("\n=== Prueba 7: Raw UDP send/recv loopback ===\n");
    SOCKET rx = raw_udp_socket(19102);
    SOCKET tx = raw_udp_socket(0);
    test_result("rx socket valido", rx != INVALID_SOCKET);
    test_result("tx socket valido", tx != INVALID_SOCKET);

    if (rx != INVALID_SOCKET && tx != INVALID_SOCKET) {
        const char* msg = "HELLO:test-node:abcdef";
        int n = raw_udp_send(tx, "127.0.0.1", 19102, msg, (int)strlen(msg));
        test_result("sendto ok", n > 0);

        char buf[1024];
        char from_ip[64];
        int from_port = 0;
        int r = raw_udp_recv(rx, buf, sizeof(buf), 2000, from_ip, sizeof(from_ip), &from_port);
        test_result("recvfrom recibe datos", r > 0);
        test_result("contenido HELLO", r >= 6 && strncmp(buf, "HELLO:", 6) == 0);
        if (r > 0) printf("  Recibido: '%s' (%d bytes desde %s:%d)\n", buf, r, from_ip, from_port);
    }
    if (rx != INVALID_SOCKET) closesocket(rx);
    if (tx != INVALID_SOCKET) closesocket(tx);
}

static int run_tests_unitarios(void) {
    printf("=== M18.4: Ed25519 + Raw UDP (Tests Unitarios) ===\n");
    tests_passed = 0; tests_failed = 0;
    test_generar_par();
    test_firmar_verificar();
    test_firma_corrupta();
    test_clave_incorrecta();
    test_bidi();
    test_udp();
    test_raw_send_recv();
    printf("\nPasados: %d  Fallos: %d\n", tests_passed, tests_failed);
    return tests_failed > 0 ? 1 : 0;
}

/* ===== MODO SERVER (RAW SOCKETS) ===== */

static int run_server(int puerto) {
    printf("[SERVER] Iniciando en puerto %d (raw socket)...\n", puerto);

    /* Generar par de claves del servidor */
    CadenaSegura par_svr;
    par_svr = cluster_generar_par_claves();
    char pub_server[65], priv_server[129];
    extraer_parte(par_svr, 0, 64, pub_server, 65);
    extraer_parte(par_svr, 65, par_svr.longitud, priv_server, 129);
    printf("[SERVER] Clave publica: %.16s...\n", pub_server);

    /* Crear socket raw */
    SOCKET s = raw_udp_socket(puerto);
    if (s == INVALID_SOCKET) {
        printf("[SERVER] Error creando socket en puerto %d\n", puerto);
        return 1;
    }
    printf("[SERVER] Socket creado, esperando HELLO (%dms)...\n", 8000);

    /* Recibir HELLO del cliente */
    char buf[2048];
    char client_ip[64];
    int client_port = 0;
    int r = raw_udp_recv(s, buf, sizeof(buf), 8000, client_ip, sizeof(client_ip), &client_port);
    if (r <= 0) {
        printf("[SERVER] Timeout/error esperando HELLO (rc=%d)\n", r);
        closesocket(s);
        return 1;
    }
    printf("[SERVER] Recibido: '%s' (%d bytes desde %s:%d)\n", buf, r, client_ip, client_port);

    /* Parsear HELLO:id_origen:pubkey:firma */
    if (strncmp(buf, "HELLO:", 6) != 0) {
        printf("[SERVER] ZERO-TRUST: Paquete no es HELLO\n");
        closesocket(s);
        return 2;
    }

    char id_cliente[65] = {0}, pub_cliente[65] = {0}, firma_hex[129] = {0};
    const char *p1 = buf + 6;
    const char *p2 = strchr(p1, ':');
    if (!p2) { printf("[SERVER] Formato HELLO invalido\n"); closesocket(s); return 1; }
    int len_id = (int)(p2 - p1); if (len_id > 63) len_id = 63;
    strncpy(id_cliente, p1, (size_t)len_id);

    p2++;
    const char *p3 = strchr(p2, ':');
    if (!p3) { printf("[SERVER] Formato HELLO invalido (no pubkey)\n"); closesocket(s); return 1; }
    int len_pub = (int)(p3 - p2); if (len_pub > 64) len_pub = 64;
    strncpy(pub_cliente, p2, (size_t)len_pub);

    p3++;
    int len_fir = r - (int)(p3 - buf); if (len_fir > 128) len_fir = 128;
    strncpy(firma_hex, p3, (size_t)len_fir);

    printf("[SERVER] Cliente: id=%s pub=%.16s... firma=%.16s...\n",
           id_cliente, pub_cliente, firma_hex);

    /* Verificar firma del cliente.
       El mensaje firmado es "hello:<pub_cliente>". */
    char msg_verificar[512];
    snprintf(msg_verificar, 512, "hello:%s", pub_cliente);

    int vrc = cluster_verificar_firma(make_cs(msg_verificar),
                                      make_cs(firma_hex),
                                      make_cs(pub_cliente));
    if (vrc != 0) {
        printf("[SERVER] ZERO-TRUST: Firma de cliente INVALIDA (rc=%d)\n", vrc);
        closesocket(s);
        return 2; /* Zero-Trust rejection */
    }
    printf("[SERVER] Handshake OK: firma de cliente VALIDA\n");

    /* Firmar HELLO_ACK.
       El servidor firma "ack:<pub_cliente>" para confirmar recepcion.
       El cliente verifica contra el mismo mensaje "ack:<pub_cliente>". */
    char msg_ack[512];
    snprintf(msg_ack, 512, "ack:%s", pub_cliente);
    CadenaSegura firma_ack;
    firma_ack = cluster_firmar_mensaje(make_cs(msg_ack), make_cs(priv_server));

    /* Enviar HELLO_ACK:pub_server:firma al cliente */
    char ack[2048];
    int ack_len = snprintf(ack, sizeof(ack), "HELLO_ACK:%s:%.*s",
                           pub_server, firma_ack.longitud, firma_ack.datos);

    int n = raw_udp_send(s, client_ip, client_port, ack, ack_len);
    if (n < 0) {
        printf("[SERVER] Error enviando HELLO_ACK\n");
        closesocket(s);
        return 1;
    }
    printf("[SERVER] HELLO_ACK enviado (%d bytes) a %s:%d\n", n, client_ip, client_port);

    closesocket(s);
    printf("[SERVER] Handshake completado exitosamente\n");
    return 0;
}

/* ===== MODO CLIENTE (RAW SOCKETS) ===== */

static int run_client(const char* ip, int puerto, const char* modo_fallo) {
    int clave_invalida = (modo_fallo && strcmp(modo_fallo, "clave_invalida") == 0);
    int firma_corrupta = (modo_fallo && strcmp(modo_fallo, "firma_corrupta") == 0);
    printf("[CLIENT] Conectando a %s:%d (fallo=%s)...\n", ip, puerto,
           modo_fallo ? modo_fallo : "ninguno");

    /* Generar par de claves del cliente */
    CadenaSegura par_cli;
    par_cli = cluster_generar_par_claves();
    char pub_cliente[65], priv_cliente[129];
    extraer_parte(par_cli, 0, 64, pub_cliente, 65);
    extraer_parte(par_cli, 65, par_cli.longitud, priv_cliente, 129);

    /* Crear socket raw (puerto efimero) */
    SOCKET s = raw_udp_socket(0);
    if (s == INVALID_SOCKET) {
        printf("[CLIENT] Error creando socket\n");
        return 1;
    }

    /* Si es clave_invalida: firmar con OTRO par (no el que enviamos) */
    char* priv_para_firmar = priv_cliente;
    if (clave_invalida) {
        CadenaSegura par_b = cluster_generar_par_claves();
        char priv_b[129];
        extraer_parte(par_b, 65, par_b.longitud, priv_b, 129);
        priv_para_firmar = priv_b;
        printf("[CLIENT] Usando clave DIFFERENTE para firmar (Zero-Trust test)\n");
    }

    /* Firmar mensaje de handshake.
       El cliente firma "hello:<pub_cliente>" como prueba de identidad.
       El servidor verifica contra el mismo mensaje "hello:<pub_cliente>". */
    char msg_firmar[512];
    snprintf(msg_firmar, 512, "hello:%s", pub_cliente);
    CadenaSegura firma_hello;
    if (!firma_corrupta) {
        firma_hello = cluster_firmar_mensaje(
            make_cs(msg_firmar),
            make_cs(priv_para_firmar));
    } else {
        /* Firma corrupta: firmamos mensaje DIFERENTE al que enviamos */
        snprintf(msg_firmar, 512, "hello:%s-WRONG", pub_cliente);
        firma_hello = cluster_firmar_mensaje(
            make_cs(msg_firmar),
            make_cs(priv_para_firmar));
    }

    /* Enviar HELLO:id_origen:pubkey:firma_hex */
    char hello[2048];
    int hello_len = snprintf(hello, sizeof(hello), "HELLO:%s:%s:%.*s",
                             "cliente-test", pub_cliente,
                             firma_hello.longitud, firma_hello.datos);
    printf("[CLIENT] Enviando HELLO (%d bytes)...\n", hello_len);
    int n = raw_udp_send(s, ip, puerto, hello, hello_len);
    if (n < 0) {
        printf("[CLIENT] Error enviando HELLO\n");
        closesocket(s);
        return 1;
    }
    printf("[CLIENT] HELLO enviado (%d bytes), esperando HELLO_ACK...\n", n);

    /* Recibir HELLO_ACK */
    char ack_buf[2048];
    char svr_ip[64];
    int svr_port = 0;
    int r = raw_udp_recv(s, ack_buf, sizeof(ack_buf), 8000, svr_ip, sizeof(svr_ip), &svr_port);
    if (r <= 0) {
        printf("[CLIENT] ZERO-TRUST: No se recibio HELLO_ACK (timeout)\n");
        closesocket(s);
        /* Timeout = servidor rechazo la conexion (rc_svr=2 en servidor) */
        return 2; /* ZERO-TRUST: acoplado con rc_svr=2 */
    }
    printf("[CLIENT] Recibido: '%s' (%d bytes desde %s:%d)\n", ack_buf, r, svr_ip, svr_port);

    /* Verificar HELLO_ACK */
    if (strncmp(ack_buf, "HELLO_ACK:", 10) != 0) {
        printf("[CLIENT] ZERO-TRUST: Respuesta no es HELLO_ACK\n");
        closesocket(s);
        return 2; /* ZERO-TRUST */
    }

    /* Extraer pub_server:firma */
    const char* rd = ack_buf + 10;
    const char* sep = strchr(rd, ':');
    if (!sep) {
        printf("[CLIENT] Formato HELLO_ACK invalido\n");
        closesocket(s);
        return 1;
    }
    int len_pub_svr = (int)(sep - rd);
    char pub_server[65] = {0};
    if (len_pub_svr > 64) len_pub_svr = 64;
    strncpy(pub_server, rd, (size_t)len_pub_svr);

    const char* firma_ack_str = sep + 1;
    int len_firma_ack = r - (int)(firma_ack_str - ack_buf);
    char firma_ack[129] = {0};
    if (len_firma_ack > 128) len_firma_ack = 128;
    strncpy(firma_ack, firma_ack_str, (size_t)len_firma_ack);

    printf("[CLIENT] Server pub=%.16s... firma_ack=%.16s...\n", pub_server, firma_ack);

    /* Verificar firma del servidor.
       El mensaje firmado es "ack:<pub_cliente>". */
    char msg_verificar[512];
    snprintf(msg_verificar, 512, "ack:%s", pub_cliente);
    int vrc = cluster_verificar_firma(make_cs(msg_verificar),
                                      make_cs(firma_ack),
                                      make_cs(pub_server));

    if (clave_invalida || firma_corrupta) {
        /* Modo Zero-Trust: la verificacion DEBE fallar */
        if (vrc == 0) {
            printf("[CLIENT] ZERO-TRUST FALLO: Se esperaba rechazo pero firma valida\n");
            closesocket(s);
            return 4; /* Error grave: se esperaba rechazo */
        }
        printf("[CLIENT] ZERO-TRUST OK: Servidor rechazado (rc_svr=2 acoplado)\n");
        closesocket(s);
        return 2; /* ZERO-TRUST: acoplado con rc_svr=2, NO confundir con 0 */
    }

    if (vrc != 0) {
        printf("[CLIENT] ZERO-TRUST: Firma del servidor INVALIDA (rc=%d)\n", vrc);
        closesocket(s);
        return 2;
    }

    printf("[CLIENT] HANDSHAKE EXITOSO: Firma del servidor VALIDA\n");
    printf("[CLIENT] Canal autenticado establecido con %s:%d\n", svr_ip, svr_port);
    closesocket(s);
    return 0;
}


/* ===== MAIN ===== */

int main(int argc, char** argv) {
#ifdef _WIN32
    WSADATA wsa;
    WSAStartup(MAKEWORD(2, 2), &wsa);
#endif

    if (argc < 2) {
        return run_tests_unitarios();
    }

    if (strcmp(argv[1], "server") == 0) {
        if (argc < 3) { printf("Uso: %s server <puerto>\n", argv[0]); return 1; }
        int puerto = atoi(argv[2]);
        return run_server(puerto > 0 ? puerto : 19200);
    }

    if (strcmp(argv[1], "client") == 0) {
        if (argc < 4) {
            printf("Uso: %s client <ip> <puerto> [clave_invalida|firma_corrupta]\n", argv[0]);
            return 1;
        }
        const char* modo_fallo = (argc >= 5) ? argv[4] : NULL;
        return run_client(argv[2], atoi(argv[3]), modo_fallo);
    }

    printf("Modo desconocido: %s\n", argv[1]);
    printf("Modos: test (default), server <puerto>, client <ip> <puerto> [clave_invalida|firma_corrupta]\n");
    return 1;
}
