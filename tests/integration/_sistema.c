#include "_synapse_shared.h"

CadenaSegura _validar_ruta_segura(CadenaSegura ruta) {
    assert_contrato(((ruta).longitud > 0LL), "Fallo en contrato: requiere");
    CadenaSegura cwd = {0};
    CadenaSegura absoluta = {0};
    CadenaSegura normalizada = {0};
    CadenaSegura _syn_tmp_cwd_1 = _syn_normalizar_ruta(_syn_obtener_cwd());
    _syn_texto_liberar(cwd);
    cwd = _syn_tmp_cwd_1;
    CadenaSegura _syn_tmp_absoluta_2 = ruta;
    _syn_texto_liberar(absoluta);
    absoluta = _syn_tmp_absoluta_2;
    if ((((str_eq(_syn_texto_subcadena(ruta, 1LL, (1LL)+(2LL)), (CadenaSegura){ .longitud = (int)strlen(":"), .datos = ":" }) == 0) && (str_eq(_syn_texto_subcadena(ruta, 0LL, (0LL)+(1LL)), (CadenaSegura){ .longitud = (int)strlen("/"), .datos = "/" }) == 0)) && (str_eq(_syn_texto_subcadena(ruta, 0LL, (0LL)+(2LL)), (CadenaSegura){ .longitud = (int)strlen("\\\\"), .datos = "\\\\" }) == 0))) {
        CadenaSegura _syn_tmp_absoluta_3 = concat(concat(cwd, (CadenaSegura){ .longitud = (int)strlen("/"), .datos = "/" }), ruta);
        _syn_texto_liberar(absoluta);
        absoluta = _syn_tmp_absoluta_3;
          /* [Lifetime Scope: exit depth=1] */
    }
    CadenaSegura _syn_tmp_normalizada_4 = _syn_normalizar_ruta(absoluta);
    _syn_texto_liberar(normalizada);
    normalizada = _syn_tmp_normalizada_4;
    if ((!_syn_ruta_en_directorio(normalizada, cwd))) {
        CadenaSegura _resultado_ = (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
        assert_contrato((((str_eq(_resultado_, (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" }) == 1) || (str_eq(_syn_texto_subcadena(_resultado_, 1LL, (1LL)+(2LL)), (CadenaSegura){ .longitud = (int)strlen(":"), .datos = ":" }) == 1)) || (str_eq(_syn_texto_subcadena(_resultado_, 0LL, (0LL)+(1LL)), (CadenaSegura){ .longitud = (int)strlen("/"), .datos = "/" }) == 1)), "Fallo en contrato: garantiza");
        _syn_texto_liberar(ruta);
        return _resultado_;
          /* [Lifetime Scope: exit depth=1] */
    }
    CadenaSegura _resultado_ = normalizada;
    assert_contrato((((str_eq(_resultado_, (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" }) == 1) || (str_eq(_syn_texto_subcadena(_resultado_, 1LL, (1LL)+(2LL)), (CadenaSegura){ .longitud = (int)strlen(":"), .datos = ":" }) == 1)) || (str_eq(_syn_texto_subcadena(_resultado_, 0LL, (0LL)+(1LL)), (CadenaSegura){ .longitud = (int)strlen("/"), .datos = "/" }) == 1)), "Fallo en contrato: garantiza");
    return _resultado_;
      /* [Lifetime Scope: exit depth=0] */
}

int64_t ejecutar_comando(CadenaSegura cmd) {
    int64_t _ret_49_5 = _syn_ejecutar_comando(cmd);
    _syn_texto_liberar(cmd);
    return _ret_49_5;
      /* [Lifetime Scope: exit depth=0] */
}

int64_t eliminar_archivo(CadenaSegura ruta) {
    CadenaSegura ruta_segura = {0};
    CadenaSegura _syn_tmp_ruta_segura_6 = _validar_ruta_segura(ruta);
    _syn_texto_liberar(ruta_segura);
    ruta_segura = _syn_tmp_ruta_segura_6;
    if ((str_eq(ruta_segura, (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" }) == 1)) {
        int64_t _ret_75_7 = (-1LL);
        _syn_texto_liberar(ruta);
        return _ret_75_7;
          /* [Lifetime Scope: exit depth=1] */
    }
    int64_t _ret_76_8 = _syn_eliminar_archivo(ruta_segura);
    return _ret_76_8;
      /* [Lifetime Scope: exit depth=0] */
}

int64_t escribir_archivo(CadenaSegura ruta, CadenaSegura contenido) {
    CadenaSegura ruta_segura = {0};
    CadenaSegura _syn_tmp_ruta_segura_9 = _validar_ruta_segura(ruta);
    _syn_texto_liberar(ruta_segura);
    ruta_segura = _syn_tmp_ruta_segura_9;
    if ((str_eq(ruta_segura, (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" }) == 1)) {
        int64_t _ret_54_10 = (-1LL);
        _syn_texto_liberar(ruta);
        _syn_texto_liberar(contenido);
        return _ret_54_10;
          /* [Lifetime Scope: exit depth=1] */
    }
    int64_t _ret_55_11 = _syn_escribir_archivo(ruta_segura, contenido);
    return _ret_55_11;
      /* [Lifetime Scope: exit depth=0] */
}

int existe_archivo(CadenaSegura ruta) {
    CadenaSegura ruta_segura = {0};
    CadenaSegura _syn_tmp_ruta_segura_12 = _validar_ruta_segura(ruta);
    _syn_texto_liberar(ruta_segura);
    ruta_segura = _syn_tmp_ruta_segura_12;
    if ((str_eq(ruta_segura, (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" }) == 1)) {
        int _ret_69_13 = 0;
        _syn_texto_liberar(ruta);
        return _ret_69_13;
          /* [Lifetime Scope: exit depth=1] */
    }
    int _ret_70_14 = (_syn_existe_archivo(ruta_segura) == 1LL);
    return _ret_70_14;
      /* [Lifetime Scope: exit depth=0] */
}

CadenaSegura leer_archivo(CadenaSegura ruta) {
    CadenaSegura ruta_segura = {0};
    CadenaSegura _syn_tmp_ruta_segura_15 = _validar_ruta_segura(ruta);
    _syn_texto_liberar(ruta_segura);
    ruta_segura = _syn_tmp_ruta_segura_15;
    if ((str_eq(ruta_segura, (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" }) == 1)) {
        CadenaSegura _ret_60_16 = (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
        _syn_texto_liberar(ruta);
        return _ret_60_16;
          /* [Lifetime Scope: exit depth=1] */
    }
    CadenaSegura _ret_61_17 = _syn_leer_archivo(ruta_segura);
    return _ret_61_17;
      /* [Lifetime Scope: exit depth=0] */
}

CadenaSegura obtener_env(CadenaSegura nombre) {
    CadenaSegura _ret_64_18 = _syn_obtener_env(nombre);
    _syn_texto_liberar(nombre);
    return _ret_64_18;
      /* [Lifetime Scope: exit depth=0] */
}
