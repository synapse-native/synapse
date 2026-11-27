// FASE 24 — Test de DB/SQLite (Manual 3 §12.1)
// TDD: este test ES la especificación. Si las funciones _syn_db_*
// no existen, el test NO compila — eso es correcto.
//
// Manual 3 §12.1: lib/db.syq — Conexión a SQLite
// Comando: pytest tests/syquex/test_db.py -v
// Criterio: CRUD completo, transacciones, NULL safety

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include "synapse_rt_types.h"
#include "runtime/core/db.h"

static int passed = 0;
static int failed = 0;

#define CHECK(cond, msg) do { \
    if (!(cond)) { printf("  [FAIL] %s\n", msg); failed++; } \
    else { printf("  [PASS] %s\n", msg); passed++; } \
} while(0)

#define CS(s) ((CadenaSegura){ .longitud = (int)strlen(s), .datos = (s) })

int main(void) {
    setbuf(stdout, NULL);

    /* Limpiar base anterior */
    remove("_test_r99.db");

    // === 1. Abrir / Cerrar ===
    printf("=== 1. Abrir / Cerrar ===\n");
    int64_t c = _syn_db_abrir(CS("_test_r99.db"));
    CHECK(c >= 0, "abrir retorna conn >= 0");
    CHECK(_syn_db_cambios_fila(c) == 0, "cambios_fila == 0 al abrir");

    // === 2. Ejecutar SQL ===
    printf("=== 2. Ejecutar SQL ===\n");
    int64_t r = _syn_db_ejecutar(c, CS(
        "CREATE TABLE IF NOT EXISTS test (id INTEGER PRIMARY KEY, nombre TEXT, edad REAL)"
    ));
    CHECK(r == 0, "CREATE TABLE rc=0");

    // === 3. INSERT ===
    printf("=== 3. INSERT ===\n");
    r = _syn_db_ejecutar(c, CS("INSERT INTO test (nombre, edad) VALUES ('Ana', 28.5)"));
    CHECK(r == 0, "INSERT rc=0");
    CHECK(_syn_db_cambios_fila(c) == 1, "cambios_fila == 1 tras INSERT");
    CHECK(_syn_db_ultima_id(c) == 1, "ultima_id == 1");

    r = _syn_db_ejecutar(c, CS("INSERT INTO test (nombre, edad) VALUES ('Bob', 35)"));
    CHECK(r == 0, "INSERT segundo rc=0");
    CHECK(_syn_db_ultima_id(c) == 2, "ultima_id == 2");

    // === 4. SELECT (cursor) ===
    printf("=== 4. SELECT ===\n");
    int64_t cur = _syn_db_consultar(c, CS("SELECT id, nombre, edad FROM test ORDER BY id"));
    CHECK(cur >= 0, "consultar retorna cursor >= 0");

    CHECK(_syn_db_cursor_siguiente(cur) == 1, "siguiente: fila 1");
    CHECK(_syn_db_cursor_entero(cur, 0) == 1, "fila 1 id == 1");
    CadenaSegura nom1 = _syn_db_cursor_texto(cur, 1);
    CHECK(nom1.longitud == 3 && memcmp(nom1.datos, "Ana", 3) == 0, "fila 1 nombre == 'Ana'");
    CHECK(_syn_db_cursor_decimal(cur, 2) > 28.0 && _syn_db_cursor_decimal(cur, 2) < 29.0,
          "fila 1 edad ~ 28.5");

    CHECK(_syn_db_cursor_siguiente(cur) == 1, "siguiente: fila 2");
    CHECK(_syn_db_cursor_entero(cur, 0) == 2, "fila 2 id == 2");
    CadenaSegura nom2 = _syn_db_cursor_texto(cur, 1);
    CHECK(nom2.longitud == 3 && memcmp(nom2.datos, "Bob", 3) == 0, "fila 2 nombre == 'Bob'");

    CHECK(_syn_db_cursor_siguiente(cur) == 0, "fin de resultados");

    _syn_db_cursor_cerrar(cur);

    // === 5. Nombre de columna ===
    printf("=== 5. Nombre de columna ===\n");
    cur = _syn_db_consultar(c, CS("SELECT nombre FROM test LIMIT 1"));
    _syn_db_cursor_siguiente(cur);
    CadenaSegura col = _syn_db_cursor_nombre_columna(cur, 0);
    CHECK(col.longitud == 6 && memcmp(col.datos, "nombre", 6) == 0, "nombre_columna == 'nombre'");
    _syn_db_cursor_cerrar(cur);

    // === 6. UPDATE ===
    printf("=== 6. UPDATE ===\n");
    r = _syn_db_ejecutar(c, CS("UPDATE test SET edad = 29.0 WHERE nombre = 'Ana'"));
    CHECK(r == 0, "UPDATE rc=0");
    CHECK(_syn_db_cambios_fila(c) == 1, "cambios_fila == 1 tras UPDATE");

    // === 7. DELETE ===
    printf("=== 7. DELETE ===\n");
    r = _syn_db_ejecutar(c, CS("DELETE FROM test WHERE nombre = 'Bob'"));
    CHECK(r == 0, "DELETE rc=0");
    CHECK(_syn_db_cambios_fila(c) == 1, "cambios_fila == 1 tras DELETE");

    // === 8. NULL ===
    printf("=== 8. NULL ===\n");
    _syn_db_ejecutar(c, CS("INSERT INTO test (nombre) VALUES (NULL)"));
    cur = _syn_db_consultar(c, CS("SELECT nombre FROM test WHERE id = 3"));
    _syn_db_cursor_siguiente(cur);
    CHECK(_syn_db_cursor_es_nulo(cur, 0) == 1, "nombre NULL detectado");
    _syn_db_cursor_cerrar(cur);

    // === 9. Transacciones ===
    printf("=== 9. Transacciones ===\n");
    _syn_db_ejecutar(c, CS("DELETE FROM test"));
    r = _syn_db_transaccion_iniciar(c);
    CHECK(r == 0, "BEGIN rc=0");
    _syn_db_ejecutar(c, CS("INSERT INTO test (nombre, edad) VALUES ('TX1', 10)"));
    _syn_db_ejecutar(c, CS("INSERT INTO test (nombre, edad) VALUES ('TX2', 20)"));
    r = _syn_db_transaccion_deshacer(c);
    CHECK(r == 0, "ROLLBACK rc=0");

    cur = _syn_db_consultar(c, CS("SELECT COUNT(*) as cnt FROM test"));
    _syn_db_cursor_siguiente(cur);
    CHECK(_syn_db_cursor_entero(cur, 0) == 0, "tras ROLLBACK: 0 filas");
    _syn_db_cursor_cerrar(cur);

    r = _syn_db_transaccion_iniciar(c);
    _syn_db_ejecutar(c, CS("INSERT INTO test (nombre, edad) VALUES ('TX3', 30)"));
    r = _syn_db_transaccion_confirmar(c);
    CHECK(r == 0, "COMMIT rc=0");

    cur = _syn_db_consultar(c, CS("SELECT COUNT(*) as cnt FROM test"));
    _syn_db_cursor_siguiente(cur);
    CHECK(_syn_db_cursor_entero(cur, 0) == 1, "tras COMMIT: 1 fila");
    _syn_db_cursor_cerrar(cur);

    // === 10. Último error ===
    printf("=== 10. Último error ===\n");
    r = _syn_db_ejecutar(c, CS("SELECT * FROM tabla_inexistente"));
    CHECK(r != 0, "SQL inválido rc != 0");
    CadenaSegura err = _syn_db_ultimo_error(c);
    CHECK(err.longitud > 0, "ultimo_error no vacío");

    // === 11. Cerrar ===
    printf("=== 11. Cerrar ===\n");
    _syn_db_cerrar(c);
    CHECK(1, "cerrar no crashea");

    /* Limpiar */
    remove("_test_r99.db");

    printf("\n=== RESULTADO: %d passed, %d failed ===\n", passed, failed);
    return failed > 0 ? 1 : 0;
}
