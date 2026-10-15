#include "_synapse_shared.h"

Canal abrir(CadenaSegura ruta, CadenaSegura modo) {
    CadenaSegura ruta_segura = {0};
    CadenaSegura _syn_tmp_ruta_segura_1 = _validar_ruta_segura(ruta);
    _syn_texto_liberar(ruta_segura);
    ruta_segura = _syn_tmp_ruta_segura_1;
    if ((str_eq(ruta_segura, (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" }) == 1)) {
        Canal _resultado_ = {0};
        _syn_texto_liberar(ruta);
        _syn_texto_liberar(modo);
        return _resultado_;
          /* [Lifetime Scope: exit depth=1] */
    }
    Canal _ret_25_2 = _syn_abrir(ruta_segura, modo);
    return _ret_25_2;
      /* [Lifetime Scope: exit depth=0] */
}

void escribir(CadenaSegura texto) {
    _syn_escribir(texto);
      /* [Lifetime Scope: exit depth=0] */
    _syn_texto_liberar(texto);
}

void escribir_linea(CadenaSegura texto) {
    _syn_escribir_linea(texto);
      /* [Lifetime Scope: exit depth=0] */
    _syn_texto_liberar(texto);
}

CadenaSegura leer(Canal c) {
    CadenaSegura _resultado_ = _syn_leer(c);
    return _resultado_;
      /* [Lifetime Scope: exit depth=0] */
}

CadenaSegura leer_bytes(int64_t cantidad) {
    CadenaSegura _resultado_ = _syn_leer_bytes(cantidad);
    return _resultado_;
      /* [Lifetime Scope: exit depth=0] */
}

CadenaSegura leer_linea(void) {
    CadenaSegura _resultado_ = _syn_leer_linea();
    return _resultado_;
      /* [Lifetime Scope: exit depth=0] */
}

int64_t stdin_eof(void) {
    int64_t _resultado_ = _syn_stdin_eof();
    return _resultado_;
      /* [Lifetime Scope: exit depth=0] */
}
