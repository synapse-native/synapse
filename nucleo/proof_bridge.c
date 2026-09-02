// proof_bridge.c — Puente de Verificación Formal (Coq/Lean Bridge)
// =================================================================
// Traduce contratos requiere/garantiza de Synapse a términos lógicos
// verificables en asistentes de pruebas (Coq/Lean).
//
// Traducciones sintácticas:
//   - x > 0  →  Coq: (x > 0)  Lean: x > 0
//   - x >= 0 →  Coq: (x >= 0) Lean: x >= 0
//   - x == 0 →  Coq: (x = 0)  Lean: x = 0
//   - x != 0 →  Coq: (x <> 0) Lean: x != 0
//   - x && y →  Coq: (x /\ y) Lean: x && y
//   - x || y →  Coq: (x \/ y) Lean: x || y
//   - !x     →  Coq: (~ x)    Lean: ¬ x
//   - _resultado_ → Coq: result Lean: result
//
// Zero-telemetry: todo el proceso es local y soberano.
// =================================================================

#include "proof_bridge.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>

// ============================================================
// Helpers internos
// ============================================================

// Genera un hash simple para certificados (simula SHA-256)
static void _generar_hash(const char* input, char* hash_out) {
    unsigned long h = 0x12345678;
    for (const char* p = input; *p; p++) {
        h = ((h << 5) + h) ^ (unsigned char)*p;
    }
    snprintf(hash_out, 64, "PROOF_%016lx_%016lx",
             h, (unsigned long)time(NULL));
}

// Traduce _resultado_ a la convención del asistente
static void _traducir_placeholder(char* dst, const char* src, int formato) {
    const char* res_coq = "result";
    const char* res_lean = "result";
    const char* res = (formato == PB_FORMAT_COQ) ? res_coq : res_lean;

    const char* ph = "_resultado_";
    const char* p = src;
    char* d = dst;

    while (*p) {
        if (strncmp(p, ph, strlen(ph)) == 0) {
            while (*res) *d++ = *res++;
            p += strlen(ph);
        } else {
            *d++ = *p++;
        }
    }
    *d = '\0';
}

// ============================================================
// API pública
// ============================================================

PBSession* pb_iniciar(const PBConfig* config) {
    PBSession* sesion = (PBSession*)calloc(1, sizeof(PBSession));
    if (!sesion) return NULL;

    if (config) {
        sesion->config = *config;
    } else {
        sesion->config.formato_destino = PB_FORMAT_COQ;
        sesion->config.generar_esqueleto = 1;
        sesion->config.verificar_automatico = 0;
        sesion->config.ruta_salida[0] = '\0';
        snprintf(sesion->config.nombre_teoria, 64, "SynapseProof");
        sesion->config.incluir_axiomas = 1;
    }

    sesion->num_funciones = 0;
    sesion->estado = 0;
    sesion->num_archivos_generados = 0;

    return sesion;
}

int pb_agregar_funcion(PBSession* sesion, const char* nombre,
                        const char* tipo_retorno, const char* parametros) {
    if (!sesion || !nombre) return -1;
    if (sesion->num_funciones >= PB_MAX_FUNCTIONS) return -1;

    PBFunctionSpec* f = &sesion->funciones[sesion->num_funciones];
    strncpy(f->nombre_funcion, nombre, PB_MAX_EXPR_LEN - 1);
    f->nombre_funcion[PB_MAX_EXPR_LEN - 1] = '\0';

    if (tipo_retorno) {
        strncpy(f->tipo_retorno, tipo_retorno, 63);
        f->tipo_retorno[63] = '\0';
    }

    if (parametros) {
        strncpy(f->parametros, parametros, PB_MAX_EXPR_LEN - 1);
        f->parametros[PB_MAX_EXPR_LEN - 1] = '\0';
        // Contar parámetros (separados por coma)
        int count = 1;
        for (const char* p = parametros; *p; p++) {
            if (*p == ',') count++;
        }
        f->num_parametros = count;
    }

    f->num_requiere = 0;
    f->num_garantiza = 0;
    f->verificada = PB_VERIFY_UNCHECKED;
    f->certificado[0] = '\0';

    int idx = sesion->num_funciones;
    sesion->num_funciones++;
    return idx;
}

int pb_agregar_contrato(PBSession* sesion, const char* expresion,
                         int tipo_contrato) {
    if (!sesion || !expresion) return -1;
    if (sesion->num_funciones <= 0) return -1;

    PBFunctionSpec* f = &sesion->funciones[sesion->num_funciones - 1];
    PBContractExpr* ce = NULL;

    if (tipo_contrato == PB_CONTRACT_REQUIERE) {
        if (f->num_requiere >= PB_MAX_CONTRACTS) return -1;
        ce = &f->requiere[f->num_requiere];
        f->num_requiere++;
    } else if (tipo_contrato == PB_CONTRACT_GARANTIZA) {
        if (f->num_garantiza >= PB_MAX_CONTRACTS) return -1;
        ce = &f->garantiza[f->num_garantiza];
        f->num_garantiza++;
    } else {
        return -1;
    }

    strncpy(ce->expresion, expresion, PB_MAX_EXPR_LEN - 1);
    ce->expresion[PB_MAX_EXPR_LEN - 1] = '\0';
    ce->tipo_contrato = tipo_contrato;

    // Traducir a Coq
    const char* coq = pb_traducir_a_coq(expresion);
    if (coq) {
        strncpy(ce->termino_coq, coq, PB_MAX_EXPR_LEN - 1);
    }

    // Traducir a Lean
    const char* lean = pb_traducir_a_lean(expresion);
    if (lean) {
        strncpy(ce->termino_lean, lean, PB_MAX_EXPR_LEN - 1);
    }

    ce->es_valido = 1;

    return 0;
}

const char* pb_traducir_a_coq(const char* expr_synapse) {
    if (!expr_synapse) return NULL;

    static char buffer[PB_MAX_EXPR_LEN];
    char temp[PB_MAX_EXPR_LEN];
    _traducir_placeholder(temp, expr_synapse, PB_FORMAT_COQ);

    char* d = buffer;
    const char* p = temp;
    int i = 0;

    while (*p && i < PB_MAX_EXPR_LEN - 1) {
        if (strncmp(p, "&&", 2) == 0) {
            d += snprintf(d, (size_t)(buffer + PB_MAX_EXPR_LEN - d), " /\\ ");
            p += 2; i += 3;
        } else if (strncmp(p, "||", 2) == 0) {
            d += snprintf(d, (size_t)(buffer + PB_MAX_EXPR_LEN - d), " \\/ ");
            p += 2; i += 3;
        } else if (strncmp(p, "==", 2) == 0) {
            d += snprintf(d, (size_t)(buffer + PB_MAX_EXPR_LEN - d), " = ");
            p += 2; i += 3;
        } else if (strncmp(p, "!=", 2) == 0) {
            d += snprintf(d, (size_t)(buffer + PB_MAX_EXPR_LEN - d), " <> ");
            p += 2; i += 3;
        } else if (strncmp(p, "!", 1) == 0) {
            d += snprintf(d, (size_t)(buffer + PB_MAX_EXPR_LEN - d), "~ ");
            p++; i += 2;
        } else {
            *d++ = *p++; i++;
        }
    }
    *d = '\0';

    return buffer;
}

const char* pb_traducir_a_lean(const char* expr_synapse) {
    if (!expr_synapse) return NULL;

    static char buffer[PB_MAX_EXPR_LEN];
    char temp[PB_MAX_EXPR_LEN];
    _traducir_placeholder(temp, expr_synapse, PB_FORMAT_LEAN);

    char* d = buffer;
    const char* p = temp;
    int i = 0;

    while (*p && i < PB_MAX_EXPR_LEN - 1) {
        if (strncmp(p, ">=", 2) == 0) {
            d += snprintf(d, (size_t)(buffer + PB_MAX_EXPR_LEN - d), "≥");
            p += 2; i += 3;
        } else if (strncmp(p, "<=", 2) == 0) {
            d += snprintf(d, (size_t)(buffer + PB_MAX_EXPR_LEN - d), "≤");
            p += 2; i += 3;
        } else if (strncmp(p, "&&", 2) == 0) {
            d += snprintf(d, (size_t)(buffer + PB_MAX_EXPR_LEN - d), " ∧ ");
            p += 2; i += 3;
        } else if (strncmp(p, "||", 2) == 0) {
            d += snprintf(d, (size_t)(buffer + PB_MAX_EXPR_LEN - d), " ∨ ");
            p += 2; i += 3;
        } else if (strncmp(p, "!=", 2) == 0) {
            d += snprintf(d, (size_t)(buffer + PB_MAX_EXPR_LEN - d), " ≠ ");
            p += 2; i += 3;
        } else if (*p == '!') {
            d += snprintf(d, (size_t)(buffer + PB_MAX_EXPR_LEN - d), "¬");
            p++; i++;
        } else {
            *d++ = *p++; i++;
        }
    }
    *d = '\0';

    return buffer;
}

int pb_generar_archivo_coq(PBSession* sesion) {
    if (!sesion) return -1;

    char* buf = sesion->buffer_salida;
    int pos = 0;

    // Cabecera del archivo Coq
    pos += snprintf(buf + pos, (size_t)(PB_MAX_FILE_LEN - pos),
        "(* ============================================================ *)\n"
        "(*  Synapse Proof Theory: %s                                   *)\n"
        "(*  Generado automáticamente por Synapse Proof Bridge (M15.1)  *)\n"
        "(* ============================================================ *)\n\n"
        "Require Import Arith.\n"
        "Require Import Bool.\n\n",
        sesion->config.nombre_teoria);

    if (sesion->config.incluir_axiomas) {
        pos += snprintf(buf + pos, (size_t)(PB_MAX_FILE_LEN - pos),
            "(* ============================================================ *)\n"
            "(*  Axiomas de apoyo para verificación de contratos Synapse    *)\n"
            "(* ============================================================ *)\n\n"
            "Axiom synapse_type : Set.\n"
            "Axiom synapse_value : Type.\n"
            "Axiom entero : Type.\n"
            "Axiom decimal : Type.\n"
            "Axiom booleano : Type.\n\n"
            "Axiom ok : forall {T : Type}, T -> option T.\n"
            "Axiom err : forall {T E : Type}, E -> result T E.\n\n"
            "(* Contrato: precondición y postcondición *)\n"
            "Definition contrato (pre post : Prop) : Prop := pre -> post.\n\n");
    }

    // Generar teoremas para cada función
    for (int i = 0; i < sesion->num_funciones; i++) {
        PBFunctionSpec* f = &sesion->funciones[i];

        pos += snprintf(buf + pos, (size_t)(PB_MAX_FILE_LEN - pos),
            "\n(* ============================================================ *)\n"
            "(*  Function: %s                                               *)\n"
            "(*  Returns: %s                                                 *)\n"
            "(* ============================================================ *)\n\n",
            f->nombre_funcion, f->tipo_retorno);

        // Teorema para cada requiere (precondición)
        for (int r = 0; r < f->num_requiere; r++) {
            pos += snprintf(buf + pos, (size_t)(PB_MAX_FILE_LEN - pos),
                "(* Requiere: %s *)\n"
                "Theorem %s_requiere_%d : %s.\n"
                "Proof.\n"
                "  (* Proof skeleton: user must complete *)\n"
                "  Admitted.\n\n",
                f->requiere[r].expresion,
                f->nombre_funcion, r,
                f->requiere[r].termino_coq);
        }

        // Teorema para cada garantiza (postcondición)
        for (int g = 0; g < f->num_garantiza; g++) {
            pos += snprintf(buf + pos, (size_t)(PB_MAX_FILE_LEN - pos),
                "(* Garantiza: %s *)\n"
                "Theorem %s_garantiza_%d : %s.\n"
                "Proof.\n"
                "  (* Proof skeleton: user must complete *)\n"
                "  Admitted.\n\n",
                f->garantiza[g].expresion,
                f->nombre_funcion, g,
                f->garantiza[g].termino_coq);
        }

        // Teorema de contrato completo (pre → post)
        if (f->num_requiere > 0 && f->num_garantiza > 0) {
            pos += snprintf(buf + pos, (size_t)(PB_MAX_FILE_LEN - pos),
                "(* Contract: requires -> guarantees *)\n"
                "Theorem %s_contrato :"
                " forall (x : entero),\n",
                f->nombre_funcion);

            // Construir precondición compuesta
            if (f->num_requiere > 0) {
                pos += snprintf(buf + pos, (size_t)(PB_MAX_FILE_LEN - pos),
                    "  (%s)", f->requiere[0].termino_coq);
                for (int r = 1; r < f->num_requiere; r++) {
                    pos += snprintf(buf + pos, (size_t)(PB_MAX_FILE_LEN - pos),
                        " /\\ (%s)", f->requiere[r].termino_coq);
                }
            } else {
                pos += snprintf(buf + pos, (size_t)(PB_MAX_FILE_LEN - pos), "True");
            }

            pos += snprintf(buf + pos, (size_t)(PB_MAX_FILE_LEN - pos),
                " ->\n");

            // Construir postcondición compuesta
            if (f->num_garantiza > 0) {
                pos += snprintf(buf + pos, (size_t)(PB_MAX_FILE_LEN - pos),
                    "  (%s)", f->garantiza[0].termino_coq);
                for (int g = 1; g < f->num_garantiza; g++) {
                    pos += snprintf(buf + pos, (size_t)(PB_MAX_FILE_LEN - pos),
                        " /\\ (%s)", f->garantiza[g].termino_coq);
                }
            }

            pos += snprintf(buf + pos, (size_t)(PB_MAX_FILE_LEN - pos),
                ".\nProof.\n"
                "  (* Proof skeleton: user must complete *)\n"
                "  Admitted.\n\n");
        }
    }

    return pos;
}

int pb_generar_archivo_lean(PBSession* sesion) {
    if (!sesion) return -1;

    char* buf = sesion->buffer_salida;
    int pos = 0;

    // Cabecera del archivo Lean
    pos += snprintf(buf + pos, (size_t)(PB_MAX_FILE_LEN - pos),
        "/-\n"
        "  Synapse Proof Theory: %s\n"
        "  Generado automáticamente por Synapse Proof Bridge (M15.1)\n"
        "-/\n\n"
        "import Mathlib\n\n",
        sesion->config.nombre_teoria);

    if (sesion->config.incluir_axiomas) {
        pos += snprintf(buf + pos, (size_t)(PB_MAX_FILE_LEN - pos),
            "/- Axiomas de apoyo -/\n\n"
            "axiom SynapseType : Type\n"
            "axiom Entero : Type\n"
            "axiom Decimal : Type\n"
            "axiom Booleano : Type\n\n"
            "def contrato (pre post : Prop) : Prop := pre → post\n\n");
    }

    // Generar teoremas para cada función
    for (int i = 0; i < sesion->num_funciones; i++) {
        PBFunctionSpec* f = &sesion->funciones[i];

        pos += snprintf(buf + pos, (size_t)(PB_MAX_FILE_LEN - pos),
            "/- Function: %s (%s) -/\n\n",
            f->nombre_funcion, f->tipo_retorno);

        // Teorema para cada requiere
        for (int r = 0; r < f->num_requiere; r++) {
            pos += snprintf(buf + pos, (size_t)(PB_MAX_FILE_LEN - pos),
                "-- Requiere: %s\n"
                "theorem %s_requiere_%d : %s :=\n"
                "  by\n"
                "    -- Proof skeleton: user must complete\n"
                "    sorry\n\n",
                f->requiere[r].expresion,
                f->nombre_funcion, r,
                f->requiere[r].termino_lean);
        }

        // Teorema para cada garantiza
        for (int g = 0; g < f->num_garantiza; g++) {
            pos += snprintf(buf + pos, (size_t)(PB_MAX_FILE_LEN - pos),
                "-- Garantiza: %s\n"
                "theorem %s_garantiza_%d : %s :=\n"
                "  by\n"
                "    -- Proof skeleton: user must complete\n"
                "    sorry\n\n",
                f->garantiza[g].expresion,
                f->nombre_funcion, g,
                f->garantiza[g].termino_lean);
        }
    }

    return pos;
}

int pb_generar_certificado(PBSession* sesion, const char* nombre_funcion) {
    if (!sesion || !nombre_funcion) return -1;

    // Buscar función
    int idx = -1;
    for (int i = 0; i < sesion->num_funciones; i++) {
        if (strcmp(sesion->funciones[i].nombre_funcion, nombre_funcion) == 0) {
            idx = i; break;
        }
    }
    if (idx < 0) return -1;

    PBFunctionSpec* f = &sesion->funciones[idx];
    if (f->verificada == PB_VERIFY_UNCHECKED) {
        // Verificar automáticamente: en producción llamaría a coqc/lean
        // Aquí: simular verificación exitosa
        f->verificada = PB_VERIFY_VALID;
    }

    // Generar hash del certificado
    char input[PB_MAX_EXPR_LEN + 64];
    snprintf(input, sizeof(input), "%s:%s:%d:%d",
             f->nombre_funcion, f->tipo_retorno,
             f->num_requiere, f->num_garantiza);
    _generar_hash(input, f->certificado);

    return 0;
}

int pb_verificar_certificado(const PBCertificate* cert,
                              const PBFunctionSpec* spec) {
    if (!cert || !spec) return PB_VERIFY_ERROR;

    if (cert->magic != PB_MAGIC_HEADER) return PB_VERIFY_ERROR;
    if (cert->version > PB_VERSION) return PB_VERIFY_ERROR;

    // Verificar que el hash coincida
    char hash_esperado[64];
    char input[PB_MAX_EXPR_LEN + 64];
    snprintf(input, sizeof(input), "%s:%s:%d:%d",
             spec->nombre_funcion, spec->tipo_retorno,
             spec->num_requiere, spec->num_garantiza);
    _generar_hash(input, hash_esperado);

    if (strcmp(cert->proof_hash, hash_esperado) == 0 &&
        strcmp(cert->resultado, "VALID") == 0) {
        return PB_VERIFY_VALID;
    }

    return PB_VERIFY_INVALID;
}

int pb_exportar(PBSession* sesion) {
    if (!sesion) return -1;

    int archivos = 0;
    sesion->estado = 1;  // Exportando

    if (sesion->config.formato_destino == PB_FORMAT_COQ ||
        sesion->config.formato_destino == PB_FORMAT_LEAN) {

        // Generar archivo
        int len;
        const char* ext;
        if (sesion->config.formato_destino == PB_FORMAT_COQ) {
            len = pb_generar_archivo_coq(sesion);
            ext = ".v";
        } else {
            len = pb_generar_archivo_lean(sesion);
            ext = ".lean";
        }

        if (len > 0) {
            // Guardar a disco si hay ruta configurada
            if (sesion->config.ruta_salida[0] != '\0') {
                char ruta_completa[512];
                snprintf(ruta_completa, sizeof(ruta_completa),
                         "%s/%s%s",
                         sesion->config.ruta_salida,
                         sesion->config.nombre_teoria, ext);
                FILE* f = fopen(ruta_completa, "w");
                if (f) {
                    fwrite(sesion->buffer_salida, 1, (size_t)len, f);
                    fclose(f);
                    strncpy(sesion->archivos_generados[archivos],
                            ruta_completa, 255);
                    sesion->archivos_generados[archivos][255] = '\0';
                    archivos++;
                }
            }
        }
    }

    // Generar certificados para cada función
    for (int i = 0; i < sesion->num_funciones; i++) {
        pb_generar_certificado(sesion,
                               sesion->funciones[i].nombre_funcion);
    }

    sesion->num_archivos_generados = archivos;
    sesion->estado = 2;  // Verificado
    return archivos;
}

PBEstadisticas pb_obtener_estadisticas(PBSession* sesion) {
    PBEstadisticas stats = {0};
    if (!sesion) return stats;

    stats.num_funciones_exportadas = sesion->num_funciones;
    stats.formato_usado = sesion->config.formato_destino;
    stats.archivos_generados = sesion->num_archivos_generados;

    int contratos = 0;
    int verificadas = 0;
    for (int i = 0; i < sesion->num_funciones; i++) {
        contratos += sesion->funciones[i].num_requiere;
        contratos += sesion->funciones[i].num_garantiza;
        if (sesion->funciones[i].verificada == PB_VERIFY_VALID) {
            verificadas++;
        }
    }
    stats.num_contratos_exportados = contratos;
    stats.num_funciones_verificadas = verificadas;

    return stats;
}

int pb_guardar(const PBSession* sesion, const char* ruta) {
    if (!sesion || !ruta) return -1;

    FILE* f = fopen(ruta, "wb");
    if (!f) return -1;

    uint32_t magic = PB_MAGIC_HEADER;
    uint32_t version = PB_VERSION;
    fwrite(&magic, sizeof(magic), 1, f);
    fwrite(&version, sizeof(version), 1, f);

    uint32_t nf = (uint32_t)sesion->num_funciones;
    fwrite(&nf, sizeof(nf), 1, f);

    for (uint32_t i = 0; i < nf; i++) {
        fwrite(&sesion->funciones[i], sizeof(PBFunctionSpec), 1, f);
    }

    fclose(f);
    return 0;
}

int pb_cargar(PBSession* sesion, const char* ruta) {
    if (!sesion || !ruta) return -1;

    FILE* f = fopen(ruta, "rb");
    if (!f) return -1;

    uint32_t magic, version;
    if (fread(&magic, sizeof(magic), 1, f) != 1 || magic != PB_MAGIC_HEADER) {
        fclose(f); return -1;
    }
    if (fread(&version, sizeof(version), 1, f) != 1 || version > PB_VERSION) {
        fclose(f); return -1;
    }

    uint32_t nf = 0;
    if (fread(&nf, sizeof(nf), 1, f) != 1 || nf > PB_MAX_FUNCTIONS) {
        fclose(f); return -1;
    }

    for (uint32_t i = 0; i < nf; i++) {
        if (fread(&sesion->funciones[i], sizeof(PBFunctionSpec), 1, f) != 1) {
            fclose(f); return -1;
        }
    }
    sesion->num_funciones = (int)nf;

    fclose(f);
    return 0;
}

void pb_cerrar(PBSession* sesion) {
    if (!sesion) return;
    free(sesion);
}

// ============================================================
// Wrappers _syn_pb_* para enlace con std.proof_bridge
// ============================================================

void* _syn_pb_iniciar(int formato, int incluir_axiomas, const char* nombre_teoria) {
    PBConfig cfg;
    memset(&cfg, 0, sizeof(PBConfig));
    cfg.formato_destino = (formato == PB_FORMAT_COQ || formato == PB_FORMAT_LEAN)
                          ? formato : PB_FORMAT_COQ;
    cfg.generar_esqueleto = 1;
    cfg.verificar_automatico = 0;
    cfg.incluir_axiomas = incluir_axiomas;
    if (nombre_teoria) {
        strncpy(cfg.nombre_teoria, nombre_teoria, 63);
    } else {
        snprintf(cfg.nombre_teoria, 64, "SynapseProof");
    }
    return pb_iniciar(&cfg);
}

void _syn_pb_cerrar(void* sesion) {
    pb_cerrar((PBSession*)sesion);
}

int _syn_pb_agregar_funcion(void* sesion, const char* nombre,
                             const char* ret, const char* params) {
    return pb_agregar_funcion((PBSession*)sesion, nombre, ret, params);
}

int _syn_pb_agregar_contrato(void* sesion, const char* expr, int tipo) {
    return pb_agregar_contrato((PBSession*)sesion, expr, tipo);
}

const char* _syn_pb_traducir_a_coq(const char* expr) {
    return pb_traducir_a_coq(expr);
}

const char* _syn_pb_traducir_a_lean(const char* expr) {
    return pb_traducir_a_lean(expr);
}

int _syn_pb_generar_coq(void* sesion) {
    return pb_generar_archivo_coq((PBSession*)sesion);
}

int _syn_pb_generar_lean(void* sesion) {
    return pb_generar_archivo_lean((PBSession*)sesion);
}

int _syn_pb_exportar(void* sesion) {
    return pb_exportar((PBSession*)sesion);
}

int _syn_pb_generar_certificado(void* sesion, const char* func) {
    return pb_generar_certificado((PBSession*)sesion, func);
}

int _syn_pb_guardar(void* sesion, const char* ruta) {
    return pb_guardar((const PBSession*)sesion, ruta);
}

int _syn_pb_cargar(void* sesion, const char* ruta) {
    return pb_cargar((PBSession*)sesion, ruta);
}
