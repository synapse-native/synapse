#include "_synapse_shared.h"

char _gen_tmp_buf[4096];

char _G_emit_buf[1048576];
int _G_emit_pos;
FILE* _G_fp;
int _G_scope_depth;
int _G_scope_vars_depth[256];
char _G_scope_vars_names[256][64];
int _G_scope_vars_total;
int _G_safe_mode;  // M22.5: --safe flag for lifetime assertions

char _G_native_structs[256][64];
int _G_native_structs_count;
int _G_native_es_estructura(const char* n) {
    if (!n) return 0;
    for (int _i = 0; _i < _G_native_structs_count; _i++) {
        if (strcmp(_G_native_structs[_i], n) == 0) return 1;
    }
    return 0;
}

char _G_native_struct_campos[256][64][64];
char _G_native_struct_campos_tipo[256][64][64];
int _G_native_struct_campos_count[256];
int _G_native_campo_tipo(const char* sn, const char* cn, char* out) {
    if (!sn || !cn || !out) return 0;
    for (int _i = 0; _i < _G_native_structs_count; _i++) {
        if (strcmp(_G_native_structs[_i], sn) == 0) {
            for (int _j = 0; _j < _G_native_struct_campos_count[_i]; _j++) {
                if (strcmp(_G_native_struct_campos[_i][_j], cn) == 0) {
                    strcpy(out, _G_native_struct_campos_tipo[_i][_j]); return 1;
                }
            }
        }
    }
    return 0;
}

char _G_native_func_returns[512][64];
int _G_native_func_returns_count;
int _G_native_tipo_retorno(const char* fn, char* out) {
    if (!fn || !out) return 0;
    for (int _i = 0; _i < _G_native_func_returns_count; _i++) {
        if (strcmp(_G_native_func_returns[_i], fn) == 0) {
            strcpy(out, _G_native_func_returns[_i + 256]); return 1;
        }
    }
    return 0;
}

char _G_native_adt_ctrs[256][64];
char _G_native_adt_ctrs_adt[256][64];
int _G_native_adt_ctrs_tag[256];
char _G_native_adt_ctrs_tipo[256][64];
int _G_native_adt_ctrs_count;
int _G_native_es_adt_ctr(const char* c) {
    if (!c) return 0;
    for (int _i = 0; _i < _G_native_adt_ctrs_count; _i++) {
        if (strcmp(_G_native_adt_ctrs[_i], c) == 0) return 1;
    }
    return 0;
}
int _G_native_adt_ctr_info(const char* c, char* adt_out, int* tag_out, char* tipo_out) {
    if (!c) return 0;
    for (int _i = 0; _i < _G_native_adt_ctrs_count; _i++) {
        if (strcmp(_G_native_adt_ctrs[_i], c) == 0) {
            if (adt_out) strcpy(adt_out, _G_native_adt_ctrs_adt[_i]);
            if (tag_out) *tag_out = _G_native_adt_ctrs_tag[_i];
            if (tipo_out) strcpy(tipo_out, _G_native_adt_ctrs_tipo[_i]);
            return 1;
        }
    }
    return 0;
}
int _G_native_adt_unwrap_tipo(const char* adt, char* tipo_out) {
    if (!adt || !tipo_out) return 0;
    for (int _i = 0; _i < _G_native_adt_ctrs_count; _i++) {
        if (_G_native_adt_ctrs_tag[_i] == 0 && strcmp(_G_native_adt_ctrs_adt[_i], adt) == 0) {
            strcpy(tipo_out, _G_native_adt_ctrs_tipo[_i]);
            return 1;
        }
    }
    return 0;
}
int _G_native_adt_unwrap_field(const char* adt, char* field_out) {
    if (!adt || !field_out) return 0;
    // D-2: normalizar la base de una instanciacion (Resultado<entero,texto> -> Resultado)
    char _ab[64]; int _ai = 0; for (; adt[_ai] && adt[_ai] != '<' && _ai < 62; _ai++) _ab[_ai] = adt[_ai]; _ab[_ai] = 0;
    for (int _i = 0; _i < _G_native_adt_ctrs_count; _i++) {
        if (_G_native_adt_ctrs_tag[_i] == 0 && strcmp(_G_native_adt_ctrs_adt[_i], _ab) == 0) {
            strcpy(field_out, _G_native_adt_ctrs[_i]);
            return 1;
        }
    }
    return 0;
}

char _G_native_adt_gen[64][64];
int _G_native_adt_gen_nparams[64];
char _G_native_adt_gen_params[64][8][64];
int _G_native_adt_gen_count;
int _G_native_adt_gen_es(const char* n) {
    if (!n) return 0;
    for (int _i = 0; _i < _G_native_adt_gen_count; _i++) { if (strcmp(_G_native_adt_gen[_i], n) == 0) return 1; }
    return 0;
}
char _G_native_adt_inst_type[64][64];
char _G_native_adt_inst_c[64][64];
char _G_native_adt_inst_base[64][64];
char _G_native_adt_inst_fields_c[64][8][64];
int _G_native_adt_inst_nfields[64];
int _G_native_adt_inst_count;
int _G_native_adt_inst_ctr(const char* base, int tag, const char* tipo_c, char* out) {
    if (!base || !out) return 0;
    int _solo = 1; int _ns = 0; for (int _j = 0; _j < _G_native_adt_inst_count; _j++) { if (strcmp(_G_native_adt_inst_base[_j], base) == 0) { _ns++; } }
    if (_ns == 1) _solo = 1; else _solo = 0;
    for (int _i = 0; _i < _G_native_adt_inst_count; _i++) {
        if (strcmp(_G_native_adt_inst_base[_i], base) != 0) continue;
        if (_solo) { strcpy(out, _G_native_adt_inst_c[_i]); return 1; }
        if (tag < _G_native_adt_inst_nfields[_i] && tipo_c && _G_native_adt_inst_fields_c[_i][tag][0] && strcmp(_G_native_adt_inst_fields_c[_i][tag], tipo_c) == 0) { strcpy(out, _G_native_adt_inst_c[_i]); return 1; }
    }
    return 0;
}

char _G_emit_func_names[2048][64];
int _G_emit_func_count;
char _G_fn_vars[2048][64];
int _G_fn_vars_count;
void* _G_fn_var_src[2048];
int _G_fn_var_auto[2048];
char _G_fn_var_tipos[2048][64];  // ME-C4: tipo inferido por hoisting
char _G_fn_ptr_vars[64][64];  // ME-B9.x: parametros puntero
int _G_fn_ptr_vars_count;
char _G_listeners[8][16384];
int _G_listeners_count;
int _G_listener_modo;

char _G_tipo_aliases[128][64];
char _G_tipo_aliases_base[128][64];
int _G_tipo_aliases_count;
int _G_parse_error = 0;


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

int64_t principal(void) {
    int64_t total_fallos;
    _simd_detectar();
    total_fallos = 0LL;
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
    if ((total_fallos > 0LL)) {
        return 1LL;
          /* [Lifetime Scope: exit depth=1] */
    }
    else {
        return 0LL;
          /* [Lifetime Scope: exit depth=1] */
    }
      /* [Lifetime Scope: exit depth=0] */
}

int64_t prueba_clave_incorrecta(void) {
    int64_t fallos;
    CadenaSegura par_a = {0};
    CadenaSegura par_b = {0};
    CadenaSegura firma = {0};
    int64_t resultado;
    fallos = 0LL;
    escribir_linea((CadenaSegura){ .longitud = (int)strlen(""), .datos = "" });
    escribir_linea((CadenaSegura){ .longitud = (int)strlen("=== Prueba 4: Rechazo de clave publica incorrecta ==="), .datos = "=== Prueba 4: Rechazo de clave publica incorrecta ===" });
    _syn_texto_liberar(par_a);
    par_a = cluster_generar_par_claves();
    _syn_texto_liberar(par_b);
    par_b = cluster_generar_par_claves();
    _syn_texto_liberar(firma);
    firma = cluster_firmar_mensaje((CadenaSegura){ .longitud = (int)strlen("synapse-handshake:test"), .datos = "synapse-handshake:test" }, par_a);
    resultado = cluster_verificar_firma((CadenaSegura){ .longitud = (int)strlen("synapse-handshake:test"), .datos = "synapse-handshake:test" }, firma, par_b);
    if ((resultado != 0LL)) {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[OK] verificar_firma() rechaza clave publica incorrecta"), .datos = "[OK] verificar_firma() rechaza clave publica incorrecta" });
          /* [Lifetime Scope: exit depth=1] */
    }
    else {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[FALLO] verificar_firma() debio rechazar clave incorrecta"), .datos = "[FALLO] verificar_firma() debio rechazar clave incorrecta" });
        fallos = (fallos + 1LL);
          /* [Lifetime Scope: exit depth=1] */
    }
    return fallos;
      /* [Lifetime Scope: exit depth=0] */
}

int64_t prueba_enviar_datos_canal(void) {
    int64_t fallos;
    int64_t rc;
    int64_t rc2;
    int64_t rc3;
    fallos = 0LL;
    escribir_linea((CadenaSegura){ .longitud = (int)strlen(""), .datos = "" });
    escribir_linea((CadenaSegura){ .longitud = (int)strlen("=== Prueba 8: Envio de datos por canal remoto ==="), .datos = "=== Prueba 8: Envio de datos por canal remoto ===" });
    rc = cluster_iniciar_nodo(0LL);
    if ((rc >= 0LL)) {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[OK] nodo iniciado para canal"), .datos = "[OK] nodo iniciado para canal" });
          /* [Lifetime Scope: exit depth=1] */
    }
    else {
        escribir_linea(concat((CadenaSegura){ .longitud = (int)strlen("[FALLO] no pudo iniciar nodo rc="), .datos = "[FALLO] no pudo iniciar nodo rc=" }, entero_a_texto(rc)));
        fallos = (fallos + 1LL);
          /* [Lifetime Scope: exit depth=1] */
    }
    rc2 = cluster_canal_remoto_enviar((CadenaSegura){ .longitud = (int)strlen("127.0.0.1"), .datos = "127.0.0.1" }, 19098LL, (CadenaSegura){ .longitud = (int)strlen("datos transmitidos"), .datos = "datos transmitidos" }, 18LL, 1LL);
    if ((rc2 >= 0LL)) {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[OK] canal_remoto_enviar retorna >= 0"), .datos = "[OK] canal_remoto_enviar retorna >= 0" });
          /* [Lifetime Scope: exit depth=1] */
    }
    else {
        escribir_linea(concat((CadenaSegura){ .longitud = (int)strlen("[FALLO] canal_remoto_enviar() fallo rc="), .datos = "[FALLO] canal_remoto_enviar() fallo rc=" }, entero_a_texto(rc2)));
        fallos = (fallos + 1LL);
          /* [Lifetime Scope: exit depth=1] */
    }
    rc3 = cluster_detener_nodo();
    if ((rc3 >= 0LL)) {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[OK] nodo detenido tras canal"), .datos = "[OK] nodo detenido tras canal" });
          /* [Lifetime Scope: exit depth=1] */
    }
    else {
        escribir_linea(concat((CadenaSegura){ .longitud = (int)strlen("[FALLO] detener nodo fallo rc="), .datos = "[FALLO] detener nodo fallo rc=" }, entero_a_texto(rc3)));
        fallos = (fallos + 1LL);
          /* [Lifetime Scope: exit depth=1] */
    }
    return fallos;
      /* [Lifetime Scope: exit depth=0] */
}

int64_t prueba_enviar_hello(void) {
    int64_t fallos;
    CadenaSegura par = {0};
    int64_t rc;
    int64_t rc2;
    int64_t rc3;
    fallos = 0LL;
    escribir_linea((CadenaSegura){ .longitud = (int)strlen(""), .datos = "" });
    escribir_linea((CadenaSegura){ .longitud = (int)strlen("=== Prueba 7: Envio HELLO ==="), .datos = "=== Prueba 7: Envio HELLO ===" });
    _syn_texto_liberar(par);
    par = cluster_generar_par_claves();
    rc = cluster_iniciar_nodo(0LL);
    if ((rc >= 0LL)) {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[OK] nodo iniciado"), .datos = "[OK] nodo iniciado" });
          /* [Lifetime Scope: exit depth=1] */
    }
    else {
        escribir_linea(concat((CadenaSegura){ .longitud = (int)strlen("[FALLO] no pudo iniciar nodo rc="), .datos = "[FALLO] no pudo iniciar nodo rc=" }, entero_a_texto(rc)));
        fallos = (fallos + 1LL);
          /* [Lifetime Scope: exit depth=1] */
    }
    rc2 = cluster_enviar_hello((CadenaSegura){ .longitud = (int)strlen("127.0.0.1"), .datos = "127.0.0.1" }, 19099LL, (CadenaSegura){ .longitud = (int)strlen("nodo-test"), .datos = "nodo-test" }, par);
    if ((rc2 >= 0LL)) {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[OK] enviar_hello a 127.0.0.1:19099 retorna >= 0"), .datos = "[OK] enviar_hello a 127.0.0.1:19099 retorna >= 0" });
          /* [Lifetime Scope: exit depth=1] */
    }
    else {
        escribir_linea(concat((CadenaSegura){ .longitud = (int)strlen("[FALLO] enviar_hello() fallo rc="), .datos = "[FALLO] enviar_hello() fallo rc=" }, entero_a_texto(rc2)));
        fallos = (fallos + 1LL);
          /* [Lifetime Scope: exit depth=1] */
    }
    rc3 = cluster_detener_nodo();
    if ((rc3 >= 0LL)) {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[OK] nodo detenido"), .datos = "[OK] nodo detenido" });
          /* [Lifetime Scope: exit depth=1] */
    }
    else {
        escribir_linea(concat((CadenaSegura){ .longitud = (int)strlen("[FALLO] detener nodo fallo rc="), .datos = "[FALLO] detener nodo fallo rc=" }, entero_a_texto(rc3)));
        fallos = (fallos + 1LL);
          /* [Lifetime Scope: exit depth=1] */
    }
    return fallos;
      /* [Lifetime Scope: exit depth=0] */
}

int64_t prueba_firma_corrupta(void) {
    int64_t fallos;
    CadenaSegura par = {0};
    CadenaSegura firma = {0};
    int64_t resultado;
    fallos = 0LL;
    escribir_linea((CadenaSegura){ .longitud = (int)strlen(""), .datos = "" });
    escribir_linea((CadenaSegura){ .longitud = (int)strlen("=== Prueba 3: Rechazo de firma corrupta (Zero-Trust) ==="), .datos = "=== Prueba 3: Rechazo de firma corrupta (Zero-Trust) ===" });
    _syn_texto_liberar(par);
    par = cluster_generar_par_claves();
    _syn_texto_liberar(firma);
    firma = cluster_firmar_mensaje((CadenaSegura){ .longitud = (int)strlen("synapse-handshake:test"), .datos = "synapse-handshake:test" }, par);
    resultado = cluster_verificar_firma((CadenaSegura){ .longitud = (int)strlen("synapse-handshake:test-DIFFERENT"), .datos = "synapse-handshake:test-DIFFERENT" }, firma, par);
    if ((resultado != 0LL)) {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[OK] verificar_firma() rechaza mensaje incorrecto"), .datos = "[OK] verificar_firma() rechaza mensaje incorrecto" });
          /* [Lifetime Scope: exit depth=1] */
    }
    else {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[FALLO] verificar_firma() debio rechazar mensaje incorrecto"), .datos = "[FALLO] verificar_firma() debio rechazar mensaje incorrecto" });
        fallos = (fallos + 1LL);
          /* [Lifetime Scope: exit depth=1] */
    }
    return fallos;
      /* [Lifetime Scope: exit depth=0] */
}

int64_t prueba_firmar_verificar(void) {
    int64_t fallos;
    CadenaSegura par = {0};
    CadenaSegura firma = {0};
    int64_t resultado;
    fallos = 0LL;
    escribir_linea((CadenaSegura){ .longitud = (int)strlen(""), .datos = "" });
    escribir_linea((CadenaSegura){ .longitud = (int)strlen("=== Prueba 2: Firma y verificacion Ed25519 ==="), .datos = "=== Prueba 2: Firma y verificacion Ed25519 ===" });
    _syn_texto_liberar(par);
    par = cluster_generar_par_claves();
    _syn_texto_liberar(firma);
    firma = cluster_firmar_mensaje((CadenaSegura){ .longitud = (int)strlen("synapse-handshake:test-message"), .datos = "synapse-handshake:test-message" }, par);
    if ((str_eq(firma, (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" }) == 1)) {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[FALLO] firmar_mensaje() retorna firma vacia"), .datos = "[FALLO] firmar_mensaje() retorna firma vacia" });
        fallos = (fallos + 1LL);
          /* [Lifetime Scope: exit depth=1] */
    }
    else {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[OK] firmar_mensaje() retorna firma no vacia"), .datos = "[OK] firmar_mensaje() retorna firma no vacia" });
          /* [Lifetime Scope: exit depth=1] */
    }
    resultado = cluster_verificar_firma((CadenaSegura){ .longitud = (int)strlen("synapse-handshake:test-message"), .datos = "synapse-handshake:test-message" }, firma, par);
    if ((resultado == 0LL)) {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[OK] verificar_firma() retorna 0 para firma valida"), .datos = "[OK] verificar_firma() retorna 0 para firma valida" });
          /* [Lifetime Scope: exit depth=1] */
    }
    else {
        escribir_linea(concat((CadenaSegura){ .longitud = (int)strlen("[FALLO] verificar_firma() debio retornar 0, obtuvo "), .datos = "[FALLO] verificar_firma() debio retornar 0, obtuvo " }, entero_a_texto(resultado)));
        fallos = (fallos + 1LL);
          /* [Lifetime Scope: exit depth=1] */
    }
    return fallos;
      /* [Lifetime Scope: exit depth=0] */
}

int64_t prueba_generar_par(void) {
    int64_t fallos;
    CadenaSegura par = {0};
    fallos = 0LL;
    escribir_linea((CadenaSegura){ .longitud = (int)strlen(""), .datos = "" });
    escribir_linea((CadenaSegura){ .longitud = (int)strlen("=== Prueba 1: Generar par Ed25519 ==="), .datos = "=== Prueba 1: Generar par Ed25519 ===" });
    _syn_texto_liberar(par);
    par = cluster_generar_par_claves();
    if ((str_eq(par, (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" }) == 1)) {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[FALLO] generar_par() retorna vacio"), .datos = "[FALLO] generar_par() retorna vacio" });
        fallos = (fallos + 1LL);
          /* [Lifetime Scope: exit depth=1] */
    }
    else {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[OK] generar_par() no retorna vacio"), .datos = "[OK] generar_par() no retorna vacio" });
          /* [Lifetime Scope: exit depth=1] */
    }
    return fallos;
      /* [Lifetime Scope: exit depth=0] */
}

int64_t prueba_handshake_bidireccional(void) {
    int64_t fallos;
    CadenaSegura par_a = {0};
    CadenaSegura par_b = {0};
    CadenaSegura firma_a = {0};
    int64_t v1;
    CadenaSegura firma_b = {0};
    int64_t v2;
    int64_t v3;
    fallos = 0LL;
    escribir_linea((CadenaSegura){ .longitud = (int)strlen(""), .datos = "" });
    escribir_linea((CadenaSegura){ .longitud = (int)strlen("=== Prueba 5: Handshake bidireccional A <-> B ==="), .datos = "=== Prueba 5: Handshake bidireccional A <-> B ===" });
    _syn_texto_liberar(par_a);
    par_a = cluster_generar_par_claves();
    _syn_texto_liberar(par_b);
    par_b = cluster_generar_par_claves();
    _syn_texto_liberar(firma_a);
    firma_a = cluster_firmar_mensaje((CadenaSegura){ .longitud = (int)strlen("synapse-handshake:pubkey-B"), .datos = "synapse-handshake:pubkey-B" }, par_a);
    if ((str_eq(firma_a, (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" }) == 1)) {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[FALLO] A no genera firma de handshake"), .datos = "[FALLO] A no genera firma de handshake" });
        fallos = (fallos + 1LL);
          /* [Lifetime Scope: exit depth=1] */
    }
    else {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[OK] A genera firma de handshake"), .datos = "[OK] A genera firma de handshake" });
          /* [Lifetime Scope: exit depth=1] */
    }
    v1 = cluster_verificar_firma((CadenaSegura){ .longitud = (int)strlen("synapse-handshake:pubkey-B"), .datos = "synapse-handshake:pubkey-B" }, firma_a, par_a);
    if ((v1 == 0LL)) {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[OK] B verifica firma de A correctamente"), .datos = "[OK] B verifica firma de A correctamente" });
          /* [Lifetime Scope: exit depth=1] */
    }
    else {
        escribir_linea(concat((CadenaSegura){ .longitud = (int)strlen("[FALLO] B debio verificar firma de A, obtuvo "), .datos = "[FALLO] B debio verificar firma de A, obtuvo " }, entero_a_texto(v1)));
        fallos = (fallos + 1LL);
          /* [Lifetime Scope: exit depth=1] */
    }
    _syn_texto_liberar(firma_b);
    firma_b = cluster_firmar_mensaje((CadenaSegura){ .longitud = (int)strlen("synapse-handshake:pubkey-A"), .datos = "synapse-handshake:pubkey-A" }, par_b);
    if ((str_eq(firma_b, (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" }) == 1)) {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[FALLO] B no genera firma de respuesta"), .datos = "[FALLO] B no genera firma de respuesta" });
        fallos = (fallos + 1LL);
          /* [Lifetime Scope: exit depth=1] */
    }
    else {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[OK] B genera firma de respuesta"), .datos = "[OK] B genera firma de respuesta" });
          /* [Lifetime Scope: exit depth=1] */
    }
    v2 = cluster_verificar_firma((CadenaSegura){ .longitud = (int)strlen("synapse-handshake:pubkey-A"), .datos = "synapse-handshake:pubkey-A" }, firma_b, par_b);
    if ((v2 == 0LL)) {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[OK] A verifica firma de B correctamente"), .datos = "[OK] A verifica firma de B correctamente" });
          /* [Lifetime Scope: exit depth=1] */
    }
    else {
        escribir_linea(concat((CadenaSegura){ .longitud = (int)strlen("[FALLO] A debio verificar firma de B, obtuvo "), .datos = "[FALLO] A debio verificar firma de B, obtuvo " }, entero_a_texto(v2)));
        fallos = (fallos + 1LL);
          /* [Lifetime Scope: exit depth=1] */
    }
    v3 = cluster_verificar_firma((CadenaSegura){ .longitud = (int)strlen("mensaje-alterado"), .datos = "mensaje-alterado" }, firma_b, par_b);
    if ((v3 != 0LL)) {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[OK] A rechaza firma de B con mensaje alterado"), .datos = "[OK] A rechaza firma de B con mensaje alterado" });
          /* [Lifetime Scope: exit depth=1] */
    }
    else {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[FALLO] A debio rechazar mensaje alterado"), .datos = "[FALLO] A debio rechazar mensaje alterado" });
        fallos = (fallos + 1LL);
          /* [Lifetime Scope: exit depth=1] */
    }
    return fallos;
      /* [Lifetime Scope: exit depth=0] */
}

int64_t prueba_iniciar_detener_nodo(void) {
    int64_t fallos;
    int64_t rc;
    int64_t rc2;
    int64_t rc3;
    int64_t rc4;
    fallos = 0LL;
    escribir_linea((CadenaSegura){ .longitud = (int)strlen(""), .datos = "" });
    escribir_linea((CadenaSegura){ .longitud = (int)strlen("=== Prueba 6: Iniciar/Detener nodo UDP ==="), .datos = "=== Prueba 6: Iniciar/Detener nodo UDP ===" });
    rc = cluster_iniciar_nodo(0LL);
    if ((rc >= 0LL)) {
        escribir_linea(concat(concat((CadenaSegura){ .longitud = (int)strlen("[OK] iniciar_nodo(0) retorna >= 0 (rc="), .datos = "[OK] iniciar_nodo(0) retorna >= 0 (rc=" }, entero_a_texto(rc)), (CadenaSegura){ .longitud = (int)strlen(")"), .datos = ")" }));
          /* [Lifetime Scope: exit depth=1] */
    }
    else {
        escribir_linea(concat((CadenaSegura){ .longitud = (int)strlen("[FALLO] iniciar_nodo(0) fallo rc="), .datos = "[FALLO] iniciar_nodo(0) fallo rc=" }, entero_a_texto(rc)));
        fallos = (fallos + 1LL);
          /* [Lifetime Scope: exit depth=1] */
    }
    rc2 = cluster_detener_nodo();
    if ((rc2 >= 0LL)) {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[OK] detener_nodo() retorna >= 0"), .datos = "[OK] detener_nodo() retorna >= 0" });
          /* [Lifetime Scope: exit depth=1] */
    }
    else {
        escribir_linea(concat((CadenaSegura){ .longitud = (int)strlen("[FALLO] detener_nodo() fallo rc="), .datos = "[FALLO] detener_nodo() fallo rc=" }, entero_a_texto(rc2)));
        fallos = (fallos + 1LL);
          /* [Lifetime Scope: exit depth=1] */
    }
    rc3 = cluster_iniciar_nodo(9701LL);
    if ((rc3 >= 0LL)) {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[OK] reiniciar_nodo(9701) retorna >= 0"), .datos = "[OK] reiniciar_nodo(9701) retorna >= 0" });
          /* [Lifetime Scope: exit depth=1] */
    }
    else {
        escribir_linea(concat((CadenaSegura){ .longitud = (int)strlen("[FALLO] reiniciar_nodo(9701) fallo rc="), .datos = "[FALLO] reiniciar_nodo(9701) fallo rc=" }, entero_a_texto(rc3)));
        fallos = (fallos + 1LL);
          /* [Lifetime Scope: exit depth=1] */
    }
    rc4 = cluster_detener_nodo();
    if ((rc4 >= 0LL)) {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[OK] redetener_nodo() retorna >= 0"), .datos = "[OK] redetener_nodo() retorna >= 0" });
          /* [Lifetime Scope: exit depth=1] */
    }
    else {
        escribir_linea(concat((CadenaSegura){ .longitud = (int)strlen("[FALLO] redetener_nodo() fallo rc="), .datos = "[FALLO] redetener_nodo() fallo rc=" }, entero_a_texto(rc4)));
        fallos = (fallos + 1LL);
          /* [Lifetime Scope: exit depth=1] */
    }
    return fallos;
      /* [Lifetime Scope: exit depth=0] */
}

int64_t prueba_resultado_algebraico(void) {
    int64_t fallos;
    struct Resultado r_ok;
    struct Resultado r_err;
    fallos = 0LL;
    escribir_linea((CadenaSegura){ .longitud = (int)strlen(""), .datos = "" });
    escribir_linea((CadenaSegura){ .longitud = (int)strlen("=== Prueba 9: Tipo algebraico Resultado ==="), .datos = "=== Prueba 9: Tipo algebraico Resultado ===" });
    r_ok = (struct Resultado){0};
    r_ok.tag = 0LL;
    r_ok.valor_str = (CadenaSegura){ .longitud = (int)strlen("operacion exitosa"), .datos = "operacion exitosa" };
    if ((r_ok.tag == 0LL)) {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[OK] Resultado.ok tiene tag=0"), .datos = "[OK] Resultado.ok tiene tag=0" });
          /* [Lifetime Scope: exit depth=1] */
    }
    else {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[FALLO] Resultado.ok tag debio ser 0"), .datos = "[FALLO] Resultado.ok tag debio ser 0" });
        fallos = (fallos + 1LL);
          /* [Lifetime Scope: exit depth=1] */
    }
    r_err = (struct Resultado){0};
    r_err.tag = 1LL;
    r_err.valor_str = (CadenaSegura){ .longitud = (int)strlen("error de autenticacion"), .datos = "error de autenticacion" };
    if ((r_err.tag == 1LL)) {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[OK] Resultado.err tiene tag=1"), .datos = "[OK] Resultado.err tiene tag=1" });
          /* [Lifetime Scope: exit depth=1] */
    }
    else {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[FALLO] Resultado.err tag debio ser 1"), .datos = "[FALLO] Resultado.err tag debio ser 1" });
        fallos = (fallos + 1LL);
          /* [Lifetime Scope: exit depth=1] */
    }
    return fallos;
      /* [Lifetime Scope: exit depth=0] */
}

int main(int argc, char** argv) {
    _g_argc = argc;
    _g_argv = argv;
    pool_init(POOL_BLOQUES, TAMANO_BLOQUE);
    int64_t _rc = principal();
    synapse_esperar_hilos();
    pool_destroy();
    return _rc;
}