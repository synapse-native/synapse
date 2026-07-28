#include "_synapse_shared.h"

char _gen_tmp_buf[4096];

char _G_emit_buf[1048576];
int _G_emit_pos;
FILE* _G_fp;

int _g_argc;
char** _g_argv;
int _argc() { return _g_argc; }

CadenaSegura _argv(int i) {
    if (i < 0 || i >= _g_argc) return (CadenaSegura){0, ""};
    return (CadenaSegura){ .longitud = (int)strlen(_g_argv[i]), .datos = _g_argv[i] };
}

void salir(int codigo) { exit(codigo); }

CadenaSegura concat(CadenaSegura a, CadenaSegura b) {
    int _tl = a.longitud + b.longitud;
    char* _buf = (char*)malloc(_tl + 1);
    if (!_buf) { fprintf(stderr,"Error: malloc fallo en concat()\\n"); exit(1); }
    memcpy(_buf, a.datos, a.longitud);
    memcpy(_buf + a.longitud, b.datos, b.longitud);
    _buf[_tl] = 0;
    return (CadenaSegura){_tl, _buf};
}

extern CadenaSegura _syn_sha256_texto(CadenaSegura datos);
extern int _syn_ed25519_verificar(CadenaSegura mensaje, CadenaSegura firma, CadenaSegura clave_publica);
extern CadenaSegura _syn_normalizar_ruta(CadenaSegura ruta);
extern CadenaSegura _syn_obtener_cwd(void);
extern int _syn_ruta_en_directorio(CadenaSegura ruta, CadenaSegura dir);
extern int _syn_ejecutar_comando(CadenaSegura cmd);
extern int _syn_escribir_archivo(CadenaSegura ruta, CadenaSegura contenido);
extern CadenaSegura _syn_leer_archivo(CadenaSegura ruta);
extern CadenaSegura _syn_obtener_env(CadenaSegura nombre);
extern int _syn_existe_archivo(CadenaSegura ruta);
extern int _syn_eliminar_archivo(CadenaSegura ruta);
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
int prueba_generar_par(void) {
    int fallos;
    fallos = 0;
    escribir_linea((CadenaSegura){ .longitud = (int)strlen(""), .datos = "" });
    escribir_linea((CadenaSegura){ .longitud = (int)strlen("=== Prueba 1: Generar par Ed25519 ==="), .datos = "=== Prueba 1: Generar par Ed25519 ===" });
    CadenaSegura par = cluster_generar_par_claves();
    if ((str_eq(par, (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" }) == 1)) {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[FALLO] generar_par() retorna vacio"), .datos = "[FALLO] generar_par() retorna vacio" });
        fallos = (fallos + 1);
    }
    else {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[OK] generar_par() no retorna vacio"), .datos = "[OK] generar_par() no retorna vacio" });
    }
    int _ret_49 = fallos;
    _syn_texto_liberar(par);
    return _ret_49;
}

int prueba_firmar_verificar(void) {
    int fallos;
    int resultado;
    fallos = 0;
    escribir_linea((CadenaSegura){ .longitud = (int)strlen(""), .datos = "" });
    escribir_linea((CadenaSegura){ .longitud = (int)strlen("=== Prueba 2: Firma y verificacion Ed25519 ==="), .datos = "=== Prueba 2: Firma y verificacion Ed25519 ===" });
    CadenaSegura par = cluster_generar_par_claves();
    CadenaSegura firma = cluster_firmar_mensaje((CadenaSegura){ .longitud = (int)strlen("synapse-handshake:test-message"), .datos = "synapse-handshake:test-message" }, par);
    if ((str_eq(firma, (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" }) == 1)) {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[FALLO] firmar_mensaje() retorna firma vacia"), .datos = "[FALLO] firmar_mensaje() retorna firma vacia" });
        fallos = (fallos + 1);
    }
    else {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[OK] firmar_mensaje() retorna firma no vacia"), .datos = "[OK] firmar_mensaje() retorna firma no vacia" });
    }
    resultado = cluster_verificar_firma((CadenaSegura){ .longitud = (int)strlen("synapse-handshake:test-message"), .datos = "synapse-handshake:test-message" }, firma, par);
    if ((resultado == 0)) {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[OK] verificar_firma() retorna 0 para firma valida"), .datos = "[OK] verificar_firma() retorna 0 para firma valida" });
    }
    else {
        escribir_linea(concat((CadenaSegura){ .longitud = (int)strlen("[FALLO] verificar_firma() debio retornar 0, obtuvo "), .datos = "[FALLO] verificar_firma() debio retornar 0, obtuvo " }, entero_a_texto(resultado)));
        fallos = (fallos + 1);
    }
    int _ret_77 = fallos;
    _syn_texto_liberar(firma);
    _syn_texto_liberar(par);
    return _ret_77;
}

int prueba_firma_corrupta(void) {
    int fallos;
    int resultado;
    fallos = 0;
    escribir_linea((CadenaSegura){ .longitud = (int)strlen(""), .datos = "" });
    escribir_linea((CadenaSegura){ .longitud = (int)strlen("=== Prueba 3: Rechazo de firma corrupta (Zero-Trust) ==="), .datos = "=== Prueba 3: Rechazo de firma corrupta (Zero-Trust) ===" });
    CadenaSegura par = cluster_generar_par_claves();
    CadenaSegura firma = cluster_firmar_mensaje((CadenaSegura){ .longitud = (int)strlen("synapse-handshake:test"), .datos = "synapse-handshake:test" }, par);
    resultado = cluster_verificar_firma((CadenaSegura){ .longitud = (int)strlen("synapse-handshake:test-DIFFERENT"), .datos = "synapse-handshake:test-DIFFERENT" }, firma, par);
    if ((resultado != 0)) {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[OK] verificar_firma() rechaza mensaje incorrecto"), .datos = "[OK] verificar_firma() rechaza mensaje incorrecto" });
    }
    else {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[FALLO] verificar_firma() debio rechazar mensaje incorrecto"), .datos = "[FALLO] verificar_firma() debio rechazar mensaje incorrecto" });
        fallos = (fallos + 1);
    }
    int _ret_99 = fallos;
    _syn_texto_liberar(firma);
    _syn_texto_liberar(par);
    return _ret_99;
}

int prueba_clave_incorrecta(void) {
    int fallos;
    int resultado;
    fallos = 0;
    escribir_linea((CadenaSegura){ .longitud = (int)strlen(""), .datos = "" });
    escribir_linea((CadenaSegura){ .longitud = (int)strlen("=== Prueba 4: Rechazo de clave publica incorrecta ==="), .datos = "=== Prueba 4: Rechazo de clave publica incorrecta ===" });
    CadenaSegura par_a = cluster_generar_par_claves();
    CadenaSegura par_b = cluster_generar_par_claves();
    CadenaSegura firma = cluster_firmar_mensaje((CadenaSegura){ .longitud = (int)strlen("synapse-handshake:test"), .datos = "synapse-handshake:test" }, par_a);
    resultado = cluster_verificar_firma((CadenaSegura){ .longitud = (int)strlen("synapse-handshake:test"), .datos = "synapse-handshake:test" }, firma, par_b);
    if ((resultado != 0)) {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[OK] verificar_firma() rechaza clave publica incorrecta"), .datos = "[OK] verificar_firma() rechaza clave publica incorrecta" });
    }
    else {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[FALLO] verificar_firma() debio rechazar clave incorrecta"), .datos = "[FALLO] verificar_firma() debio rechazar clave incorrecta" });
        fallos = (fallos + 1);
    }
    int _ret_122 = fallos;
    _syn_texto_liberar(firma);
    _syn_texto_liberar(par_b);
    _syn_texto_liberar(par_a);
    return _ret_122;
}

int prueba_handshake_bidireccional(void) {
    int fallos;
    int v1;
    int v2;
    int v3;
    fallos = 0;
    escribir_linea((CadenaSegura){ .longitud = (int)strlen(""), .datos = "" });
    escribir_linea((CadenaSegura){ .longitud = (int)strlen("=== Prueba 5: Handshake bidireccional A <-> B ==="), .datos = "=== Prueba 5: Handshake bidireccional A <-> B ===" });
    CadenaSegura par_a = cluster_generar_par_claves();
    CadenaSegura par_b = cluster_generar_par_claves();
    CadenaSegura firma_a = cluster_firmar_mensaje((CadenaSegura){ .longitud = (int)strlen("synapse-handshake:pubkey-B"), .datos = "synapse-handshake:pubkey-B" }, par_a);
    if ((str_eq(firma_a, (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" }) == 1)) {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[FALLO] A no genera firma de handshake"), .datos = "[FALLO] A no genera firma de handshake" });
        fallos = (fallos + 1);
    }
    else {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[OK] A genera firma de handshake"), .datos = "[OK] A genera firma de handshake" });
    }
    v1 = cluster_verificar_firma((CadenaSegura){ .longitud = (int)strlen("synapse-handshake:pubkey-B"), .datos = "synapse-handshake:pubkey-B" }, firma_a, par_a);
    if ((v1 == 0)) {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[OK] B verifica firma de A correctamente"), .datos = "[OK] B verifica firma de A correctamente" });
    }
    else {
        escribir_linea(concat((CadenaSegura){ .longitud = (int)strlen("[FALLO] B debio verificar firma de A, obtuvo "), .datos = "[FALLO] B debio verificar firma de A, obtuvo " }, entero_a_texto(v1)));
        fallos = (fallos + 1);
    }
    CadenaSegura firma_b = cluster_firmar_mensaje((CadenaSegura){ .longitud = (int)strlen("synapse-handshake:pubkey-A"), .datos = "synapse-handshake:pubkey-A" }, par_b);
    if ((str_eq(firma_b, (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" }) == 1)) {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[FALLO] B no genera firma de respuesta"), .datos = "[FALLO] B no genera firma de respuesta" });
        fallos = (fallos + 1);
    }
    else {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[OK] B genera firma de respuesta"), .datos = "[OK] B genera firma de respuesta" });
    }
    v2 = cluster_verificar_firma((CadenaSegura){ .longitud = (int)strlen("synapse-handshake:pubkey-A"), .datos = "synapse-handshake:pubkey-A" }, firma_b, par_b);
    if ((v2 == 0)) {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[OK] A verifica firma de B correctamente"), .datos = "[OK] A verifica firma de B correctamente" });
    }
    else {
        escribir_linea(concat((CadenaSegura){ .longitud = (int)strlen("[FALLO] A debio verificar firma de B, obtuvo "), .datos = "[FALLO] A debio verificar firma de B, obtuvo " }, entero_a_texto(v2)));
        fallos = (fallos + 1);
    }
    v3 = cluster_verificar_firma((CadenaSegura){ .longitud = (int)strlen("mensaje-alterado"), .datos = "mensaje-alterado" }, firma_b, par_b);
    if ((v3 != 0)) {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[OK] A rechaza firma de B con mensaje alterado"), .datos = "[OK] A rechaza firma de B con mensaje alterado" });
    }
    else {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[FALLO] A debio rechazar mensaje alterado"), .datos = "[FALLO] A debio rechazar mensaje alterado" });
        fallos = (fallos + 1);
    }
    int _ret_178 = fallos;
    _syn_texto_liberar(firma_b);
    _syn_texto_liberar(firma_a);
    _syn_texto_liberar(par_b);
    _syn_texto_liberar(par_a);
    return _ret_178;
}

int prueba_iniciar_detener_nodo(void) {
    int fallos;
    int rc;
    int rc2;
    int rc3;
    int rc4;
    fallos = 0;
    escribir_linea((CadenaSegura){ .longitud = (int)strlen(""), .datos = "" });
    escribir_linea((CadenaSegura){ .longitud = (int)strlen("=== Prueba 6: Iniciar/Detener nodo UDP ==="), .datos = "=== Prueba 6: Iniciar/Detener nodo UDP ===" });
    rc = cluster_iniciar_nodo(0);
    if ((rc >= 0)) {
        escribir_linea(concat(concat((CadenaSegura){ .longitud = (int)strlen("[OK] iniciar_nodo(0) retorna >= 0 (rc="), .datos = "[OK] iniciar_nodo(0) retorna >= 0 (rc=" }, entero_a_texto(rc)), (CadenaSegura){ .longitud = (int)strlen(")"), .datos = ")" }));
    }
    else {
        escribir_linea(concat((CadenaSegura){ .longitud = (int)strlen("[FALLO] iniciar_nodo(0) fallo rc="), .datos = "[FALLO] iniciar_nodo(0) fallo rc=" }, entero_a_texto(rc)));
        fallos = (fallos + 1);
    }
    rc2 = cluster_detener_nodo();
    if ((rc2 >= 0)) {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[OK] detener_nodo() retorna >= 0"), .datos = "[OK] detener_nodo() retorna >= 0" });
    }
    else {
        escribir_linea(concat((CadenaSegura){ .longitud = (int)strlen("[FALLO] detener_nodo() fallo rc="), .datos = "[FALLO] detener_nodo() fallo rc=" }, entero_a_texto(rc2)));
        fallos = (fallos + 1);
    }
    rc3 = cluster_iniciar_nodo(9701);
    if ((rc3 >= 0)) {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[OK] reiniciar_nodo(9701) retorna >= 0"), .datos = "[OK] reiniciar_nodo(9701) retorna >= 0" });
    }
    else {
        escribir_linea(concat((CadenaSegura){ .longitud = (int)strlen("[FALLO] reiniciar_nodo(9701) fallo rc="), .datos = "[FALLO] reiniciar_nodo(9701) fallo rc=" }, entero_a_texto(rc3)));
        fallos = (fallos + 1);
    }
    rc4 = cluster_detener_nodo();
    if ((rc4 >= 0)) {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[OK] redetener_nodo() retorna >= 0"), .datos = "[OK] redetener_nodo() retorna >= 0" });
    }
    else {
        escribir_linea(concat((CadenaSegura){ .longitud = (int)strlen("[FALLO] redetener_nodo() fallo rc="), .datos = "[FALLO] redetener_nodo() fallo rc=" }, entero_a_texto(rc4)));
        fallos = (fallos + 1);
    }
    int _ret_218 = fallos;
    return _ret_218;
}

int prueba_enviar_hello(void) {
    int fallos;
    int rc;
    int rc2;
    int rc3;
    fallos = 0;
    escribir_linea((CadenaSegura){ .longitud = (int)strlen(""), .datos = "" });
    escribir_linea((CadenaSegura){ .longitud = (int)strlen("=== Prueba 7: Envio HELLO ==="), .datos = "=== Prueba 7: Envio HELLO ===" });
    CadenaSegura par = cluster_generar_par_claves();
    rc = cluster_iniciar_nodo(0);
    if ((rc >= 0)) {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[OK] nodo iniciado"), .datos = "[OK] nodo iniciado" });
    }
    else {
        escribir_linea(concat((CadenaSegura){ .longitud = (int)strlen("[FALLO] no pudo iniciar nodo rc="), .datos = "[FALLO] no pudo iniciar nodo rc=" }, entero_a_texto(rc)));
        fallos = (fallos + 1);
    }
    rc2 = cluster_enviar_hello((CadenaSegura){ .longitud = (int)strlen("127.0.0.1"), .datos = "127.0.0.1" }, 19099, (CadenaSegura){ .longitud = (int)strlen("nodo-test"), .datos = "nodo-test" }, par);
    if ((rc2 >= 0)) {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[OK] enviar_hello a 127.0.0.1:19099 retorna >= 0"), .datos = "[OK] enviar_hello a 127.0.0.1:19099 retorna >= 0" });
    }
    else {
        escribir_linea(concat((CadenaSegura){ .longitud = (int)strlen("[FALLO] enviar_hello() fallo rc="), .datos = "[FALLO] enviar_hello() fallo rc=" }, entero_a_texto(rc2)));
        fallos = (fallos + 1);
    }
    rc3 = cluster_detener_nodo();
    if ((rc3 >= 0)) {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[OK] nodo detenido"), .datos = "[OK] nodo detenido" });
    }
    else {
        escribir_linea(concat((CadenaSegura){ .longitud = (int)strlen("[FALLO] detener nodo fallo rc="), .datos = "[FALLO] detener nodo fallo rc=" }, entero_a_texto(rc3)));
        fallos = (fallos + 1);
    }
    int _ret_252 = fallos;
    _syn_texto_liberar(par);
    return _ret_252;
}

int prueba_enviar_datos_canal(void) {
    int fallos;
    int rc;
    int rc2;
    int rc3;
    fallos = 0;
    escribir_linea((CadenaSegura){ .longitud = (int)strlen(""), .datos = "" });
    escribir_linea((CadenaSegura){ .longitud = (int)strlen("=== Prueba 8: Envio de datos por canal remoto ==="), .datos = "=== Prueba 8: Envio de datos por canal remoto ===" });
    rc = cluster_iniciar_nodo(0);
    if ((rc >= 0)) {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[OK] nodo iniciado para canal"), .datos = "[OK] nodo iniciado para canal" });
    }
    else {
        escribir_linea(concat((CadenaSegura){ .longitud = (int)strlen("[FALLO] no pudo iniciar nodo rc="), .datos = "[FALLO] no pudo iniciar nodo rc=" }, entero_a_texto(rc)));
        fallos = (fallos + 1);
    }
    rc2 = cluster_canal_remoto_enviar((CadenaSegura){ .longitud = (int)strlen("127.0.0.1"), .datos = "127.0.0.1" }, 19098, (CadenaSegura){ .longitud = (int)strlen("datos transmitidos"), .datos = "datos transmitidos" }, 18, 1);
    if ((rc2 >= 0)) {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[OK] canal_remoto_enviar retorna >= 0"), .datos = "[OK] canal_remoto_enviar retorna >= 0" });
    }
    else {
        escribir_linea(concat((CadenaSegura){ .longitud = (int)strlen("[FALLO] canal_remoto_enviar() fallo rc="), .datos = "[FALLO] canal_remoto_enviar() fallo rc=" }, entero_a_texto(rc2)));
        fallos = (fallos + 1);
    }
    rc3 = cluster_detener_nodo();
    if ((rc3 >= 0)) {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[OK] nodo detenido tras canal"), .datos = "[OK] nodo detenido tras canal" });
    }
    else {
        escribir_linea(concat((CadenaSegura){ .longitud = (int)strlen("[FALLO] detener nodo fallo rc="), .datos = "[FALLO] detener nodo fallo rc=" }, entero_a_texto(rc3)));
        fallos = (fallos + 1);
    }
    int _ret_284 = fallos;
    return _ret_284;
}

int prueba_resultado_algebraico(void) {
    int fallos;
    struct Resultado r_ok;
    struct Resultado r_err;
    fallos = 0;
    escribir_linea((CadenaSegura){ .longitud = (int)strlen(""), .datos = "" });
    escribir_linea((CadenaSegura){ .longitud = (int)strlen("=== Prueba 9: Tipo algebraico Resultado ==="), .datos = "=== Prueba 9: Tipo algebraico Resultado ===" });
    r_ok = (struct Resultado){0};
    r_ok.tag = 0;
    r_ok.valor_str = (CadenaSegura){ .longitud = (int)strlen("operacion exitosa"), .datos = "operacion exitosa" };
    if ((r_ok.tag == 0)) {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[OK] Resultado.ok tiene tag=0"), .datos = "[OK] Resultado.ok tiene tag=0" });
    }
    else {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[FALLO] Resultado.ok tag debio ser 0"), .datos = "[FALLO] Resultado.ok tag debio ser 0" });
        fallos = (fallos + 1);
    }
    r_err = (struct Resultado){0};
    r_err.tag = 1;
    r_err.valor_str = (CadenaSegura){ .longitud = (int)strlen("error de autenticacion"), .datos = "error de autenticacion" };
    if ((r_err.tag == 1)) {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[OK] Resultado.err tiene tag=1"), .datos = "[OK] Resultado.err tiene tag=1" });
    }
    else {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[FALLO] Resultado.err tag debio ser 1"), .datos = "[FALLO] Resultado.err tag debio ser 1" });
        fallos = (fallos + 1);
    }
    int _ret_313 = fallos;
    return _ret_313;
}

int principal(void) {
    int total_fallos;
    _simd_detectar();
    total_fallos = 0;
    escribir_linea((CadenaSegura){ .longitud = (int)strlen(""), .datos = "" });
    escribir_linea((CadenaSegura){ .longitud = (int)strlen("========================================"), .datos = "========================================" });
    escribir_linea((CadenaSegura){ .longitud = (int)strlen("  M18.3: Handshake Ed25519 Zero-Trust"), .datos = "  M18.3: Handshake Ed25519 Zero-Trust" });
    escribir_linea((CadenaSegura){ .longitud = (int)strlen("========================================"), .datos = "========================================" });
    escribir_linea((CadenaSegura){ .longitud = (int)strlen(""), .datos = "" });
    total_fallos = (total_fallos + prueba_generar_par());
    total_fallos = (total_fallos + prueba_firmar_verificar());
    total_fallos = (total_fallos + prueba_firma_corrupta());
    total_fallos = (total_fallos + prueba_clave_incorrecta());
    total_fallos = (total_fallos + prueba_handshake_bidireccional());
    total_fallos = (total_fallos + prueba_iniciar_detener_nodo());
    total_fallos = (total_fallos + prueba_enviar_hello());
    total_fallos = (total_fallos + prueba_enviar_datos_canal());
    total_fallos = (total_fallos + prueba_resultado_algebraico());
    escribir_linea((CadenaSegura){ .longitud = (int)strlen(""), .datos = "" });
    escribir_linea((CadenaSegura){ .longitud = (int)strlen("========================================"), .datos = "========================================" });
    escribir_linea((CadenaSegura){ .longitud = (int)strlen("  RESULTADOS"), .datos = "  RESULTADOS" });
    escribir_linea(concat((CadenaSegura){ .longitud = (int)strlen("  Total fallos: "), .datos = "  Total fallos: " }, entero_a_texto(total_fallos)));
    escribir_linea((CadenaSegura){ .longitud = (int)strlen("========================================"), .datos = "========================================" });
    escribir_linea((CadenaSegura){ .longitud = (int)strlen(""), .datos = "" });
    if ((total_fallos > 0)) {
        int _ret_346 = 1;
        return _ret_346;
    }
    else {
        int _ret_348 = 0;
        return _ret_348;
    }
}

int main(int argc, char** argv) {
    _g_argc = argc;
    _g_argv = argv;
    pool_init(POOL_BLOQUES, TAMANO_BLOQUE);
    return principal();
    synapse_esperar_hilos();
    pool_destroy();
    return 0;
}