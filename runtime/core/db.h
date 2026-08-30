// runtime/core/db.h — Database (SQLite) module declarations
// Manual 3 §12.1: lib/db.syq

#ifndef SYNAPSE_RT_DB_H
#define SYNAPSE_RT_DB_H

#include "synapse_rt_types.h"

// §12.1 — Apertura / Cierre
int64_t _syn_db_abrir(CadenaSegura ruta);
void _syn_db_cerrar(int64_t conn);

// §12.1 — Ejecución directa
int64_t _syn_db_ejecutar(int64_t conn, CadenaSegura sql);

// §12.1 — Consulta (cursor)
int64_t _syn_db_consultar(int64_t conn, CadenaSegura sql);
int _syn_db_cursor_siguiente(int64_t cursor);
int64_t _syn_db_cursor_num_columnas(int64_t cursor);
CadenaSegura _syn_db_cursor_nombre_columna(int64_t cursor, int64_t indice);
CadenaSegura _syn_db_cursor_texto(int64_t cursor, int64_t indice);
int64_t _syn_db_cursor_entero(int64_t cursor, int64_t indice);
double _syn_db_cursor_decimal(int64_t cursor, int64_t indice);
int _syn_db_cursor_es_nulo(int64_t cursor, int64_t indice);
void _syn_db_cursor_cerrar(int64_t cursor);

// §12.1 — Transacciones
int64_t _syn_db_transaccion_iniciar(int64_t conn);
int64_t _syn_db_transaccion_confirmar(int64_t conn);
int64_t _syn_db_transaccion_deshacer(int64_t conn);

// §12.1 — Información
CadenaSegura _syn_db_ultimo_error(int64_t conn);
int64_t _syn_db_cambios_fila(int64_t conn);
int64_t _syn_db_ultima_id(int64_t conn);

#endif // SYNAPSE_RT_DB_H
