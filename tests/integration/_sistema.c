#include "_synapse_shared.h"

extern CadenaSegura _syn_sha256_texto(CadenaSegura datos);
extern int _syn_ed25519_verificar(CadenaSegura mensaje, CadenaSegura firma, CadenaSegura clave_publica);
extern CadenaSegura _syn_normalizar_ruta(CadenaSegura ruta);
extern CadenaSegura _syn_obtener_cwd(void);
extern int _syn_ruta_en_directorio(CadenaSegura ruta, CadenaSegura dir);
CadenaSegura _validar_ruta_segura(CadenaSegura ruta) {
    CadenaSegura normalizada = _syn_normalizar_ruta(ruta);
    CadenaSegura cwd = _syn_obtener_cwd();
    if ((!_syn_ruta_en_directorio(normalizada, cwd))) {
        CadenaSegura _ret_22 = (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
        _syn_texto_liberar(cwd);
        _syn_texto_liberar(normalizada);
        return _ret_22;
    }
    CadenaSegura _ret_23 = normalizada;
    return _ret_23;
}

extern int _syn_ejecutar_comando(CadenaSegura cmd);
extern int _syn_escribir_archivo(CadenaSegura ruta, CadenaSegura contenido);
extern CadenaSegura _syn_leer_archivo(CadenaSegura ruta);
extern CadenaSegura _syn_obtener_env(CadenaSegura nombre);
extern int _syn_existe_archivo(CadenaSegura ruta);
extern int _syn_eliminar_archivo(CadenaSegura ruta);
int ejecutar_comando(CadenaSegura cmd) {
    int _ret_33 = _syn_ejecutar_comando(cmd);
    return _ret_33;
}

int escribir_archivo(CadenaSegura ruta, CadenaSegura contenido) {
    CadenaSegura ruta_segura = _validar_ruta_segura(ruta);
    if ((str_eq(ruta_segura, (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" }) == 1)) {
        int _ret_38 = (-1);
        _syn_texto_liberar(ruta_segura);
        return _ret_38;
    }
    int _ret_39 = _syn_escribir_archivo(ruta_segura, contenido);
    return _ret_39;
}

CadenaSegura leer_archivo(CadenaSegura ruta) {
    CadenaSegura ruta_segura = _validar_ruta_segura(ruta);
    if ((str_eq(ruta_segura, (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" }) == 1)) {
        CadenaSegura _ret_44 = (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
        _syn_texto_liberar(ruta_segura);
        return _ret_44;
    }
    CadenaSegura _ret_45 = _syn_leer_archivo(ruta_segura);
    return _ret_45;
}

CadenaSegura obtener_env(CadenaSegura nombre) {
    CadenaSegura _ret_48 = _syn_obtener_env(nombre);
    return _ret_48;
}

int existe_archivo(CadenaSegura ruta) {
    CadenaSegura ruta_segura = _validar_ruta_segura(ruta);
    if ((str_eq(ruta_segura, (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" }) == 1)) {
        int _ret_53 = 0;
        _syn_texto_liberar(ruta_segura);
        return _ret_53;
    }
    int _ret_54 = (_syn_existe_archivo(ruta_segura) == 1);
    return _ret_54;
}

int eliminar_archivo(CadenaSegura ruta) {
    CadenaSegura ruta_segura = _validar_ruta_segura(ruta);
    if ((str_eq(ruta_segura, (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" }) == 1)) {
        int _ret_59 = (-1);
        _syn_texto_liberar(ruta_segura);
        return _ret_59;
    }
    int _ret_60 = _syn_eliminar_archivo(ruta_segura);
    return _ret_60;
}

extern Canal _syn_abrir(CadenaSegura ruta, CadenaSegura modo);
extern CadenaSegura _syn_leer(Canal c);
extern void _syn_escribir(CadenaSegura texto);
extern void _syn_escribir_linea(CadenaSegura texto);
extern CadenaSegura _syn_leer_linea(void);
extern CadenaSegura cluster_generar_par_claves(void);
extern CadenaSegura cluster_firmar_mensaje(CadenaSegura mensaje, CadenaSegura clave_privada_hex);
extern int cluster_verificar_firma(CadenaSegura mensaje, CadenaSegura firma_hex, CadenaSegura clave_publica_hex);
extern int cluster_iniciar_nodo(int puerto);
extern int cluster_detener_nodo(void);
extern int cluster_enviar_hello(CadenaSegura ip, int puerto, CadenaSegura id_origen, CadenaSegura pubkey_hex);
extern int cluster_canal_remoto_enviar(CadenaSegura ip, int puerto, CadenaSegura datos, int lon, int chan_id);