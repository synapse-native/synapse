// axon_build.c — Orchestrador nativo de compilacion Axon
// Fase 8: Auto-Alojamiento Total
// Compilar: gcc -o axon_build.exe axon_build.c

#define _CRT_SECURE_NO_WARNINGS
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <sys/stat.h>

#ifdef _WIN32
  #include <direct.h>
  #include <dirent.h>
#else
  #include <unistd.h>
  #include <dirent.h>
#endif

#define AXON_MODULES "axon_modules"
#define LOCK_FILE "axon.lock"
#define TOML_FILE "axon.toml"

// --- Exit codes ---
#define EC_OK 0
#define EC_MANIFEST_NOT_FOUND 1
#define EC_PARSE_ERROR 2
#define EC_MISSING_PUNTO_ENTRADA 3
#define EC_GIT_FAILURE 4
#define EC_LOCK_MISMATCH 5
#define EC_INTERNAL 6

// ============================================================
// Minimal TOML parser (axon.toml subset)
// ============================================================
typedef struct NodoToml NodoToml;
typedef struct ParToml ParToml;

struct ParToml {
    char* clave;
    NodoToml* valor;
};

struct NodoToml {
    int tipo;         // 1=tabla, 2=cadena, 3=tabla_en_linea
    char* valor_str;
    ParToml* pares;
    int longitud;
    int capacidad;
};

static NodoToml* _nd_new(int tipo) {
    NodoToml* n = (NodoToml*)calloc(1, sizeof(NodoToml));
    if (n) n->tipo = tipo;
    return n;
}

static void _nd_liberar(NodoToml* n) {
    if (!n) return;
    if (n->valor_str) { free(n->valor_str); n->valor_str = NULL; }
    for (int i = 0; i < n->longitud; i++) {
        if (n->pares[i].clave) free(n->pares[i].clave);
        if (n->pares[i].valor) _nd_liberar(n->pares[i].valor);
    }
    if (n->pares) { free(n->pares); n->pares = NULL; }
    n->longitud = 0; n->capacidad = 0;
}

static void _nd_agregar(NodoToml* n, const char* clave, NodoToml* valor) {
    if (n->longitud >= n->capacidad) {
        n->capacidad = n->capacidad == 0 ? 4 : n->capacidad * 2;
        n->pares = (ParToml*)realloc(n->pares, n->capacidad * sizeof(ParToml));
    }
    ParToml* p = &n->pares[n->longitud++];
    p->clave = clave ? _strdup(clave) : NULL;
    p->valor = valor;
}

static NodoToml* _nd_buscar(NodoToml* n, const char* clave) {
    if (!n || (n->tipo != 1 && n->tipo != 3) || !clave) return NULL;
    for (int i = 0; i < n->longitud; i++) {
        if (n->pares[i].clave && strcmp(n->pares[i].clave, clave) == 0)
            return n->pares[i].valor;
    }
    return NULL;
}

// --- Lexer state ---
typedef struct {
    const char* entrada;
    int pos;
    int longitud;
    int linea;
    int error;
    char err_msg[256];
} TomlLexer;

static int _tl_peek(TomlLexer* l) {
    return l->pos < l->longitud ? (unsigned char)l->entrada[l->pos] : -1;
}

static void _tl_adv(TomlLexer* l) { if (l->pos < l->longitud) l->pos++; }

static void _tl_skip_ws(TomlLexer* l) {
    while (l->pos < l->longitud) {
        char c = l->entrada[l->pos];
        if (c == ' ' || c == '\t') { l->pos++; continue; }
        break;
    }
}

static void _tl_skip_line(TomlLexer* l) {
    while (l->pos < l->longitud && l->entrada[l->pos] != '\n') l->pos++;
    if (l->pos < l->longitud) l->pos++;
    l->linea++;
}

static int _tl_skip_newline(TomlLexer* l) {
    if (_tl_peek(l) == '\r') _tl_adv(l);
    if (_tl_peek(l) == '\n') { _tl_adv(l); l->linea++; return 1; }
    return 0;
}

static char* _tl_parse_bare_key(TomlLexer* l) {
    int start = l->pos;
    while (l->pos < l->longitud) {
        char c = l->entrada[l->pos];
        if (c == '=' || c == ' ' || c == '\t' || c == '\n' || c == '\r' || c == '#' || c == '}' || c == ',' || c == ']')
            break;
        l->pos++;
    }
    int len = l->pos - start;
    if (len <= 0) return NULL;
    char* s = (char*)malloc(len + 1);
    if (!s) return NULL;
    memcpy(s, l->entrada + start, len);
    s[len] = '\0';
    return s;
}

static char* _tl_parse_string(TomlLexer* l) {
    if (_tl_peek(l) != '"') { l->error = 1; snprintf(l->err_msg, sizeof(l->err_msg), "linea %d: esperaba '\"'", l->linea); return NULL; }
    _tl_adv(l);
    int cap = 64, len = 0;
    char* buf = (char*)malloc(cap);
    if (!buf) { l->error = 1; return NULL; }
    while (l->pos < l->longitud) {
        char c = l->entrada[l->pos];
        if (c == '"') { _tl_adv(l); buf[len] = '\0'; return buf; }
        if (c == '\\') {
            _tl_adv(l);
            if (l->pos >= l->longitud) break;
            char esc = l->entrada[l->pos];
            switch (esc) {
                case '"': buf[len++] = '"'; break;
                case '\\': buf[len++] = '\\'; break;
                case 'n': buf[len++] = '\n'; break;
                case 't': buf[len++] = '\t'; break;
                case 'r': buf[len++] = '\r'; break;
                default: buf[len++] = esc; break;
            }
            _tl_adv(l);
        } else {
            buf[len++] = c;
            _tl_adv(l);
        }
        if (len + 1 >= cap) {
            cap *= 2;
            buf = (char*)realloc(buf, cap);
        }
    }
    free(buf);
    l->error = 1;
    snprintf(l->err_msg, sizeof(l->err_msg), "linea %d: cadena sin cerrar", l->linea);
    return NULL;
}

static NodoToml* _tl_parse_inline_table(TomlLexer* l) {
    NodoToml* tbl = _nd_new(3);
    while (l->pos < l->longitud && !l->error) {
        _tl_skip_ws(l);
        int c = _tl_peek(l);
        if (c == '}') { _tl_adv(l); return tbl; }
        if (c == ',' || c == '\n' || c == '\r') { _tl_adv(l); continue; }
        char* key = _tl_parse_bare_key(l);
        if (!key || l->error) { free(key); break; }
        _tl_skip_ws(l);
        if (_tl_peek(l) != '=') { l->error = 1; free(key); break; }
        _tl_adv(l);
        _tl_skip_ws(l);
        if (_tl_peek(l) == '"') {
            char* val = _tl_parse_string(l);
            NodoToml* vn = _nd_new(2);
            vn->valor_str = val;
            _nd_agregar(tbl, key, vn);
        } else {
            char* val = _tl_parse_bare_key(l);
            NodoToml* vn = _nd_new(2);
            vn->valor_str = val;
            _nd_agregar(tbl, key, vn);
        }
        free(key);
        _tl_skip_ws(l);
        if (_tl_peek(l) == '}') { _tl_adv(l); return tbl; }
        if (_tl_peek(l) == ',') _tl_adv(l);
    }
    return tbl;
}

static char* _tl_parse_section_key(TomlLexer* l) {
    _tl_skip_ws(l);
    int start = l->pos;
    while (l->pos < l->longitud) {
        char c = l->entrada[l->pos];
        if (c == ']' || c == '\n' || c == '\r') break;
        l->pos++;
    }
    int end = l->pos;
    while (end > start && (l->entrada[end-1] == ' ' || l->entrada[end-1] == '\t')) end--;
    if (_tl_peek(l) != ']') return NULL;
    int len = end - start;
    if (len <= 0) return NULL;
    char* s = (char*)malloc(len + 1);
    memcpy(s, l->entrada + start, len);
    s[len] = '\0';
    return s;
}

static NodoToml* _toml_parse(const char* entrada, int longitud) {
    TomlLexer l;
    l.entrada = entrada; l.pos = 0; l.longitud = longitud; l.linea = 1; l.error = 0;
    l.err_msg[0] = '\0';

    NodoToml* root = _nd_new(1);
    NodoToml* current = root;

    while (l.pos < l.longitud && !l.error) {
        _tl_skip_ws(&l);
        int c = _tl_peek(&l);
        if (c < 0) break;
        if (c == '\n' || c == '\r') { _tl_skip_newline(&l); continue; }
        if (c == '#') { _tl_skip_line(&l); continue; }

        if (c == '[') {
            _tl_adv(&l);
            char* sec_name = _tl_parse_section_key(&l);
            if (!sec_name || l.error) { free(sec_name); l.error = 1; break; }
            _tl_adv(&l);
            NodoToml* tbl = _nd_buscar(root, sec_name);
            if (!tbl) {
                tbl = _nd_new(1);
                _nd_agregar(root, sec_name, tbl);
            }
            free(sec_name);
            current = tbl;
            _tl_skip_line(&l);
            continue;
        }

        // key = value
        char* key = _tl_parse_bare_key(&l);
        if (!key || l.error) { free(key); break; }
        _tl_skip_ws(&l);
        if (_tl_peek(&l) != '=') { l.error = 1; free(key); break; }
        _tl_adv(&l);
        _tl_skip_ws(&l);

        NodoToml* val = NULL;
        if (_tl_peek(&l) == '"') {
            char* vs = _tl_parse_string(&l);
            if (!l.error) { val = _nd_new(2); val->valor_str = vs; }
        } else if (_tl_peek(&l) == '{') {
            _tl_adv(&l);
            val = _tl_parse_inline_table(&l);
        } else {
            char* vs = _tl_parse_bare_key(&l);
            if (!l.error) { val = _nd_new(2); val->valor_str = vs; }
        }

        if (l.error) { free(key); if (val) _nd_liberar(val); break; }
        _nd_agregar(current, key, val);
        free(key);
        _tl_skip_line(&l);
    }

    if (l.error) {
        fprintf(stderr, "ERROR: Error TOML %s\n", l.err_msg[0] ? l.err_msg : "desconocido");
        _nd_liberar(root);
        return NULL;
    }
    return root;
}

// ============================================================
// File hashing (FNV-1a 64-bit)
// ============================================================
static uint64_t _hash_file(const char* path) {
    FILE* f = fopen(path, "rb");
    if (!f) return 0;
    uint64_t h = 14695981039346656037ULL;
    int c;
    while ((c = fgetc(f)) != EOF) {
        h ^= (unsigned char)c;
        h *= 1099511628211ULL;
    }
    fclose(f);
    return h;
}

static void _hash_dir(const char* dir, uint64_t* hash) {
    DIR* d = opendir(dir);
    if (!d) return;
    struct dirent* ent;
    while ((ent = readdir(d)) != NULL) {
        if (strcmp(ent->d_name, ".") == 0 || strcmp(ent->d_name, "..") == 0) continue;
        char path[4096];
        snprintf(path, sizeof(path), "%s/%s", dir, ent->d_name);
        struct stat st;
        if (stat(path, &st) != 0) continue;
        if (st.st_mode & S_IFDIR) {
            _hash_dir(path, hash);
        } else {
            const char* ext = strrchr(ent->d_name, '.');
            if (ext && strcmp(ext, ".syn") == 0) {
                *hash = (*hash ^ _hash_file(path)) * 1099511628211ULL;
            }
        }
    }
    closedir(d);
}

// ============================================================
// Lock file I/O
// ============================================================
typedef struct {
    char nombre[256];
    char hash[17]; // 16 hex + null
} DepHash;

static int _lock_read(const char* ruta, DepHash* hashes, int max) {
    FILE* f = fopen(ruta, "r");
    if (!f) return 0;
    int n = 0;
    char buf[512];
    while (n < max && fgets(buf, sizeof(buf), f)) {
        char* eq = strchr(buf, '=');
        if (!eq) continue;
        *eq = '\0';
        char* name = buf;
        char* hval = eq + 1;
        while (*name == ' ' || *name == '\t') name++;
        char* end = name + strlen(name) - 1;
        while (end > name && (*end == ' ' || *end == '\t' || *end == '\n' || *end == '\r')) end--;
        end[1] = '\0';
        if (strlen(name) == 0) continue;
        strncpy(hashes[n].nombre, name, sizeof(hashes[n].nombre) - 1);
        strncpy(hashes[n].hash, hval, 16);
        hashes[n].hash[16] = '\0';
        n++;
    }
    fclose(f);
    return n;
}

static void _lock_write(const char* ruta, DepHash* hashes, int n) {
    FILE* f = fopen(ruta, "w");
    if (!f) return;
    for (int i = 0; i < n; i++) {
        fprintf(f, "%s=%s\n", hashes[i].nombre, hashes[i].hash);
    }
    fclose(f);
}

// ============================================================
// Build orchestrator
// ============================================================
static int _es_dep_git(NodoToml* val) {
    return val && val->tipo == 3 && _nd_buscar(val, "git") && _nd_buscar(val, "rev");
}

int main(int argc, char** argv) {
    const char* ruta_proyecto = ".";
    if (argc > 1) ruta_proyecto = argv[1];

    char ruta_toml[4096];
    snprintf(ruta_toml, sizeof(ruta_toml), "%s/%s", ruta_proyecto, TOML_FILE);

    FILE* f = fopen(ruta_toml, "rb");
    if (!f) {
        fprintf(stderr, "ERROR:%d\n", EC_MANIFEST_NOT_FOUND);
        return EC_MANIFEST_NOT_FOUND;
    }

    fseek(f, 0, SEEK_END);
    long sz = ftell(f);
    rewind(f);
    if (sz <= 0) { fclose(f); fprintf(stderr, "ERROR:%d\n", EC_MANIFEST_NOT_FOUND); return EC_MANIFEST_NOT_FOUND; }

    char* content = (char*)malloc(sz + 1);
    size_t nread = fread(content, 1, sz, f);
    content[nread] = '\0';
    fclose(f);
    // Strip UTF-8 BOM
    if (nread >= 3 && (unsigned char)content[0] == 0xEF &&
        (unsigned char)content[1] == 0xBB && (unsigned char)content[2] == 0xBF) {
        memmove(content, content + 3, nread - 3 + 1);
        nread -= 3;
    }

    NodoToml* doc = _toml_parse(content, (int)nread);
    free(content);
    if (!doc) {
        return EC_PARSE_ERROR;
    }

    NodoToml* proyecto = _nd_buscar(doc, "proyecto");
    if (!proyecto || proyecto->tipo != 1) {
        fprintf(stderr, "ERROR:%d\n", EC_MISSING_PUNTO_ENTRADA);
        _nd_liberar(doc);
        return EC_MISSING_PUNTO_ENTRADA;
    }

    NodoToml* punto_entrada = _nd_buscar(proyecto, "punto_entrada");
    if (!punto_entrada || punto_entrada->tipo != 2) {
        fprintf(stderr, "ERROR:%d\n", EC_MISSING_PUNTO_ENTRADA);
        _nd_liberar(doc);
        return EC_MISSING_PUNTO_ENTRADA;
    }

    // --- Dependencies ---
    NodoToml* deps = _nd_buscar(doc, "dependencias");
    int ndeps = (deps && deps->tipo == 1) ? deps->longitud : 0;

    // Read existing lock
    char ruta_lock[4096];
    snprintf(ruta_lock, sizeof(ruta_lock), "%s/%s", ruta_proyecto, LOCK_FILE);
    DepHash lock_hashes[256];
    int nlock = _lock_read(ruta_lock, lock_hashes, 256);

    DepHash new_hashes[256];
    int nnew = 0;

    for (int i = 0; i < ndeps; i++) {
        ParToml* dep = &deps->pares[i];
        if (!_es_dep_git(dep->valor)) continue;

        const char* nombre = dep->clave;
        NodoToml* git = _nd_buscar(dep->valor, "git");
        NodoToml* rev = _nd_buscar(dep->valor, "rev");
        if (!git || !git->valor_str || !rev || !rev->valor_str) continue;

        char dir_dep[4096];
        snprintf(dir_dep, sizeof(dir_dep), "%s/%s/%s", ruta_proyecto, AXON_MODULES, nombre);

        struct stat st;
        if (stat(dir_dep, &st) != 0 || !(st.st_mode & S_IFDIR)) {
            fprintf(stderr, "[Axon] Clonando '%s' desde %s...\n", nombre, git->valor_str);
            char cmd[8192];
            snprintf(cmd, sizeof(cmd), "git clone %s %s", git->valor_str, dir_dep);
            int r = system(cmd);
            if (r != 0) {
                fprintf(stderr, "ERROR:%d\n", EC_GIT_FAILURE);
                _nd_liberar(doc);
                return EC_GIT_FAILURE;
            }
            snprintf(cmd, sizeof(cmd), "git -C %s checkout %s", dir_dep, rev->valor_str);
            r = system(cmd);
            if (r != 0) {
                fprintf(stderr, "ERROR:%d\n", EC_GIT_FAILURE);
                _nd_liberar(doc);
                return EC_GIT_FAILURE;
            }
        }

        uint64_t hash_val = 14695981039346656037ULL;
        _hash_dir(dir_dep, &hash_val);

        char hash_hex[17];
        snprintf(hash_hex, sizeof(hash_hex), "%016llx", (unsigned long long)hash_val);

        strncpy(new_hashes[nnew].nombre, nombre, sizeof(new_hashes[nnew].nombre) - 1);
        strncpy(new_hashes[nnew].hash, hash_hex, 16);
        new_hashes[nnew].hash[16] = '\0';

        // Check lock
        for (int j = 0; j < nlock; j++) {
            if (strcmp(lock_hashes[j].nombre, nombre) == 0 &&
                strcmp(lock_hashes[j].hash, hash_hex) != 0) {
                fprintf(stderr, "ERROR:%d:%s\n", EC_LOCK_MISMATCH, nombre);
                _nd_liberar(doc);
                return EC_LOCK_MISMATCH;
            }
        }

        nnew++;
    }

    // Preserve lock entries for deps no longer in manifest
    for (int j = 0; j < nlock; j++) {
        int found = 0;
        for (int k = 0; k < nnew; k++) {
            if (strcmp(new_hashes[k].nombre, lock_hashes[j].nombre) == 0) {
                found = 1; break;
            }
        }
        if (!found) {
            int in_manifest = 0;
            for (int k = 0; k < ndeps; k++) {
                if (strcmp(deps->pares[k].clave, lock_hashes[j].nombre) == 0) {
                    in_manifest = 1; break;
                }
            }
            if (in_manifest) {
                strncpy(new_hashes[nnew].nombre, lock_hashes[j].nombre, sizeof(new_hashes[nnew].nombre) - 1);
                strncpy(new_hashes[nnew].hash, lock_hashes[j].hash, 16);
                new_hashes[nnew].hash[16] = '\0';
                nnew++;
            }
        }
    }

    // Sort by nombre
    for (int i = 0; i < nnew - 1; i++) {
        for (int j = i + 1; j < nnew; j++) {
            if (strcmp(new_hashes[i].nombre, new_hashes[j].nombre) > 0) {
                DepHash tmp = new_hashes[i];
                new_hashes[i] = new_hashes[j];
                new_hashes[j] = tmp;
            }
        }
    }

    _lock_write(ruta_lock, new_hashes, nnew);

    // --- Output for Python ---
    // punto_entrada, then dep list
    printf("punto_entrada=%s\n", punto_entrada->valor_str);
    for (int i = 0; i < ndeps; i++) {
        printf("%s\n", deps->pares[i].clave);
    }

    _nd_liberar(doc);
    return EC_OK;
}
