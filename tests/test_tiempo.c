// FASE 24 — Test de Tiempo (Manual 3 §12.1)
// TDD: este test ES la especificación. Si las funciones _syn_tiempo_*
// no existen, el test NO compila — eso es correcto.
//
// Manual 3 §12.1: lib/tiempo.syq — Fechas y tiempos
// Comando: pytest tests/syquex/test_tiempo.py -v
// Criterio: valores razonables para la fecha/hora del sistema

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <time.h>
#include "synapse_rt_types.h"
#include "runtime/core/tiempo.h"

static int passed = 0;
static int failed = 0;

#define CHECK(cond, msg) do { \
    if (!(cond)) { printf("  [FAIL] %s\n", msg); failed++; } \
    else { printf("  [PASS] %s\n", msg); passed++; } \
} while(0)

int main(void) {
    setbuf(stdout, NULL);
    struct tm* now = localtime(&(time_t){time(NULL)});
    int year = now->tm_year + 1900;
    int month = now->tm_mon + 1;
    int mday = now->tm_mday;
    int hour = now->tm_hour;
    int min = now->tm_min;

    // === 1. Timestamp Unix ===
    printf("=== 1. Timestamp Unix ===\n");
    int64_t ts = _syn_timestamp_unix();
    CHECK(ts > 1700000000, "timestamp_unix > 1700000000 (2023-11)");
    CHECK(ts < 2000000000, "timestamp_unix < 2000000000 (2033)");

    // === 2. Timestamp ms ===
    printf("=== 2. Timestamp ms ===\n");
    int64_t ts_ms = _syn_timestamp_ms();
    CHECK(ts_ms >= ts * 1000, "timestamp_ms >= timestamp_unix * 1000");
    CHECK(ts_ms < (ts + 2) * 1000, "timestamp_ms < (ts+2) * 1000");

    // === 3. Componentes de fecha ===
    printf("=== 3. Componentes de fecha ===\n");
    CHECK(_syn_tiempo_anio() == year, "anio coincide con sistema");
    CHECK(_syn_tiempo_mes() == month, "mes coincide con sistema");
    CHECK(_syn_tiempo_dia() == mday, "dia coincide con sistema");

    // === 4. Componentes de hora ===
    printf("=== 4. Componentes de hora ===\n");
    CHECK(_syn_tiempo_hora() == hour, "hora coincide con sistema");
    CHECK(_syn_tiempo_minuto() == min, "minuto coincide con sistema");
    CHECK(_syn_tiempo_segundo() >= 0 && _syn_tiempo_segundo() < 60,
          "segundo en rango 0-59");

    // === 5. Día de la semana ===
    printf("=== 5. Dia de semana ===\n");
    int64_t dow = _syn_tiempo_dia_semana();
    CHECK(dow >= 0 && dow <= 6, "dia_semana en rango 0-6");

    // === 6. Día del año ===
    printf("=== 6. Dia del anio ===\n");
    int64_t doy = _syn_tiempo_dia_anio();
    CHECK(doy >= 1 && doy <= 366, "dia_anio en rango 1-366");

    // === 7. Formateo fecha ===
    printf("=== 7. Formateo fecha ===\n");
    CadenaSegura fecha = _syn_tiempo_fecha_actual();
    CHECK(fecha.longitud == 10, "fecha_actual longitud == 10 (YYYY-MM-DD)");
    CHECK(fecha.datos[4] == '-' && fecha.datos[7] == '-',
          "fecha_actual formato YYYY-MM-DD");

    // === 8. Formateo hora ===
    printf("=== 8. Formateo hora ===\n");
    CadenaSegura hora_s = _syn_tiempo_hora_actual();
    CHECK(hora_s.longitud == 8, "hora_actual longitud == 8 (HH:MM:SS)");
    CHECK(hora_s.datos[2] == ':' && hora_s.datos[5] == ':',
          "hora_actual formato HH:MM:SS");

    // === 9. Formateo datetime ===
    printf("=== 9. Formateo datetime ===\n");
    CadenaSegura dt = _syn_tiempo_datetime_actual();
    CHECK(dt.longitud == 19, "datetime_actual longitud == 19 (YYYY-MM-DD HH:MM:SS)");
    CHECK(dt.datos[10] == ' ', "datetime_actual tiene espacio entre fecha y hora");

    // === 10. Diferencia ===
    printf("=== 10. Diferencia ===\n");
    CHECK(_syn_tiempo_diferencia_segundos(ts + 10, ts + 20) == 10,
          "diferencia(10, 20) == 10");
    CHECK(_syn_tiempo_diferencia_segundos(ts, ts) == 0,
          "diferencia(ts, ts) == 0");
    CHECK(_syn_tiempo_diferencia_segundos(ts + 5, ts) == -5,
          "diferencia(5, 0) == -5");

    printf("\n=== RESULTADO: %d passed, %d failed ===\n", passed, failed);
    return failed > 0 ? 1 : 0;
}
