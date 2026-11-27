#include "_synapse_shared.h"

Canal abrir(CadenaSegura ruta, CadenaSegura modo) {
    assert_contrato(((modo).longitud > 0LL), "Fallo en contrato: requiere");
    CadenaSegura ruta_segura = {0};
    CadenaSegura _syn_tmp_ruta_segura_1 = _validar_ruta_segura(ruta);
    _syn_texto_liberar(ruta_segura);
    ruta_segura = _syn_tmp_ruta_segura_1;
    if ((str_eq(ruta_segura, (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" }) == 1)) {
        Canal _resultado_ = {0};
        assert_contrato(((_resultado_.es_valido == 0LL) || (_resultado_.es_valido == 1LL)), "Fallo en contrato: garantiza");
        _syn_texto_liberar(ruta);
        _syn_texto_liberar(modo);
        return _resultado_;
          /* [Lifetime Scope: exit depth=1] */
    }
    Canal _resultado_ = _syn_abrir(ruta_segura, modo);
    assert_contrato(((_resultado_.es_valido == 0LL) || (_resultado_.es_valido == 1LL)), "Fallo en contrato: garantiza");
    return _resultado_;
      /* [Lifetime Scope: exit depth=0] */
}

void escribir(CadenaSegura texto) {
    assert_contrato(((texto).longitud >= 0LL), "Fallo en contrato: requiere");
    _syn_escribir(texto);
      /* [Lifetime Scope: exit depth=0] */
    _syn_texto_liberar(texto);
}

void escribir_linea(CadenaSegura texto) {
    assert_contrato(((texto).longitud >= 0LL), "Fallo en contrato: requiere");
    _syn_escribir_linea(texto);
      /* [Lifetime Scope: exit depth=0] */
    _syn_texto_liberar(texto);
}

CadenaSegura leer(Canal c) {
    assert_contrato((c.es_valido == 1LL), "Fallo en contrato: requiere");
    CadenaSegura _resultado_ = _syn_leer(c);
    assert_contrato(((_resultado_).longitud >= 0LL), "Fallo en contrato: garantiza");
    return _resultado_;
      /* [Lifetime Scope: exit depth=0] */
}

CadenaSegura leer_bytes(int64_t cantidad) {
    assert_contrato((cantidad >= 0LL), "Fallo en contrato: requiere");
    CadenaSegura _resultado_ = _syn_leer_bytes(cantidad);
    assert_contrato(((_resultado_).longitud >= 0LL), "Fallo en contrato: garantiza");
    return _resultado_;
      /* [Lifetime Scope: exit depth=0] */
}

CadenaSegura leer_linea(void) {
    CadenaSegura _resultado_ = _syn_leer_linea();
    assert_contrato(((_resultado_).longitud >= 0LL), "Fallo en contrato: garantiza");
    return _resultado_;
      /* [Lifetime Scope: exit depth=0] */
}

int64_t stdin_eof(void) {
    int64_t _resultado_ = _syn_stdin_eof();
    assert_contrato(((_resultado_ == 0LL) || (_resultado_ == 1LL)), "Fallo en contrato: garantiza");
    return _resultado_;
      /* [Lifetime Scope: exit depth=0] */
}
