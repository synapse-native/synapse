#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <winsock2.h>
#include <windows.h>

typedef struct { int campo0; } DatosRed;

static inline struct DatosRed DatosRed_nuevo() {
    struct DatosRed _r = {0};
    return _r;
}

int iniciar_red(void) {
    struct DatosRed datos = DatosRed_nuevo();
    return WSAStartup(514, (&datos));
}

void cerrar_red(void) {
    WSACleanup();
}

int crear_socket(void) {
    return socket(2, 1, 0);
}

void pool_init(unsigned int a, unsigned int b) {}
void synapse_esperar_hilos() {}

int main(int argc, char** argv) {
    printf("step 1\n");
    int r = iniciar_red();
    printf("iniciar_red: %d\n", r);
    printf("step 2\n");
    int s = crear_socket();
    printf("socket: %d\n", s);
    printf("step 3\n");
    cerrar_red();
    printf("red cerrada\n");
    return 0;
}
