// runtime/core/cluster.c — std.cluster module (M8.1-M8.6): transport UDP/Ed25519,
// distributed work-stealing, Raft consensus, checkpoint/live-migration,
// auto-discovery & membership, UDP multicast.
// Extracted from synapse_rt.c (D-9(d) corte 4, patron modelo.c R39).
// Texto de las funciones BYTE-IDENTICO al original (CRLF preservado).
// El bloque M9.1-M9.3 (debug time-travel) permanece en synapse_rt.c
// (corte 5: debug reversible).
// Consumido por std.cluster (externs Synapse, link-time).

#include "synapse_rt_types.h"
#include "runtime/core/cluster.h"
#include "axon/tweetnacl.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <pthread.h>
#include <time.h>
#ifdef _WIN32
  #include <winsock2.h>
  #include <ws2tcpip.h>
  #include <windows.h>
  #include <io.h>
#else
  #include <sys/socket.h>
  #include <netinet/in.h>
  #include <arpa/inet.h>
  #include <unistd.h>
  #include <sys/select.h>
  #include <fcntl.h>
#endif

// --- Externs del resto del runtime (permanecen en synapse_rt.c) ---
// D-9(d) corte 4: el bloque cluster usa estas funciones definidas fuera.
#include "runtime/core/network.h"  // D-9(d) corte 6: std.net extraido a network.c
extern long long _get_timestamp_ns(void);
extern void sha256_init(SHA256_CTX* ctx);
extern void sha256_update(SHA256_CTX* ctx, const uint8_t* data, size_t len);
extern void sha256_final(SHA256_CTX* ctx, uint8_t* digest);
// TweetNaCl CSPRNG (definida en axon/tweetnacl.c; no declarada en tweetnacl.h)
extern void randombytes(unsigned char* x, unsigned long long xlen);

// ============================================================
// M8.1 — std.cluster — Transport Layer for Distributed Nodes
// UDP-based messaging with Ed25519 authentication
// ============================================================

// --- Ed25519 Key Generation (via TweetNaCl) ---
// Generates a new Ed25519 key pair.
// Returns colon-separated "public_key_hex:private_key_hex"
CadenaSegura cluster_generar_par_claves(void) {
    unsigned char pk[32], sk[64];
    if (crypto_sign_keypair(pk, sk) != 0) {
        return (CadenaSegura){ .longitud = 0, .datos = "" };
    }
    char hex_pk[65], hex_sk[129];
    for (int i = 0; i < 32; i++)
        sprintf(hex_pk + i * 2, "%02x", pk[i]);
    hex_pk[64] = '\0';
    for (int i = 0; i < 64; i++)
        sprintf(hex_sk + i * 2, "%02x", sk[i]);
    hex_sk[128] = '\0';
    int total_len = 64 + 1 + 128;
    char* result = (char*)pool_alloc((size_t)(total_len + 1));
    if (!result) return (CadenaSegura){ .longitud = 0, .datos = "" };
    sprintf(result, "%s:%s", hex_pk, hex_sk);
    return (CadenaSegura){ .longitud = total_len, .datos = result };
}

// --- Ed25519 Signing ---
// clave_privada_hex can be the full "pubkey:privkey" string or just "privkey" (128 chars)
CadenaSegura cluster_firmar_mensaje(CadenaSegura mensaje, CadenaSegura clave_privada_hex) {
    const char* key_start = clave_privada_hex.datos;
    int key_len = clave_privada_hex.longitud;
    // If full par string "pubkey:privkey", skip past pubkey and ':'
    if (key_len == 193) { // 64 + 1 + 128
        key_start += 65;
        key_len = 128;
    }
    if (key_len < 128)
        return (CadenaSegura){ .longitud = 0, .datos = "" };
    unsigned char sk[64];
    for (int i = 0; i < 64; i++) {
        unsigned int byte;
        sscanf(key_start + i * 2, "%02x", &byte);
        sk[i] = (unsigned char)byte;
    }
    unsigned char sm[2048];
    unsigned long long smlen;
    if (crypto_sign(sm, &smlen, (const unsigned char*)mensaje.datos,
                    (unsigned long long)mensaje.longitud, sk) != 0)
        return (CadenaSegura){ .longitud = 0, .datos = "" };
    char hex_sig[129];
    for (int i = 0; i < 64; i++)
        sprintf(hex_sig + i * 2, "%02x", sm[i]);
    hex_sig[128] = '\0';
    char* result = (char*)pool_alloc(129);
    if (!result) return (CadenaSegura){ .longitud = 0, .datos = "" };
    memcpy(result, hex_sig, 129);
    return (CadenaSegura){ .longitud = 128, .datos = result };
}

// --- Ed25519 Signature Verification ---
int cluster_verificar_firma(CadenaSegura mensaje, CadenaSegura firma_hex,
                             CadenaSegura clave_publica_hex) {
    const char* pk_start = clave_publica_hex.datos;
    int pk_len = clave_publica_hex.longitud;
    // If full par string "pubkey:privkey", only use pubkey part
    if (pk_len == 193) pk_len = 64;
    if (firma_hex.longitud < 128 || pk_len < 64) return -1;
    unsigned char firma[64], pk[32];
    for (int i = 0; i < 64; i++) {
        unsigned int byte;
        sscanf(firma_hex.datos + i * 2, "%02x", &byte);
        firma[i] = (unsigned char)byte;
    }
    for (int i = 0; i < 32; i++) {
        unsigned int byte;
        sscanf(pk_start + i * 2, "%02x", &byte);
        pk[i] = (unsigned char)byte;
    }
    unsigned long long mlen = 0;
    unsigned char* sm = (unsigned char*)malloc((size_t)(mensaje.longitud + 64));
    if (!sm) return -1;
    memcpy(sm, firma, 64);
    memcpy(sm + 64, mensaje.datos, (size_t)mensaje.longitud);
    unsigned char* m_buf = (unsigned char*)malloc((size_t)(mensaje.longitud + 64));
    if (!m_buf) { free(sm); return -1; }
    int rc = crypto_sign_open(m_buf, &mlen, sm, (unsigned long long)(mensaje.longitud + 64), pk);
    free(sm);
    free(m_buf);
    return rc;
}

// --- Session Key Derivation (Manual 5 §6.2 paso 3, "o similar") ---
// Derives a 32-byte session key from both Ed25519 public keys using SHA-256.
// No external deps: uses the SHA-256 implementation already in synapse_rt_types.h.
static void cluster_derivar_clave_sesion(const char* pubkey_local_hex,
                                         const char* pubkey_remota_hex,
                                         unsigned char* out_clave) {
    SHA256_CTX ctx;
    sha256_init(&ctx);
    sha256_update(&ctx, (const uint8_t*)pubkey_local_hex, 64);
    sha256_update(&ctx, (const uint8_t*)pubkey_remota_hex, 64);
    sha256_final(&ctx, out_clave);
}

// --- Cifrado AEAD del transporte (R83, Manual 6 §5.3 paso 4 "DATOS_CIFRADOS") ---
// crypto_secretbox de TweetNaCl: XSalsa20-Poly1305 con la clave de sesión
// derivada por KX (R78). Formato en el wire: [nonce 24B][MAC 16B][ciphertext].
// Sustituye al XOR repetitivo pre-R83 (keystream reutilizable entre paquetes).
int cluster_sesion_cifrar_buffer(const unsigned char* clave32,
                                  const char* entrada, int lon,
                                  char* salida, int* lon_salida) {
    if (!clave32 || !entrada || !salida || !lon_salida || lon <= 0) return -1;
    // layout interno TweetNaCl: m=[32 ceros][msg] (d=lon+32) → c=[16 ceros][MAC16][ct]
    // el blob transmitido es c+16 con longitud d-16 = MAC16 + ct
    size_t d = (size_t)lon + 32;
    unsigned char* m = (unsigned char*)calloc(d, 1);
    unsigned char* c = (unsigned char*)malloc(d);
    unsigned char n[24];
    if (!m || !c) { free(m); free(c); return -1; }
    memcpy(m + 32, entrada, (size_t)lon);
    randombytes(n, 24); // nonce aleatorio por mensaje, viaja inline
    if (crypto_secretbox(c, m, d, n, clave32) != 0) {
        free(m); free(c); return -1;
    }
    memcpy(salida, n, 24);
    memcpy(salida + 24, c + 16, d - 16);
    *lon_salida = 24 + (int)(d - 16);
    free(m); free(c);
    return 0;
}

int cluster_sesion_descifrar_buffer(const unsigned char* clave32,
                                     const char* entrada, int lon,
                                     char* salida, int* lon_salida) {
    if (!clave32 || !entrada || !salida || !lon_salida) return -1;
    if (lon < 24 + 16 + 1) return -1; // nonce+mac+mínimo 1 byte
    // Padding TweetNaCl: buffer reconstruido = [0..16 ceros][MAC 16][ct]
    // => tamaño total = (lon-24) + 16   (el blob ya trae la MAC)
    size_t clen = (size_t)(lon - 24) + 16;
    unsigned char* c = (unsigned char*)calloc(clen, 1);
    unsigned char* m = (unsigned char*)malloc(clen);
    if (!c || !m) { free(c); free(m); return -1; }
    memcpy(c + 16, entrada + 24, (size_t)(lon - 24));
    int rc = crypto_secretbox_open(m, c, clen,
                                    (const unsigned char*)entrada, clave32);
    free(c);
    if (rc != 0) { free(m); return -2; } // MAC inválida / clave incorrecta
    *lon_salida = (int)(clen - 32);
    memcpy(salida, m + 32, (size_t)*lon_salida);
    free(m);
    return 0;
}

// --- UDP Socket Helpers ---
static int _cluster_udp_socket(int puerto) {
    int fd = (int)socket(AF_INET, SOCK_DGRAM, 0);
    if (fd < 0) return -1;
    int opt = 1;
    setsockopt(fd, SOL_SOCKET, SO_REUSEADDR, (const char*)&opt, sizeof(opt));
    struct sockaddr_in addr;
    memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_port = htons((unsigned short)puerto);
    addr.sin_addr.s_addr = INADDR_ANY;
    if (bind(fd, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
#ifdef _WIN32
        closesocket(fd);
#else
        close(fd);
#endif
        return -1;
    }
    return fd;
}

static int _cluster_udp_enviar(int fd, const char* ip, int puerto,
                                const char* datos, int lon) {
    struct sockaddr_in addr;
    memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_port = htons((unsigned short)puerto);
    addr.sin_addr.s_addr = inet_addr(ip);
    if (addr.sin_addr.s_addr == INADDR_NONE) return -1;
    return (int)sendto(fd, datos, (size_t)lon, 0,
                       (struct sockaddr*)&addr, sizeof(addr));
}

// --- Cluster Initialization ---
static int _cluster_sock_global = -1;

// Session key state (Manual 5 §6.2 paso 3)
static unsigned char _cluster_sesion_clave[32];
static int _cluster_sesion_activa = 0;

// Ephemeral X25519 keypair for session key derivation (crypto_kx-equivalent,
// Manual 5 §6.2 paso 3 / Manual 6 §5.3 paso 4; R78)
static unsigned char _cluster_kx_sk[32];
static int _cluster_kx_listo = 0;

// Peer identity retained from the verified HELLO (binds KX_INIT to the
// authenticated client, zero-trust per Manual 6 §5.3)
static char _cluster_peer_pk_hex[65] = {0};
static char _cluster_peer_nonce_hex[65] = {0};
static char _cluster_server_nonce_hex[65] = {0};

// Server identity for handshake (generated on iniciar_nodo if not set)
static unsigned char _cluster_server_pk[32];
static unsigned char _cluster_server_sk[64];
static char _cluster_server_sk_hex[129] = {0};
static int _cluster_server_identity = 0;
static char _cluster_server_id[64] = "synapse-server";

void cluster_establecer_clave_sesion(const char* pubkey_local_hex,
                                     const char* pubkey_remota_hex) {
    cluster_derivar_clave_sesion(pubkey_local_hex, pubkey_remota_hex, _cluster_sesion_clave);
    _cluster_sesion_activa = 1;
}

void cluster_limpiar_clave_sesion(void) {
    _cluster_sesion_activa = 0;
    memset(_cluster_sesion_clave, 0, sizeof(_cluster_sesion_clave));
}

// --- Session Key Derivation v2 (R78, Manual 5 §6.2 paso 3 / Manual 6 §5.3 paso 4) ---
// crypto_kx-equivalent built only on TweetNaCl primitives (cero dependencias, regla 8):
//   q    = X25519(sk_local, kx_pk_remota)              [crypto_scalarmult]
//   h    = SHA-512(q || kxpk_cliente || kxpk_servidor) [crypto_hash]
//   clave= h[0..31]  -> _cluster_sesion_clave (XOR transport cipher)
// The client/server ordering is by ROLE (whoever sent the HELLO is the client),
// so both parties derive the identical key without exchanging extra material.
int cluster_kx_secreto_compartido(const unsigned char* sk_local,
                                   const unsigned char* pk_local,
                                   const char* kx_pk_remota_hex,
                                   int rol_cliente,
                                   unsigned char* clave_out32) {
    if (!sk_local || !pk_local || !kx_pk_remota_hex || !clave_out32) return -1;
    if (strlen(kx_pk_remota_hex) != 64) return -1;
    unsigned char peer[32], q[32], buf[96], h[64];
    for (int i = 0; i < 32; i++) {
        unsigned int b;
        if (sscanf(kx_pk_remota_hex + i * 2, "%2x", &b) != 1) return -1;
        peer[i] = (unsigned char)b;
    }
    if (crypto_scalarmult(q, sk_local, peer) != 0) return -1;
    int todo_cero = 1;
    for (int i = 0; i < 32; i++) if (q[i]) { todo_cero = 0; break; }
    if (todo_cero) return -1; // shared secret degenerado (punto de orden pequeño)
    const unsigned char* primero = rol_cliente ? pk_local : peer;
    const unsigned char* segundo = rol_cliente ? peer : pk_local;
    memcpy(buf, q, 32);
    memcpy(buf + 32, primero, 32);
    memcpy(buf + 64, segundo, 32);
    crypto_hash(h, buf, 96);
    memcpy(clave_out32, h, 32);
    return 0;
}

// Variante PURA (sin estado global): genera un par X25519 en buffers del
// caller — usada por las pruebas unitarias (test_cluster_kx.c).
int cluster_kx_par(char* pk_hex_out65, unsigned char* sk_out32) {
    if (!pk_hex_out65 || !sk_out32) return -1;
    randombytes(sk_out32, 32);
    unsigned char pk[32];
    crypto_scalarmult_base(pk, sk_out32);
    for (int i = 0; i < 32; i++) sprintf(pk_hex_out65 + i * 2, "%02x", pk[i]);
    pk_hex_out65[64] = '\0';
    return 0;
}

// Genera el par efímero X25519 del nodo (el secreto queda en el estado del
// runtime); retorna la clave pública en hex (64 chars).
CadenaSegura cluster_kx_generar_par(void) {
    randombytes(_cluster_kx_sk, 32);
    unsigned char pk[32];
    crypto_scalarmult_base(pk, _cluster_kx_sk);
    _cluster_kx_listo = 1;
    char hex[65];
    for (int i = 0; i < 32; i++) sprintf(hex + i * 2, "%02x", pk[i]);
    hex[64] = '\0';
    char* out = (char*)pool_alloc(65);
    if (!out) return (CadenaSegura){ .longitud = 0, .datos = "" };
    memcpy(out, hex, 65);
    return (CadenaSegura){ .longitud = 64, .datos = out };
}

// Deriva y ACTIVA la clave de sesión desde el par efímero global del nodo.
// rol_cliente: 1 si este nodo inició el HELLO, 0 si lo respondió.
int cluster_kx_derivar(const char* kx_pk_remota_hex, int rol_cliente) {
    if (!_cluster_kx_listo) return -1;
    unsigned char lcl[32], clave[32];
    crypto_scalarmult_base(lcl, _cluster_kx_sk);
    if (cluster_kx_secreto_compartido(_cluster_kx_sk, lcl, kx_pk_remota_hex,
                                       rol_cliente, clave) != 0)
        return -1;
    memcpy(_cluster_sesion_clave, clave, sizeof(_cluster_sesion_clave));
    _cluster_sesion_activa = 1;
    return 0;
}

// Hex de la clave de sesión activa (vacía si no hay sesión). Diagnóstico/verificación.
CadenaSegura cluster_clave_sesion_hex(void) {
    if (!_cluster_sesion_activa) return (CadenaSegura){ .longitud = 0, .datos = "" };
    char hex[65];
    for (int i = 0; i < 32; i++) sprintf(hex + i * 2, "%02x", _cluster_sesion_clave[i]);
    hex[64] = '\0';
    char* out = (char*)pool_alloc(65);
    if (!out) return (CadenaSegura){ .longitud = 0, .datos = "" };
    memcpy(out, hex, 65);
    return (CadenaSegura){ .longitud = 64, .datos = out };
}

// --- Send the client's signed ephemeral X25519 public key ---
// Formato: KX_INIT:<kxpub_hex>:<firma_hex>
int cluster_enviar_kx_init(const char* ip, int puerto,
                            CadenaSegura kx_pk_hex, CadenaSegura firma_hex) {
    if (_cluster_sock_global < 0) return -1;
    char buf[512];
    int len = snprintf(buf, sizeof(buf), "KX_INIT:%.*s:%.*s",
                       (int)kx_pk_hex.longitud, kx_pk_hex.datos,
                       (int)firma_hex.longitud, firma_hex.datos);
    return _cluster_udp_enviar(_cluster_sock_global, ip, puerto, buf, len);
}

int cluster_iniciar_nodo(int puerto) {
    _syn_iniciar_red();
    int fd = _cluster_udp_socket(puerto);
    if (fd < 0) return -1;
    _cluster_sock_global = fd;
    cluster_limpiar_clave_sesion();
    if (!_cluster_server_identity) {
        if (crypto_sign_keypair(_cluster_server_pk, _cluster_server_sk) != 0) {
            _cluster_server_identity = 0;
            return -1;
        }
        // Canonical hex form of the full Ed25519 secret key (128 chars):
        // cluster_firmar_mensaje hex-decodes its input, so the raw bytes
        // must NEVER be passed directly (latent bug fixed in R78).
        for (int i = 0; i < 64; i++)
            sprintf(_cluster_server_sk_hex + i * 2, "%02x", _cluster_server_sk[i]);
        _cluster_server_sk_hex[128] = '\0';
        _cluster_server_identity = 1;
    }
    return 0;
}

int cluster_detener_nodo(void) {
    if (_cluster_sock_global >= 0) {
#ifdef _WIN32
        closesocket(_cluster_sock_global);
#else
        close(_cluster_sock_global);
#endif
    }
    _cluster_sock_global = -1;
    return 0;
}

// --- Send HELLO handshake message ---
int cluster_enviar_hello(const char* ip, int puerto,
                          CadenaSegura id_origen, CadenaSegura pubkey_hex) {
    if (_cluster_sock_global < 0) return -1;
    char buf[1024];
    int len = snprintf(buf, sizeof(buf), "HELLO:%.*s:%.*s",
                       (int)id_origen.longitud, id_origen.datos,
                       (int)pubkey_hex.longitud, pubkey_hex.datos);
    return _cluster_udp_enviar(_cluster_sock_global, ip, puerto, buf, len);
}

// --- Generate 32-byte random nonce as 64-char hex ---
CadenaSegura cluster_generar_nonce(void) {
    unsigned char raw[32];
    for (int i = 0; i < 32; i++) raw[i] = (unsigned char)(rand() % 256);
    char hex[65];
    for (int i = 0; i < 32; i++) sprintf(hex + i * 2, "%02x", raw[i]);
    hex[64] = '\0';
    char* out = (char*)pool_alloc(65);
    if (!out) return (CadenaSegura){ .longitud = 0, .datos = "" };
    memcpy(out, hex, 65);
    return (CadenaSegura){ .longitud = 64, .datos = out };
}

// --- Send signed HELLO handshake message ---
// Formato: HELLO:id:nonce_hex:pubkey_hex:firma_hex
int cluster_enviar_hello_firmado(const char* ip, int puerto,
                                  CadenaSegura id_origen,
                                  CadenaSegura pubkey_hex,
                                  CadenaSegura nonce_hex,
                                  CadenaSegura firma_hex) {
    if (_cluster_sock_global < 0) return -1;
    char buf[1024];
    int len = snprintf(buf, sizeof(buf), "HELLO:%.*s:%.*s:%.*s:%.*s",
                       (int)id_origen.longitud, id_origen.datos,
                       (int)nonce_hex.longitud, nonce_hex.datos,
                       (int)pubkey_hex.longitud, pubkey_hex.datos,
                       (int)firma_hex.longitud, firma_hex.datos);
    return _cluster_udp_enviar(_cluster_sock_global, ip, puerto, buf, len);
}

// --- Remote Channel: send data ---
int cluster_canal_remoto_enviar(const char* ip, int puerto,
                                const char* datos, int lon,
                                int chan_id) {
    if (_cluster_sock_global < 0) return -1;
    char header[64];
    static int seq_counter = 0;
    int hdr_len = snprintf(header, sizeof(header), "DATA:%d:%d:", chan_id, seq_counter++);
    uint32_t len_be = htonl((uint32_t)lon);
    // R83: con sesión activa el payload viaja como [nonce24][mac16][ct]
    int overhead = _cluster_sesion_activa ? (24 + 16) : 0;
    int total = hdr_len + 1 + 4 + lon + overhead;
    char* paquete = (char*)pool_alloc((size_t)total);
    if (!paquete) return -1;
    memcpy(paquete, header, (size_t)hdr_len);
    paquete[hdr_len] = 0x06;
    memcpy(paquete + hdr_len + 1, &len_be, 4);
    if (_cluster_sesion_activa)
        cluster_sesion_cifrar_buffer(_cluster_sesion_clave, datos, lon,
                                      paquete + hdr_len + 1 + 4, &overhead);
    else
        memcpy(paquete + hdr_len + 1 + 4, datos, (size_t)lon);
    int n = _cluster_udp_enviar(_cluster_sock_global, ip, puerto,
                                 paquete, total);
    pool_free(paquete);
    return n;
}

// --- Serialization helpers (Manual 5 §6.3, MessagePack-like) ---
static CadenaSegura cluster_deserializar_texto(const char* buf, int len) {
    if (len < 1 + 4) return (CadenaSegura){ .longitud = 0, .datos = "" };
    if ((unsigned char)buf[0] != 0x06) return (CadenaSegura){ .longitud = 0, .datos = "" };
    uint32_t text_len;
    memcpy(&text_len, buf + 1, 4);
    text_len = ntohl(text_len);
    if (text_len > (unsigned)(len - 5)) return (CadenaSegura){ .longitud = 0, .datos = "" };
    char* out = (char*)pool_alloc((size_t)text_len + 1);
    if (!out) return (CadenaSegura){ .longitud = 0, .datos = "" };
    memcpy(out, buf + 5, (size_t)text_len);
    out[text_len] = '\0';
    return (CadenaSegura){ .longitud = (int)text_len, .datos = out };
}

// --- Process incoming HELLO handshake and respond with HELLO_RESP ---
// Formato HELLO: HELLO:id:nonce_hex:pubkey_hex:firma_hex
// Formato HELLO_RESP: HELLO_RESP:id_servidor:nonce_hex:pubkey_hex:firma_hex
static int _cluster_procesar_hello_entrante(const char* buf, int n,
                                             const struct sockaddr_in* from) {
    if (n < 6 || memcmp(buf, "HELLO:", 6) != 0) return 0;
    char id[128] = {0};
    char nonce_hex[65] = {0};
    char pubkey_hex[65] = {0};
    char firma_hex[129] = {0};
    int fields = sscanf(buf + 6, "%127[^:]:%64[^:]:%64[^:]:%128[^:]",
                        id, nonce_hex, pubkey_hex, firma_hex);
    if (fields != 4) return 0;
    if (strlen(nonce_hex) != 64 || strlen(pubkey_hex) != 64 || strlen(firma_hex) != 128)
        return 0;

    CadenaSegura nonce = { .longitud = 64, .datos = nonce_hex };
    CadenaSegura firma = { .longitud = 128, .datos = firma_hex };
    CadenaSegura pk = { .longitud = 64, .datos = pubkey_hex };
    if (cluster_verificar_firma(nonce, firma, pk) != 0) return 0;

    // Retain the authenticated client identity to bind its KX_INIT
    // (zero-trust, Manual 6 §5.3; R78)
    snprintf(_cluster_peer_pk_hex, sizeof(_cluster_peer_pk_hex), "%s", pubkey_hex);
    snprintf(_cluster_peer_nonce_hex, sizeof(_cluster_peer_nonce_hex), "%s", nonce_hex);

    char nonce_serv_hex[65];
    CadenaSegura nonce_serv = cluster_generar_nonce();
    if (nonce_serv.longitud != 64) return 0;
    memcpy(nonce_serv_hex, nonce_serv.datos, 65);
    snprintf(_cluster_server_nonce_hex, sizeof(_cluster_server_nonce_hex), "%s", nonce_serv_hex);

    char pk_serv_hex[65];
    for (int i = 0; i < 32; i++) sprintf(pk_serv_hex + i * 2, "%02x", _cluster_server_pk[i]);
    pk_serv_hex[64] = '\0';

    CadenaSegura mensaje_serv = { .longitud = 64, .datos = nonce_serv_hex };
    CadenaSegura sk_serv_hex = { .longitud = 128, .datos = _cluster_server_sk_hex };
    CadenaSegura firma_serv_hex = cluster_firmar_mensaje(mensaje_serv, sk_serv_hex);
    if (firma_serv_hex.longitud != 128) return 0;

    char resp[1024];
    int resp_len = snprintf(resp, sizeof(resp), "HELLO_RESP:%s:%s:%s:%s",
                            _cluster_server_id, nonce_serv_hex, pk_serv_hex, firma_serv_hex.datos);
    char ip_str[64];
    snprintf(ip_str, sizeof(ip_str), "%s", inet_ntoa(from->sin_addr));
    _cluster_udp_enviar(_cluster_sock_global, ip_str, ntohs(from->sin_port), resp, resp_len);
    return 1;
}

// --- Process incoming KX_INIT: client's signed ephemeral X25519 public key ---
// Formato: KX_INIT:<kxpub_hex>:<firma_hex>
// firma = Ed25519_sign("<kxpub_hex>:<nonce_HELLO_del_cliente>") con la identidad
// del cliente autenticado en HELLO (zero-trust, Manual 6 §5.3; R78).
static int _cluster_procesar_kx_entrante(const char* buf, int n,
                                          const struct sockaddr_in* from) {
    if (n < 8 || memcmp(buf, "KX_INIT:", 8) != 0) return 0;
    if (_cluster_server_identity != 1 || _cluster_peer_pk_hex[0] == '\0') return 0;
    char kx_hex[65] = {0};
    char firma_hex[129] = {0};
    if (sscanf(buf + 8, "%64[^:]:%128s", kx_hex, firma_hex) != 2) return 0;
    if (strlen(kx_hex) != 64 || strlen(firma_hex) != 128) return 0;

    char msg[160];
    snprintf(msg, sizeof(msg), "%s:%s", kx_hex, _cluster_peer_nonce_hex);
    CadenaSegura m = { .longitud = (int)strlen(msg), .datos = msg };
    CadenaSegura f = { .longitud = 128, .datos = firma_hex };
    CadenaSegura pk = { .longitud = 64, .datos = _cluster_peer_pk_hex };
    if (cluster_verificar_firma(m, f, pk) != 0) return 0;

    CadenaSegura pk_serv = cluster_kx_generar_par();
    if (pk_serv.longitud != 64) return 0;
    if (cluster_kx_derivar(kx_hex, 0) != 0) return 0;

    char msg2[160];
    snprintf(msg2, sizeof(msg2), "%.*s:%s", 64, pk_serv.datos, _cluster_server_nonce_hex);
    CadenaSegura m2 = { .longitud = (int)strlen(msg2), .datos = msg2 };
    CadenaSegura sk_srv_hex = { .longitud = 128, .datos = _cluster_server_sk_hex };
    CadenaSegura firma = cluster_firmar_mensaje(m2, sk_srv_hex);
    if (firma.longitud != 128) return 0;

    char resp[256];
    int rl = snprintf(resp, sizeof(resp), "KX_RESP:%.*s:%.*s",
                      64, pk_serv.datos, 128, firma.datos);
    char ip_str[64];
    snprintf(ip_str, sizeof(ip_str), "%s", inet_ntoa(from->sin_addr));
    _cluster_udp_enviar(_cluster_sock_global, ip_str, ntohs(from->sin_port), resp, rl);
    return 1;
}

// --- Receive a datagram (non-blocking) ---
// R78 (fix): honra timeout_ms vía select() — la API documentada
// (std/cluster.syn recibir) promete "tiempo máximo de espera"; la versión
// previa hacía un único recvfrom no bloqueante y retornaba al instante.
CadenaSegura cluster_recibir_paquete(int timeout_ms) {
    if (_cluster_sock_global < 0) return (CadenaSegura){ .longitud = 0, .datos = "" };
    if (timeout_ms > 0) {
        fd_set leer;
        struct timeval tv;
        tv.tv_sec = timeout_ms / 1000;
        tv.tv_usec = (timeout_ms % 1000) * 1000;
        FD_ZERO(&leer);
        FD_SET((unsigned int)_cluster_sock_global, &leer);
        int listo = select((int)_cluster_sock_global + 1, &leer, NULL, NULL, &tv);
        if (listo <= 0) return (CadenaSegura){ .longitud = 0, .datos = "" };
    }
#ifdef _WIN32
    u_long mode = 1;
    ioctlsocket(_cluster_sock_global, FIONBIO, &mode);
#else
    int flags = fcntl(_cluster_sock_global, F_GETFL, 0);
    fcntl(_cluster_sock_global, F_SETFL, flags | O_NONBLOCK);
#endif
    char buf[65536];
    struct sockaddr_in from;
    socklen_t fromlen = sizeof(from);
    int n = (int)recvfrom(_cluster_sock_global, buf, sizeof(buf) - 1, 0,
                           (struct sockaddr*)&from, &fromlen);
    if (n <= 0) return (CadenaSegura){ .longitud = 0, .datos = "" };
    buf[n] = '\0';
    if (_cluster_procesar_hello_entrante(buf, n, &from)) {
        return (CadenaSegura){ .longitud = 0, .datos = "" };
    }
    if (_cluster_procesar_kx_entrante(buf, n, &from)) {
        return (CadenaSegura){ .longitud = 0, .datos = "" };
    }
        if (n >= 5 && memcmp(buf, "DATA:", 5) == 0) {
            // R83: parseo determinista "DATA:<chan>:<seq>:<payload>" — el
            // payload binario (nonce/MAC) puede contener 0x3A, así que NO se
            // busca el último ':' en todo el datagrama.
            const char* c1 = memchr(buf + 5, ':', (size_t)(n - 5));
            const char* c2 = c1 ? memchr(c1 + 1, ':', (size_t)(buf + n - c1 - 1)) : NULL;
            if (c2 && c2 + 1 < buf + n) {
                int seg_len = (int)(buf + n - (c2 + 1));
                const char* seg = c2 + 1;
            if (_cluster_sesion_activa && seg_len > 1 + 4 + 24 + 16) {
                // R83: [0x06][len_be][nonce24][mac16+ct] — descifrar y validar
                uint32_t len_be;
                memcpy(&len_be, seg + 1, 4);
                int lon_plain = (int)(seg_len - 1 - 4 - 24 - 16);
                if (lon_plain > 0 && ntohl(len_be) == (uint32_t)lon_plain) {
                    char* plain = (char*)pool_alloc((size_t)lon_plain);
                    int lon_out = 0;
                    if (plain &&
                        cluster_sesion_descifrar_buffer(_cluster_sesion_clave,
                                                         seg + 1 + 4, seg_len - 1 - 4,
                                                         plain, &lon_out) == 0 &&
                        lon_out == lon_plain) {
                        return (CadenaSegura){ .longitud = lon_out, .datos = plain };
                    }
                    // MAC inválida o clave distinta → descartar datagrama
                    return (CadenaSegura){ .longitud = 0, .datos = "" };
                }
            }
            CadenaSegura texto = cluster_deserializar_texto(seg, seg_len);
            if (texto.longitud > 0) {
                return texto;
            }
        }
    }
    char* result = (char*)pool_alloc((size_t)(n + 1));
    if (!result) return (CadenaSegura){ .longitud = 0, .datos = "" };
    memcpy(result, buf, (size_t)(n + 1));
    return (CadenaSegura){ .longitud = n, .datos = result };
}

// ============================================================
// M8.2 — Distributed Work-Stealing Scheduler
// Lock-free-ish distributed task scheduler using local queues
// and UDP-based stealing protocol (STEAL/STOLEN messages).
// Each node maintains a local deque protected by a pthread mutex.
// ============================================================

// --- Work queue entry ---
typedef struct {
    int id;
    char* datos;
    int len;
} WsTarea;

// --- Work queue state ---
static WsTarea* _ws_cola = NULL;
static int _ws_capacidad = 0;
static int _ws_cabeza = 0;  // pop from front (stealing)
static int _ws_cola_idx = 0; // push to back (local)
static int _ws_contador = 0;
static pthread_mutex_t _ws_mutex = PTHREAD_MUTEX_INITIALIZER;
static int _ws_robo_seq = 0;
static int _ws_ultimo_robo_seq = -1;

// --- Stolen task buffer (for receiving stolen tasks) ---
static WsTarea _ws_robada = {0, NULL, 0};
static int _ws_robada_valida = 0;

int ws_inicializar(int capacidad) {
    if (capacidad <= 0) capacidad = 1024;
    if (_ws_cola) {
        free(_ws_cola);
        _ws_cola = NULL;
    }
    _ws_cola = (WsTarea*)malloc((size_t)capacidad * sizeof(WsTarea));
    if (!_ws_cola) return -1;
    memset(_ws_cola, 0, (size_t)capacidad * sizeof(WsTarea));
    _ws_capacidad = capacidad;
    _ws_cabeza = 0;
    _ws_cola_idx = 0;
    _ws_contador = 0;
    _ws_robo_seq = 0;
    _ws_ultimo_robo_seq = -1;
    _ws_robada_valida = 0;
    return 0;
}

int ws_encolar(int id, CadenaSegura datos) {
    pthread_mutex_lock(&_ws_mutex);
    if (_ws_contador >= _ws_capacidad) {
        pthread_mutex_unlock(&_ws_mutex);
        return -1;
    }
    char* copia = (char*)malloc((size_t)(datos.longitud + 1));
    if (!copia) { pthread_mutex_unlock(&_ws_mutex); return -1; }
    memcpy(copia, datos.datos, (size_t)datos.longitud);
    copia[datos.longitud] = '\0';
    _ws_cola[_ws_cola_idx].id = id;
    _ws_cola[_ws_cola_idx].datos = copia;
    _ws_cola[_ws_cola_idx].len = datos.longitud;
    _ws_cola_idx = (_ws_cola_idx + 1) % _ws_capacidad;
    _ws_contador++;
    pthread_mutex_unlock(&_ws_mutex);
    return 0;
}

CadenaSegura ws_desencolar(void) {
    pthread_mutex_lock(&_ws_mutex);
    if (_ws_contador <= 0) {
        pthread_mutex_unlock(&_ws_mutex);
        return (CadenaSegura){ .longitud = 0, .datos = "" };
    }
    // Pop from back (LIFO) for local worker — better cache locality
    int idx = (_ws_cola_idx - 1 + _ws_capacidad) % _ws_capacidad;
    // But if only 1 item, pop from front
    if (_ws_contador == 1) idx = _ws_cabeza;
    WsTarea t = _ws_cola[idx];
    _ws_cola[idx].datos = NULL;
    // Recalculate indices
    if (_ws_contador == 1) {
        _ws_cabeza = 0;
        _ws_cola_idx = 0;
    } else if (idx == _ws_cabeza) {
        _ws_cabeza = (_ws_cabeza + 1) % _ws_capacidad;
    } else {
        _ws_cola_idx = (_ws_cola_idx - 1 + _ws_capacidad) % _ws_capacidad;
    }
    _ws_contador--;
    pthread_mutex_unlock(&_ws_mutex);
    // Build result string "id:datos"
    char id_str[32];
    int id_len = snprintf(id_str, sizeof(id_str), "%d:", t.id);
    int total_len = id_len + t.len;
    char* buf = (char*)pool_alloc((size_t)(total_len + 1));
    if (!buf) { free(t.datos); return (CadenaSegura){ .longitud = 0, .datos = "" }; }
    memcpy(buf, id_str, (size_t)id_len);
    memcpy(buf + id_len, t.datos, (size_t)t.len);
    buf[total_len] = '\0';
    free(t.datos);
    return (CadenaSegura){ .longitud = total_len, .datos = buf };
}

int ws_profundidad(void) {
    pthread_mutex_lock(&_ws_mutex);
    int n = _ws_contador;
    pthread_mutex_unlock(&_ws_mutex);
    return n;
}

int ws_carga_estimada(void) {
    pthread_mutex_lock(&_ws_mutex);
    int pct = (_ws_capacidad > 0) ? (_ws_contador * 100 / _ws_capacidad) : 0;
    if (pct > 100) pct = 100;
    pthread_mutex_unlock(&_ws_mutex);
    return pct;
}

// --- Steal from front (for stealing by remote nodes) ---
// Called by the responder: removes task from front and returns it.
// The caller must format the response message.
static int _ws_robar_frontal(int* out_id, char** out_data, int* out_len) {
    pthread_mutex_lock(&_ws_mutex);
    if (_ws_contador <= 0) {
        pthread_mutex_unlock(&_ws_mutex);
        return -1;
    }
    WsTarea t = _ws_cola[_ws_cabeza];
    _ws_cola[_ws_cabeza].datos = NULL;
    _ws_cabeza = (_ws_cabeza + 1) % _ws_capacidad;
    _ws_contador--;
    pthread_mutex_unlock(&_ws_mutex);
    *out_id = t.id;
    *out_data = t.datos;
    *out_len = t.len;
    return 0;
}

// --- Send steal request to a remote node ---
// Format: "WSTEAL:<seq>"
int ws_enviar_solicitud_robo(CadenaSegura ip, int puerto) {
    if (_cluster_sock_global < 0) return -1;
    int seq = __atomic_fetch_add(&_ws_robo_seq, 1, __ATOMIC_SEQ_CST);
    _ws_ultimo_robo_seq = seq;
    char buf[64];
    int len = snprintf(buf, sizeof(buf), "WSTEAL:%d", seq);
    const char* ip_str = ip.datos;
    int puerto_int = puerto;
    return _cluster_udp_enviar(_cluster_sock_global, ip_str, puerto_int, buf, len);
}

// --- Process incoming message for work-stealing protocol ---
// Returns structured text:
//   "ROBADA:id:data" — a stolen task was received (the caller's steal was answered)
//   "ATENDIDO" — a WSTEAL request was handled (stolen task sent back)
//   "VACIA" — a WSTEAL request came but local queue was empty
//   original data — pass-through for non-steal messages
CadenaSegura ws_procesar_mensaje(CadenaSegura paquete) {
    if (paquete.longitud < 7) return paquete;
    const char* p = paquete.datos;
    int plen = paquete.longitud;

    // Check for "WSTEAL:" prefix (incoming steal request)
    if (plen >= 7 && memcmp(p, "WSTEAL:", 7) == 0) {
        // Responder: dequeue from front and send back as "WSTOLEN:<seq>:<id>:<data>"
        int seq = 0;
        sscanf(p + 7, "%d", &seq);
        int task_id;
        char* task_data;
        int task_len;
        if (_ws_robar_frontal(&task_id, &task_data, &task_len) != 0) {
            // Queue empty — send "WNONE:<seq>"
            char resp[64];
            int rlen = snprintf(resp, sizeof(resp), "WNONE:%d", seq);
            (void)rlen;
            // We need to know who sent it. Since we don't track sender addr,
            // we can't respond. The requester will timeout.
            // For now, just store that we were empty.
            return (CadenaSegura){ .longitud = 5, .datos = "VACIA" };
        }
        // Build response: "WSTOLEN:<seq>:<id>:<data>"
        char hdr[64];
        int hdr_len = snprintf(hdr, sizeof(hdr), "WSTOLEN:%d:%d:", seq, task_id);
        int total = hdr_len + task_len;
        char* resp = (char*)pool_alloc((size_t)(total + 1));
        if (!resp) { free(task_data); return (CadenaSegura){ .longitud = 0, .datos = "" }; }
        memcpy(resp, hdr, (size_t)hdr_len);
        memcpy(resp + hdr_len, task_data, (size_t)task_len);
        resp[total] = '\0';
        free(task_data);
        // In a real scenario, we'd send this back to the requester.
        // For the simulation test, we return it as "ATENDIDO" + the response data
        // to allow the test harness to route it.
        char* result = (char*)pool_alloc((size_t)(total + 10));
        if (!result) return (CadenaSegura){ .longitud = 0, .datos = "" };
        memcpy(result, "ATENDIDO:", 9);
        memcpy(result + 9, resp, (size_t)total);
        result[total + 9] = '\0';
        pool_free(resp);
        return (CadenaSegura){ .longitud = total + 9, .datos = result };
    }

    // Check for "WSTOLEN:" prefix (incoming steal response)
    if (plen >= 8 && memcmp(p, "WSTOLEN:", 8) == 0) {
        // Parse: "WSTOLEN:<seq>:<id>:<data>"
        int seq, task_id;
        int consumed = 0;
        if (sscanf(p + 8, "%d:%d%n", &seq, &task_id, &consumed) >= 2) {
            int data_start = 8 + consumed + 1; // skip past ":<data>"
            if (data_start < plen) {
                int data_len = plen - data_start;
                char* copia = (char*)malloc((size_t)(data_len + 1));
                if (copia) {
                    memcpy(copia, p + data_start, (size_t)data_len);
                    copia[data_len] = '\0';
                    // Store in stolen buffer
                    pthread_mutex_lock(&_ws_mutex);
                    if (_ws_robada.datos) free(_ws_robada.datos);
                    _ws_robada.id = task_id;
                    _ws_robada.datos = copia;
                    _ws_robada.len = data_len;
                    _ws_robada_valida = 1;
                    pthread_mutex_unlock(&_ws_mutex);
                    // Return "ROBADA:id:data"
                    char id_str[32];
                    int id_len = snprintf(id_str, sizeof(id_str), "%d:", task_id);
                    int total = 7 + id_len + data_len; // "ROBADA:" + "id:" + data
                    char* buf = (char*)pool_alloc((size_t)(total + 1));
                    if (buf) {
                        memcpy(buf, "ROBADA:", 7);
                        memcpy(buf + 7, id_str, (size_t)id_len);
                        memcpy(buf + 7 + id_len, copia, (size_t)data_len);
                        buf[total] = '\0';
                        return (CadenaSegura){ .longitud = total, .datos = buf };
                    }
                }
            }
        }
        return (CadenaSegura){ .longitud = 0, .datos = "" };
    }

    // Check for "WNONE:" prefix (steal response with no tasks)
    if (plen >= 6 && memcmp(p, "WNONE:", 6) == 0) {
        return (CadenaSegura){ .longitud = 5, .datos = "VACIA" };
    }

    // Not a steal message — pass through
    return paquete;
}

// --- Retrieve the last stolen task ---
// Returns "id:data" or "" if none
CadenaSegura ws_ultima_robada(void) {
    pthread_mutex_lock(&_ws_mutex);
    if (!_ws_robada_valida || !_ws_robada.datos) {
        pthread_mutex_unlock(&_ws_mutex);
        return (CadenaSegura){ .longitud = 0, .datos = "" };
    }
    char id_str[32];
    int id_len = snprintf(id_str, sizeof(id_str), "%d:", _ws_robada.id);
    int total = id_len + _ws_robada.len;
    char* buf = (char*)pool_alloc((size_t)(total + 1));
    if (!buf) {
        pthread_mutex_unlock(&_ws_mutex);
        return (CadenaSegura){ .longitud = 0, .datos = "" };
    }
    memcpy(buf, id_str, (size_t)id_len);
    memcpy(buf + id_len, _ws_robada.datos, (size_t)_ws_robada.len);
    buf[total] = '\0';
    pthread_mutex_unlock(&_ws_mutex);
    return (CadenaSegura){ .longitud = total, .datos = buf };
}

// --- Manually forward a WSTEAL response to the requester ---
// Used in simulation: the test harness routes ATENDIDO responses back.
int ws_reenviar_respuesta(CadenaSegura ip, int puerto, CadenaSegura respuesta) {
    if (_cluster_sock_global < 0 || respuesta.longitud <= 0) return -1;
    return _cluster_udp_enviar(_cluster_sock_global, ip.datos, puerto,
                                respuesta.datos, respuesta.longitud);
}

// ============================================================
// M8.3 — Raft Consensus Algorithm for Shared State
// Simplified Raft implementation:
//   - Leader election with randomized timeouts
//   - Term-based voting
//   - Heartbeat mechanism (AppendEntries)
//   - Log replication tracking
// Supports multi-node simulation via node_id-indexed state array.
// ============================================================

#define RAFT_FOLLOWER  0
#define RAFT_CANDIDATE 1
#define RAFT_LEADER    2

#define MAX_RAFT_NODES 8
#define RAFT_HEARTBEAT_MS 50
#define RAFT_ELECTION_MIN_MS 150
#define RAFT_ELECTION_MAX_MS 300

typedef struct {
    int current_term;
    int voted_for;
    int state;
    int node_id;
    int num_nodes;
    long long election_deadline_ns;
    long long next_heartbeat_ns;
    int leader_id;
    int log_count;
    int last_log_index;   // Raft: index of last log entry
    int last_log_term;    // Raft: term of last log entry
    int commit_index;
    int last_applied;
    int votes_granted;
    int votes_needed;
    unsigned int seed;
    // Ed25519 signing keypair for Raft RPC authentication
    char clave_publica_hex[65];   // 32 bytes -> 64 hex chars + null
    char clave_privada_hex[65];   // 32 bytes -> 64 hex chars + null
} RaftNode;

static RaftNode _raft_nodes[MAX_RAFT_NODES];
static int _raft_inicializado = 0;
// static int _raft_simulation_mode = 0;

static long long _raft_now_ns(void) {
    return _get_timestamp_ns();
}

static int _raft_rand_range(RaftNode* n, int min, int max) {
    n->seed = n->seed * 1103515245u + 12345u;
    return min + (int)((n->seed >> 16) % (unsigned int)(max - min + 1));
}

static RaftNode* _raft_get(int node_id) {
    if (node_id < 0 || node_id >= MAX_RAFT_NODES) return NULL;
    return &_raft_nodes[node_id];
}

int raft_inicializar(int node_id, int num_nodes, int seed) {
    if (node_id < 0 || node_id >= MAX_RAFT_NODES) return -1;
    if (num_nodes < 1 || num_nodes > MAX_RAFT_NODES) return -1;
    RaftNode* n = &_raft_nodes[node_id];
    n->current_term = 0;
    n->voted_for = -1;
    n->state = RAFT_FOLLOWER;
    n->node_id = node_id;
    n->num_nodes = num_nodes;
    n->election_deadline_ns = 0;
    n->next_heartbeat_ns = 0;
    n->leader_id = -1;
    n->log_count = 0;
    n->last_log_index = 0;
    n->last_log_term = 0;
    n->commit_index = 0;
    n->last_applied = 0;
    n->votes_granted = 0;
    n->votes_needed = num_nodes / 2 + 1;
    n->seed = (unsigned int)(seed ^ node_id);
    // Generate Ed25519 keypair for Raft RPC authentication
    {
        unsigned char pk[32], sk[64];
        crypto_sign_keypair(pk, sk);
        for (int i = 0; i < 32; i++) {
            snprintf(n->clave_publica_hex + i * 2, 3, "%02x", pk[i]);
            snprintf(n->clave_privada_hex + i * 2, 3, "%02x", sk[i]);
        }
        n->clave_publica_hex[64] = '\0';
        n->clave_privada_hex[64] = '\0';
    }
    _raft_inicializado = 1;
    return 0;
}

int raft_iniciar(long long tiempo_actual_ns, int node_id) {
    RaftNode* n = _raft_get(node_id);
    if (!n) return -1;
    n->state = RAFT_FOLLOWER;
    n->leader_id = -1;
    n->voted_for = -1;
    int timeout = _raft_rand_range(n, RAFT_ELECTION_MIN_MS, RAFT_ELECTION_MAX_MS);
    n->election_deadline_ns = tiempo_actual_ns + (long long)timeout * 1000000LL;
    n->next_heartbeat_ns = 0;
    return 0;
}

int raft_estado(int node_id) {
    RaftNode* n = _raft_get(node_id);
    return n ? n->state : -1;
}

int raft_term_actual(int node_id) {
    RaftNode* n = _raft_get(node_id);
    return n ? n->current_term : -1;
}

int raft_lider_actual(int node_id) {
    RaftNode* n = _raft_get(node_id);
    return n ? n->leader_id : -1;
}

int raft_log_entradas(int node_id) {
    RaftNode* n = _raft_get(node_id);
    return n ? n->log_count : -1;
}

int raft_commit_index(int node_id) {
    RaftNode* n = _raft_get(node_id);
    return n ? n->commit_index : -1;
}

// --- Start election (called by follower/candidate on timeout) ---
static void _raft_iniciar_eleccion(RaftNode* n, long long now_ns) {
    n->current_term++;
    n->state = RAFT_CANDIDATE;
    n->voted_for = n->node_id;
    n->votes_granted = 1;  // vote for self
    n->leader_id = -1;

    // Reset election timeout for this node
    int timeout = _raft_rand_range(n, RAFT_ELECTION_MIN_MS, RAFT_ELECTION_MAX_MS);
    n->election_deadline_ns = now_ns + (long long)timeout * 1000000LL;

    // In simulation mode: send RequestVote to all other nodes
    // (handled by the test harness calling raft_procesar_solicitud_voto)
}

// --- Ed25519 signing for Raft RPC messages ---
// Signs a Raft message with the node's Ed25519 private key.
// msg: the raw message bytes (e.g., "RVOTE:<term>:<id>:<log_idx>:<log_term>")
// firma_out: output buffer for 64-byte hex signature (128 chars + null)
// Returns: 0 on success, -1 on error
int raft_firmar_mensaje(int node_id, const char* msg, int msg_len,
                         char* firma_out) {
    RaftNode* n = _raft_get(node_id);
    if (!n || !msg || !firma_out || msg_len <= 0) return -1;

    // Decode private key from hex
    unsigned char sk[64];
    for (int i = 0; i < 64; i++) {
        unsigned int byte;
        sscanf(n->clave_privada_hex + i * 2, "%02x", &byte);
        sk[i] = (unsigned char)byte;
    }

    // Sign: crypto_sign returns signature || message
    unsigned long long smlen = 0;
    unsigned char* sm = (unsigned char*)malloc((size_t)(msg_len + 64));
    if (!sm) return -1;
    crypto_sign(sm, &smlen, (const unsigned char*)msg,
                (unsigned long long)msg_len, sk);

    // Extract first 64 bytes (signature) and encode to hex
    for (int i = 0; i < 64; i++) {
        snprintf(firma_out + i * 2, 3, "%02x", sm[i]);
    }
    firma_out[128] = '\0';
    free(sm);
    return 0;
}

// Verifies an Ed25519 signature on a Raft message.
// msg: the raw message bytes
// firma_hex: 128-char hex signature
// pk_hex: 64-char hex public key
// Returns: 0 if valid, -1 if invalid
int raft_verificar_firma_rpc(const char* msg, int msg_len,
                              const char* firma_hex, const char* pk_hex) {
    if (!msg || !firma_hex || !pk_hex || msg_len <= 0) return -1;
    if (strlen(firma_hex) < 128 || strlen(pk_hex) < 64) return -1;

    // Decode signature and public key
    unsigned char sig[64], pk[32];
    for (int i = 0; i < 64; i++) {
        unsigned int byte;
        sscanf(firma_hex + i * 2, "%02x", &byte);
        sig[i] = (unsigned char)byte;
    }
    for (int i = 0; i < 32; i++) {
        unsigned int byte;
        sscanf(pk_hex + i * 2, "%02x", &byte);
        pk[i] = (unsigned char)byte;
    }

    // Build signed message: signature || original message
    unsigned long long smlen = (unsigned long long)(msg_len + 64);
    unsigned char* sm = (unsigned char*)malloc(smlen);
    if (!sm) return -1;
    memcpy(sm, sig, 64);
    memcpy(sm + 64, msg, (size_t)msg_len);

    // Verify
    unsigned char* mout = (unsigned char*)malloc(smlen);
    if (!mout) { free(sm); return -1; }
    unsigned long long mlen = 0;
    int rc = crypto_sign_open(mout, &mlen, sm, smlen, pk);
    free(sm);
    free(mout);
    return rc;  // 0 = valid, -1 = invalid
}

// --- Process a RequestVote message ---
// msg format: "RVOTE:<term>:<candidate_id>:<last_log_idx>:<last_log_term>"
// Returns: 1=voted, 0=denied, -1=error
int raft_procesar_solicitud_voto(int voter_id, int candidate_term,
                                  int candidate_id, int candidate_last_log,
                                  int candidate_last_log_term) {
    RaftNode* n = _raft_get(voter_id);
    if (!n) return -1;

    // If candidate term < current term, deny
    if (candidate_term < n->current_term) return 0;

    // If candidate term > current term, step down and update
    if (candidate_term > n->current_term) {
        n->current_term = candidate_term;
        n->state = RAFT_FOLLOWER;
        n->voted_for = -1;
        n->leader_id = -1;
    }

    // If already voted in this term, deny
    if (n->voted_for != -1 && n->voted_for != candidate_id) return 0;

    // Raft safety: Log Comparison
    // A candidate must have a log at least as up-to-date as the voter's log.
    // Compare last_log_term first; if equal, compare last_log_index.
    if (candidate_last_log_term < n->last_log_term) return 0;
    if (candidate_last_log_term == n->last_log_term &&
        candidate_last_log < n->last_log_index) return 0;

    // Grant vote
    n->voted_for = candidate_id;
    long long now = _raft_now_ns();
    int timeout = _raft_rand_range(n, RAFT_ELECTION_MIN_MS, RAFT_ELECTION_MAX_MS);
    n->election_deadline_ns = now + (long long)timeout * 1000000LL;
    return 1;
}

// --- Process a RequestVote response ---
// msg format: "RVOTED:<term>:<voter_id>:<granted>"
// Returns: 1=leader elected, 0=still candidate, -1=error
int raft_procesar_respuesta_voto(int candidate_id, int responder_term,
                                  int responder_id, int granted) {
    RaftNode* n = _raft_get(candidate_id);
    if (!n || n->state != RAFT_CANDIDATE) return -1;

    // Ignore stale responses
    if (responder_term != n->current_term) return 0;

    if (granted) {
        n->votes_granted++;
        if (n->votes_granted >= n->votes_needed) {
            // Become leader
            n->state = RAFT_LEADER;
            n->leader_id = n->node_id;
            long long now = _raft_now_ns();
            n->next_heartbeat_ns = now;
            return 1;  // leader elected
        }
    }
    return 0;
}

// --- Process a heartbeat / AppendEntries from leader ---
// msg format: "RHB:<term>:<leader_id>:<leader_commit>"
// Returns: 1=accepted, 0=rejected (stale term), -1=error
int raft_procesar_heartbeat(int follower_id, int leader_term,
                             int leader_id, int leader_commit) {
    RaftNode* n = _raft_get(follower_id);
    if (!n) return -1;

    // Reject stale term
    if (leader_term < n->current_term) return 0;

    // Leader term >= current term: acknowledge
    if (leader_term > n->current_term) {
        n->current_term = leader_term;
        n->state = RAFT_FOLLOWER;
        n->voted_for = -1;
    }

    n->leader_id = leader_id;
    n->state = RAFT_FOLLOWER;

    // Update commit index
    if (leader_commit > n->commit_index) {
        n->commit_index = leader_commit;
        if (n->commit_index > n->log_count)
            n->commit_index = n->log_count;
    }

    // Reset election timeout (we have a valid leader)
    long long now = _raft_now_ns();
    int timeout = _raft_rand_range(n, RAFT_ELECTION_MIN_MS, RAFT_ELECTION_MAX_MS);
    n->election_deadline_ns = now + (long long)timeout * 1000000LL;

    return 1;
}

// --- Tick: advance Raft time. Call periodically ---
// Handles election timeouts and heartbeat scheduling.
// Returns: event code — 0=no event, 1=election started, 2=heartbeat sent
int raft_tick(long long tiempo_actual_ns, int node_id) {
    RaftNode* n = _raft_get(node_id);
    if (!n) return -1;

    if (n->state == RAFT_LEADER) {
        // Send heartbeats periodically
        if (tiempo_actual_ns >= n->next_heartbeat_ns) {
            n->next_heartbeat_ns = tiempo_actual_ns + (long long)RAFT_HEARTBEAT_MS * 1000000LL;
            return 2;  // heartbeat due
        }
        return 0;
    }

    // Follower or candidate: check election timeout
    if (tiempo_actual_ns >= n->election_deadline_ns) {
        if (n->state == RAFT_FOLLOWER) {
            _raft_iniciar_eleccion(n, tiempo_actual_ns);
            return 1;  // election started
        } else if (n->state == RAFT_CANDIDATE) {
            // Election timeout: start new election
            _raft_iniciar_eleccion(n, tiempo_actual_ns);
            return 1;  // new election started
        }
    }

    return 0;
}

// --- Force leader to step down (for testing) ---
int raft_forzar_abdicacion(int node_id) {
    RaftNode* n = _raft_get(node_id);
    if (!n || n->state != RAFT_LEADER) return -1;
    n->state = RAFT_FOLLOWER;
    n->leader_id = -1;
    n->voted_for = -1;
    long long now = _raft_now_ns();
    int timeout = _raft_rand_range(n, RAFT_ELECTION_MIN_MS, RAFT_ELECTION_MAX_MS);
    n->election_deadline_ns = now + (long long)timeout * 1000000LL;
    return 0;
}

// --- Append a log entry to the leader (for testing) ---
int raft_agregar_entrada(int node_id) {
    RaftNode* n = _raft_get(node_id);
    if (!n || n->state != RAFT_LEADER) return -1;
    n->log_count++;
    n->last_log_index = n->log_count;
    n->last_log_term = n->current_term;
    return n->log_count;
}

// --- Reset state for a node (for testing) ---
int raft_reiniciar_nodo(int node_id) {
    RaftNode* n = _raft_get(node_id);
    if (!n) return -1;
    return raft_inicializar(node_id, n->num_nodes, (int)(_raft_now_ns() & 0x7FFFFFFF));
}

// --- Get node info string for diagnostics ---
// Returns comma-separated "term,state,leader,log,commit"
CadenaSegura raft_info(int node_id) {
    RaftNode* n = _raft_get(node_id);
    if (!n) return (CadenaSegura){ .longitud = 0, .datos = "" };
    char buf[128];
    int len = snprintf(buf, sizeof(buf), "%d,%d,%d,%d,%d",
                       n->current_term, n->state, n->leader_id,
                       n->log_count, n->commit_index);
    char* result = (char*)pool_alloc((size_t)(len + 1));
    if (!result) return (CadenaSegura){ .longitud = 0, .datos = "" };
    memcpy(result, buf, (size_t)len);
    result[len] = '\0';
    return (CadenaSegura){ .longitud = len, .datos = result };
}

// =========================================================================
// M8.4 — Checkpoint/Restore (Migración de Tareas Live)
// =========================================================================
// Serialización de estado de tareas para migración en caliente entre nodos.
// Formato checkpoint: CKPT:<task_id>:<seq>:<sha256_hex>:<data_len>:<data>
// Checksum: SHA-256 (64-char hex) for cryptographic integrity verification
// =========================================================================

static int _cm_seq = 0;
static int _cm_completadas = 0;
static int _cm_fallidas = 0;
static char _cm_ultimo_resultado[256];

static pthread_mutex_t _cm_mutex = PTHREAD_MUTEX_INITIALIZER;

// --- Compute full SHA-256 hex hash for checkpoint integrity ---
// Returns 64-char hex string (caller must free if pool_alloc'd).
static void _cm_sha256_hex(const char* data, int len, char* hex_out) {
    SHA256_CTX ctx;
    uint8_t digest[32];
    sha256_init(&ctx);
    sha256_update(&ctx, (const uint8_t*)data, (size_t)len);
    sha256_final(&ctx, digest);
    for (int i = 0; i < 32; i++) {
        snprintf(hex_out + i * 2, 3, "%02x", digest[i]);
    }
    hex_out[64] = '\0';
}

// --- Initialize checkpoint subsystem ---
int cm_inicializar(void) {
    pthread_mutex_lock(&_cm_mutex);
    _cm_seq = 0;
    _cm_completadas = 0;
    _cm_fallidas = 0;
    _cm_ultimo_resultado[0] = '\0';
    pthread_mutex_unlock(&_cm_mutex);
    return 0;
}

// --- Serialize a task into a CKPT checkpoint string ---
// Returns: "CKPT:<id>:<seq>:<sha256_hex>:<data_len>:<data>"
CadenaSegura cm_serializar_checkpoint(int task_id, CadenaSegura datos) {
    if (datos.longitud <= 0 || !datos.datos)
        return (CadenaSegura){ .longitud = 0, .datos = NULL };

    pthread_mutex_lock(&_cm_mutex);
    int seq = _cm_seq++;
    pthread_mutex_unlock(&_cm_mutex);

    // Full SHA-256 hash for cryptographic integrity
    char sha256_hex[65];
    _cm_sha256_hex(datos.datos, datos.longitud, sha256_hex);

    char header[128];
    int hdr_len = snprintf(header, sizeof(header), "CKPT:%d:%d:%s:%d:",
                           task_id, seq, sha256_hex, datos.longitud);

    int total_len = hdr_len + datos.longitud;
    char* buf = (char*)pool_alloc((size_t)(total_len + 1));
    if (!buf) return (CadenaSegura){ .longitud = 0, .datos = NULL };

    memcpy(buf, header, (size_t)hdr_len);
    memcpy(buf + hdr_len, datos.datos, (size_t)datos.longitud);
    buf[total_len] = '\0';

    return (CadenaSegura){ .longitud = total_len, .datos = buf };
}

// --- Deserialize a CKPT checkpoint string ---
// Parses "CKPT:<id>:<seq>:<sha256_hex>:<len>:<data>"
// Returns: { task_id via out pointer, datos as CadenaSegura }
// On error returns CadenaSegura with longitud=0 and datos=NULL
CadenaSegura cm_deserializar_checkpoint(CadenaSegura checkpoint_str,
                                         int* out_task_id, int* out_seq) {
    if (checkpoint_str.longitud < 5 || !checkpoint_str.datos
        || memcmp(checkpoint_str.datos, "CKPT:", 5) != 0)
        return (CadenaSegura){ .longitud = 0, .datos = NULL };

    const char* p = checkpoint_str.datos + 5;
    const char* end = checkpoint_str.datos + checkpoint_str.longitud;

    // Parse task_id
    char* endp = NULL;
    long task_id = strtol(p, &endp, 10);
    if (endp == p || *endp != ':' || endp >= end)
        return (CadenaSegura){ .longitud = 0, .datos = NULL };
    p = endp + 1;

    // Parse seq
    long seq = strtol(p, &endp, 10);
    if (endp == p || *endp != ':' || endp >= end)
        return (CadenaSegura){ .longitud = 0, .datos = NULL };
    p = endp + 1;

    // Parse SHA-256 hex checksum (64 chars)
    char cksum_str[65];
    if (end - p < 64) return (CadenaSegura){ .longitud = 0, .datos = NULL };
    memcpy(cksum_str, p, 64);
    cksum_str[64] = '\0';
    p += 64;

    if (*p != ':') return (CadenaSegura){ .longitud = 0, .datos = NULL };
    p++;

    // Parse data length
    long data_len = strtol(p, &endp, 10);
    if (endp == p || *endp != ':' || endp >= end)
        return (CadenaSegura){ .longitud = 0, .datos = NULL };
    p = endp + 1;

    // Verify remaining data matches claimed length
    int remaining = (int)(end - p);
    if (remaining != (int)data_len)
        return (CadenaSegura){ .longitud = 0, .datos = NULL };

    // Verify SHA-256 checksum
    char computed_hex[65];
    _cm_sha256_hex(p, (int)data_len, computed_hex);
    if (memcmp(computed_hex, cksum_str, 64) != 0)
        return (CadenaSegura){ .longitud = 0, .datos = NULL };

    // Copy data into pool-allocated buffer
    char* data_buf = (char*)pool_alloc((size_t)(data_len + 1));
    if (!data_buf) return (CadenaSegura){ .longitud = 0, .datos = NULL };
    memcpy(data_buf, p, (size_t)data_len);
    data_buf[data_len] = '\0';

    if (out_task_id) *out_task_id = (int)task_id;
    if (out_seq) *out_seq = (int)seq;

    return (CadenaSegura){ .longitud = (int)data_len, .datos = data_buf };
}

// --- Verify checkpoint integrity (re-compute checksum) ---
// Returns: 0 = valid, -1 = corrupted
int cm_verificar_integridad(CadenaSegura checkpoint_str) {
    int task_id_dummy, seq_dummy;
    CadenaSegura data = cm_deserializar_checkpoint(checkpoint_str,
                                                    &task_id_dummy, &seq_dummy);
    if (data.longitud <= 0 || !data.datos) return -1;
    pool_free((void*)data.datos);
    return 0;
}

// --- Restore a task from a checkpoint string into the WS queue ---
// Returns: 0 = ok, -1 = error
int cm_restaurar_checkpoint(CadenaSegura checkpoint_str) {
    int task_id;
    int seq;
    CadenaSegura task_data = cm_deserializar_checkpoint(checkpoint_str,
                                                         &task_id, &seq);
    if (task_data.longitud <= 0 || !task_data.datos) return -1;

    int rc = ws_encolar(task_id, task_data);
    pool_free((void*)task_data.datos);
    return rc;
}

// --- Full migration: checkpoint + remove from WS queue ---
// This simulates the migration of a task:
//   1. Create checkpoint from task data
//   2. Remove task from local WS queue (ownership transfer)
//   3. Return checkpoint string for transport to remote node
// Returns: checkpoint string, or empty on failure
CadenaSegura cm_migrar_tarea(CadenaSegura datos_debug) {
    pthread_mutex_lock(&_cm_mutex);

    // Dequeue a task from the WS queue
    CadenaSegura tarea = ws_desencolar();
    if (tarea.longitud <= 0) {
        _cm_fallidas++;
        snprintf(_cm_ultimo_resultado, sizeof(_cm_ultimo_resultado),
                 "MIGRACION_FALLIDA:cola_vacia");
        pthread_mutex_unlock(&_cm_mutex);
        return (CadenaSegura){ .longitud = 0, .datos = NULL };
    }

    // Parse task_id from "id:data" format returned by ws_desencolar
    const char* p = tarea.datos;
    const char* colon = memchr(p, ':', (size_t)tarea.longitud);
    int task_id = 0;
    int data_offset = 0;
    int data_len = 0;
    if (colon) {
        char id_str[32];
        int id_len = (int)(colon - p);
        if (id_len >= 32) id_len = 31;
        memcpy(id_str, p, (size_t)id_len);
        id_str[id_len] = '\0';
        task_id = atoi(id_str);
        data_offset = id_len + 1;
        data_len = tarea.longitud - data_offset;
    } else {
        pool_free((void*)tarea.datos);
        _cm_fallidas++;
        snprintf(_cm_ultimo_resultado, sizeof(_cm_ultimo_resultado),
                 "MIGRACION_FALLIDA:formato_invalido");
        pthread_mutex_unlock(&_cm_mutex);
        return (CadenaSegura){ .longitud = 0, .datos = NULL };
    }

    // Build CadenaSegura for just the payload
    CadenaSegura payload = { .longitud = data_len,
                             .datos = tarea.datos + data_offset };

    // Create checkpoint with SHA-256 integrity
    int seq = _cm_seq++;
    char sha256_hex[65];
    _cm_sha256_hex(payload.datos, payload.longitud, sha256_hex);

    char header[128];
    int hdr_len = snprintf(header, sizeof(header), "CKPT:%d:%d:%s:%d:",
                           task_id, seq, sha256_hex, payload.longitud);

    int ckpt_total = hdr_len + payload.longitud;
    char* ckpt_buf = (char*)pool_alloc((size_t)(ckpt_total + 1));
    if (!ckpt_buf) {
        pool_free((void*)tarea.datos);
        _cm_fallidas++;
        snprintf(_cm_ultimo_resultado, sizeof(_cm_ultimo_resultado),
                 "MIGRACION_FALLIDA:pool_alloc_ckpt");
        pthread_mutex_unlock(&_cm_mutex);
        return (CadenaSegura){ .longitud = 0, .datos = NULL };
    }
    memcpy(ckpt_buf, header, (size_t)hdr_len);
    memcpy(ckpt_buf + hdr_len, payload.datos, (size_t)payload.longitud);
    ckpt_buf[ckpt_total] = '\0';

    _cm_completadas++;
    snprintf(_cm_ultimo_resultado, sizeof(_cm_ultimo_resultado),
             "MIGRACION_OK:%d:seq=%d", task_id, seq);

    pool_free((void*)tarea.datos);
    pthread_mutex_unlock(&_cm_mutex);

    return (CadenaSegura){ .longitud = ckpt_total, .datos = ckpt_buf };
}

// --- Simulate full migration lifecycle between two nodes ---
int cm_migrar_entre_nodos(CadenaSegura ip_destino, int puerto_destino) {
    (void)ip_destino;
    (void)puerto_destino;

    CadenaSegura ckpt = cm_migrar_tarea((CadenaSegura){ .longitud = 0, .datos = NULL });
    if (ckpt.longitud <= 0 || !ckpt.datos) return -1;

    int rc = cm_restaurar_checkpoint(ckpt);
    pool_free((void*)ckpt.datos);

    pthread_mutex_lock(&_cm_mutex);
    if (rc == 0)
        _cm_completadas++;
    else
        _cm_fallidas++;
    pthread_mutex_unlock(&_cm_mutex);

    return rc;
}

// --- Get last migration result string ---
CadenaSegura cm_ultima_migracion(void) {
    pthread_mutex_lock(&_cm_mutex);
    int len = (int)strlen(_cm_ultimo_resultado);
    char* buf = (char*)pool_alloc((size_t)(len + 1));
    if (!buf) {
        pthread_mutex_unlock(&_cm_mutex);
        return (CadenaSegura){ .longitud = 0, .datos = NULL };
    }
    memcpy(buf, _cm_ultimo_resultado, (size_t)(len + 1));
    pthread_mutex_unlock(&_cm_mutex);
    return (CadenaSegura){ .longitud = len, .datos = buf };
}

// --- Get completed migration count ---
int cm_migraciones_completadas(void) {
    pthread_mutex_lock(&_cm_mutex);
    int n = _cm_completadas;
    pthread_mutex_unlock(&_cm_mutex);
    return n;
}

// --- Get failed migration count ---
int cm_migraciones_fallidas(void) {
    pthread_mutex_lock(&_cm_mutex);
    int n = _cm_fallidas;
    pthread_mutex_unlock(&_cm_mutex);
    return n;
}

// ============================================================
// M8.5 — Cluster Auto-Discovery & Membership
// ============================================================
// UDP multicast discovery, heartbeat-based health tracking,
// and dynamic node table management.
// ============================================================

#define MAX_NODOS_CLUSTER 64
#define MAX_ID_LEN 64
#define MAX_IP_LEN 48
#define MAX_PUBKEY_LEN 128
#define DESCUBRIMIENTO_MAGIC "SYNCLUSTER"

// --- Node table entry ---
typedef struct {
    char id[MAX_ID_LEN];
    char ip[MAX_IP_LEN];
    int puerto;
    char pubkey[MAX_PUBKEY_LEN];
    int estado;         // 0=DESCONOCIDO, 1=VIVO, 2=SOSPECHOSO, 3=MUERTO
    int ultimo_latido_s; // timestamp (unix epoch seconds) of last heartbeat
    int primer_visto_s;   // timestamp when first discovered
    int num_heartbeats;   // total heartbeats received
} NodoClusterMembresia;

static NodoClusterMembresia _tabla_membresia[MAX_NODOS_CLUSTER];
static int _num_nodos_membresia = 0;
static int _max_nodos_membresia = MAX_NODOS_CLUSTER;
static int _heartbeat_intervalo_s = 5;   // default: 5 seconds
static int _heartbeat_timeout_s = 15;     // default: 15 seconds without = dead
static int _ultimo_tick_heartbeat_s = 0;
static pthread_mutex_t _membresia_mutex = PTHREAD_MUTEX_INITIALIZER;
static int _descubrimiento_inicializado = 0;

// --- Inicializa la tabla de membresía ---
int cluster_descubrimiento_inicializar(int max_nodos) {
    pthread_mutex_lock(&_membresia_mutex);
    if (max_nodos > MAX_NODOS_CLUSTER || max_nodos <= 0)
        max_nodos = MAX_NODOS_CLUSTER;
    _max_nodos_membresia = max_nodos;
    _num_nodos_membresia = 0;
    memset(_tabla_membresia, 0, sizeof(_tabla_membresia));
    _descubrimiento_inicializado = 1;
    _ultimo_tick_heartbeat_s = 0;
    pthread_mutex_unlock(&_membresia_mutex);
    return 0;
}

// --- Detiene el subsistema de descubrimiento ---
int cluster_descubrimiento_detener(void) {
    pthread_mutex_lock(&_membresia_mutex);
    _num_nodos_membresia = 0;
    memset(_tabla_membresia, 0, sizeof(_tabla_membresia));
    _descubrimiento_inicializado = 0;
    pthread_mutex_unlock(&_membresia_mutex);
    return 0;
}

// --- Encuentra índice de nodo por ID, o -1 si no existe ---
static int _buscar_nodo_por_id(const char* id) {
    for (int i = 0; i < _num_nodos_membresia; i++) {
        if (strcmp(_tabla_membresia[i].id, id) == 0)
            return i;
    }
    return -1;
}

// --- Encuentra índice de nodo por IP+puerto, o -1 ---
static int _buscar_nodo_por_direccion(const char* ip, int puerto) {
    for (int i = 0; i < _num_nodos_membresia; i++) {
        if (strcmp(_tabla_membresia[i].ip, ip) == 0 &&
            _tabla_membresia[i].puerto == puerto)
            return i;
    }
    return -1;
}

// --- Registrar o actualizar un nodo en la tabla de membresía ---
// Retorna índice del nodo (0+), o -1 si tabla llena
int cluster_registrar_nodo(CadenaSegura id, CadenaSegura ip, int puerto, CadenaSegura pubkey) {
    if (!_descubrimiento_inicializado) return -2;
    if (!id.datos || !ip.datos || puerto <= 0) return -3;

    pthread_mutex_lock(&_membresia_mutex);

    // Check if already exists
    int idx = _buscar_nodo_por_id(id.datos);
    if (idx < 0)
        idx = _buscar_nodo_por_direccion(ip.datos, puerto);

    if (idx >= 0) {
        // Update existing entry
        _tabla_membresia[idx].estado = 1; // VIVO
        _tabla_membresia[idx].ultimo_latido_s = (int)time(NULL);
        _tabla_membresia[idx].num_heartbeats++;
        strncpy(_tabla_membresia[idx].ip, ip.datos, MAX_IP_LEN - 1);
        _tabla_membresia[idx].puerto = puerto;
        if (pubkey.datos)
            strncpy(_tabla_membresia[idx].pubkey, pubkey.datos, MAX_PUBKEY_LEN - 1);
        pthread_mutex_unlock(&_membresia_mutex);
        return idx;
    }

    // New node: add if space available
    if (_num_nodos_membresia >= _max_nodos_membresia) {
        pthread_mutex_unlock(&_membresia_mutex);
        return -1;
    }

    int nuevo = _num_nodos_membresia++;
    strncpy(_tabla_membresia[nuevo].id, id.datos, MAX_ID_LEN - 1);
    _tabla_membresia[nuevo].id[MAX_ID_LEN - 1] = '\0';
    strncpy(_tabla_membresia[nuevo].ip, ip.datos, MAX_IP_LEN - 1);
    _tabla_membresia[nuevo].ip[MAX_IP_LEN - 1] = '\0';
    _tabla_membresia[nuevo].puerto = puerto;
    if (pubkey.datos) {
        strncpy(_tabla_membresia[nuevo].pubkey, pubkey.datos, MAX_PUBKEY_LEN - 1);
        _tabla_membresia[nuevo].pubkey[MAX_PUBKEY_LEN - 1] = '\0';
    } else {
        _tabla_membresia[nuevo].pubkey[0] = '\0';
    }
    _tabla_membresia[nuevo].estado = 1; // VIVO
    _tabla_membresia[nuevo].ultimo_latido_s = (int)time(NULL);
    _tabla_membresia[nuevo].primer_visto_s = (int)time(NULL);
    _tabla_membresia[nuevo].num_heartbeats = 1;

    pthread_mutex_unlock(&_membresia_mutex);
    return nuevo;
}

// --- Eliminar un nodo de la tabla por ID ---
// Retorna 0 si se eliminó, -1 si no se encontró
int cluster_eliminar_nodo(CadenaSegura id) {
    if (!_descubrimiento_inicializado || !id.datos) return -1;

    pthread_mutex_lock(&_membresia_mutex);
    int idx = _buscar_nodo_por_id(id.datos);
    if (idx < 0) {
        pthread_mutex_unlock(&_membresia_mutex);
        return -1;
    }
    // Shift remaining nodes
    for (int i = idx; i < _num_nodos_membresia - 1; i++) {
        _tabla_membresia[i] = _tabla_membresia[i + 1];
    }
    _num_nodos_membresia--;
    memset(&_tabla_membresia[_num_nodos_membresia], 0, sizeof(NodoClusterMembresia));
    pthread_mutex_unlock(&_membresia_mutex);
    return 0;
}

// --- Retorna número de nodos activos (estado VIVO) ---
int cluster_nodos_activos(void) {
    if (!_descubrimiento_inicializado) return 0;
    pthread_mutex_lock(&_membresia_mutex);
    int count = 0;
    for (int i = 0; i < _num_nodos_membresia; i++) {
        if (_tabla_membresia[i].estado == 1) count++;
    }
    pthread_mutex_unlock(&_membresia_mutex);
    return count;
}

// --- Retorna número total de nodos en tabla ---
int cluster_total_nodos(void) {
    if (!_descubrimiento_inicializado) return 0;
    pthread_mutex_lock(&_membresia_mutex);
    int n = _num_nodos_membresia;
    pthread_mutex_unlock(&_membresia_mutex);
    return n;
}

// --- Obtener información de un nodo por índice ---
// Retorna "id:ip:puerto:pubkey:estado:heartbeats"
CadenaSegura cluster_obtener_nodo(int idx) {
    if (!_descubrimiento_inicializado || idx < 0)
        return (CadenaSegura){ .longitud = 0, .datos = NULL };

    pthread_mutex_lock(&_membresia_mutex);
    if (idx >= _num_nodos_membresia) {
        pthread_mutex_unlock(&_membresia_mutex);
        return (CadenaSegura){ .longitud = 0, .datos = NULL };
    }

    NodoClusterMembresia* n = &_tabla_membresia[idx];
    char buf[512];
    int len = snprintf(buf, sizeof(buf), "%s:%s:%d:%s:%d:%d",
                       n->id, n->ip, n->puerto, n->pubkey,
                       n->estado, n->num_heartbeats);
    if (len < 0 || len >= (int)sizeof(buf)) {
        pthread_mutex_unlock(&_membresia_mutex);
        return (CadenaSegura){ .longitud = 0, .datos = NULL };
    }
    char* result = (char*)pool_alloc((size_t)(len + 1));
    if (!result) {
        pthread_mutex_unlock(&_membresia_mutex);
        return (CadenaSegura){ .longitud = 0, .datos = NULL };
    }
    memcpy(result, buf, (size_t)(len + 1));
    pthread_mutex_unlock(&_membresia_mutex);
    return (CadenaSegura){ .longitud = len, .datos = result };
}

// --- Inicializar subsistema de heartbeat ---
// intervalo_s: segundos entre ticks de heartbeat
// timeout_s: segundos sin heartbeat para marcar nodo como caído
int cluster_heartbeat_inicializar(int intervalo_s, int timeout_s) {
    if (intervalo_s <= 0) intervalo_s = 5;
    if (timeout_s <= 0) timeout_s = 15;
    if (timeout_s < intervalo_s * 2) timeout_s = intervalo_s * 3; // timeout >= 3*interval

    pthread_mutex_lock(&_membresia_mutex);
    _heartbeat_intervalo_s = intervalo_s;
    _heartbeat_timeout_s = timeout_s;
    _ultimo_tick_heartbeat_s = (int)time(NULL);
    pthread_mutex_unlock(&_membresia_mutex);
    return 0;
}

// --- Tick del heartbeat: verifica latidos y purga nodos caídos ---
// tiempo_actual_s: timestamp UNIX actual en segundos
// Retorna cantidad de nodos purgados
int cluster_tick_heartbeat(int tiempo_actual_s) {
    if (!_descubrimiento_inicializado) return -1;
    if (tiempo_actual_s <= 0) tiempo_actual_s = (int)time(NULL);

    pthread_mutex_lock(&_membresia_mutex);

    int purgados = 0;
    for (int i = 0; i < _num_nodos_membresia; i++) {
        if (_tabla_membresia[i].estado == 1) { // VIVO
            int edad = tiempo_actual_s - _tabla_membresia[i].ultimo_latido_s;
            if (edad >= _heartbeat_timeout_s) {
                _tabla_membresia[i].estado = 3; // MUERTO
                purgados++;
            } else if (edad >= _heartbeat_timeout_s / 2) {
                _tabla_membresia[i].estado = 2; // SOSPECHOSO
            }
        }
    }

    _ultimo_tick_heartbeat_s = tiempo_actual_s;
    pthread_mutex_unlock(&_membresia_mutex);
    return purgados;
}

// --- Registrar un heartbeat recibido de un nodo ---
// Retorna 0 si ok, -1 si nodo no encontrado
int cluster_recibir_heartbeat(CadenaSegura id) {
    if (!_descubrimiento_inicializado || !id.datos) return -1;

    pthread_mutex_lock(&_membresia_mutex);
    int idx = _buscar_nodo_por_id(id.datos);
    if (idx < 0) {
        pthread_mutex_unlock(&_membresia_mutex);
        return -1;
    }
    _tabla_membresia[idx].estado = 1; // VIVO
    _tabla_membresia[idx].ultimo_latido_s = (int)time(NULL);
    _tabla_membresia[idx].num_heartbeats++;
    pthread_mutex_unlock(&_membresia_mutex);
    return 0;
}

// --- Generar paquete de descubrimiento (SYNCLUSTER announcement) ---
// Formato: "SYNCLUSTER:id:ip:puerto:pubkey_hex"
// Retorna el paquete como CadenaSegura (heap-allocated, caller debe liberar)
CadenaSegura cluster_generar_anuncio(CadenaSegura id, CadenaSegura ip, int puerto, CadenaSegura pubkey) {
    if (!id.datos || !ip.datos || puerto <= 0)
        return (CadenaSegura){ .longitud = 0, .datos = NULL };

    char buf[512];
    const char* pk = pubkey.datos ? pubkey.datos : "";
    int len = snprintf(buf, sizeof(buf), "%s:%s:%s:%d:%s",
                       DESCUBRIMIENTO_MAGIC, id.datos, ip.datos, puerto, pk);
    if (len < 0 || len >= (int)sizeof(buf))
        return (CadenaSegura){ .longitud = 0, .datos = NULL };

    char* result = (char*)pool_alloc((size_t)(len + 1));
    if (!result) return (CadenaSegura){ .longitud = 0, .datos = NULL };
    memcpy(result, buf, (size_t)(len + 1));
    return (CadenaSegura){ .longitud = len, .datos = result };
}

// --- Procesar paquete de descubrimiento entrante ---
// Formato esperado: "SYNCLUSTER:id:ip:puerto:pubkey_hex"
// Retorna 0 si se procesó correctamente, -1 si es inválido
int cluster_procesar_anuncio(CadenaSegura paquete) {
    if (!paquete.datos || paquete.longitud <= (int)strlen(DESCUBRIMIENTO_MAGIC))
        return -1;

    // Verify magic prefix
    if (strncmp(paquete.datos, DESCUBRIMIENTO_MAGIC, strlen(DESCUBRIMIENTO_MAGIC)) != 0)
        return -2;

    // Parse: SYNCLUSTER:id:ip:puerto:pubkey
    const char* p = paquete.datos + strlen(DESCUBRIMIENTO_MAGIC) + 1;

    // Extract id (up to next ':')
    const char* id_start = p;
    while (*p && *p != ':') p++;
    if (!*p) return -3;
    int id_len = (int)(p - id_start);
    if (id_len <= 0 || id_len >= MAX_ID_LEN) return -3;

    // Extract ip (up to next ':')
    p++; // skip ':'
    const char* ip_start = p;
    while (*p && *p != ':') p++;
    if (!*p) return -4;
    int ip_len = (int)(p - ip_start);
    if (ip_len <= 0 || ip_len >= MAX_IP_LEN) return -4;

    // Extract puerto (up to next ':')
    p++; // skip ':'
    int puerto = 0;
    while (*p && *p != ':') {
        puerto = puerto * 10 + (*p - '0');
        p++;
    }
    if (puerto <= 0 || puerto > 65535) return -5;

    // Extract pubkey (rest of string)
    const char* pubkey_start = p + 1; // skip ':' or end of string
    int pubkey_len = (int)(paquete.datos + paquete.longitud - pubkey_start);
    if (pubkey_len < 0) pubkey_len = 0;

    // Build temporary strings for registration
    char id_buf[MAX_ID_LEN];
    char ip_buf[MAX_IP_LEN];
    char pk_buf[MAX_PUBKEY_LEN];

    memcpy(id_buf, id_start, (size_t)id_len);
    id_buf[id_len] = '\0';

    memcpy(ip_buf, ip_start, (size_t)ip_len);
    ip_buf[ip_len] = '\0';

    if (pubkey_len > 0 && pubkey_len < MAX_PUBKEY_LEN) {
        memcpy(pk_buf, pubkey_start, (size_t)pubkey_len);
        pk_buf[pubkey_len] = '\0';
    } else {
        pk_buf[0] = '\0';
    }

    CadenaSegura cid = { .longitud = id_len, .datos = id_buf };
    CadenaSegura cip = { .longitud = ip_len, .datos = ip_buf };
    CadenaSegura cpk = { .longitud = pubkey_len, .datos = pk_buf };

    int rc = cluster_registrar_nodo(cid, cip, puerto, cpk);
    return (rc >= 0) ? 0 : -6;
}

// --- Generar representación textual de la tabla de membresía ---
// Formato: "nodo1|nodo2|..." donde cada nodo es "id:ip:puerto:estado"
CadenaSegura cluster_info_membresia_como_texto(void) {
    if (!_descubrimiento_inicializado)
        return (CadenaSegura){ .longitud = 0, .datos = NULL };

    pthread_mutex_lock(&_membresia_mutex);

    // Calculate total size needed
    int total = 0;
    for (int i = 0; i < _num_nodos_membresia; i++) {
        total += (int)strlen(_tabla_membresia[i].id) + 1 +
                 (int)strlen(_tabla_membresia[i].ip) + 1 + 6 + 1 + 1; // :ip:puerto:estado|
    }
    if (total <= 0) {
        pthread_mutex_unlock(&_membresia_mutex);
        return (CadenaSegura){ .longitud = 0, .datos = NULL };
    }

    char* result = (char*)pool_alloc((size_t)(total + 1));
    if (!result) {
        pthread_mutex_unlock(&_membresia_mutex);
        return (CadenaSegura){ .longitud = 0, .datos = NULL };
    }

    int pos = 0;
    for (int i = 0; i < _num_nodos_membresia; i++) {
        NodoClusterMembresia* n = &_tabla_membresia[i];
        int nlen = snprintf(result + pos, (size_t)(total - pos + 1),
                            "%s:%s:%d:%d|",
                            n->id, n->ip, n->puerto, n->estado);
        if (nlen > 0) pos += nlen;
    }
    result[pos] = '\0';

    pthread_mutex_unlock(&_membresia_mutex);
    return (CadenaSegura){ .longitud = pos, .datos = result };
}

// --- Verificar salud de un nodo específico ---
// Retorna: 1=VIVO, 2=SOSPECHOSO, 3=MUERTO, -1=desconocido
int cluster_verificar_salud_nodo(CadenaSegura id) {
    if (!_descubrimiento_inicializado || !id.datos) return -1;

    pthread_mutex_lock(&_membresia_mutex);
    int idx = _buscar_nodo_por_id(id.datos);
    if (idx < 0) {
        pthread_mutex_unlock(&_membresia_mutex);
        return -1;
    }
    int estado = _tabla_membresia[idx].estado;
    pthread_mutex_unlock(&_membresia_mutex);
    return estado;
}

// --- Obtener timestamp del último tick de heartbeat ---
int cluster_ultimo_tick_heartbeat(void) {
    return _ultimo_tick_heartbeat_s;
}

// --- Obtener configuración de heartbeat ---
// Retorna "intervalo:timeout"
CadenaSegura cluster_info_heartbeat(void) {
    char buf[64];
    int len = snprintf(buf, sizeof(buf), "%d:%d", _heartbeat_intervalo_s, _heartbeat_timeout_s);
    char* result = (char*)pool_alloc((size_t)(len + 1));
    if (!result) return (CadenaSegura){ .longitud = 0, .datos = NULL };
    memcpy(result, buf, (size_t)(len + 1));
    return (CadenaSegura){ .longitud = len, .datos = result };
}

// ============================================================
// M8.6 — UDP Multicast Real para Auto-Descubrimiento en Red
// ============================================================
// Conecta cluster_generar_anuncio / cluster_procesar_anuncio
// con sockets UDP reales mediante multicast.
// Grupo por defecto: 239.255.0.1:9700
// ============================================================

#define SYNAPSE_MC_GRUPO "239.255.0.1"
#define SYNAPSE_MC_PUERTO 9700

static int _cluster_mc_sock = -1;
static char _cluster_mc_grupo[32];
static int _cluster_mc_puerto = SYNAPSE_MC_PUERTO;
static volatile int _hilo_descubrimiento_activo = 0;
static pthread_t _hilo_descubrimiento_tid;

// --- Inicializar socket multicast y unirse al grupo ---
// grupo: "239.255.0.1" por defecto
// Retorna fd del socket, o -1 si error
int cluster_multicast_iniciar(const char* grupo, int puerto) {
    if (!grupo) grupo = SYNAPSE_MC_GRUPO;
    if (puerto <= 0) puerto = SYNAPSE_MC_PUERTO;

    strncpy(_cluster_mc_grupo, grupo, sizeof(_cluster_mc_grupo) - 1);
    _cluster_mc_grupo[sizeof(_cluster_mc_grupo) - 1] = '\0';
    _cluster_mc_puerto = puerto;

    if (_cluster_mc_sock >= 0) {
        return _cluster_mc_sock;
    }

    _syn_iniciar_red();

    int fd = (int)socket(AF_INET, SOCK_DGRAM, 0);
    if (fd < 0) return -1;

    int opt = 1;
    setsockopt(fd, SOL_SOCKET, SO_REUSEADDR, (const char*)&opt, sizeof(opt));

#ifdef SO_REUSEPORT
    setsockopt(fd, SOL_SOCKET, SO_REUSEPORT, (const char*)&opt, sizeof(opt));
#endif

    struct sockaddr_in addr;
    memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_port = htons((unsigned short)puerto);
    addr.sin_addr.s_addr = htonl(INADDR_ANY);

    if (bind(fd, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
#ifdef _WIN32
        closesocket(fd);
#else
        close(fd);
#endif
        return -2;
    }

    struct ip_mreq mreq;
    memset(&mreq, 0, sizeof(mreq));
    mreq.imr_multiaddr.s_addr = inet_addr(grupo);
    mreq.imr_interface.s_addr = htonl(INADDR_ANY);

    if (setsockopt(fd, IPPROTO_IP, IP_ADD_MEMBERSHIP,
                   (const char*)&mreq, sizeof(mreq)) < 0) {
#ifdef _WIN32
        closesocket(fd);
#else
        close(fd);
#endif
        return -3;
    }

#ifdef _WIN32
    u_long mode = 1;
    ioctlsocket(fd, FIONBIO, &mode);
#else
    int flags = fcntl(fd, F_GETFL, 0);
    fcntl(fd, F_SETFL, flags | O_NONBLOCK);
#endif

    _cluster_mc_sock = fd;
    return fd;
}

// --- Salir del grupo multicast y cerrar socket ---
int cluster_multicast_detener(void) {
    if (_cluster_mc_sock < 0) return 0;

    struct ip_mreq mreq;
    memset(&mreq, 0, sizeof(mreq));
    mreq.imr_multiaddr.s_addr = inet_addr(_cluster_mc_grupo);
    mreq.imr_interface.s_addr = htonl(INADDR_ANY);
    setsockopt(_cluster_mc_sock, IPPROTO_IP, IP_DROP_MEMBERSHIP,
               (const char*)&mreq, sizeof(mreq));

#ifdef _WIN32
    closesocket(_cluster_mc_sock);
#else
    close(_cluster_mc_sock);
#endif
    _cluster_mc_sock = -1;
    return 0;
}

// --- Enviar anuncio SYNCLUSTER al grupo multicast ---
int cluster_anunciar_por_multicast(CadenaSegura id, CadenaSegura ip_host,
                                    int puerto_host, CadenaSegura pubkey) {
    if (_cluster_mc_sock < 0) return -1;
    if (!id.datos || !ip_host.datos || puerto_host <= 0) return -2;

    CadenaSegura anuncio = cluster_generar_anuncio(id, ip_host, puerto_host, pubkey);
    if (!anuncio.datos || anuncio.longitud <= 0) return -3;

    struct sockaddr_in dest;
    memset(&dest, 0, sizeof(dest));
    dest.sin_family = AF_INET;
    dest.sin_port = htons((unsigned short)_cluster_mc_puerto);
    dest.sin_addr.s_addr = inet_addr(_cluster_mc_grupo);

    int n = (int)sendto(_cluster_mc_sock, anuncio.datos, (size_t)anuncio.longitud, 0,
                        (struct sockaddr*)&dest, sizeof(dest));

    return (n > 0) ? 0 : -4;
}

// --- Recibir y procesar un paquete multicast ---
// timeout_ms: tiempo máximo de espera en ms (0 = no bloqueante)
// Retorna: 0 si se procesó un anuncio, 1 si no hay datos, -1 si error
int cluster_escuchar_multicast(int timeout_ms) {
    if (_cluster_mc_sock < 0) return -1;

    if (timeout_ms > 0) {
#ifdef _WIN32
        u_long mode = 0;
        ioctlsocket(_cluster_mc_sock, FIONBIO, &mode);
        struct timeval tv;
        tv.tv_sec = timeout_ms / 1000;
        tv.tv_usec = (timeout_ms % 1000) * 1000;
        fd_set fds;
        FD_ZERO(&fds);
        FD_SET(_cluster_mc_sock, &fds);
        int sr = select(0, &fds, NULL, NULL, &tv);
        if (sr <= 0) {
            u_long nb = 1;
            ioctlsocket(_cluster_mc_sock, FIONBIO, &nb);
            return (sr == 0) ? 1 : -2;
        }
#else
        struct timeval tv;
        tv.tv_sec = timeout_ms / 1000;
        tv.tv_usec = (timeout_ms % 1000) * 1000;
        fd_set fds;
        FD_ZERO(&fds);
        FD_SET(_cluster_mc_sock, &fds);
        int sr = select(_cluster_mc_sock + 1, &fds, NULL, NULL, &tv);
        if (sr <= 0) return (sr == 0) ? 1 : -2;
#endif
    }

    char buf[65536];
    struct sockaddr_in from;
    socklen_t fromlen = sizeof(from);
    int n = (int)recvfrom(_cluster_mc_sock, buf, sizeof(buf) - 1, 0,
                          (struct sockaddr*)&from, &fromlen);

    if (n <= 0) {
#ifdef _WIN32
        u_long mode = 1;
        ioctlsocket(_cluster_mc_sock, FIONBIO, &mode);
#endif
        return 1;
    }

    buf[n] = '\0';
    CadenaSegura paquete = { .longitud = n, .datos = buf };
    int rc = cluster_procesar_anuncio(paquete);

#ifdef _WIN32
    u_long mode = 1;
    ioctlsocket(_cluster_mc_sock, FIONBIO, &mode);
#endif

    return (rc == 0) ? 0 : -3;
}

// --- Argumentos para el hilo de descubrimiento ---
typedef struct {
    char id[MAX_ID_LEN];
    char ip[MAX_IP_LEN];
    int puerto;
    char pubkey[MAX_PUBKEY_LEN];
    int intervalo_s;
} HiloDescubrimientoArgs;

// --- Función del hilo de descubrimiento en segundo plano ---
static void* _hilo_descubrimiento_func(void* arg) {
    HiloDescubrimientoArgs* args = (HiloDescubrimientoArgs*)arg;

    CadenaSegura id = { .longitud = (int)strlen(args->id), .datos = args->id };
    CadenaSegura ip = { .longitud = (int)strlen(args->ip), .datos = args->ip };
    CadenaSegura pk = { .longitud = (int)strlen(args->pubkey), .datos = args->pubkey };

    while (_hilo_descubrimiento_activo) {
        cluster_anunciar_por_multicast(id, ip, args->puerto, pk);

        for (int i = 0; i < 5; i++) {
            int rc = cluster_escuchar_multicast(200);
            if (rc != 0 && rc != -3) break;
        }

        for (int s = 0; s < args->intervalo_s && _hilo_descubrimiento_activo; s++) {
#ifdef _WIN32
            Sleep(1000);
#else
            sleep(1);
#endif
        }
    }

    free(args);
    return NULL;
}

// --- Iniciar hilo de descubrimiento activo en segundo plano ---
int cluster_iniciar_hilo_descubrimiento(CadenaSegura id, CadenaSegura ip_host,
                                         int puerto_host, CadenaSegura pubkey,
                                         int intervalo_s) {
    if (_hilo_descubrimiento_activo) return -1;
    if (!id.datos || !ip_host.datos || puerto_host <= 0) return -2;
    if (intervalo_s < 1) intervalo_s = 5;

    _hilo_descubrimiento_activo = 1;

    HiloDescubrimientoArgs* args = (HiloDescubrimientoArgs*)malloc(sizeof(HiloDescubrimientoArgs));
    if (!args) { _hilo_descubrimiento_activo = 0; return -3; }

    strncpy(args->id, id.datos, MAX_ID_LEN - 1);
    args->id[MAX_ID_LEN - 1] = '\0';
    strncpy(args->ip, ip_host.datos, MAX_IP_LEN - 1);
    args->ip[MAX_IP_LEN - 1] = '\0';
    args->puerto = puerto_host;
    if (pubkey.datos) {
        strncpy(args->pubkey, pubkey.datos, MAX_PUBKEY_LEN - 1);
        args->pubkey[MAX_PUBKEY_LEN - 1] = '\0';
    } else {
        args->pubkey[0] = '\0';
    }
    args->intervalo_s = intervalo_s;

    pthread_create(&_hilo_descubrimiento_tid, NULL,
                   _hilo_descubrimiento_func, args);
    pthread_detach(_hilo_descubrimiento_tid);

    return 0;
}

// --- Detener hilo de descubrimiento activo ---
int cluster_detener_hilo_descubrimiento(void) {
    _hilo_descubrimiento_activo = 0;
    return 0;
}

// --- Verificar si el hilo de descubrimiento está activo ---
int cluster_hilo_descubrimiento_activo(void) {
    return _hilo_descubrimiento_activo ? 1 : 0;
}

// --- Consultar grupo multicast configurado ---
CadenaSegura cluster_multicast_info(void) {
    char buf[128];
    int len = snprintf(buf, sizeof(buf), "%s:%d:%d",
                       _cluster_mc_grupo, _cluster_mc_puerto, _cluster_mc_sock);
    char* result = (char*)pool_alloc((size_t)(len + 1));
    if (!result) return (CadenaSegura){ .longitud = 0, .datos = NULL };
    memcpy(result, buf, (size_t)(len + 1));
    return (CadenaSegura){ .longitud = len, .datos = result };
}

