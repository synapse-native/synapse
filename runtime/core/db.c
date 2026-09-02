// cumple Manual 6 §4: base de datos
// runtime/core/db.c — Database module (SQLite bundled) for Syquex
// Manual 3 §12.1: lib/db.syq
// Compilar: gcc -c runtime/core/db.c -o db.o -Ivendor/sqlite3

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "synapse_rt_types.h"
#include "db.h"

/* Include SQLite amalgamation header */
#include "../../vendor/sqlite3/sqlite3.h"

// ============================================================
// Internal storage: connections and cursors (static tables)
// ============================================================

#define MAX_CONNECTIONS 32
#define MAX_CURSORS 64
#define ERROR_BUF_SIZE 256

typedef struct {
    sqlite3* db;
    char error[ERROR_BUF_SIZE];
    int active;
} DbConn;

typedef struct {
    sqlite3_stmt* stmt;
    int conn_idx;
    int active;
} DbCursor;

static DbConn _conns[MAX_CONNECTIONS];
static DbCursor _cursors[MAX_CURSORS];
static int _db_initialized = 0;

static void _db_init(void) {
    if (_db_initialized) return;
    memset(_conns, 0, sizeof(_conns));
    memset(_cursors, 0, sizeof(_cursors));
    _db_initialized = 1;
}

static int _find_free_conn(void) {
    for (int i = 0; i < MAX_CONNECTIONS; i++) {
        if (!_conns[i].active) return i;
    }
    return -1;
}

static int _find_free_cursor(void) {
    for (int i = 0; i < MAX_CURSORS; i++) {
        if (!_cursors[i].active) return i;
    }
    return -1;
}

// ============================================================
// §12.1 — Apertura / Cierre
// ============================================================

int64_t _syn_db_abrir(CadenaSegura ruta) {
    _db_init();
    if (ruta.datos == NULL || ruta.longitud <= 0) return -1;

    char* path = (char*)malloc(ruta.longitud + 1);
    if (!path) return -1;
    memcpy(path, ruta.datos, ruta.longitud);
    path[ruta.longitud] = '\0';

    int idx = _find_free_conn();
    if (idx < 0) { free(path); return -1; }

    sqlite3* db = NULL;
    int rc = sqlite3_open(path, &db);
    free(path);

    if (rc != SQLITE_OK) {
        if (db) sqlite3_close(db);
        return -1;
    }

    _conns[idx].db = db;
    _conns[idx].error[0] = '\0';
    _conns[idx].active = 1;
    return (int64_t)idx;
}

void _syn_db_cerrar(int64_t conn) {
    if (conn < 0 || conn >= MAX_CONNECTIONS) return;
    if (!_conns[conn].active) return;

    /* Close any open cursors for this connection */
    for (int i = 0; i < MAX_CURSORS; i++) {
        if (_cursors[i].active && _cursors[i].conn_idx == (int)conn) {
            if (_cursors[i].stmt) sqlite3_finalize(_cursors[i].stmt);
            _cursors[i].active = 0;
            _cursors[i].stmt = NULL;
        }
    }

    if (_conns[conn].db) sqlite3_close(_conns[conn].db);
    _conns[conn].db = NULL;
    _conns[conn].active = 0;
}

// ============================================================
// §12.1 — Ejecución directa
// ============================================================

int64_t _syn_db_ejecutar(int64_t conn, CadenaSegura sql) {
    if (conn < 0 || conn >= MAX_CONNECTIONS) return -1;
    if (!_conns[conn].active || !_conns[conn].db) return -1;
    if (sql.datos == NULL || sql.longitud <= 0) return -1;

    char* sql_c = (char*)malloc(sql.longitud + 1);
    if (!sql_c) return -1;
    memcpy(sql_c, sql.datos, sql.longitud);
    sql_c[sql.longitud] = '\0';

    char* err_msg = NULL;
    int rc = sqlite3_exec(_conns[conn].db, sql_c, NULL, NULL, &err_msg);
    free(sql_c);

    if (rc != SQLITE_OK) {
        if (err_msg) {
            strncpy(_conns[conn].error, err_msg, ERROR_BUF_SIZE - 1);
            _conns[conn].error[ERROR_BUF_SIZE - 1] = '\0';
            sqlite3_free(err_msg);
        }
        return (int64_t)rc;
    }
    _conns[conn].error[0] = '\0';
    return 0;
}

// ============================================================
// §12.1 — Consulta (cursor)
// ============================================================

int64_t _syn_db_consultar(int64_t conn, CadenaSegura sql) {
    if (conn < 0 || conn >= MAX_CONNECTIONS) return -1;
    if (!_conns[conn].active || !_conns[conn].db) return -1;
    if (sql.datos == NULL || sql.longitud <= 0) return -1;

    int cidx = _find_free_cursor();
    if (cidx < 0) return -1;

    char* sql_c = (char*)malloc(sql.longitud + 1);
    if (!sql_c) return -1;
    memcpy(sql_c, sql.datos, sql.longitud);
    sql_c[sql.longitud] = '\0';

    sqlite3_stmt* stmt = NULL;
    int rc = sqlite3_prepare_v2(_conns[conn].db, sql_c, -1, &stmt, NULL);
    free(sql_c);

    if (rc != SQLITE_OK) {
        if (stmt) sqlite3_finalize(stmt);
        const char* err = sqlite3_errmsg(_conns[conn].db);
        if (err) {
            strncpy(_conns[conn].error, err, ERROR_BUF_SIZE - 1);
            _conns[conn].error[ERROR_BUF_SIZE - 1] = '\0';
        }
        return -1;
    }

    _cursors[cidx].stmt = stmt;
    _cursors[cidx].conn_idx = (int)conn;
    _cursors[cidx].active = 1;
    return (int64_t)cidx;
}

int _syn_db_cursor_siguiente(int64_t cursor) {
    if (cursor < 0 || cursor >= MAX_CURSORS) return 0;
    if (!_cursors[cursor].active || !_cursors[cursor].stmt) return 0;
    int rc = sqlite3_step(_cursors[cursor].stmt);
    return (rc == SQLITE_ROW) ? 1 : 0;
}

int64_t _syn_db_cursor_num_columnas(int64_t cursor) {
    if (cursor < 0 || cursor >= MAX_CURSORS) return 0;
    if (!_cursors[cursor].active || !_cursors[cursor].stmt) return 0;
    return (int64_t)sqlite3_column_count(_cursors[cursor].stmt);
}

CadenaSegura _syn_db_cursor_nombre_columna(int64_t cursor, int64_t indice) {
    if (cursor < 0 || cursor >= MAX_CURSORS) return (CadenaSegura){0, ""};
    if (!_cursors[cursor].active || !_cursors[cursor].stmt) return (CadenaSegura){0, ""};
    const char* name = sqlite3_column_name(_cursors[cursor].stmt, (int)indice);
    if (!name) return (CadenaSegura){0, ""};
    int len = (int)strlen(name);
    char* dup = (char*)malloc(len + 1);
    if (!dup) return (CadenaSegura){0, ""};
    memcpy(dup, name, len + 1);
    return (CadenaSegura){.longitud = len, .datos = dup};
}

CadenaSegura _syn_db_cursor_texto(int64_t cursor, int64_t indice) {
    if (cursor < 0 || cursor >= MAX_CURSORS) return (CadenaSegura){0, ""};
    if (!_cursors[cursor].active || !_cursors[cursor].stmt) return (CadenaSegura){0, ""};
    const unsigned char* text = sqlite3_column_text(_cursors[cursor].stmt, (int)indice);
    if (!text) return (CadenaSegura){0, ""};
    int len = (int)strlen((const char*)text);
    char* dup = (char*)malloc(len + 1);
    if (!dup) return (CadenaSegura){0, ""};
    memcpy(dup, text, len + 1);
    return (CadenaSegura){.longitud = len, .datos = dup};
}

int64_t _syn_db_cursor_entero(int64_t cursor, int64_t indice) {
    if (cursor < 0 || cursor >= MAX_CURSORS) return 0;
    if (!_cursors[cursor].active || !_cursors[cursor].stmt) return 0;
    return (int64_t)sqlite3_column_int64(_cursors[cursor].stmt, (int)indice);
}

double _syn_db_cursor_decimal(int64_t cursor, int64_t indice) {
    if (cursor < 0 || cursor >= MAX_CURSORS) return 0.0;
    if (!_cursors[cursor].active || !_cursors[cursor].stmt) return 0.0;
    return sqlite3_column_double(_cursors[cursor].stmt, (int)indice);
}

int _syn_db_cursor_es_nulo(int64_t cursor, int64_t indice) {
    if (cursor < 0 || cursor >= MAX_CURSORS) return 1;
    if (!_cursors[cursor].active || !_cursors[cursor].stmt) return 1;
    return (sqlite3_column_type(_cursors[cursor].stmt, (int)indice) == SQLITE_NULL) ? 1 : 0;
}

void _syn_db_cursor_cerrar(int64_t cursor) {
    if (cursor < 0 || cursor >= MAX_CURSORS) return;
    if (!_cursors[cursor].active) return;
    if (_cursors[cursor].stmt) sqlite3_finalize(_cursors[cursor].stmt);
    _cursors[cursor].stmt = NULL;
    _cursors[cursor].active = 0;
}

// ============================================================
// §12.1 — Transacciones
// ============================================================

int64_t _syn_db_transaccion_iniciar(int64_t conn) {
    return _syn_db_ejecutar(conn, (CadenaSegura){9, "BEGIN"});
}

int64_t _syn_db_transaccion_confirmar(int64_t conn) {
    return _syn_db_ejecutar(conn, (CadenaSegura){7, "COMMIT"});
}

int64_t _syn_db_transaccion_deshacer(int64_t conn) {
    return _syn_db_ejecutar(conn, (CadenaSegura){9, "ROLLBACK"});
}

// ============================================================
// §12.1 — Información
// ============================================================

CadenaSegura _syn_db_ultimo_error(int64_t conn) {
    if (conn < 0 || conn >= MAX_CONNECTIONS) return (CadenaSegura){0, ""};
    if (!_conns[conn].active) return (CadenaSegura){0, ""};

    /* Try sqlite3_errmsg first */
    if (_conns[conn].db) {
        const char* msg = sqlite3_errmsg(_conns[conn].db);
        if (msg && msg[0] != '\0') {
            int len = (int)strlen(msg);
            char* dup = (char*)malloc(len + 1);
            if (dup) {
                memcpy(dup, msg, len + 1);
                return (CadenaSegura){.longitud = len, .datos = dup};
            }
        }
    }

    /* Fallback to stored error */
    int len = (int)strlen(_conns[conn].error);
    if (len == 0) return (CadenaSegura){0, ""};
    char* dup = (char*)malloc(len + 1);
    if (!dup) return (CadenaSegura){0, ""};
    memcpy(dup, _conns[conn].error, len + 1);
    return (CadenaSegura){.longitud = len, .datos = dup};
}

int64_t _syn_db_cambios_fila(int64_t conn) {
    if (conn < 0 || conn >= MAX_CONNECTIONS) return 0;
    if (!_conns[conn].active || !_conns[conn].db) return 0;
    return (int64_t)sqlite3_changes(_conns[conn].db);
}

int64_t _syn_db_ultima_id(int64_t conn) {
    if (conn < 0 || conn >= MAX_CONNECTIONS) return 0;
    if (!_conns[conn].active || !_conns[conn].db) return 0;
    return (int64_t)sqlite3_last_insert_rowid(_conns[conn].db);
}
