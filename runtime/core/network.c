// cumple Manual 6 2: network runtime
// runtime/core/network.c — std.net: Socket helpers (TCP client)
// D-9(d): extracted from synapse_rt.c (modularization, patrón tensor.c R39)
// Texto byte-idéntico al original (CRLF preservado).
//
// Manual 5 §6: std.net (networking primitives)
// Consumido por cluster.c (M8.1 transporte UDP), principal.syn (Axon HTTP),
// debug.c (M9.4 debug distribuido).

#include "synapse_rt_types.h"
#include "runtime/core/network.h"

#ifdef _WIN32
  #include <winsock2.h>
  #include <ws2tcpip.h>
  #include <windows.h>
#else
  #include <sys/socket.h>
  #include <netinet/in.h>
  #include <arpa/inet.h>
  #include <unistd.h>
#endif

#include <string.h>

// ============================================================
// std.net — Socket helpers (TCP client)
// ============================================================

int _syn_iniciar_red(void) {
#ifdef _WIN32
    WSADATA wsa;
    return WSAStartup(MAKEWORD(2,2), &wsa);
#else
    return 0;
#endif
}

int _syn_cerrar_red(void) {
#ifdef _WIN32
    return WSACleanup();
#else
    return 0;
#endif
}

int _syn_socket(void) {
    return (int)socket(AF_INET, SOCK_STREAM, 0);
}

int _syn_conectar(int fd, const char* ip, int puerto) {
    struct sockaddr_in addr;
    memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_port = htons((unsigned short)puerto);
    addr.sin_addr.s_addr = inet_addr(ip);
    if (addr.sin_addr.s_addr == INADDR_NONE)
        return -1;
    return connect(fd, (struct sockaddr*)&addr, sizeof(addr));
}

int _syn_enviar(int fd, const char* datos, int lon) {
    return (int)send(fd, datos, (size_t)lon, 0);
}

int _syn_recibir(int fd, char* buf, int lon) {
    return (int)recv(fd, buf, (size_t)lon, 0);
}

int _syn_cerrar_socket(int fd) {
#ifdef _WIN32
    return closesocket(fd);
#else
    return close(fd);
#endif
}
