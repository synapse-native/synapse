#include "detect_hardware.h"
#include <stdio.h>
#include <string.h>

int main(int argc, char** argv) {
    (void)argc;
    HwProfile perfil;
    if (synapse_detectar_hardware(&perfil) != 0) {
        fprintf(stderr, "ERROR: No se pudo detectar hardware\n");
        return 1;
    }
    if (argc > 1 && strcmp(argv[1], "--json") == 0) {
        char buf[512];
        if (synapse_hw_to_json(&perfil, buf, sizeof(buf)) == 0)
            printf("%s\n", buf);
        return 0;
    }
    synapse_hw_imprimir_perfil(&perfil);
    return 0;
}
