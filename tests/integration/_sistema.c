#include "_synapse_shared.h"

CadenaSegura _validar_ruta_segura(CadenaSegura ruta) {
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
        _syn_texto_liberar(ruta);
        return _resultado_;
          /* [Lifetime Scope: exit depth=1] */
    }
    CadenaSegura _ret_38_5 = normalizada;
    return _ret_38_5;
      /* [Lifetime Scope: exit depth=0] */
}

int64_t ejecutar_comando(CadenaSegura cmd) {
    int64_t _ret_48_6 = _syn_ejecutar_comando(cmd);
    _syn_texto_liberar(cmd);
    return _ret_48_6;
      /* [Lifetime Scope: exit depth=0] */
}

int64_t eliminar_archivo(CadenaSegura ruta) {
    CadenaSegura ruta_segura = {0};
    CadenaSegura _syn_tmp_ruta_segura_7 = _validar_ruta_segura(ruta);
    _syn_texto_liberar(ruta_segura);
    ruta_segura = _syn_tmp_ruta_segura_7;
    if ((str_eq(ruta_segura, (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" }) == 1)) {
        int64_t _ret_74_8 = (-1LL);
        _syn_texto_liberar(ruta);
        return _ret_74_8;
          /* [Lifetime Scope: exit depth=1] */
    }
    int64_t _ret_75_9 = _syn_eliminar_archivo(ruta_segura);
    return _ret_75_9;
      /* [Lifetime Scope: exit depth=0] */
}

int64_t escribir_archivo(CadenaSegura ruta, CadenaSegura contenido) {
    CadenaSegura ruta_segura = {0};
    CadenaSegura _syn_tmp_ruta_segura_10 = _validar_ruta_segura(ruta);
    _syn_texto_liberar(ruta_segura);
    ruta_segura = _syn_tmp_ruta_segura_10;
    if ((str_eq(ruta_segura, (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" }) == 1)) {
        int64_t _ret_53_11 = (-1LL);
        _syn_texto_liberar(ruta);
        _syn_texto_liberar(contenido);
        return _ret_53_11;
          /* [Lifetime Scope: exit depth=1] */
    }
    int64_t _ret_54_12 = _syn_escribir_archivo(ruta_segura, contenido);
    return _ret_54_12;
      /* [Lifetime Scope: exit depth=0] */
}

int existe_archivo(CadenaSegura ruta) {
    CadenaSegura ruta_segura = {0};
    CadenaSegura _syn_tmp_ruta_segura_13 = _validar_ruta_segura(ruta);
    _syn_texto_liberar(ruta_segura);
    ruta_segura = _syn_tmp_ruta_segura_13;
    if ((str_eq(ruta_segura, (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" }) == 1)) {
        int _ret_68_14 = 0;
        _syn_texto_liberar(ruta);
        return _ret_68_14;
          /* [Lifetime Scope: exit depth=1] */
    }
    int _ret_69_15 = (_syn_existe_archivo(ruta_segura) == 1LL);
    return _ret_69_15;
      /* [Lifetime Scope: exit depth=0] */
}

CadenaSegura leer_archivo(CadenaSegura ruta) {
    CadenaSegura ruta_segura = {0};
    CadenaSegura _syn_tmp_ruta_segura_16 = _validar_ruta_segura(ruta);
    _syn_texto_liberar(ruta_segura);
    ruta_segura = _syn_tmp_ruta_segura_16;
    if ((str_eq(ruta_segura, (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" }) == 1)) {
        CadenaSegura _ret_59_17 = (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
        _syn_texto_liberar(ruta);
        return _ret_59_17;
          /* [Lifetime Scope: exit depth=1] */
    }
    CadenaSegura _ret_60_18 = _syn_leer_archivo(ruta_segura);
    return _ret_60_18;
      /* [Lifetime Scope: exit depth=0] */
}

CadenaSegura obtener_env(CadenaSegura nombre) {
    CadenaSegura _ret_63_19 = _syn_obtener_env(nombre);
    _syn_texto_liberar(nombre);
    return _ret_63_19;
      /* [Lifetime Scope: exit depth=0] */
}
