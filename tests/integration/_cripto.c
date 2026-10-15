#include "_synapse_shared.h"

int64_t ed25519_verificar(CadenaSegura mensaje, CadenaSegura firma, CadenaSegura clave_publica) {
    int64_t _ret_23_1 = _syn_ed25519_verificar(mensaje, firma, clave_publica);
    _syn_texto_liberar(mensaje);
    _syn_texto_liberar(firma);
    _syn_texto_liberar(clave_publica);
    return _ret_23_1;
      /* [Lifetime Scope: exit depth=0] */
}

CadenaSegura sha256_texto(CadenaSegura datos) {
    CadenaSegura _ret_20_2 = _syn_sha256_texto(datos);
    _syn_texto_liberar(datos);
    return _ret_20_2;
      /* [Lifetime Scope: exit depth=0] */
}
