// cumple Manual 6 §2: network runtime
// runtime/core/network.h — std.net: Socket helpers (TCP client)
// D-9(d): extracted from synapse_rt.c (modularization)
//
// Manual 5 §6: std.net (networking primitives)
//
// Platform-specific: Windows (Winsock2) / POSIX (BSD sockets)

#ifndef SYNAPSE_NETWORK_H
#define SYNAPSE_NETWORK_H

#ifdef _WIN32
  #include <winsock2.h>
  #include <ws2tcpip.h>
#else
  #include <sys/socket.h>
  #include <netinet/in.h>
  #include <arpa/inet.h>
  #include <unistd.h>
#endif

// Inicializar/red limpiar (Windows: WSAStartup/WSACleanup; POSIX: stub)
int _syn_iniciar_red(void);
int _syn_cerrar_red(void);

// Crear/conectar/cerrar socket TCP
int _syn_socket(void);
int _syn_conectar(int fd, const char* ip, int puerto);
int _syn_cerrar_socket(int fd);

// Enviar/recibir datos
int _syn_enviar(int fd, const char* datos, int lon);
int _syn_recibir(int fd, char* buf, int lon);

#endif // SYNAPSE_NETWORK_H
