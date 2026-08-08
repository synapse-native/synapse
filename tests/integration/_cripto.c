#include "_synapse_shared.h"

int64_t ed25519_verificar(CadenaSegura mensaje, CadenaSegura firma, CadenaSegura clave_publica) {
    return _syn_ed25519_verificar(mensaje, firma, clave_publica);
      /* [Lifetime Scope: exit depth=0] */
}

CadenaSegura sha256_texto(CadenaSegura datos) {
    return _syn_sha256_texto(datos);
      /* [Lifetime Scope: exit depth=0] */
}
