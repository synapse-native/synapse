/*
 * test_axon_serializacion.c — R84: Serialización binaria de valores
 *
 * Manual 6 §5.2 (serializar_valor / deserializar_valor) y tablas de tipos
 * Manual 5 §6.3 / Manual 6 §5.1. Verifica:
 *   - Bytes EXACTOS del ejemplo del Manual 5 §6.3 (entero 42 como [0x02]+4B BE)
 *   - Decodificación adaptativa de enteros (acepta 0x00/0x01/0x02/0x03)
 *   - Roundtrip de decimal64/decimal32(→normaliza a 64), texto, tensor,
 *     lista y mapa etiquetados
 *   - Rechazo: buffer truncado, ESTRUCTURA (0x08), tipo desconocido
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "synapse_rt_types.h"
#include "runtime/core/axon.h"

static int tests_passed = 0, tests_failed = 0;
static void check(int cond, const char* nombre) {
    if (cond) { printf("[PASS] %s\n", nombre); tests_passed++; }
    else      { printf("[FAIL] %s\n", nombre); tests_failed++; }
}

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    uint8_t* buf = NULL; size_t len = 0;

    /* ===== Entero: ejemplo literal del Manual 5 §6.3 ===== */
    {
        int64_t v = 42;
        _syn_axon_serializar_valor(&v, AXON_T_ENTERO32, &buf, &len);
        check(len == 5 && buf[0] == 0x02 && buf[1] == 0 && buf[2] == 0 &&
              buf[3] == 0 && buf[4] == 0x2A,
              "S1 entero 42 = [0x02][00 00 00 2A] (Manual 5 §6.3)");
        int tipo = 0;
        AxonValor* d = (AxonValor*)_syn_axon_deserializar_valor(buf, len, &tipo);
        check(d != NULL && tipo == AXON_T_ENTERO32 && d->dato.entero == 42,
              "S2 decodificacion entero 42");
        _syn_axon_liberar_valor(d); free(buf);
    }

    /* ===== Decodificación adaptativa de anchos ===== */
    {
        int ok = 1;
        const uint8_t b8[]  = {AXON_T_ENTERO8, 0x2A};
        const uint8_t b16[] = {AXON_T_ENTERO16, 0x01, 0x2C};   // 300
        const uint8_t b64[] = {AXON_T_ENTERO64, 0xFF,0xFF,0xFF,0xFF,
                               0xFF,0xFF,0xFF,0xC6};           // -58
        int tipo; AxonValor* d;
        d = (AxonValor*)_syn_axon_deserializar_valor(b8, sizeof b8, &tipo);
        ok &= d && d->dato.entero == 42;   _syn_axon_liberar_valor(d);
        d = (AxonValor*)_syn_axon_deserializar_valor(b16, sizeof b16, &tipo);
        ok &= d && d->dato.entero == 300;  _syn_axon_liberar_valor(d);
        d = (AxonValor*)_syn_axon_deserializar_valor(b64, sizeof b64, &tipo);
        ok &= d && d->dato.entero == -58;  _syn_axon_liberar_valor(d);
        check(ok, "S3 decodificacion adaptativa 8/16/64 bits");
    }

    /* ===== Decimal 64 y 32 ===== */
    {
        double pi = 3.141592653589793;
        _syn_axon_serializar_valor(&pi, AXON_T_DECIMAL64, &buf, &len);
        int tipo; AxonValor* d =
            (AxonValor*)_syn_axon_deserializar_valor(buf, len, &tipo);
        check(d != NULL && tipo == AXON_T_DECIMAL64 &&
              fabs(d->dato.decimal - pi) < 1e-15, "S4 decimal64 roundtrip");
        _syn_axon_liberar_valor(d); free(buf);

        double half = 0.5;
        _syn_axon_serializar_valor(&half, AXON_T_DECIMAL32, &buf, &len);
        d = (AxonValor*)_syn_axon_deserializar_valor(buf, len, &tipo);
        check(d != NULL && tipo == AXON_T_DECIMAL64 &&
              fabs(d->dato.decimal - 0.5) < 1e-7,
              "S5 decimal32 normaliza a decimal64");
        _syn_axon_liberar_valor(d); free(buf);
    }

    /* ===== Texto: bytes exactos ===== */
    {
        _syn_axon_serializar_valor("hola", AXON_T_TEXTO, &buf, &len);
        check(len == 9 && buf[0] == 0x06 && buf[1] == 0 && buf[2] == 0 &&
              buf[3] == 0 && buf[4] == 4 && memcmp(buf + 5, "hola", 4) == 0,
              "S6 texto \"hola\" = [0x06][4BE][UTF-8]");
        int tipo; AxonValor* d =
            (AxonValor*)_syn_axon_deserializar_valor(buf, len, &tipo);
        check(d != NULL && strcmp(d->dato.texto, "hola") == 0, "S7 texto roundtrip");
        _syn_axon_liberar_valor(d); free(buf);
    }

    /* ===== Nulo / booleanos ===== */
    {
        int ok = 1, tipo;
        int64_t dummy = 0;
        _syn_axon_serializar_valor(&dummy, AXON_T_NULO, &buf, &len);
        AxonValor* d = (AxonValor*)_syn_axon_deserializar_valor(buf, len, &tipo);
        ok &= (buf[0] == 0xC0) && d && tipo == AXON_T_NULO;
        _syn_axon_liberar_valor(d); free(buf);
        _syn_axon_serializar_valor(&dummy, AXON_T_VERDADERO, &buf, &len);
        d = (AxonValor*)_syn_axon_deserializar_valor(buf, len, &tipo);
        ok &= (buf[0] == 0xC3) && d && d->dato.entero == 1;
        _syn_axon_liberar_valor(d); free(buf);
        check(ok, "S8 nulo/verdadero");
    }

    /* ===== Tensor 2x2 ===== */
    {
        float datos[4] = {1.0f, 2.0f, 3.5f, -4.25f};
        Tensor t = {2, 2, datos, 0};
        _syn_axon_serializar_valor(&t, AXON_T_TENSOR, &buf, &len);
        check(len == 1 + 8 + 16, "S9 tamano tensor 2x2");
        int tipo; AxonValor* d =
            (AxonValor*)_syn_axon_deserializar_valor(buf, len, &tipo);
        check(d != NULL && d->dato.tensor->filas == 2 &&
              d->dato.tensor->columnas == 2 &&
              fabsf(d->dato.tensor->datos[2] - 3.5f) < 1e-6 &&
              fabsf(d->dato.tensor->datos[3] + 4.25f) < 1e-6,
              "S10 tensor roundtrip");
        _syn_axon_liberar_valor(d); free(buf);
    }

    /* ===== Lista etiquetada ===== */
    {
        int64_t a = 10, b = 20;
        AxonValor elems[2];
        memset(elems, 0, sizeof elems);
        elems[0].tipo = AXON_T_ENTERO64; elems[0].dato.entero = a;
        elems[1].tipo = AXON_T_ENTERO64; elems[1].dato.entero = b;
        AxonLista l = {2, elems};
        _syn_axon_serializar_valor(&l, AXON_T_LISTA, &buf, &len);
        int tipo; AxonValor* d =
            (AxonValor*)_syn_axon_deserializar_valor(buf, len, &tipo);
        check(d != NULL && d->tipo == AXON_T_LISTA && d->dato.lista.n == 2 &&
              d->dato.lista.elems[0].dato.entero == 10 &&
              d->dato.lista.elems[1].dato.entero == 20, "S11 lista roundtrip");
        _syn_axon_liberar_valor(d); free(buf);
    }

    /* ===== Mapa etiquetado ===== */
    {
        int64_t uno = 1;
        char clave[] = "a";
        AxonValor v; memset(&v, 0, sizeof v);
        v.tipo = AXON_T_ENTERO64; v.dato.entero = uno;
        AxonPar par = {clave, &v};
        AxonMapa m = {1, &par};
        _syn_axon_serializar_valor(&m, AXON_T_MAPA, &buf, &len);
        int tipo; AxonValor* d =
            (AxonValor*)_syn_axon_deserializar_valor(buf, len, &tipo);
        check(d != NULL && d->tipo == AXON_T_MAPA && d->dato.mapa.n == 1 &&
              strcmp(d->dato.mapa.pares[0].clave, "a") == 0 &&
              d->dato.mapa.pares[0].valor->dato.entero == 1,
              "S12 mapa roundtrip");
        _syn_axon_liberar_valor(d); free(buf);
    }

    /* ===== Rechazos ===== */
    {
        int tipo = 0;
        int64_t v = 42;
        _syn_axon_serializar_valor(&v, AXON_T_ENTERO32, &buf, &len);
        check(_syn_axon_deserializar_valor(buf, len - 1, &tipo) == NULL,
              "S13 buffer truncado rechazado");
        free(buf);
        buf = (uint8_t*)malloc(2); buf[0] = 0x08; buf[1] = 0x00; // ESTRUCTURA
        check(_syn_axon_deserializar_valor(buf, 2, &tipo) == NULL,
              "S14 estructura 0x08 no soportada (sin esquema)");
        buf[0] = 0xFF;                                            // desconocido
        check(_syn_axon_deserializar_valor(buf, 2, &tipo) == NULL,
              "S15 tipo desconocido rechazado");
        free(buf);
    }

    printf("RESUMEN: Exitos: %d Fallos: %d\n", tests_passed, tests_failed);
    printf(tests_failed == 0 ? "[PASS] 0 fallos\n" : "[FAIL] hay fallos\n");
    return tests_failed == 0 ? 0 : 1;
}
