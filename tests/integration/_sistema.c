#include "_synapse_shared.h"

CadenaSegura _validar_ruta_segura(CadenaSegura ruta) {
    CadenaSegura normalizada = {0};
    CadenaSegura cwd = {0};
    _syn_texto_liberar(normalizada);
    normalizada = _syn_normalizar_ruta(ruta);
    _syn_texto_liberar(cwd);
    cwd = _syn_obtener_cwd();
    if ((!_syn_ruta_en_directorio(normalizada, cwd))) {
        _syn_texto_liberar(ruta);
        _syn_texto_liberar(normalizada);
        _syn_texto_liberar(cwd);
        return (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
          /* [Lifetime Scope: exit depth=1] */
    }
    return normalizada;
      /* [Lifetime Scope: exit depth=0] */
}

int64_t ejecutar_comando(CadenaSegura cmd) {
    _syn_texto_liberar(cmd);
    return _syn_ejecutar_comando(cmd);
      /* [Lifetime Scope: exit depth=0] */
}

int64_t eliminar_archivo(CadenaSegura ruta) {
    CadenaSegura ruta_segura = {0};
    _syn_texto_liberar(ruta_segura);
    ruta_segura = _validar_ruta_segura(ruta);
    if ((str_eq(ruta_segura, (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" }) == 1)) {
        _syn_texto_liberar(ruta_segura);
        _syn_texto_liberar(ruta);
        return (-1LL);
          /* [Lifetime Scope: exit depth=1] */
    }
    return _syn_eliminar_archivo(ruta_segura);
      /* [Lifetime Scope: exit depth=0] */
}

int64_t escribir_archivo(CadenaSegura ruta, CadenaSegura contenido) {
    CadenaSegura ruta_segura = {0};
    _syn_texto_liberar(ruta_segura);
    ruta_segura = _validar_ruta_segura(ruta);
    if ((str_eq(ruta_segura, (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" }) == 1)) {
        _syn_texto_liberar(ruta_segura);
        _syn_texto_liberar(ruta);
        _syn_texto_liberar(contenido);
        return (-1LL);
          /* [Lifetime Scope: exit depth=1] */
    }
    return _syn_escribir_archivo(ruta_segura, contenido);
      /* [Lifetime Scope: exit depth=0] */
}

int existe_archivo(CadenaSegura ruta) {
    CadenaSegura ruta_segura = {0};
    _syn_texto_liberar(ruta_segura);
    ruta_segura = _validar_ruta_segura(ruta);
    if ((str_eq(ruta_segura, (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" }) == 1)) {
        _syn_texto_liberar(ruta_segura);
        _syn_texto_liberar(ruta);
        return 0;
          /* [Lifetime Scope: exit depth=1] */
    }
    return (_syn_existe_archivo(ruta_segura) == 1LL);
      /* [Lifetime Scope: exit depth=0] */
}

CadenaSegura leer_archivo(CadenaSegura ruta) {
    CadenaSegura ruta_segura = {0};
    _syn_texto_liberar(ruta_segura);
    ruta_segura = _validar_ruta_segura(ruta);
    if ((str_eq(ruta_segura, (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" }) == 1)) {
        _syn_texto_liberar(ruta_segura);
        _syn_texto_liberar(ruta);
        return (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
          /* [Lifetime Scope: exit depth=1] */
    }
    return _syn_leer_archivo(ruta_segura);
      /* [Lifetime Scope: exit depth=0] */
}

CadenaSegura obtener_env(CadenaSegura nombre) {
    _syn_texto_liberar(nombre);
    return _syn_obtener_env(nombre);
      /* [Lifetime Scope: exit depth=0] */
}
