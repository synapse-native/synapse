#include "_synapse_shared.h"

char _gen_tmp_buf[4096];

char _G_emit_buf[1048576];
int _G_emit_pos;
FILE* _G_fp;
int _G_scope_depth;
int _G_scope_vars_depth[256];
char _G_scope_vars_names[256][64];
int _G_scope_vars_total;
int _G_scope_vars_kind[256];  // D-1.2: 0=texto,1=rc,2=arc,3=debil
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

char _G_native_func_returns[2048][64];
int _G_native_func_returns_count;
int _G_native_tipo_retorno(const char* fn, char* out) {
    if (!fn || !out) return 0;
    for (int _i = 0; _i < _G_native_func_returns_count; _i++) {
        if (strcmp(_G_native_func_returns[_i], fn) == 0) {
            strcpy(out, _G_native_func_returns[_i + 1024]); return 1;
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
char _G_native_canal_names[512][64];
char _G_native_canal_elem[512][64];
int _G_native_canal_count;
void _G_native_canal_elem_set(const char* _cname, const char* _celem) {
    if (!_cname || !_celem) return;
    for (int _ci = 0; _ci < _G_native_canal_count; _ci++) { if (strcmp(_G_native_canal_names[_ci], _cname) == 0) { strncpy(_G_native_canal_elem[_ci], _celem, 63); _G_native_canal_elem[_ci][63] = 0; return; } }
    if (_G_native_canal_count < 512) { strncpy(_G_native_canal_names[_G_native_canal_count], _cname, 63); _G_native_canal_names[_G_native_canal_count][63] = 0; strncpy(_G_native_canal_elem[_G_native_canal_count], _celem, 63); _G_native_canal_elem[_G_native_canal_count][63] = 0; _G_native_canal_count++; }
}
int _G_native_canal_elem_tipo(const char* _cname, char* _cout) {
    if (!_cname || !_cout) return 0;
    for (int _ci = 0; _ci < _G_native_canal_count; _ci++) { if (strcmp(_G_native_canal_names[_ci], _cname) == 0) { strncpy(_cout, _G_native_canal_elem[_ci], 63); _cout[63] = 0; return 1; } }
    return 0;
}
char _G_listeners[8][16384];
int _G_listeners_count;
int _G_listener_modo;
char _G_lanzar_wrappers[8][4096];
int _G_lanzar_wrappers_count;
int _G_lanzar_count;

void* _G_fn_garantizas_actuales = 0;
char _G_fn_ret_tipo_c[64];

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

int64_t buscar_def_funcion(CadenaSegura doc, CadenaSegura nombre) {
    #ifndef SYNAPSE_RELEASE
    assert((1) && "Fallo en contrato: requiere");
    #endif
    CadenaSegura patron = concat(concat((CadenaSegura){ .longitud = (int)strlen("funcion "), .datos = "funcion " }, nombre), (CadenaSegura){ .longitud = (int)strlen("("), .datos = "(" });
    int64_t _resultado_ = strstr_f(doc, patron);
    #ifndef SYNAPSE_RELEASE
    assert(((_resultado_ >= (-1LL))) && "Fallo en contrato: garantiza");
    #endif
    _syn_texto_liberar(patron);
    _syn_texto_liberar(nombre);
    _syn_texto_liberar(doc);
    return _resultado_;
      /* [Lifetime Scope: exit depth=0] */
}

int64_t buscar_def_variable(CadenaSegura doc, CadenaSegura nombre) {
    #ifndef SYNAPSE_RELEASE
    assert((1) && "Fallo en contrato: requiere");
    #endif
    CadenaSegura patron1 = concat(nombre, (CadenaSegura){ .longitud = (int)strlen(" = "), .datos = " = " });
    CadenaSegura patron2 = concat(concat((CadenaSegura){ .longitud = (int)strlen("let "), .datos = "let " }, nombre), (CadenaSegura){ .longitud = (int)strlen(" = "), .datos = " = " });
    int64_t idx1 = strstr_f(doc, patron1);
    int64_t idx2 = strstr_f(doc, patron2);
    if ((idx1 >= 0LL)) {
        if ((idx2 >= 0LL)) {
            if ((idx1 < idx2)) {
                int64_t _resultado_ = idx1;
                #ifndef SYNAPSE_RELEASE
                assert(((_resultado_ >= (-1LL))) && "Fallo en contrato: garantiza");
                #endif
                _syn_texto_liberar(patron2);
                _syn_texto_liberar(patron1);
                _syn_texto_liberar(nombre);
                _syn_texto_liberar(doc);
                return _resultado_;
                  /* [Lifetime Scope: exit depth=3] */
            }
            int64_t _resultado_ = idx2;
            #ifndef SYNAPSE_RELEASE
            assert(((_resultado_ >= (-1LL))) && "Fallo en contrato: garantiza");
            #endif
            return _resultado_;
              /* [Lifetime Scope: exit depth=2] */
        }
        int64_t _resultado_ = idx1;
        #ifndef SYNAPSE_RELEASE
        assert(((_resultado_ >= (-1LL))) && "Fallo en contrato: garantiza");
        #endif
        return _resultado_;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((idx2 >= 0LL)) {
        int64_t _resultado_ = idx2;
        #ifndef SYNAPSE_RELEASE
        assert(((_resultado_ >= (-1LL))) && "Fallo en contrato: garantiza");
        #endif
        return _resultado_;
          /* [Lifetime Scope: exit depth=1] */
    }
    int64_t _resultado_ = (-1LL);
    #ifndef SYNAPSE_RELEASE
    assert(((_resultado_ >= (-1LL))) && "Fallo en contrato: garantiza");
    #endif
    return _resultado_;
      /* [Lifetime Scope: exit depth=0] */
}

CadenaSegura construir_error(int64_t id, int64_t codigo, CadenaSegura mensaje) {
    #ifndef SYNAPSE_RELEASE
    assert(((id >= 0LL)) && "Fallo en contrato: requiere");
    #endif
    CadenaSegura _resultado_ = concat(concat(concat(concat(concat(concat((CadenaSegura){ .longitud = (int)strlen("{\"jsonrpc\":\"2.0\",\"id\":"), .datos = "{\"jsonrpc\":\"2.0\",\"id\":" }, a_texto(id)), (CadenaSegura){ .longitud = (int)strlen(",\"error\":{\"code\":"), .datos = ",\"error\":{\"code\":" }), a_texto(codigo)), (CadenaSegura){ .longitud = (int)strlen(",\"message\":\""), .datos = ",\"message\":\"" }), mensaje), (CadenaSegura){ .longitud = (int)strlen("\"}}"), .datos = "\"}}" });
    #ifndef SYNAPSE_RELEASE
    assert(((strlen_s(_resultado_) > 0LL)) && "Fallo en contrato: garantiza");
    #endif
    _syn_texto_liberar(mensaje);
    return _resultado_;
      /* [Lifetime Scope: exit depth=0] */
}

CadenaSegura construir_notificacion(CadenaSegura metodo, CadenaSegura params) {
    #ifndef SYNAPSE_RELEASE
    assert(((strlen_s(metodo) > 0LL)) && "Fallo en contrato: requiere");
    #endif
    CadenaSegura _resultado_ = concat(concat(concat(concat((CadenaSegura){ .longitud = (int)strlen("{\"jsonrpc\":\"2.0\",\"method\":\""), .datos = "{\"jsonrpc\":\"2.0\",\"method\":\"" }, metodo), (CadenaSegura){ .longitud = (int)strlen("\",\"params\":"), .datos = "\",\"params\":" }), params), (CadenaSegura){ .longitud = (int)strlen("}"), .datos = "}" });
    #ifndef SYNAPSE_RELEASE
    assert(((strlen_s(_resultado_) > 0LL)) && "Fallo en contrato: garantiza");
    #endif
    _syn_texto_liberar(params);
    _syn_texto_liberar(metodo);
    return _resultado_;
      /* [Lifetime Scope: exit depth=0] */
}

CadenaSegura construir_respuesta(int64_t id, CadenaSegura resultado) {
    #ifndef SYNAPSE_RELEASE
    assert(((id >= 0LL)) && "Fallo en contrato: requiere");
    #endif
    CadenaSegura _resultado_ = concat(concat(concat(concat((CadenaSegura){ .longitud = (int)strlen("{\"jsonrpc\":\"2.0\",\"id\":"), .datos = "{\"jsonrpc\":\"2.0\",\"id\":" }, a_texto(id)), (CadenaSegura){ .longitud = (int)strlen(",\"result\":"), .datos = ",\"result\":" }), resultado), (CadenaSegura){ .longitud = (int)strlen("}"), .datos = "}" });
    #ifndef SYNAPSE_RELEASE
    assert(((strlen_s(_resultado_) > 0LL)) && "Fallo en contrato: garantiza");
    #endif
    _syn_texto_liberar(resultado);
    return _resultado_;
      /* [Lifetime Scope: exit depth=0] */
}

void enviar_respuesta(CadenaSegura respuesta) {
    #ifndef SYNAPSE_RELEASE
    assert(((strlen_s(respuesta) > 0LL)) && "Fallo en contrato: requiere");
    #endif
    int64_t len = strlen_s(respuesta);
    CadenaSegura header = concat(concat((CadenaSegura){ .longitud = (int)strlen("Content-Length: "), .datos = "Content-Length: " }, a_texto(len)), (CadenaSegura){ .longitud = (int)strlen("\r\n\r\n"), .datos = "\r\n\r\n" });
    escribir(header);
    escribir(respuesta);
      /* [Lifetime Scope: exit depth=0] */
    _syn_texto_liberar(respuesta);
    _syn_texto_liberar(header);
}

int64_t extraer_entero(CadenaSegura texto) {
    #ifndef SYNAPSE_RELEASE
    assert((1) && "Fallo en contrato: requiere");
    #endif
    int64_t len = strlen_s(texto);
    int64_t resultado = 0LL;
    int64_t negativo = 0LL;
    int64_t i = 0LL;
    while ((i < len)) {
        CadenaSegura c = ((CadenaSegura){.longitud=1LL, .datos=((char*)memcpy(malloc(1LL+1),(texto).datos+i,1LL))});
        if ((cmp_texto(c, (CadenaSegura){ .longitud = (int)strlen(" "), .datos = " " }) != 0LL)) {
            break;
              /* [Lifetime Scope: exit depth=2] */
        }
        i = (i + 1LL);
          /* [Lifetime Scope: exit depth=1] */
        _syn_texto_liberar(c);
    }
    if ((i < len)) {
        CadenaSegura c = ((CadenaSegura){.longitud=1LL, .datos=((char*)memcpy(malloc(1LL+1),(texto).datos+i,1LL))});
        if ((cmp_texto(c, (CadenaSegura){ .longitud = (int)strlen("-"), .datos = "-" }) == 0LL)) {
            negativo = 1LL;
            i = (i + 1LL);
              /* [Lifetime Scope: exit depth=2] */
        }
        else {
            if ((cmp_texto(c, (CadenaSegura){ .longitud = (int)strlen("+"), .datos = "+" }) == 0LL)) {
                i = (i + 1LL);
                  /* [Lifetime Scope: exit depth=3] */
            }
              /* [Lifetime Scope: exit depth=2] */
        }
          /* [Lifetime Scope: exit depth=1] */
        _syn_texto_liberar(c);
    }
    while ((i < len)) {
        CadenaSegura c = ((CadenaSegura){.longitud=1LL, .datos=((char*)memcpy(malloc(1LL+1),(texto).datos+i,1LL))});
        int64_t digito = (-1LL);
        if ((cmp_texto(c, (CadenaSegura){ .longitud = (int)strlen("0"), .datos = "0" }) == 0LL)) {
            digito = 0LL;
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((cmp_texto(c, (CadenaSegura){ .longitud = (int)strlen("1"), .datos = "1" }) == 0LL)) {
            digito = 1LL;
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((cmp_texto(c, (CadenaSegura){ .longitud = (int)strlen("2"), .datos = "2" }) == 0LL)) {
            digito = 2LL;
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((cmp_texto(c, (CadenaSegura){ .longitud = (int)strlen("3"), .datos = "3" }) == 0LL)) {
            digito = 3LL;
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((cmp_texto(c, (CadenaSegura){ .longitud = (int)strlen("4"), .datos = "4" }) == 0LL)) {
            digito = 4LL;
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((cmp_texto(c, (CadenaSegura){ .longitud = (int)strlen("5"), .datos = "5" }) == 0LL)) {
            digito = 5LL;
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((cmp_texto(c, (CadenaSegura){ .longitud = (int)strlen("6"), .datos = "6" }) == 0LL)) {
            digito = 6LL;
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((cmp_texto(c, (CadenaSegura){ .longitud = (int)strlen("7"), .datos = "7" }) == 0LL)) {
            digito = 7LL;
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((cmp_texto(c, (CadenaSegura){ .longitud = (int)strlen("8"), .datos = "8" }) == 0LL)) {
            digito = 8LL;
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((cmp_texto(c, (CadenaSegura){ .longitud = (int)strlen("9"), .datos = "9" }) == 0LL)) {
            digito = 9LL;
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((digito == (-1LL))) {
            break;
              /* [Lifetime Scope: exit depth=2] */
        }
        resultado = ((resultado * 10LL) + digito);
        i = (i + 1LL);
          /* [Lifetime Scope: exit depth=1] */
        _syn_texto_liberar(c);
    }
    if ((negativo == 1LL)) {
        resultado = (0LL - resultado);
          /* [Lifetime Scope: exit depth=1] */
    }
    int64_t _resultado_ = resultado;
    #ifndef SYNAPSE_RELEASE
    assert((1) && "Fallo en contrato: garantiza");
    #endif
    _syn_texto_liberar(texto);
    return _resultado_;
      /* [Lifetime Scope: exit depth=0] */
}

int64_t extraer_id_body(CadenaSegura body) {
    #ifndef SYNAPSE_RELEASE
    assert((1) && "Fallo en contrato: requiere");
    #endif
    CadenaSegura patron = (CadenaSegura){ .longitud = (int)strlen("\"id\":"), .datos = "\"id\":" };
    int64_t idx = strstr_f(body, patron);
    if ((idx == (-1LL))) {
        int64_t _resultado_ = (-1LL);
        #ifndef SYNAPSE_RELEASE
        assert((1) && "Fallo en contrato: garantiza");
        #endif
        _syn_texto_liberar(patron);
        _syn_texto_liberar(body);
        return _resultado_;
          /* [Lifetime Scope: exit depth=1] */
    }
    int64_t inicio_num = (idx + 5LL);
    int64_t len_body = strlen_s(body);
    if ((inicio_num >= len_body)) {
        int64_t _resultado_ = (-1LL);
        #ifndef SYNAPSE_RELEASE
        assert((1) && "Fallo en contrato: garantiza");
        #endif
        return _resultado_;
          /* [Lifetime Scope: exit depth=1] */
    }
    int64_t pos = inicio_num;
    while ((pos < len_body)) {
        CadenaSegura c = ((CadenaSegura){.longitud=1LL, .datos=((char*)memcpy(malloc(1LL+1),(body).datos+pos,1LL))});
        if ((cmp_texto(c, (CadenaSegura){ .longitud = (int)strlen(" "), .datos = " " }) != 0LL)) {
            break;
              /* [Lifetime Scope: exit depth=2] */
        }
        pos = (pos + 1LL);
          /* [Lifetime Scope: exit depth=1] */
        _syn_texto_liberar(c);
    }
    int64_t fin = pos;
    while ((fin < len_body)) {
        CadenaSegura c = ((CadenaSegura){.longitud=1LL, .datos=((char*)memcpy(malloc(1LL+1),(body).datos+fin,1LL))});
        if ((cmp_texto(c, (CadenaSegura){ .longitud = (int)strlen("0"), .datos = "0" }) >= 0LL)) {
            if ((cmp_texto(c, (CadenaSegura){ .longitud = (int)strlen("9"), .datos = "9" }) <= 0LL)) {
                fin = (fin + 1LL);
                  /* [Lifetime Scope: exit depth=3] */
            }
            else {
                break;
                  /* [Lifetime Scope: exit depth=3] */
            }
              /* [Lifetime Scope: exit depth=2] */
        }
        else {
            if ((cmp_texto(c, (CadenaSegura){ .longitud = (int)strlen("-"), .datos = "-" }) == 0LL)) {
                if ((fin == pos)) {
                    fin = (fin + 1LL);
                      /* [Lifetime Scope: exit depth=4] */
                }
                else {
                    break;
                      /* [Lifetime Scope: exit depth=4] */
                }
                  /* [Lifetime Scope: exit depth=3] */
            }
            else {
                break;
                  /* [Lifetime Scope: exit depth=3] */
            }
              /* [Lifetime Scope: exit depth=2] */
        }
          /* [Lifetime Scope: exit depth=1] */
        _syn_texto_liberar(c);
    }
    if ((fin <= pos)) {
        int64_t _resultado_ = (-1LL);
        #ifndef SYNAPSE_RELEASE
        assert((1) && "Fallo en contrato: garantiza");
        #endif
        return _resultado_;
          /* [Lifetime Scope: exit depth=1] */
    }
    CadenaSegura num_str = ((CadenaSegura){.longitud=(fin - pos), .datos=((char*)memcpy(malloc((fin - pos)+1),(body).datos+pos,(fin - pos)))});
    int64_t _resultado_ = extraer_entero(num_str);
    #ifndef SYNAPSE_RELEASE
    assert((1) && "Fallo en contrato: garantiza");
    #endif
    _syn_texto_liberar(num_str);
    return _resultado_;
      /* [Lifetime Scope: exit depth=0] */
}

CadenaSegura extraer_texto_doc(CadenaSegura params) {
    #ifndef SYNAPSE_RELEASE
    assert((1) && "Fallo en contrato: requiere");
    #endif
    int64_t len_params = strlen_s(params);
    CadenaSegura patron = (CadenaSegura){ .longitud = (int)strlen(",\"text\":\""), .datos = ",\"text\":\"" };
    int64_t patron_len = 9LL;
    if ((len_params < patron_len)) {
        CadenaSegura _resultado_ = (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
        #ifndef SYNAPSE_RELEASE
        assert((1) && "Fallo en contrato: garantiza");
        #endif
        _syn_texto_liberar(patron);
        _syn_texto_liberar(params);
        return _resultado_;
          /* [Lifetime Scope: exit depth=1] */
    }
    int64_t mejor_idx = (-1LL);
    int64_t scan = (len_params - patron_len);
    while ((scan >= 0LL)) {
        CadenaSegura chunk = ((CadenaSegura){.longitud=patron_len, .datos=((char*)memcpy(malloc(patron_len+1),(params).datos+scan,patron_len))});
        if ((cmp_texto(chunk, patron) == 0LL)) {
            mejor_idx = scan;
            scan = 0LL;
              /* [Lifetime Scope: exit depth=2] */
        }
        else {
            scan = (scan - 1LL);
              /* [Lifetime Scope: exit depth=2] */
        }
          /* [Lifetime Scope: exit depth=1] */
        _syn_texto_liberar(chunk);
    }
    if ((mejor_idx == (-1LL))) {
        CadenaSegura _resultado_ = (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
        #ifndef SYNAPSE_RELEASE
        assert((1) && "Fallo en contrato: garantiza");
        #endif
        return _resultado_;
          /* [Lifetime Scope: exit depth=1] */
    }
    int64_t valor_inicio = (mejor_idx + patron_len);
    CadenaSegura valor_resto = ((CadenaSegura){.longitud=(len_params - valor_inicio), .datos=((char*)memcpy(malloc((len_params - valor_inicio)+1),(params).datos+valor_inicio,(len_params - valor_inicio)))});
    // cumple Manual 8 1.2: find closing quote, skip escaped quotes (\")
    int64_t cierre = (-1LL);
    {
        const char* vd = valor_resto.datos;
        int64_t vl = valor_resto.longitud;
        int64_t ci = 0;
        while (ci < vl) {
            if (vd[ci] == '\\') {
                ci += 2; // skip escaped char
            } else if (vd[ci] == '"') {
                cierre = ci;
                break;
            } else {
                ci++;
            }
        }
    }
    if ((cierre == (-1LL))) {
        CadenaSegura _resultado_ = (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
        #ifndef SYNAPSE_RELEASE
        assert((1) && "Fallo en contrato: garantiza");
        #endif
        _syn_texto_liberar(valor_resto);
        return _resultado_;
          /* [Lifetime Scope: exit depth=1] */
    }
    CadenaSegura _resultado_ = ((CadenaSegura){.longitud=cierre, .datos=((char*)memcpy(malloc(cierre+1),(valor_resto).datos+0LL,cierre))});
    #ifndef SYNAPSE_RELEASE
    assert((1) && "Fallo en contrato: garantiza");
    #endif
    return _resultado_;
      /* [Lifetime Scope: exit depth=0] */
}

CadenaSegura extraer_uri(CadenaSegura params) {
    #ifndef SYNAPSE_RELEASE
    assert((1) && "Fallo en contrato: requiere");
    #endif
    int64_t uri_idx = strstr_f(params, (CadenaSegura){ .longitud = (int)strlen("\"uri\""), .datos = "\"uri\"" });
    if ((uri_idx == (-1LL))) {
        CadenaSegura _resultado_ = (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
        #ifndef SYNAPSE_RELEASE
        assert((1) && "Fallo en contrato: garantiza");
        #endif
        _syn_texto_liberar(params);
        return _resultado_;
          /* [Lifetime Scope: exit depth=1] */
    }
    int64_t despues = (uri_idx + 5LL);
    CadenaSegura resto = ((CadenaSegura){.longitud=(strlen_s(params) - despues), .datos=((char*)memcpy(malloc((strlen_s(params) - despues)+1),(params).datos+despues,(strlen_s(params) - despues)))});
    int64_t comilla1 = strstr_f(resto, (CadenaSegura){ .longitud = (int)strlen("\""), .datos = "\"" });
    if ((comilla1 == (-1LL))) {
        CadenaSegura _resultado_ = (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
        #ifndef SYNAPSE_RELEASE
        assert((1) && "Fallo en contrato: garantiza");
        #endif
        _syn_texto_liberar(resto);
        return _resultado_;
          /* [Lifetime Scope: exit depth=1] */
    }
    CadenaSegura dentro = ((CadenaSegura){.longitud=((strlen_s(resto) - comilla1) - 1LL), .datos=((char*)memcpy(malloc(((strlen_s(resto) - comilla1) - 1LL)+1),(resto).datos+(comilla1 + 1LL),((strlen_s(resto) - comilla1) - 1LL)))});
    int64_t comilla2 = strstr_f(dentro, (CadenaSegura){ .longitud = (int)strlen("\""), .datos = "\"" });
    if ((comilla2 == (-1LL))) {
        CadenaSegura _resultado_ = (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
        #ifndef SYNAPSE_RELEASE
        assert((1) && "Fallo en contrato: garantiza");
        #endif
        _syn_texto_liberar(dentro);
        return _resultado_;
          /* [Lifetime Scope: exit depth=1] */
    }
    CadenaSegura _resultado_ = ((CadenaSegura){.longitud=comilla2, .datos=((char*)memcpy(malloc(comilla2+1),(dentro).datos+0LL,comilla2))});
    #ifndef SYNAPSE_RELEASE
    assert((1) && "Fallo en contrato: garantiza");
    #endif
    return _resultado_;
      /* [Lifetime Scope: exit depth=0] */
}

void handle_code_action(int64_t id, CadenaSegura doc, CadenaSegura params) {
    #ifndef SYNAPSE_RELEASE
    assert(((id >= 0LL)) && "Fallo en contrato: requiere");
    #endif
    int64_t range_idx = strstr_f(params, (CadenaSegura){ .longitud = (int)strlen("\"range\""), .datos = "\"range\"" });
    if ((range_idx == (-1LL))) {
        enviar_respuesta(construir_respuesta(id, (CadenaSegura){ .longitud = (int)strlen("[]"), .datos = "[]" }));
        #ifndef SYNAPSE_RELEASE
        assert((1) && "Fallo en contrato: garantiza");
        #endif
        _syn_texto_liberar(params);
        _syn_texto_liberar(doc);
        return;
          /* [Lifetime Scope: exit depth=1] */
    }
    int64_t len_params = strlen_s(params);
    int64_t start_idx = strstr_f(params, (CadenaSegura){ .longitud = (int)strlen("\"start\""), .datos = "\"start\"" });
    if ((start_idx == (-1LL))) {
        enviar_respuesta(construir_respuesta(id, (CadenaSegura){ .longitud = (int)strlen("[]"), .datos = "[]" }));
        #ifndef SYNAPSE_RELEASE
        assert((1) && "Fallo en contrato: garantiza");
        #endif
        return;
          /* [Lifetime Scope: exit depth=1] */
    }
    int64_t line_idx = strstr_f(((CadenaSegura){.longitud=(len_params - start_idx), .datos=((char*)memcpy(malloc((len_params - start_idx)+1),(params).datos+start_idx,(len_params - start_idx)))}), (CadenaSegura){ .longitud = (int)strlen("\"line\""), .datos = "\"line\"" });
    if ((line_idx == (-1LL))) {
        enviar_respuesta(construir_respuesta(id, (CadenaSegura){ .longitud = (int)strlen("[]"), .datos = "[]" }));
        #ifndef SYNAPSE_RELEASE
        assert((1) && "Fallo en contrato: garantiza");
        #endif
        return;
          /* [Lifetime Scope: exit depth=1] */
    }
    int64_t abs_line = (start_idx + line_idx);
    CadenaSegura line_seg = ((CadenaSegura){.longitud=((len_params - abs_line) - 7LL), .datos=((char*)memcpy(malloc(((len_params - abs_line) - 7LL)+1),(params).datos+(abs_line + 7LL),((len_params - abs_line) - 7LL)))});
    int64_t comma_pos = strstr_f(line_seg, (CadenaSegura){ .longitud = (int)strlen(","), .datos = "," });
    if ((comma_pos == (-1LL))) {
        comma_pos = strlen_s(line_seg);
          /* [Lifetime Scope: exit depth=1] */
    }
    int64_t line_val = extraer_entero(((CadenaSegura){.longitud=comma_pos, .datos=((char*)memcpy(malloc(comma_pos+1),(line_seg).datos+0LL,comma_pos))}));
    int64_t len_doc = strlen_s(doc);
    int64_t scan = 0LL;
    int64_t func_inicio = (-1LL);
    int64_t func_fin = (-1LL);
    while ((scan < len_doc)) {
        CadenaSegura patron = (CadenaSegura){ .longitud = (int)strlen("funcion "), .datos = "funcion " };
        int64_t plen = 8LL;
        if (((scan + plen) <= len_doc)) {
            CadenaSegura chunk = ((CadenaSegura){.longitud=plen, .datos=((char*)memcpy(malloc(plen+1),(doc).datos+scan,plen))});
            if ((cmp_texto(chunk, patron) == 0LL)) {
                int64_t def_linea = linea_de_posicion(doc, scan);
                if ((def_linea <= line_val)) {
                    func_inicio = scan;
                      /* [Lifetime Scope: exit depth=4] */
                }
                  /* [Lifetime Scope: exit depth=3] */
            }
              /* [Lifetime Scope: exit depth=2] */
            _syn_texto_liberar(chunk);
        }
        scan = (scan + 1LL);
          /* [Lifetime Scope: exit depth=1] */
        _syn_texto_liberar(patron);
    }
    if ((func_inicio >= 0LL)) {
        int64_t scan2 = (func_inicio + 8LL);
        func_fin = len_doc;
        while ((scan2 < len_doc)) {
            CadenaSegura p2 = (CadenaSegura){ .longitud = (int)strlen("funcion "), .datos = "funcion " };
            if (((scan2 + 8LL) <= len_doc)) {
                CadenaSegura chunk2 = ((CadenaSegura){.longitud=8LL, .datos=((char*)memcpy(malloc(8LL+1),(doc).datos+scan2,8LL))});
                if ((cmp_texto(chunk2, p2) == 0LL)) {
                    func_fin = scan2;
                    scan2 = len_doc;
                      /* [Lifetime Scope: exit depth=4] */
                }
                  /* [Lifetime Scope: exit depth=3] */
                _syn_texto_liberar(chunk2);
            }
            scan2 = (scan2 + 1LL);
              /* [Lifetime Scope: exit depth=2] */
            _syn_texto_liberar(p2);
        }
        int64_t tiene_retornar = 0LL;
        CadenaSegura body = ((CadenaSegura){.longitud=(func_fin - func_inicio), .datos=((char*)memcpy(malloc((func_fin - func_inicio)+1),(doc).datos+func_inicio,(func_fin - func_inicio)))});
        if ((strstr_f(body, (CadenaSegura){ .longitud = (int)strlen("retornar"), .datos = "retornar" }) >= 0LL)) {
            tiene_retornar = 1LL;
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((tiene_retornar == 0LL)) {
            CadenaSegura edit = (CadenaSegura){ .longitud = (int)strlen("{\"title\":\"Agregar retornar 0\",\"kind\":\"quickfix\",\"diagnostics\":[],\"edit\":{\"changes\":{}}}"), .datos = "{\"title\":\"Agregar retornar 0\",\"kind\":\"quickfix\",\"diagnostics\":[],\"edit\":{\"changes\":{}}}" };
            enviar_respuesta(construir_respuesta(id, concat(concat((CadenaSegura){ .longitud = (int)strlen("["), .datos = "[" }, edit), (CadenaSegura){ .longitud = (int)strlen("]"), .datos = "]" })));
            #ifndef SYNAPSE_RELEASE
            assert((1) && "Fallo en contrato: garantiza");
            #endif
            _syn_texto_liberar(edit);
            _syn_texto_liberar(body);
            _syn_texto_liberar(line_seg);
            return;
              /* [Lifetime Scope: exit depth=2] */
        }
          /* [Lifetime Scope: exit depth=1] */
    }
    enviar_respuesta(construir_respuesta(id, (CadenaSegura){ .longitud = (int)strlen("[]"), .datos = "[]" }));
      /* [Lifetime Scope: exit depth=0] */
}

void handle_completion(int64_t id, CadenaSegura doc, CadenaSegura params) {
    #ifndef SYNAPSE_RELEASE
    assert(((id >= 0LL)) && "Fallo en contrato: requiere");
    #endif
    CadenaSegura items = (CadenaSegura){ .longitud = (int)strlen("[{\"label\":\"funcion\",\"kind\":14},{\"label\":\"retorno\",\"kind\":14},{\"label\":\"si\",\"kind\":14},{\"label\":\"sino\",\"kind\":14},{\"label\":\"mientras\",\"kind\":14},{\"label\":\"para\",\"kind\":14},{\"label\":\"verdadero\",\"kind\":14},{\"label\":\"falso\",\"kind\":14},{\"label\":\"nulo\",\"kind\":14},{\"label\":\"entero\",\"kind\":14},{\"label\":\"decimal\",\"kind\":14},{\"label\":\"texto\",\"kind\":14},{\"label\":\"booleano\",\"kind\":14},{\"label\":\"estructura\",\"kind\":14},{\"label\":\"importar\",\"kind\":14},{\"label\":\"externo\",\"kind\":14}]"), .datos = "[{\"label\":\"funcion\",\"kind\":14},{\"label\":\"retorno\",\"kind\":14},{\"label\":\"si\",\"kind\":14},{\"label\":\"sino\",\"kind\":14},{\"label\":\"mientras\",\"kind\":14},{\"label\":\"para\",\"kind\":14},{\"label\":\"verdadero\",\"kind\":14},{\"label\":\"falso\",\"kind\":14},{\"label\":\"nulo\",\"kind\":14},{\"label\":\"entero\",\"kind\":14},{\"label\":\"decimal\",\"kind\":14},{\"label\":\"texto\",\"kind\":14},{\"label\":\"booleano\",\"kind\":14},{\"label\":\"estructura\",\"kind\":14},{\"label\":\"importar\",\"kind\":14},{\"label\":\"externo\",\"kind\":14}]" };
    enviar_respuesta(construir_respuesta(id, concat(concat((CadenaSegura){ .longitud = (int)strlen("{\"isIncomplete\":false,\"items\":"), .datos = "{\"isIncomplete\":false,\"items\":" }, items), (CadenaSegura){ .longitud = (int)strlen("}"), .datos = "}" })));
      /* [Lifetime Scope: exit depth=0] */
    _syn_texto_liberar(params);
    _syn_texto_liberar(items);
    _syn_texto_liberar(doc);
}

void handle_definition(int64_t id, CadenaSegura uri, CadenaSegura doc, CadenaSegura params) {
    #ifndef SYNAPSE_RELEASE
    assert(((id >= 0LL)) && "Fallo en contrato: requiere");
    #endif
    int64_t line_idx = strstr_f(params, (CadenaSegura){ .longitud = (int)strlen("\"line\""), .datos = "\"line\"" });
    if ((line_idx == (-1LL))) {
        enviar_respuesta(construir_respuesta(id, (CadenaSegura){ .longitud = (int)strlen("null"), .datos = "null" }));
        #ifndef SYNAPSE_RELEASE
        assert((1) && "Fallo en contrato: garantiza");
        #endif
        _syn_texto_liberar(uri);
        _syn_texto_liberar(params);
        _syn_texto_liberar(doc);
        return;
          /* [Lifetime Scope: exit depth=1] */
    }
    CadenaSegura line_seg = ((CadenaSegura){.longitud=((strlen_s(params) - line_idx) - 7LL), .datos=((char*)memcpy(malloc(((strlen_s(params) - line_idx) - 7LL)+1),(params).datos+(line_idx + 7LL),((strlen_s(params) - line_idx) - 7LL)))});
    int64_t comma_pos = strstr_f(line_seg, (CadenaSegura){ .longitud = (int)strlen(","), .datos = "," });
    int64_t line_val = extraer_entero(((CadenaSegura){.longitud=comma_pos, .datos=((char*)memcpy(malloc(comma_pos+1),(line_seg).datos+0LL,comma_pos))}));
    int64_t char_idx = strstr_f(params, (CadenaSegura){ .longitud = (int)strlen("\"character\""), .datos = "\"character\"" });
    if ((char_idx == (-1LL))) {
        enviar_respuesta(construir_respuesta(id, (CadenaSegura){ .longitud = (int)strlen("null"), .datos = "null" }));
        #ifndef SYNAPSE_RELEASE
        assert((1) && "Fallo en contrato: garantiza");
        #endif
        _syn_texto_liberar(line_seg);
        return;
          /* [Lifetime Scope: exit depth=1] */
    }
    CadenaSegura char_seg = ((CadenaSegura){.longitud=((strlen_s(params) - char_idx) - 12LL), .datos=((char*)memcpy(malloc(((strlen_s(params) - char_idx) - 12LL)+1),(params).datos+(char_idx + 12LL),((strlen_s(params) - char_idx) - 12LL)))});
    int64_t brace_pos = strstr_f(char_seg, (CadenaSegura){ .longitud = (int)strlen("}"), .datos = "}" });
    int64_t char_val = extraer_entero(((CadenaSegura){.longitud=brace_pos, .datos=((char*)memcpy(malloc(brace_pos+1),(char_seg).datos+0LL,brace_pos))}));
    int64_t len_doc = strlen_s(doc);
    if ((len_doc == 0LL)) {
        enviar_respuesta(construir_respuesta(id, (CadenaSegura){ .longitud = (int)strlen("null"), .datos = "null" }));
        #ifndef SYNAPSE_RELEASE
        assert((1) && "Fallo en contrato: garantiza");
        #endif
        _syn_texto_liberar(char_seg);
        return;
          /* [Lifetime Scope: exit depth=1] */
    }
    int64_t linea_inicio = 0LL;
    int64_t num_linea = 0LL;
    int64_t scan = 0LL;
    while ((scan < len_doc)) {
        CadenaSegura c = ((CadenaSegura){.longitud=1LL, .datos=((char*)memcpy(malloc(1LL+1),(doc).datos+scan,1LL))});
        if ((cmp_texto(c, (CadenaSegura){ .longitud = (int)strlen("\n"), .datos = "\n" }) == 0LL)) {
            if ((num_linea == line_val)) {
                scan = len_doc;
                  /* [Lifetime Scope: exit depth=3] */
            }
            else {
                linea_inicio = (scan + 1LL);
                num_linea = (num_linea + 1LL);
                  /* [Lifetime Scope: exit depth=3] */
            }
              /* [Lifetime Scope: exit depth=2] */
        }
        scan = (scan + 1LL);
          /* [Lifetime Scope: exit depth=1] */
        _syn_texto_liberar(c);
    }
    int64_t linea_fin = len_doc;
    if ((linea_inicio < len_doc)) {
        CadenaSegura busqueda = ((CadenaSegura){.longitud=(len_doc - linea_inicio), .datos=((char*)memcpy(malloc((len_doc - linea_inicio)+1),(doc).datos+linea_inicio,(len_doc - linea_inicio)))});
        int64_t nl_idx = strstr_f(busqueda, (CadenaSegura){ .longitud = (int)strlen("\n"), .datos = "\n" });
        if ((nl_idx >= 0LL)) {
            linea_fin = (linea_inicio + nl_idx);
              /* [Lifetime Scope: exit depth=2] */
        }
          /* [Lifetime Scope: exit depth=1] */
        _syn_texto_liberar(busqueda);
    }
    if ((linea_inicio >= linea_fin)) {
        enviar_respuesta(construir_respuesta(id, (CadenaSegura){ .longitud = (int)strlen("null"), .datos = "null" }));
        #ifndef SYNAPSE_RELEASE
        assert((1) && "Fallo en contrato: garantiza");
        #endif
        return;
          /* [Lifetime Scope: exit depth=1] */
    }
    CadenaSegura linea_texto = ((CadenaSegura){.longitud=(linea_fin - linea_inicio), .datos=((char*)memcpy(malloc((linea_fin - linea_inicio)+1),(doc).datos+linea_inicio,(linea_fin - linea_inicio)))});
    int64_t len_lin = strlen_s(linea_texto);
    if ((char_val >= len_lin)) {
        enviar_respuesta(construir_respuesta(id, (CadenaSegura){ .longitud = (int)strlen("null"), .datos = "null" }));
        #ifndef SYNAPSE_RELEASE
        assert((1) && "Fallo en contrato: garantiza");
        #endif
        _syn_texto_liberar(linea_texto);
        return;
          /* [Lifetime Scope: exit depth=1] */
    }
    CadenaSegura palabra = palabra_en_posicion(linea_texto, char_val);
    if ((strlen_s(palabra) == 0LL)) {
        enviar_respuesta(construir_respuesta(id, (CadenaSegura){ .longitud = (int)strlen("null"), .datos = "null" }));
        #ifndef SYNAPSE_RELEASE
        assert((1) && "Fallo en contrato: garantiza");
        #endif
        _syn_texto_liberar(palabra);
        return;
          /* [Lifetime Scope: exit depth=1] */
    }
    CadenaSegura patron_func = concat(concat((CadenaSegura){ .longitud = (int)strlen("funcion "), .datos = "funcion " }, palabra), (CadenaSegura){ .longitud = (int)strlen("("), .datos = "(" });
    int64_t func_idx = strstr_f(doc, patron_func);
    if ((func_idx >= 0LL)) {
        int64_t def_linea = linea_de_posicion(doc, func_idx);
        CadenaSegura result = concat(concat(concat(concat(concat(concat((CadenaSegura){ .longitud = (int)strlen("{\"uri\":"), .datos = "{\"uri\":" }, json_string(uri)), (CadenaSegura){ .longitud = (int)strlen(",\"range\":{\"start\":{\"line\":"), .datos = ",\"range\":{\"start\":{\"line\":" }), a_texto(def_linea)), (CadenaSegura){ .longitud = (int)strlen(",\"character\":9},\"end\":{\"line\":"), .datos = ",\"character\":9},\"end\":{\"line\":" }), a_texto(def_linea)), (CadenaSegura){ .longitud = (int)strlen(",\"character\":9}}}"), .datos = ",\"character\":9}}}" });
        enviar_respuesta(construir_respuesta(id, result));
        #ifndef SYNAPSE_RELEASE
        assert((1) && "Fallo en contrato: garantiza");
        #endif
        _syn_texto_liberar(result);
        _syn_texto_liberar(patron_func);
        return;
          /* [Lifetime Scope: exit depth=1] */
    }
    CadenaSegura patron_var1 = concat(palabra, (CadenaSegura){ .longitud = (int)strlen(" = "), .datos = " = " });
    CadenaSegura patron_var2 = concat(concat((CadenaSegura){ .longitud = (int)strlen("let "), .datos = "let " }, palabra), (CadenaSegura){ .longitud = (int)strlen(" = "), .datos = " = " });
    int64_t var_idx1 = strstr_f(doc, patron_var1);
    int64_t var_idx2 = strstr_f(doc, patron_var2);
    int64_t var_idx = (-1LL);
    if ((var_idx1 >= 0LL)) {
        var_idx = var_idx1;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((var_idx2 >= 0LL)) {
        if ((var_idx < 0LL)) {
            var_idx = var_idx2;
              /* [Lifetime Scope: exit depth=2] */
        }
        else {
            if ((var_idx2 < var_idx)) {
                var_idx = var_idx2;
                  /* [Lifetime Scope: exit depth=3] */
            }
              /* [Lifetime Scope: exit depth=2] */
        }
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((var_idx >= 0LL)) {
        int64_t def_linea = linea_de_posicion(doc, var_idx);
        int64_t scan_l = var_idx;
        while ((scan_l > 0LL)) {
            CadenaSegura c = ((CadenaSegura){.longitud=1LL, .datos=((char*)memcpy(malloc(1LL+1),(doc).datos+(scan_l - 1LL),1LL))});
            if ((cmp_texto(c, (CadenaSegura){ .longitud = (int)strlen("\n"), .datos = "\n" }) == 0LL)) {
                break;
                  /* [Lifetime Scope: exit depth=3] */
            }
            scan_l = (scan_l - 1LL);
              /* [Lifetime Scope: exit depth=2] */
            _syn_texto_liberar(c);
        }
        int64_t char_offset = (var_idx - scan_l);
        CadenaSegura result = concat(concat(concat(concat(concat(concat(concat(concat(concat(concat((CadenaSegura){ .longitud = (int)strlen("{\"uri\":"), .datos = "{\"uri\":" }, json_string(uri)), (CadenaSegura){ .longitud = (int)strlen(",\"range\":{\"start\":{\"line\":"), .datos = ",\"range\":{\"start\":{\"line\":" }), a_texto(def_linea)), (CadenaSegura){ .longitud = (int)strlen(",\"character\":"), .datos = ",\"character\":" }), a_texto(char_offset)), (CadenaSegura){ .longitud = (int)strlen("},\"end\":{\"line\":"), .datos = "},\"end\":{\"line\":" }), a_texto(def_linea)), (CadenaSegura){ .longitud = (int)strlen(",\"character\":"), .datos = ",\"character\":" }), a_texto(char_offset)), (CadenaSegura){ .longitud = (int)strlen("}}}"), .datos = "}}}" });
        enviar_respuesta(construir_respuesta(id, result));
        #ifndef SYNAPSE_RELEASE
        assert((1) && "Fallo en contrato: garantiza");
        #endif
        _syn_texto_liberar(result);
        _syn_texto_liberar(patron_var2);
        _syn_texto_liberar(patron_var1);
        return;
          /* [Lifetime Scope: exit depth=1] */
    }
    enviar_respuesta(construir_respuesta(id, (CadenaSegura){ .longitud = (int)strlen("null"), .datos = "null" }));
      /* [Lifetime Scope: exit depth=0] */
}

void handle_did_change_configuration(CadenaSegura params) {
    #ifndef SYNAPSE_RELEASE
    assert((1) && "Fallo en contrato: requiere");
    #endif
    #ifndef SYNAPSE_RELEASE
    assert((1) && "Fallo en contrato: garantiza");
    #endif
    _syn_texto_liberar(params);
    return;
      /* [Lifetime Scope: exit depth=0] */
}

void handle_formatting(int64_t id, CadenaSegura doc, CadenaSegura params) {
    #ifndef SYNAPSE_RELEASE
    assert(((id >= 0LL)) && "Fallo en contrato: requiere");
    #endif
    int64_t len_doc = strlen_s(doc);
    if ((len_doc == 0LL)) {
        enviar_respuesta(construir_respuesta(id, (CadenaSegura){ .longitud = (int)strlen("[]"), .datos = "[]" }));
        #ifndef SYNAPSE_RELEASE
        assert((1) && "Fallo en contrato: garantiza");
        #endif
        _syn_texto_liberar(params);
        _syn_texto_liberar(doc);
        return;
          /* [Lifetime Scope: exit depth=1] */
    }
    CadenaSegura resultado = (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
    int64_t i = 0LL;
    int64_t nivel = 0LL;
    int64_t en_linea = 0LL;
    while ((i < len_doc)) {
        CadenaSegura c = ((CadenaSegura){.longitud=1LL, .datos=((char*)memcpy(malloc(1LL+1),(doc).datos+i,1LL))});
        if ((cmp_texto(c, (CadenaSegura){ .longitud = (int)strlen("\n"), .datos = "\n" }) == 0LL)) {
            _syn_texto_liberar(resultado);
            resultado = concat(resultado, (CadenaSegura){ .longitud = (int)strlen("\n"), .datos = "\n" });
            i = (i + 1LL);
            en_linea = 0LL;
            int64_t indent = 0LL;
            int64_t j = i;
            while ((j < len_doc)) {
                CadenaSegura cc = ((CadenaSegura){.longitud=1LL, .datos=((char*)memcpy(malloc(1LL+1),(doc).datos+j,1LL))});
                if ((cmp_texto(cc, (CadenaSegura){ .longitud = (int)strlen(" "), .datos = " " }) == 0LL)) {
                    indent = (indent + 1LL);
                    j = (j + 1LL);
                      /* [Lifetime Scope: exit depth=4] */
                }
                if ((cmp_texto(cc, (CadenaSegura){ .longitud = (int)strlen("\t"), .datos = "\t" }) == 0LL)) {
                    indent = (indent + 4LL);
                    j = (j + 1LL);
                      /* [Lifetime Scope: exit depth=4] */
                }
                else {
                    break;
                      /* [Lifetime Scope: exit depth=4] */
                }
                  /* [Lifetime Scope: exit depth=3] */
                _syn_texto_liberar(cc);
            }
            CadenaSegura espacios = (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
            int64_t k = 0LL;
            while ((k < indent)) {
                _syn_texto_liberar(espacios);
                espacios = concat(espacios, (CadenaSegura){ .longitud = (int)strlen(" "), .datos = " " });
                k = (k + 1LL);
                  /* [Lifetime Scope: exit depth=3] */
                _syn_texto_liberar(espacios);
            }
            _syn_texto_liberar(resultado);
            resultado = concat(resultado, espacios);
            i = j;
            en_linea = 1LL;
              /* [Lifetime Scope: exit depth=2] */
            _syn_texto_liberar(resultado);
        }
        else {
            if ((cmp_texto(c, (CadenaSegura){ .longitud = (int)strlen("\t"), .datos = "\t" }) == 0LL)) {
                _syn_texto_liberar(resultado);
                resultado = concat(resultado, (CadenaSegura){ .longitud = (int)strlen("    "), .datos = "    " });
                  /* [Lifetime Scope: exit depth=3] */
                _syn_texto_liberar(resultado);
            }
            else {
                _syn_texto_liberar(resultado);
                resultado = concat(resultado, c);
                  /* [Lifetime Scope: exit depth=3] */
                _syn_texto_liberar(resultado);
            }
            i = (i + 1LL);
            en_linea = 1LL;
              /* [Lifetime Scope: exit depth=2] */
        }
          /* [Lifetime Scope: exit depth=1] */
        _syn_texto_liberar(c);
    }
    CadenaSegura edit = concat(concat((CadenaSegura){ .longitud = (int)strlen("{\"range\":{\"start\":{\"line\":0,\"character\":0},\"end\":{\"line\":99999,\"character\":0}},\"newText\":\""), .datos = "{\"range\":{\"start\":{\"line\":0,\"character\":0},\"end\":{\"line\":99999,\"character\":0}},\"newText\":\"" }, escapar_json(resultado)), (CadenaSegura){ .longitud = (int)strlen("\"}"), .datos = "\"}" });
    enviar_respuesta(construir_respuesta(id, concat(concat((CadenaSegura){ .longitud = (int)strlen("["), .datos = "[" }, edit), (CadenaSegura){ .longitud = (int)strlen("]"), .datos = "]" })));
      /* [Lifetime Scope: exit depth=0] */
    _syn_texto_liberar(edit);
}

void handle_hover(int64_t id, CadenaSegura doc, CadenaSegura params) {
    #ifndef SYNAPSE_RELEASE
    assert(((id >= 0LL)) && "Fallo en contrato: requiere");
    #endif
    int64_t line_idx = strstr_f(params, (CadenaSegura){ .longitud = (int)strlen("\"line\""), .datos = "\"line\"" });
    if ((line_idx == (-1LL))) {
        enviar_respuesta(construir_respuesta(id, (CadenaSegura){ .longitud = (int)strlen("null"), .datos = "null" }));
        #ifndef SYNAPSE_RELEASE
        assert((1) && "Fallo en contrato: garantiza");
        #endif
        _syn_texto_liberar(params);
        _syn_texto_liberar(doc);
        return;
          /* [Lifetime Scope: exit depth=1] */
    }
    CadenaSegura line_seg = ((CadenaSegura){.longitud=((strlen_s(params) - line_idx) - 7LL), .datos=((char*)memcpy(malloc(((strlen_s(params) - line_idx) - 7LL)+1),(params).datos+(line_idx + 7LL),((strlen_s(params) - line_idx) - 7LL)))});
    int64_t comma_pos = strstr_f(line_seg, (CadenaSegura){ .longitud = (int)strlen(","), .datos = "," });
    int64_t line_val = extraer_entero(((CadenaSegura){.longitud=comma_pos, .datos=((char*)memcpy(malloc(comma_pos+1),(line_seg).datos+0LL,comma_pos))}));
    int64_t char_idx = strstr_f(params, (CadenaSegura){ .longitud = (int)strlen("\"character\""), .datos = "\"character\"" });
    if ((char_idx == (-1LL))) {
        enviar_respuesta(construir_respuesta(id, (CadenaSegura){ .longitud = (int)strlen("null"), .datos = "null" }));
        #ifndef SYNAPSE_RELEASE
        assert((1) && "Fallo en contrato: garantiza");
        #endif
        _syn_texto_liberar(line_seg);
        return;
          /* [Lifetime Scope: exit depth=1] */
    }
    CadenaSegura char_seg = ((CadenaSegura){.longitud=((strlen_s(params) - char_idx) - 12LL), .datos=((char*)memcpy(malloc(((strlen_s(params) - char_idx) - 12LL)+1),(params).datos+(char_idx + 12LL),((strlen_s(params) - char_idx) - 12LL)))});
    int64_t brace_pos = strstr_f(char_seg, (CadenaSegura){ .longitud = (int)strlen("}"), .datos = "}" });
    int64_t char_val = extraer_entero(((CadenaSegura){.longitud=brace_pos, .datos=((char*)memcpy(malloc(brace_pos+1),(char_seg).datos+0LL,brace_pos))}));
    int64_t len_doc = strlen_s(doc);
    if ((len_doc == 0LL)) {
        enviar_respuesta(construir_respuesta(id, (CadenaSegura){ .longitud = (int)strlen("null"), .datos = "null" }));
        #ifndef SYNAPSE_RELEASE
        assert((1) && "Fallo en contrato: garantiza");
        #endif
        _syn_texto_liberar(char_seg);
        return;
          /* [Lifetime Scope: exit depth=1] */
    }
    int64_t linea_inicio = 0LL;
    int64_t num_linea = 0LL;
    int64_t scan = 0LL;
    while ((scan < len_doc)) {
        CadenaSegura c = ((CadenaSegura){.longitud=1LL, .datos=((char*)memcpy(malloc(1LL+1),(doc).datos+scan,1LL))});
        if ((cmp_texto(c, (CadenaSegura){ .longitud = (int)strlen("\n"), .datos = "\n" }) == 0LL)) {
            if ((num_linea == line_val)) {
                scan = len_doc;
                  /* [Lifetime Scope: exit depth=3] */
            }
            else {
                linea_inicio = (scan + 1LL);
                num_linea = (num_linea + 1LL);
                  /* [Lifetime Scope: exit depth=3] */
            }
              /* [Lifetime Scope: exit depth=2] */
        }
        scan = (scan + 1LL);
          /* [Lifetime Scope: exit depth=1] */
        _syn_texto_liberar(c);
    }
    int64_t linea_fin = len_doc;
    if ((linea_inicio < len_doc)) {
        CadenaSegura busqueda = ((CadenaSegura){.longitud=(len_doc - linea_inicio), .datos=((char*)memcpy(malloc((len_doc - linea_inicio)+1),(doc).datos+linea_inicio,(len_doc - linea_inicio)))});
        int64_t nl_idx = strstr_f(busqueda, (CadenaSegura){ .longitud = (int)strlen("\n"), .datos = "\n" });
        if ((nl_idx >= 0LL)) {
            linea_fin = (linea_inicio + nl_idx);
              /* [Lifetime Scope: exit depth=2] */
        }
          /* [Lifetime Scope: exit depth=1] */
        _syn_texto_liberar(busqueda);
    }
    if ((linea_inicio >= linea_fin)) {
        enviar_respuesta(construir_respuesta(id, (CadenaSegura){ .longitud = (int)strlen("null"), .datos = "null" }));
        #ifndef SYNAPSE_RELEASE
        assert((1) && "Fallo en contrato: garantiza");
        #endif
        return;
          /* [Lifetime Scope: exit depth=1] */
    }
    CadenaSegura linea_texto = ((CadenaSegura){.longitud=(linea_fin - linea_inicio), .datos=((char*)memcpy(malloc((linea_fin - linea_inicio)+1),(doc).datos+linea_inicio,(linea_fin - linea_inicio)))});
    int64_t len_lin = strlen_s(linea_texto);
    if ((char_val >= len_lin)) {
        enviar_respuesta(construir_respuesta(id, (CadenaSegura){ .longitud = (int)strlen("null"), .datos = "null" }));
        #ifndef SYNAPSE_RELEASE
        assert((1) && "Fallo en contrato: garantiza");
        #endif
        _syn_texto_liberar(linea_texto);
        return;
          /* [Lifetime Scope: exit depth=1] */
    }
    CadenaSegura palabra = palabra_en_posicion(linea_texto, char_val);
    if ((strlen_s(palabra) == 0LL)) {
        enviar_respuesta(construir_respuesta(id, (CadenaSegura){ .longitud = (int)strlen("null"), .datos = "null" }));
        #ifndef SYNAPSE_RELEASE
        assert((1) && "Fallo en contrato: garantiza");
        #endif
        _syn_texto_liberar(palabra);
        return;
          /* [Lifetime Scope: exit depth=1] */
    }
    CadenaSegura patron_func = concat(concat((CadenaSegura){ .longitud = (int)strlen("funcion "), .datos = "funcion " }, palabra), (CadenaSegura){ .longitud = (int)strlen("("), .datos = "(" });
    int64_t func_idx = strstr_f(doc, patron_func);
    if ((func_idx >= 0LL)) {
        int64_t def_linea = linea_de_posicion(doc, func_idx);
        int64_t def_lin_inicio = func_idx;
        while ((def_lin_inicio > 0LL)) {
            CadenaSegura c = ((CadenaSegura){.longitud=1LL, .datos=((char*)memcpy(malloc(1LL+1),(doc).datos+(def_lin_inicio - 1LL),1LL))});
            if ((cmp_texto(c, (CadenaSegura){ .longitud = (int)strlen("\n"), .datos = "\n" }) == 0LL)) {
                break;
                  /* [Lifetime Scope: exit depth=3] */
            }
            def_lin_inicio = (def_lin_inicio - 1LL);
              /* [Lifetime Scope: exit depth=2] */
            _syn_texto_liberar(c);
        }
        int64_t def_lin_fin = ((func_idx + strlen_s(palabra)) + 8LL);
        while ((def_lin_fin < len_doc)) {
            CadenaSegura c = ((CadenaSegura){.longitud=1LL, .datos=((char*)memcpy(malloc(1LL+1),(doc).datos+def_lin_fin,1LL))});
            if ((cmp_texto(c, (CadenaSegura){ .longitud = (int)strlen("\n"), .datos = "\n" }) == 0LL)) {
                break;
                  /* [Lifetime Scope: exit depth=3] */
            }
            def_lin_fin = (def_lin_fin + 1LL);
              /* [Lifetime Scope: exit depth=2] */
            _syn_texto_liberar(c);
        }
        CadenaSegura firma = ((CadenaSegura){.longitud=(def_lin_fin - def_lin_inicio), .datos=((char*)memcpy(malloc((def_lin_fin - def_lin_inicio)+1),(doc).datos+def_lin_inicio,(def_lin_fin - def_lin_inicio)))});
        CadenaSegura result = concat(concat((CadenaSegura){ .longitud = (int)strlen("{\"contents\":{\"kind\":\"markdown\",\"value\":\"**funcion** `"), .datos = "{\"contents\":{\"kind\":\"markdown\",\"value\":\"**funcion** `" }, escapar_json(firma)), (CadenaSegura){ .longitud = (int)strlen("\"}}"), .datos = "\"}}" });
        enviar_respuesta(construir_respuesta(id, result));
        #ifndef SYNAPSE_RELEASE
        assert((1) && "Fallo en contrato: garantiza");
        #endif
        _syn_texto_liberar(result);
        _syn_texto_liberar(firma);
        _syn_texto_liberar(patron_func);
        return;
          /* [Lifetime Scope: exit depth=1] */
    }
    CadenaSegura patron_var1 = concat(palabra, (CadenaSegura){ .longitud = (int)strlen(" = "), .datos = " = " });
    CadenaSegura patron_var2 = concat(concat((CadenaSegura){ .longitud = (int)strlen("let "), .datos = "let " }, palabra), (CadenaSegura){ .longitud = (int)strlen(" = "), .datos = " = " });
    int64_t var_idx1 = strstr_f(doc, patron_var1);
    int64_t var_idx2 = strstr_f(doc, patron_var2);
    int64_t var_idx = (-1LL);
    if ((var_idx1 >= 0LL)) {
        var_idx = var_idx1;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((var_idx2 >= 0LL)) {
        if ((var_idx < 0LL)) {
            var_idx = var_idx2;
              /* [Lifetime Scope: exit depth=2] */
        }
        else {
            if ((var_idx2 < var_idx)) {
                var_idx = var_idx2;
                  /* [Lifetime Scope: exit depth=3] */
            }
              /* [Lifetime Scope: exit depth=2] */
        }
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((var_idx >= 0LL)) {
        CadenaSegura tipo = lsp_get_enclosing_return_type(palabra);
        if ((strlen_s(tipo) > 0LL)) {
            CadenaSegura result = concat(concat(concat(concat((CadenaSegura){ .longitud = (int)strlen("{\"contents\":{\"kind\":\"markdown\",\"value\":\"**variable** `"), .datos = "{\"contents\":{\"kind\":\"markdown\",\"value\":\"**variable** `" }, palabra), (CadenaSegura){ .longitud = (int)strlen("` : `"), .datos = "` : `" }), tipo), (CadenaSegura){ .longitud = (int)strlen("`\"}}"), .datos = "`\"}}" });
            enviar_respuesta(construir_respuesta(id, result));
            #ifndef SYNAPSE_RELEASE
            assert((1) && "Fallo en contrato: garantiza");
            #endif
            _syn_texto_liberar(result);
            _syn_texto_liberar(tipo);
            _syn_texto_liberar(patron_var2);
            _syn_texto_liberar(patron_var1);
            return;
              /* [Lifetime Scope: exit depth=2] */
        }
        CadenaSegura result = concat(concat((CadenaSegura){ .longitud = (int)strlen("{\"contents\":{\"kind\":\"markdown\",\"value\":\"**variable** `"), .datos = "{\"contents\":{\"kind\":\"markdown\",\"value\":\"**variable** `" }, palabra), (CadenaSegura){ .longitud = (int)strlen("\"}}"), .datos = "\"}}" });
        enviar_respuesta(construir_respuesta(id, result));
        #ifndef SYNAPSE_RELEASE
        assert((1) && "Fallo en contrato: garantiza");
        #endif
        _syn_texto_liberar(result);
        return;
          /* [Lifetime Scope: exit depth=1] */
    }
    enviar_respuesta(construir_respuesta(id, (CadenaSegura){ .longitud = (int)strlen("null"), .datos = "null" }));
      /* [Lifetime Scope: exit depth=0] */
}

void handle_initialize(int64_t id) {
    #ifndef SYNAPSE_RELEASE
    assert(((id >= 0LL)) && "Fallo en contrato: requiere");
    #endif
    CadenaSegura caps = (CadenaSegura){ .longitud = (int)strlen("{\"textDocumentSync\":{\"openClose\":true,\"change\":1,\"save\":{\"includeText\":true}},\"hoverProvider\":true,\"completionProvider\":{\"triggerCharacters\":[\".\",\":\",\"(\"]},\"definitionProvider\":true,\"codeActionProvider\":true,\"documentFormattingProvider\":true,\"signatureHelpProvider\":{\"triggerCharacters\":[\"(\",\",\"],\"workspace\":{\"didChangeConfiguration\":{\"supported\":true}}}}"), .datos = "{\"textDocumentSync\":{\"openClose\":true,\"change\":1,\"save\":{\"includeText\":true}},\"hoverProvider\":true,\"completionProvider\":{\"triggerCharacters\":[\".\",\":\",\"(\"]},\"definitionProvider\":true,\"codeActionProvider\":true,\"documentFormattingProvider\":true,\"signatureHelpProvider\":{\"triggerCharacters\":[\"(\",\",\"],\"workspace\":{\"didChangeConfiguration\":{\"supported\":true}}}}" };
    CadenaSegura server_info = (CadenaSegura){ .longitud = (int)strlen("{\"name\":\"synapse-lsp-native\",\"version\":\"0.3.0\"}"), .datos = "{\"name\":\"synapse-lsp-native\",\"version\":\"0.3.0\"}" };
    CadenaSegura result = concat(concat(concat(concat((CadenaSegura){ .longitud = (int)strlen("{\"capabilities\":"), .datos = "{\"capabilities\":" }, caps), (CadenaSegura){ .longitud = (int)strlen(",\"serverInfo\":"), .datos = ",\"serverInfo\":" }), server_info), (CadenaSegura){ .longitud = (int)strlen("}"), .datos = "}" });
    enviar_respuesta(construir_respuesta(id, result));
      /* [Lifetime Scope: exit depth=0] */
    _syn_texto_liberar(server_info);
    _syn_texto_liberar(result);
    _syn_texto_liberar(caps);
}

void handle_shutdown(int64_t id) {
    // cumple Manual 8 §1.4: shutdown acepta id (request) o sin id (notification)
    int64_t rid = (id >= 0LL) ? id : 0LL;
    enviar_respuesta(concat(concat((CadenaSegura){ .longitud = (int)strlen("{\"jsonrpc\":\"2.0\",\"id\":"), .datos = "{\"jsonrpc\":\"2.0\",\"id\":" }, a_texto(rid)), (CadenaSegura){ .longitud = (int)strlen(",\"result\":null}"), .datos = ",\"result\":null}" }));
      /* [Lifetime Scope: exit depth=0] */
}

void handle_signature_help(int64_t id, CadenaSegura doc, CadenaSegura params) {
    #ifndef SYNAPSE_RELEASE
    assert(((id >= 0LL)) && "Fallo en contrato: requiere");
    #endif
    int64_t pos_idx = strstr_f(params, (CadenaSegura){ .longitud = (int)strlen("\"position\""), .datos = "\"position\"" });
    if ((pos_idx == (-1LL))) {
        enviar_respuesta(construir_respuesta(id, (CadenaSegura){ .longitud = (int)strlen("{\"signatures\":[]}"), .datos = "{\"signatures\":[]}" }));
        #ifndef SYNAPSE_RELEASE
        assert((1) && "Fallo en contrato: garantiza");
        #endif
        _syn_texto_liberar(params);
        _syn_texto_liberar(doc);
        return;
          /* [Lifetime Scope: exit depth=1] */
    }
    int64_t len_params = strlen_s(params);
    int64_t line_idx = strstr_f(((CadenaSegura){.longitud=(len_params - pos_idx), .datos=((char*)memcpy(malloc((len_params - pos_idx)+1),(params).datos+pos_idx,(len_params - pos_idx)))}), (CadenaSegura){ .longitud = (int)strlen("\"line\""), .datos = "\"line\"" });
    if ((line_idx == (-1LL))) {
        enviar_respuesta(construir_respuesta(id, (CadenaSegura){ .longitud = (int)strlen("{\"signatures\":[]}"), .datos = "{\"signatures\":[]}" }));
        #ifndef SYNAPSE_RELEASE
        assert((1) && "Fallo en contrato: garantiza");
        #endif
        return;
          /* [Lifetime Scope: exit depth=1] */
    }
    int64_t abs_line = (pos_idx + line_idx);
    CadenaSegura line_seg = ((CadenaSegura){.longitud=((len_params - abs_line) - 7LL), .datos=((char*)memcpy(malloc(((len_params - abs_line) - 7LL)+1),(params).datos+(abs_line + 7LL),((len_params - abs_line) - 7LL)))});
    int64_t comma_pos = strstr_f(line_seg, (CadenaSegura){ .longitud = (int)strlen(","), .datos = "," });
    if ((comma_pos == (-1LL))) {
        comma_pos = strlen_s(line_seg);
          /* [Lifetime Scope: exit depth=1] */
    }
    int64_t line_val = extraer_entero(((CadenaSegura){.longitud=comma_pos, .datos=((char*)memcpy(malloc(comma_pos+1),(line_seg).datos+0LL,comma_pos))}));
    int64_t len_doc = strlen_s(doc);
    int64_t linea_inicio = 0LL;
    int64_t num_linea = 0LL;
    int64_t scan = 0LL;
    while ((scan < len_doc)) {
        CadenaSegura c = ((CadenaSegura){.longitud=1LL, .datos=((char*)memcpy(malloc(1LL+1),(doc).datos+scan,1LL))});
        if ((cmp_texto(c, (CadenaSegura){ .longitud = (int)strlen("\n"), .datos = "\n" }) == 0LL)) {
            if ((num_linea == line_val)) {
                scan = len_doc;
                  /* [Lifetime Scope: exit depth=3] */
            }
            else {
                linea_inicio = (scan + 1LL);
                num_linea = (num_linea + 1LL);
                  /* [Lifetime Scope: exit depth=3] */
            }
              /* [Lifetime Scope: exit depth=2] */
        }
        scan = (scan + 1LL);
          /* [Lifetime Scope: exit depth=1] */
        _syn_texto_liberar(c);
    }
    int64_t linea_fin = len_doc;
    if ((linea_inicio < len_doc)) {
        CadenaSegura busqueda = ((CadenaSegura){.longitud=(len_doc - linea_inicio), .datos=((char*)memcpy(malloc((len_doc - linea_inicio)+1),(doc).datos+linea_inicio,(len_doc - linea_inicio)))});
        int64_t nl_idx = strstr_f(busqueda, (CadenaSegura){ .longitud = (int)strlen("\n"), .datos = "\n" });
        if ((nl_idx >= 0LL)) {
            linea_fin = (linea_inicio + nl_idx);
              /* [Lifetime Scope: exit depth=2] */
        }
          /* [Lifetime Scope: exit depth=1] */
        _syn_texto_liberar(busqueda);
    }
    if ((linea_inicio >= linea_fin)) {
        enviar_respuesta(construir_respuesta(id, (CadenaSegura){ .longitud = (int)strlen("{\"signatures\":[]}"), .datos = "{\"signatures\":[]}" }));
        #ifndef SYNAPSE_RELEASE
        assert((1) && "Fallo en contrato: garantiza");
        #endif
        _syn_texto_liberar(line_seg);
        return;
          /* [Lifetime Scope: exit depth=1] */
    }
    CadenaSegura linea_texto = ((CadenaSegura){.longitud=(linea_fin - linea_inicio), .datos=((char*)memcpy(malloc((linea_fin - linea_inicio)+1),(doc).datos+linea_inicio,(linea_fin - linea_inicio)))});
    int64_t char_idx = strstr_f(((CadenaSegura){.longitud=(len_params - pos_idx), .datos=((char*)memcpy(malloc((len_params - pos_idx)+1),(params).datos+pos_idx,(len_params - pos_idx)))}), (CadenaSegura){ .longitud = (int)strlen("\"character\""), .datos = "\"character\"" });
    if ((char_idx == (-1LL))) {
        enviar_respuesta(construir_respuesta(id, (CadenaSegura){ .longitud = (int)strlen("{\"signatures\":[]}"), .datos = "{\"signatures\":[]}" }));
        #ifndef SYNAPSE_RELEASE
        assert((1) && "Fallo en contrato: garantiza");
        #endif
        _syn_texto_liberar(linea_texto);
        return;
          /* [Lifetime Scope: exit depth=1] */
    }
    int64_t abs_char = (pos_idx + char_idx);
    CadenaSegura char_seg = ((CadenaSegura){.longitud=((len_params - abs_char) - 12LL), .datos=((char*)memcpy(malloc(((len_params - abs_char) - 12LL)+1),(params).datos+(abs_char + 12LL),((len_params - abs_char) - 12LL)))});
    int64_t brace_pos = strstr_f(char_seg, (CadenaSegura){ .longitud = (int)strlen("}"), .datos = "}" });
    if ((brace_pos == (-1LL))) {
        brace_pos = strlen_s(char_seg);
          /* [Lifetime Scope: exit depth=1] */
    }
    int64_t char_val = extraer_entero(((CadenaSegura){.longitud=brace_pos, .datos=((char*)memcpy(malloc(brace_pos+1),(char_seg).datos+0LL,brace_pos))}));
    int64_t paren_pos = (-1LL);
    int64_t scan2 = char_val;
    while ((scan2 > 0LL)) {
        CadenaSegura cc = ((CadenaSegura){.longitud=1LL, .datos=((char*)memcpy(malloc(1LL+1),(linea_texto).datos+scan2,1LL))});
        if ((cmp_texto(cc, (CadenaSegura){ .longitud = (int)strlen("("), .datos = "(" }) == 0LL)) {
            paren_pos = scan2;
            scan2 = 0LL;
              /* [Lifetime Scope: exit depth=2] */
        }
        else {
            if ((cmp_texto(cc, (CadenaSegura){ .longitud = (int)strlen(")"), .datos = ")" }) == 0LL)) {
                scan2 = (scan2 - 1LL);
                  /* [Lifetime Scope: exit depth=3] */
            }
            else {
                scan2 = (scan2 - 1LL);
                  /* [Lifetime Scope: exit depth=3] */
            }
              /* [Lifetime Scope: exit depth=2] */
        }
          /* [Lifetime Scope: exit depth=1] */
        _syn_texto_liberar(cc);
    }
    if ((paren_pos == (-1LL))) {
        enviar_respuesta(construir_respuesta(id, (CadenaSegura){ .longitud = (int)strlen("{\"signatures\":[]}"), .datos = "{\"signatures\":[]}" }));
        #ifndef SYNAPSE_RELEASE
        assert((1) && "Fallo en contrato: garantiza");
        #endif
        _syn_texto_liberar(char_seg);
        return;
          /* [Lifetime Scope: exit depth=1] */
    }
    int64_t nombre_inicio = paren_pos;
    while ((nombre_inicio > 0LL)) {
        CadenaSegura cc = ((CadenaSegura){.longitud=1LL, .datos=((char*)memcpy(malloc(1LL+1),(linea_texto).datos+(nombre_inicio - 1LL),1LL))});
        if ((cmp_texto(cc, (CadenaSegura){ .longitud = (int)strlen(" "), .datos = " " }) == 0LL)) {
            break;
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((cmp_texto(cc, (CadenaSegura){ .longitud = (int)strlen("\t"), .datos = "\t" }) == 0LL)) {
            break;
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((cmp_texto(cc, (CadenaSegura){ .longitud = (int)strlen("="), .datos = "=" }) == 0LL)) {
            break;
              /* [Lifetime Scope: exit depth=2] */
        }
        nombre_inicio = (nombre_inicio - 1LL);
          /* [Lifetime Scope: exit depth=1] */
        _syn_texto_liberar(cc);
    }
    if ((nombre_inicio >= paren_pos)) {
        enviar_respuesta(construir_respuesta(id, (CadenaSegura){ .longitud = (int)strlen("{\"signatures\":[]}"), .datos = "{\"signatures\":[]}" }));
        #ifndef SYNAPSE_RELEASE
        assert((1) && "Fallo en contrato: garantiza");
        #endif
        return;
          /* [Lifetime Scope: exit depth=1] */
    }
    CadenaSegura nombre_func = ((CadenaSegura){.longitud=(paren_pos - nombre_inicio), .datos=((char*)memcpy(malloc((paren_pos - nombre_inicio)+1),(linea_texto).datos+nombre_inicio,(paren_pos - nombre_inicio)))});
    if ((strlen_s(nombre_func) == 0LL)) {
        enviar_respuesta(construir_respuesta(id, (CadenaSegura){ .longitud = (int)strlen("{\"signatures\":[]}"), .datos = "{\"signatures\":[]}" }));
        #ifndef SYNAPSE_RELEASE
        assert((1) && "Fallo en contrato: garantiza");
        #endif
        _syn_texto_liberar(nombre_func);
        return;
          /* [Lifetime Scope: exit depth=1] */
    }
    CadenaSegura patron = concat(concat((CadenaSegura){ .longitud = (int)strlen("funcion "), .datos = "funcion " }, nombre_func), (CadenaSegura){ .longitud = (int)strlen("("), .datos = "(" });
    int64_t def_idx = strstr_f(doc, patron);
    if ((def_idx == (-1LL))) {
        enviar_respuesta(construir_respuesta(id, (CadenaSegura){ .longitud = (int)strlen("{\"signatures\":[]}"), .datos = "{\"signatures\":[]}" }));
        #ifndef SYNAPSE_RELEASE
        assert((1) && "Fallo en contrato: garantiza");
        #endif
        _syn_texto_liberar(patron);
        return;
          /* [Lifetime Scope: exit depth=1] */
    }
    int64_t firma_inicio = def_idx;
    int64_t firma_fin = (def_idx + strlen_s(patron));
    while ((firma_fin < len_doc)) {
        CadenaSegura cc = ((CadenaSegura){.longitud=1LL, .datos=((char*)memcpy(malloc(1LL+1),(doc).datos+firma_fin,1LL))});
        if ((cmp_texto(cc, (CadenaSegura){ .longitud = (int)strlen(")"), .datos = ")" }) == 0LL)) {
            firma_fin = (firma_fin + 1LL);
            break;
              /* [Lifetime Scope: exit depth=2] */
        }
        firma_fin = (firma_fin + 1LL);
          /* [Lifetime Scope: exit depth=1] */
        _syn_texto_liberar(cc);
    }
    CadenaSegura firma = ((CadenaSegura){.longitud=(firma_fin - firma_inicio), .datos=((char*)memcpy(malloc((firma_fin - firma_inicio)+1),(doc).datos+firma_inicio,(firma_fin - firma_inicio)))});
    CadenaSegura sig = concat(concat(concat(concat((CadenaSegura){ .longitud = (int)strlen("{\"label\":\""), .datos = "{\"label\":\"" }, escapar_json(nombre_func)), (CadenaSegura){ .longitud = (int)strlen("\",\"documentation\":\""), .datos = "\",\"documentation\":\"" }), escapar_json(firma)), (CadenaSegura){ .longitud = (int)strlen("\"}"), .datos = "\"}" });
    enviar_respuesta(construir_respuesta(id, concat(concat((CadenaSegura){ .longitud = (int)strlen("{\"signatures\":["), .datos = "{\"signatures\":[" }, sig), (CadenaSegura){ .longitud = (int)strlen("]}"), .datos = "]}" })));
      /* [Lifetime Scope: exit depth=0] */
    _syn_texto_liberar(sig);
    _syn_texto_liberar(firma);
}

void handle_unknown(int64_t id) {
    #ifndef SYNAPSE_RELEASE
    assert(((id >= 0LL)) && "Fallo en contrato: requiere");
    #endif
    enviar_respuesta(construir_error(id, (-32601LL), (CadenaSegura){ .longitud = (int)strlen("Method not found"), .datos = "Method not found" }));
      /* [Lifetime Scope: exit depth=0] */
}

CadenaSegura json_string(CadenaSegura valor) {
    #ifndef SYNAPSE_RELEASE
    assert((1) && "Fallo en contrato: requiere");
    #endif
    CadenaSegura escaped = escapar_json(valor);
    CadenaSegura _resultado_ = concat(concat((CadenaSegura){ .longitud = (int)strlen("\""), .datos = "\"" }, escaped), (CadenaSegura){ .longitud = (int)strlen("\""), .datos = "\"" });
    #ifndef SYNAPSE_RELEASE
    assert(((strlen_s(_resultado_) >= 2LL)) && "Fallo en contrato: garantiza");
    #endif
    _syn_texto_liberar(valor);
    _syn_texto_liberar(escaped);
    return _resultado_;
      /* [Lifetime Scope: exit depth=0] */
}

int64_t leer_cabecera(void) {
    #ifndef SYNAPSE_RELEASE
    assert((1) && "Fallo en contrato: requiere");
    #endif
    int64_t content_length = (-1LL);
    while (1) {
        CadenaSegura linea = leer_linea();
        if ((str_eq(linea, (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" }) == 1)) {
            break;
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((str_eq(linea, (CadenaSegura){ .longitud = (int)strlen("\r"), .datos = "\r" }) == 1)) {
            break;
              /* [Lifetime Scope: exit depth=2] */
        }
        int64_t idx = strstr_f(linea, (CadenaSegura){ .longitud = (int)strlen("Content-Length:"), .datos = "Content-Length:" });
        if ((idx == (-1LL))) {
            idx = strstr_f(linea, (CadenaSegura){ .longitud = (int)strlen("content-length:"), .datos = "content-length:" });
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((idx >= 0LL)) {
            int64_t despues = (idx + 15LL);
            int64_t len_total = strlen_s(linea);
            int64_t pos_num = despues;
            while ((pos_num < len_total)) {
                CadenaSegura c = ((CadenaSegura){.longitud=1LL, .datos=((char*)memcpy(malloc(1LL+1),(linea).datos+pos_num,1LL))});
                if ((cmp_texto(c, (CadenaSegura){ .longitud = (int)strlen(" "), .datos = " " }) != 0LL)) {
                    break;
                      /* [Lifetime Scope: exit depth=4] */
                }
                pos_num = (pos_num + 1LL);
                  /* [Lifetime Scope: exit depth=3] */
                _syn_texto_liberar(c);
            }
            int64_t fin_num = strlen_s(linea);
            CadenaSegura busqueda_resto = ((CadenaSegura){.longitud=(fin_num - pos_num), .datos=((char*)memcpy(malloc((fin_num - pos_num)+1),(linea).datos+pos_num,(fin_num - pos_num)))});
            int64_t cr_idx = strstr_f(busqueda_resto, (CadenaSegura){ .longitud = (int)strlen("\r"), .datos = "\r" });
            if ((cr_idx >= 0LL)) {
                fin_num = (pos_num + cr_idx);
                  /* [Lifetime Scope: exit depth=3] */
            }
            int64_t num_len = (fin_num - pos_num);
            if ((num_len > 0LL)) {
                CadenaSegura num_text = ((CadenaSegura){.longitud=num_len, .datos=((char*)memcpy(malloc(num_len+1),(linea).datos+pos_num,num_len))});
                content_length = extraer_entero(num_text);
                  /* [Lifetime Scope: exit depth=3] */
                _syn_texto_liberar(num_text);
            }
              /* [Lifetime Scope: exit depth=2] */
            _syn_texto_liberar(busqueda_resto);
        }
          /* [Lifetime Scope: exit depth=1] */
        _syn_texto_liberar(linea);
    }
    int64_t _resultado_ = content_length;
    #ifndef SYNAPSE_RELEASE
    assert(((_resultado_ >= (-1LL))) && "Fallo en contrato: garantiza");
    #endif
    return _resultado_;
      /* [Lifetime Scope: exit depth=0] */
}

CadenaSegura leer_mensaje(int64_t cantidad) {
    #ifndef SYNAPSE_RELEASE
    assert(((cantidad >= 0LL)) && "Fallo en contrato: requiere");
    #endif
    if ((cantidad <= 0LL)) {
        CadenaSegura _resultado_ = (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
        #ifndef SYNAPSE_RELEASE
        assert((1) && "Fallo en contrato: garantiza");
        #endif
        return _resultado_;
          /* [Lifetime Scope: exit depth=1] */
    }
    CadenaSegura _resultado_ = leer_bytes(cantidad);
    #ifndef SYNAPSE_RELEASE
    assert((1) && "Fallo en contrato: garantiza");
    #endif
    return _resultado_;
      /* [Lifetime Scope: exit depth=0] */
}

int64_t linea_de_posicion(CadenaSegura doc, int64_t pos) {
    #ifndef SYNAPSE_RELEASE
    assert(((pos >= 0LL)) && "Fallo en contrato: requiere");
    #endif
    int64_t num = 0LL;
    int64_t i = 0LL;
    while ((i < pos)) {
        CadenaSegura c = ((CadenaSegura){.longitud=1LL, .datos=((char*)memcpy(malloc(1LL+1),(doc).datos+i,1LL))});
        if ((cmp_texto(c, (CadenaSegura){ .longitud = (int)strlen("\n"), .datos = "\n" }) == 0LL)) {
            num = (num + 1LL);
              /* [Lifetime Scope: exit depth=2] */
        }
        i = (i + 1LL);
          /* [Lifetime Scope: exit depth=1] */
        _syn_texto_liberar(c);
    }
    int64_t _resultado_ = num;
    #ifndef SYNAPSE_RELEASE
    assert(((_resultado_ >= 0LL)) && "Fallo en contrato: garantiza");
    #endif
    _syn_texto_liberar(doc);
    return _resultado_;
      /* [Lifetime Scope: exit depth=0] */
}

CadenaSegura palabra_en_posicion(CadenaSegura linea, int64_t pos) {
    #ifndef SYNAPSE_RELEASE
    assert(((pos >= 0LL)) && "Fallo en contrato: requiere");
    #endif
    int64_t len_lin = strlen_s(linea);
    if ((pos >= len_lin)) {
        CadenaSegura _resultado_ = (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
        #ifndef SYNAPSE_RELEASE
        assert((1) && "Fallo en contrato: garantiza");
        #endif
        _syn_texto_liberar(linea);
        return _resultado_;
          /* [Lifetime Scope: exit depth=1] */
    }
    int64_t word_start = pos;
    while ((word_start > 0LL)) {
        CadenaSegura c = ((CadenaSegura){.longitud=1LL, .datos=((char*)memcpy(malloc(1LL+1),(linea).datos+(word_start - 1LL),1LL))});
        if ((cmp_texto(c, (CadenaSegura){ .longitud = (int)strlen(" "), .datos = " " }) == 0LL)) {
            break;
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((cmp_texto(c, (CadenaSegura){ .longitud = (int)strlen("("), .datos = "(" }) == 0LL)) {
            break;
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((cmp_texto(c, (CadenaSegura){ .longitud = (int)strlen(")"), .datos = ")" }) == 0LL)) {
            break;
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((cmp_texto(c, (CadenaSegura){ .longitud = (int)strlen(","), .datos = "," }) == 0LL)) {
            break;
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((cmp_texto(c, (CadenaSegura){ .longitud = (int)strlen(":"), .datos = ":" }) == 0LL)) {
            break;
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((cmp_texto(c, (CadenaSegura){ .longitud = (int)strlen("="), .datos = "=" }) == 0LL)) {
            break;
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((cmp_texto(c, (CadenaSegura){ .longitud = (int)strlen("\t"), .datos = "\t" }) == 0LL)) {
            break;
              /* [Lifetime Scope: exit depth=2] */
        }
        word_start = (word_start - 1LL);
          /* [Lifetime Scope: exit depth=1] */
        _syn_texto_liberar(c);
    }
    int64_t word_end = pos;
    while ((word_end < len_lin)) {
        CadenaSegura c = ((CadenaSegura){.longitud=1LL, .datos=((char*)memcpy(malloc(1LL+1),(linea).datos+word_end,1LL))});
        if ((cmp_texto(c, (CadenaSegura){ .longitud = (int)strlen(" "), .datos = " " }) == 0LL)) {
            break;
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((cmp_texto(c, (CadenaSegura){ .longitud = (int)strlen("("), .datos = "(" }) == 0LL)) {
            break;
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((cmp_texto(c, (CadenaSegura){ .longitud = (int)strlen(")"), .datos = ")" }) == 0LL)) {
            break;
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((cmp_texto(c, (CadenaSegura){ .longitud = (int)strlen(","), .datos = "," }) == 0LL)) {
            break;
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((cmp_texto(c, (CadenaSegura){ .longitud = (int)strlen(":"), .datos = ":" }) == 0LL)) {
            break;
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((cmp_texto(c, (CadenaSegura){ .longitud = (int)strlen("="), .datos = "=" }) == 0LL)) {
            break;
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((cmp_texto(c, (CadenaSegura){ .longitud = (int)strlen("\t"), .datos = "\t" }) == 0LL)) {
            break;
              /* [Lifetime Scope: exit depth=2] */
        }
        word_end = (word_end + 1LL);
          /* [Lifetime Scope: exit depth=1] */
        _syn_texto_liberar(c);
    }
    if ((word_end <= word_start)) {
        CadenaSegura _resultado_ = (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
        #ifndef SYNAPSE_RELEASE
        assert((1) && "Fallo en contrato: garantiza");
        #endif
        return _resultado_;
          /* [Lifetime Scope: exit depth=1] */
    }
    int64_t word_len = (word_end - word_start);
    CadenaSegura _resultado_ = ((CadenaSegura){.longitud=word_len, .datos=((char*)memcpy(malloc(word_len+1),(linea).datos+word_start,word_len))});
    #ifndef SYNAPSE_RELEASE
    assert((1) && "Fallo en contrato: garantiza");
    #endif
    return _resultado_;
      /* [Lifetime Scope: exit depth=0] */
}

int64_t _principal_impl(void) {
    _simd_detectar();
    int64_t ejecutando = 1LL;
    CadenaSegura uri_actual = (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
    while ((ejecutando == 1LL)) {
        int64_t content_length = leer_cabecera();
        if ((content_length <= 0LL)) {
            break;
              /* [Lifetime Scope: exit depth=2] */
        }
        CadenaSegura body = leer_mensaje(content_length);
        if ((strlen_s(body) == 0LL)) {
            break;
              /* [Lifetime Scope: exit depth=2] */
        }
        int64_t id_val = (-1LL);
        int64_t method_handled = 0LL;
        CadenaSegura patron_id = (CadenaSegura){ .longitud = (int)strlen("\"id\":"), .datos = "\"id\":" };
        int64_t patron_len_id = 5LL;
        int64_t body_len = strlen_s(body);
        int64_t idx_id = strstr_f(body, patron_id);
        if ((idx_id >= 0LL)) {
            int64_t id_start = (idx_id + patron_len_id);
            int64_t id_pos = id_start;
            while ((id_pos < body_len)) {
                CadenaSegura c = ((CadenaSegura){.longitud=1LL, .datos=((char*)memcpy(malloc(1LL+1),(body).datos+id_pos,1LL))});
                if ((cmp_texto(c, (CadenaSegura){ .longitud = (int)strlen(" "), .datos = " " }) != 0LL)) {
                    break;
                      /* [Lifetime Scope: exit depth=4] */
                }
                id_pos = (id_pos + 1LL);
                  /* [Lifetime Scope: exit depth=3] */
                _syn_texto_liberar(c);
            }
            int64_t id_fin = id_pos;
            while ((id_fin < body_len)) {
                CadenaSegura c = ((CadenaSegura){.longitud=1LL, .datos=((char*)memcpy(malloc(1LL+1),(body).datos+id_fin,1LL))});
                if ((cmp_texto(c, (CadenaSegura){ .longitud = (int)strlen("0"), .datos = "0" }) >= 0LL)) {
                    if ((cmp_texto(c, (CadenaSegura){ .longitud = (int)strlen("9"), .datos = "9" }) <= 0LL)) {
                        id_fin = (id_fin + 1LL);
                          /* [Lifetime Scope: exit depth=5] */
                    }
                    else {
                        break;
                          /* [Lifetime Scope: exit depth=5] */
                    }
                      /* [Lifetime Scope: exit depth=4] */
                }
                else {
                    if ((cmp_texto(c, (CadenaSegura){ .longitud = (int)strlen("-"), .datos = "-" }) == 0LL)) {
                        if ((id_fin == id_pos)) {
                            id_fin = (id_fin + 1LL);
                              /* [Lifetime Scope: exit depth=6] */
                        }
                        else {
                            break;
                              /* [Lifetime Scope: exit depth=6] */
                        }
                          /* [Lifetime Scope: exit depth=5] */
                    }
                    else {
                        break;
                          /* [Lifetime Scope: exit depth=5] */
                    }
                      /* [Lifetime Scope: exit depth=4] */
                }
                  /* [Lifetime Scope: exit depth=3] */
                _syn_texto_liberar(c);
            }
            if ((id_fin > id_pos)) {
                id_val = extraer_entero(((CadenaSegura){.longitud=(id_fin - id_pos), .datos=((char*)memcpy(malloc((id_fin - id_pos)+1),(body).datos+id_pos,(id_fin - id_pos)))}));
                  /* [Lifetime Scope: exit depth=3] */
            }
              /* [Lifetime Scope: exit depth=2] */
        }
        struct NodoJson msg = desde_texto(body);
        struct NodoJson method_nodo = obtener_campo(msg, (CadenaSegura){ .longitud = (int)strlen("method"), .datos = "method" });
        CadenaSegura method_str = strcpy_f(_json_a_texto(method_nodo));
        struct NodoJson params_nodo = obtener_campo(msg, (CadenaSegura){ .longitud = (int)strlen("params"), .datos = "params" });
        CadenaSegura params_str = strcpy_f(_json_a_texto(params_nodo));
        if ((cmp_texto(method_str, (CadenaSegura){ .longitud = (int)strlen("\"initialize\""), .datos = "\"initialize\"" }) == 0LL)) {
            handle_initialize(id_val);
            method_handled = 1LL;
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((cmp_texto(method_str, (CadenaSegura){ .longitud = (int)strlen("\"shutdown\""), .datos = "\"shutdown\"" }) == 0LL)) {
            handle_shutdown(id_val);
            method_handled = 1LL;
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((cmp_texto(method_str, (CadenaSegura){ .longitud = (int)strlen("\"exit\""), .datos = "\"exit\"" }) == 0LL)) {
            if ((id_val >= 0LL)) {
                handle_unknown(id_val);
                  /* [Lifetime Scope: exit depth=3] */
            }
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((cmp_texto(method_str, (CadenaSegura){ .longitud = (int)strlen("\"textDocument/didOpen\""), .datos = "\"textDocument/didOpen\"" }) == 0LL)) {
            _syn_texto_liberar(uri_actual);
            uri_actual = strcpy_f(extraer_uri(params_str));
            CadenaSegura doc_abierto = extraer_texto_doc(params_str);
            lsp_doc_store(doc_abierto);
            // cumple Manual 8 §1.4: publishDiagnostics con check #lang
            int _tiene_lang_o = 0;
            if (doc_abierto.datos && doc_abierto.longitud >= 5) {
                for (int _lio = 0; _lio < doc_abierto.longitud && _lio < 200; _lio++) {
                    if (doc_abierto.datos[_lio] == '#') {
                        if (_lio + 5 <= doc_abierto.longitud &&
                            doc_abierto.datos[_lio+1] == 'l' && doc_abierto.datos[_lio+2] == 'a' &&
                            doc_abierto.datos[_lio+3] == 'n' && doc_abierto.datos[_lio+4] == 'g') {
                            _tiene_lang_o = 1;
                            break;
                        }
                    }
                    if (doc_abierto.datos[_lio] == '\n') break;
                }
            }
            char _diag_buf_o[1024];
            if (!_tiene_lang_o && doc_abierto.datos && doc_abierto.longitud > 0) {
                CadenaSegura uri_esc_o = json_string(uri_actual);
                char _err_msg_o[] = "Falta declaracion de idioma '#lang: <codigo>' en la linea 1";
                snprintf(_diag_buf_o, sizeof(_diag_buf_o),
                    "{\"uri\":%.*s,\"diagnostics\":[{\"range\":{\"start\":{\"line\":0,\"character\":0},\"end\":{\"line\":0,\"character\":0}},\"severity\":1,\"code\":\"ERR_LANG_MISSING\",\"message\":\"%s\"}]}",
                    uri_esc_o.longitud, uri_esc_o.datos ? uri_esc_o.datos : "\"\"",
                    _err_msg_o);
            } else {
                CadenaSegura uri_esc_o = json_string(uri_actual);
                snprintf(_diag_buf_o, sizeof(_diag_buf_o),
                    "{\"uri\":%.*s,\"diagnostics\":[]}",
                    uri_esc_o.longitud, uri_esc_o.datos ? uri_esc_o.datos : "\"\"");
            }
            CadenaSegura diag_o = { .longitud = (int)strlen(_diag_buf_o), .datos = _diag_buf_o };
            enviar_respuesta(construir_notificacion((CadenaSegura){ .longitud = (int)strlen("textDocument/publishDiagnostics"), .datos = "textDocument/publishDiagnostics" }, diag_o));
              /* [Lifetime Scope: exit depth=2] */
            _syn_texto_liberar(uri_actual);
        }
        if ((cmp_texto(method_str, (CadenaSegura){ .longitud = (int)strlen("\"textDocument/didChange\""), .datos = "\"textDocument/didChange\"" }) == 0LL)) {            _syn_texto_liberar(uri_actual);
            uri_actual = strcpy_f(extraer_uri(params_str));
            CadenaSegura nuevo_doc = extraer_texto_doc(params_str);
            lsp_doc_store(nuevo_doc);
            // cumple Manual 8 §1.4: publishDiagnostics tras didChange
            int tiene_lang = 0;
            if (nuevo_doc.datos && nuevo_doc.longitud >= 5) {
                for (int _li = 0; _li < nuevo_doc.longitud && _li < 200; _li++) {
                    if (nuevo_doc.datos[_li] == '#') {
                        if (_li + 5 <= nuevo_doc.longitud &&
                            nuevo_doc.datos[_li+1] == 'l' && nuevo_doc.datos[_li+2] == 'a' &&
                            nuevo_doc.datos[_li+3] == 'n' && nuevo_doc.datos[_li+4] == 'g') {
                            tiene_lang = 1;
                            break;
                        }
                    }
                    if (nuevo_doc.datos[_li] == '\n') break;
                }
            }
            // cumple Manual 8 §1.4: publishDiagnostics con ERR_LANG_MISSING
            char _diag_buf[1024];
            if (!tiene_lang && nuevo_doc.datos && nuevo_doc.longitud > 0) {
                CadenaSegura uri_esc = json_string(uri_actual);
                char _err_msg[] = "Falta declaracion de idioma '#lang: <codigo>' en la linea 1";
                snprintf(_diag_buf, sizeof(_diag_buf),
                    "{\"uri\":%.*s,\"diagnostics\":[{\"range\":{\"start\":{\"line\":0,\"character\":0},\"end\":{\"line\":0,\"character\":0}},\"severity\":1,\"code\":\"ERR_LANG_MISSING\",\"message\":\"%s\"}]}",
                    uri_esc.longitud, uri_esc.datos ? uri_esc.datos : "\"\"",
                    _err_msg);
            } else {
                CadenaSegura uri_esc = json_string(uri_actual);
                snprintf(_diag_buf, sizeof(_diag_buf),
                    "{\"uri\":%.*s,\"diagnostics\":[]}",
                    uri_esc.longitud, uri_esc.datos ? uri_esc.datos : "\"\"");
            }
            CadenaSegura diag_payload = { .longitud = (int)strlen(_diag_buf), .datos = _diag_buf };
            enviar_respuesta(construir_notificacion((CadenaSegura){ .longitud = (int)strlen("textDocument/publishDiagnostics"), .datos = "textDocument/publishDiagnostics" }, diag_payload));
              /* [Lifetime Scope: exit depth=2] */
            _syn_texto_liberar(uri_actual);
        }
        if ((cmp_texto(method_str, (CadenaSegura){ .longitud = (int)strlen("\"textDocument/didClose\""), .datos = "\"textDocument/didClose\"" }) == 0LL)) {
            lsp_doc_clear();
            _syn_texto_liberar(uri_actual);
            uri_actual = (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
            CadenaSegura diag = concat(concat((CadenaSegura){ .longitud = (int)strlen("{\"uri\":"), .datos = "{\"uri\":" }, json_string(uri_actual)), (CadenaSegura){ .longitud = (int)strlen(",\"diagnostics\":[]}"), .datos = ",\"diagnostics\":[]}" });
            enviar_respuesta(construir_notificacion((CadenaSegura){ .longitud = (int)strlen("textDocument/publishDiagnostics"), .datos = "textDocument/publishDiagnostics" }, diag));
              /* [Lifetime Scope: exit depth=2] */
            _syn_texto_liberar(uri_actual);
            _syn_texto_liberar(diag);
        }
        if ((cmp_texto(method_str, (CadenaSegura){ .longitud = (int)strlen("\"textDocument/hover\""), .datos = "\"textDocument/hover\"" }) == 0LL)) {
            CadenaSegura doc = reemplazar(lsp_doc_get(), (CadenaSegura){ .longitud = (int)strlen("\\n"), .datos = "\\n" }, (CadenaSegura){ .longitud = (int)strlen("\n"), .datos = "\n" });
            handle_hover(id_val, doc, params_str);
            method_handled = 1LL;
              /* [Lifetime Scope: exit depth=2] */
            _syn_texto_liberar(doc);
        }
        if ((cmp_texto(method_str, (CadenaSegura){ .longitud = (int)strlen("\"textDocument/completion\""), .datos = "\"textDocument/completion\"" }) == 0LL)) {
            CadenaSegura items = lsp_build_completion_items();
            enviar_respuesta(construir_respuesta(id_val, concat(concat((CadenaSegura){ .longitud = (int)strlen("{\"isIncomplete\":false,\"items\":"), .datos = "{\"isIncomplete\":false,\"items\":" }, items), (CadenaSegura){ .longitud = (int)strlen("}"), .datos = "}" })));
            method_handled = 1LL;
              /* [Lifetime Scope: exit depth=2] */
            _syn_texto_liberar(items);
        }
        if ((cmp_texto(method_str, (CadenaSegura){ .longitud = (int)strlen("\"textDocument/definition\""), .datos = "\"textDocument/definition\"" }) == 0LL)) {
            CadenaSegura doc = reemplazar(lsp_doc_get(), (CadenaSegura){ .longitud = (int)strlen("\\n"), .datos = "\\n" }, (CadenaSegura){ .longitud = (int)strlen("\n"), .datos = "\n" });
            handle_definition(id_val, uri_actual, doc, params_str);
            method_handled = 1LL;
              /* [Lifetime Scope: exit depth=2] */
            _syn_texto_liberar(doc);
        }
        if ((cmp_texto(method_str, (CadenaSegura){ .longitud = (int)strlen("\"textDocument/codeAction\""), .datos = "\"textDocument/codeAction\"" }) == 0LL)) {
            CadenaSegura doc = reemplazar(lsp_doc_get(), (CadenaSegura){ .longitud = (int)strlen("\\n"), .datos = "\\n" }, (CadenaSegura){ .longitud = (int)strlen("\n"), .datos = "\n" });
            handle_code_action(id_val, doc, params_str);
            method_handled = 1LL;
              /* [Lifetime Scope: exit depth=2] */
            _syn_texto_liberar(doc);
        }
        if ((cmp_texto(method_str, (CadenaSegura){ .longitud = (int)strlen("\"textDocument/formatting\""), .datos = "\"textDocument/formatting\"" }) == 0LL)) {
            CadenaSegura doc = reemplazar(lsp_doc_get(), (CadenaSegura){ .longitud = (int)strlen("\\n"), .datos = "\\n" }, (CadenaSegura){ .longitud = (int)strlen("\n"), .datos = "\n" });
            handle_formatting(id_val, doc, params_str);
            method_handled = 1LL;
              /* [Lifetime Scope: exit depth=2] */
            _syn_texto_liberar(doc);
        }
        if ((cmp_texto(method_str, (CadenaSegura){ .longitud = (int)strlen("\"textDocument/signatureHelp\""), .datos = "\"textDocument/signatureHelp\"" }) == 0LL)) {
            CadenaSegura doc = reemplazar(lsp_doc_get(), (CadenaSegura){ .longitud = (int)strlen("\\n"), .datos = "\\n" }, (CadenaSegura){ .longitud = (int)strlen("\n"), .datos = "\n" });
            handle_signature_help(id_val, doc, params_str);
            method_handled = 1LL;
              /* [Lifetime Scope: exit depth=2] */
            _syn_texto_liberar(doc);
        }
        if ((cmp_texto(method_str, (CadenaSegura){ .longitud = (int)strlen("\"workspace/didChangeConfiguration\""), .datos = "\"workspace/didChangeConfiguration\"" }) == 0LL)) {
            handle_did_change_configuration(params_str);
            method_handled = 1LL;
              /* [Lifetime Scope: exit depth=2] */
        }
        // cumple Manual 8 §1.4: stubs para comandos IA
        if ((cmp_texto(method_str, (CadenaSegura){ .longitud = (int)strlen("\"synapse/aiComplete\""), .datos = "\"synapse/aiComplete\"" }) == 0LL)) {
            enviar_respuesta(construir_respuesta(id_val, (CadenaSegura){ .longitud = (int)strlen("null"), .datos = "null" }));
            method_handled = 1LL;
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((cmp_texto(method_str, (CadenaSegura){ .longitud = (int)strlen("\"synapse/aiFix\""), .datos = "\"synapse/aiFix\"" }) == 0LL)) {
            enviar_respuesta(construir_respuesta(id_val, (CadenaSegura){ .longitud = (int)strlen("null"), .datos = "null" }));
            method_handled = 1LL;
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((cmp_texto(method_str, (CadenaSegura){ .longitud = (int)strlen("\"synapse/aiTranspile\""), .datos = "\"synapse/aiTranspile\"" }) == 0LL)) {
            enviar_respuesta(construir_respuesta(id_val, (CadenaSegura){ .longitud = (int)strlen("null"), .datos = "null" }));
            method_handled = 1LL;
              /* [Lifetime Scope: exit depth=2] */
        }
        // cumple Manual 8 §1.2: error -32601 para metodo desconocido
        if ((method_handled == 0LL) && (id_val >= 0LL)) {
            enviar_respuesta(concat(concat((CadenaSegura){ .longitud = (int)strlen("{\"jsonrpc\":\"2.0\",\"id\":"), .datos = "{\"jsonrpc\":\"2.0\",\"id\":" }, a_texto(id_val)), (CadenaSegura){ .longitud = (int)strlen(",\"error\":{\"code\":-32601,\"message\":\"Method not found\"}}"), .datos = ",\"error\":{\"code\":-32601,\"message\":\"Method not found\"}}" }));
        }
        liberar_nodo(msg);
          /* [Lifetime Scope: exit depth=1] */
        _syn_texto_liberar(patron_id);
        _syn_texto_liberar(params_str);
        _json_nodo_liberar(params_nodo);
        _json_nodo_liberar(msg);
        _syn_texto_liberar(method_str);
        _json_nodo_liberar(method_nodo);
        _syn_texto_liberar(body);
    }
    return 0LL;
      /* [Lifetime Scope: exit depth=0] */
}

int main(int argc, char** argv) {
    _g_argc = argc;
    _g_argv = argv;
    pool_init(POOL_BLOQUES, TAMANO_BLOQUE);
    _principal_impl();
    synapse_esperar_hilos();
    synapse_esperar_fibras();
    pool_destroy();
    return 0;
}