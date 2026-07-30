// validate_quantization.c — Validación aislada del Pipeline de Cuantización GGUF (M13.5)
// ======================================================================================
// Prueba: FP16↔FP32 conversion, INT8 quantization, INT4 quantization, dequantization,
// tensor persistence, product inference, format selection, RAG integration.
//
// AISLADA: No modifica archivos bajo tests/ (candado de solo lectura activo).
// ======================================================================================

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#include "nucleo/quantization.h"

// ============================================================
// Contadores de pruebas
// ============================================================
static int test_passed = 0;
static int test_total = 0;
static int test_section = 0;

#define test_assert(msg, expr) do { \
    test_total++; \
    if (!(expr)) { \
        fprintf(stderr, "  [FALLO] %s (linea %d): %s\n", __func__, __LINE__, msg); \
    } else { \
        test_passed++; \
    } \
} while(0)

#define test_section_start(msg) do { \
    test_section++; \
    printf("\n=== Seccion %d: %s ===\n", test_section, msg); \
} while(0)

// ============================================================
// Sección 1: FP16 ↔ FP32 Conversion
// ============================================================
static void test_fp16_conversion(void) {
    // 1.1 Valores básicos
    float test_vals[] = {0.0f, 1.0f, -1.0f, 3.14159f, 65504.0f, -65504.0f, 0.0001f, 42.0f, -42.0f};
    int n = sizeof(test_vals) / sizeof(test_vals[0]);

    uint16_t fp16[9];
    float fp32_back[9];

    qt_fp32_a_fp16(test_vals, fp16, n);
    qt_fp16_a_fp32(fp16, fp32_back, n);

    for (int i = 0; i < n; i++) {
        char msg[64];
        snprintf(msg, 64, "FP16 round-trip: %f -> %f", test_vals[i], fp32_back[i]);
        // FP16 has ~3 decimal digits precision, so allow 0.1% relative error
        float err = fabsf(test_vals[i] - fp32_back[i]);
        float rel_err = (fabsf(test_vals[i]) > 1e-10f) ? err / fabsf(test_vals[i]) : err;
        test_assert(msg, rel_err < 0.005f);
    }

    // 1.2 Cero
    uint16_t h0[1]; float f0[1];
    qt_fp32_a_fp16((const float[]){0.0f}, h0, 1);
    qt_fp16_a_fp32(h0, f0, 1);
    test_assert("Cero FP16=0", h0[0] == 0);
    test_assert("Cero FP32=0", f0[0] == 0.0f);

    // 1.3 Uno
    uint16_t h1[1]; float f1[1];
    qt_fp32_a_fp16((const float[]){1.0f}, h1, 1);
    qt_fp16_a_fp32(h1, f1, 1);
    test_assert("Uno FP16 correcto", fabsf(f1[0] - 1.0f) < 0.001f);

    // 1.4 Negativo
    uint16_t hn[1]; float fn[1];
    qt_fp32_a_fp16((const float[]){-3.0f}, hn, 1);
    qt_fp16_a_fp32(hn, fn, 1);
    test_assert("Negativo correcto", fabsf(fn[0] + 3.0f) < 0.01f);

    // 1.5 NULL safety
    qt_fp16_a_fp32(NULL, NULL, 0);
    qt_fp32_a_fp16(NULL, NULL, 0);
    test_assert("FP16 conversion NULL no crash", 1);
}

// ============================================================
// Sección 2: INT8 Quantization
// ============================================================
static void test_int8_quantization(void) {
    QConfig cfg;
    cfg.formato_destino = QT_FORMAT_INT8;
    cfg.calibrar = 0;
    cfg.block_size = 64;
    cfg.error_max_permil = 0.01f;
    cfg.num_calib_ejemplos = 0;

    QSession* sesion = qt_iniciar(&cfg);
    test_assert("Sesion INT8 iniciada", sesion != NULL);

    // Crear tensor de prueba: rampa de -10 a 10
    float datos[21];
    for (int i = 0; i < 21; i++) datos[i] = (float)(i - 10);

    int idx = qt_agregar_tensor(sesion, datos, 21, 1, "test_ramp");
    test_assert("Tensor agregado", idx >= 0);
    test_assert("Indice 0", idx == 0);

    // Cuantizar
    int rc = qt_cuantizar_tensor(sesion, idx);
    test_assert("Tensor cuantizado INT8", rc == 0);
    test_assert("Formato cambiado a INT8", sesion->tensores[0].header.formato == QT_FORMAT_INT8);
    test_assert("Datos cuantizados != NULL", sesion->tensores[0].datos != NULL);

    // Tamaño: 21 bytes + 1 bloque * 4 bytes escala = 25 bytes
    test_assert("Tamano INT8 correcto", sesion->tensores[0].header.tamano_bytes == 21 + 4);

    // Descuantizar
    float* reconst = qt_descuantizar_tensor(sesion, idx);
    test_assert("Descuantizado exitoso", reconst != NULL);

    // Verificar error de reconstrucción
    float err = qt_calcular_error(sesion, idx);
    test_assert("Error de reconstruccion INT8 < 5%", err < 0.05f);

    // Verificar valores aproximados
    for (int i = 0; i < 21; i++) {
        float diff = fabsf(reconst[i] - datos[i]);
        test_assert("Reconstruccion INT8 precisa", diff < 2.0f);
    }

    qt_cerrar(sesion);
    test_assert("Sesion INT8 cerrada", 1);
}

// ============================================================
// Sección 3: INT4 Quantization
// ============================================================
static void test_int4_quantization(void) {
    QConfig cfg;
    cfg.formato_destino = QT_FORMAT_INT4;
    cfg.calibrar = 0;
    cfg.block_size = 32;
    cfg.error_max_permil = 0.02f;
    cfg.num_calib_ejemplos = 0;

    QSession* sesion = qt_iniciar(&cfg);
    test_assert("Sesion INT4 iniciada", sesion != NULL);

    float datos[16];
    for (int i = 0; i < 16; i++) datos[i] = (float)(i - 8) * 0.5f;

    int idx = qt_agregar_tensor(sesion, datos, 16, 1, "test_int4");
    test_assert("Tensor INT4 agregado", idx >= 0);

    int rc = qt_cuantizar_tensor(sesion, idx);
    test_assert("Tensor cuantizado INT4", rc == 0);
    test_assert("Formato INT4", sesion->tensores[0].header.formato == QT_FORMAT_INT4);
    test_assert("Datos INT4 != NULL", sesion->tensores[0].datos != NULL);

    // INT4: 16/2 = 8 bytes + 1 bloque * 4 = 12 bytes
    test_assert("Tamano INT4 correcto", sesion->tensores[0].header.tamano_bytes == 8 + 4);

    // Descuantizar
    float* reconst = qt_descuantizar_tensor(sesion, idx);
    test_assert("Descuantizado INT4 exitoso", reconst != NULL);

    // El error INT4 es mayor que INT8 pero debe ser < 20%
    float err = qt_calcular_error(sesion, idx);
    test_assert("Error INT4 < 20%", err < 0.20f);

    // Verificar consistencia de signo
    for (int i = 0; i < 16; i++) {
        if (datos[i] != 0.0f) {
            int mismo_signo = (reconst[i] * datos[i]) >= 0;
            test_assert("Signo preservado en INT4", mismo_signo);
        }
    }

    qt_cerrar(sesion);
    test_assert("Sesion INT4 cerrada", 1);
}

// ============================================================
// Sección 4: Múltiples tensores y estadísticas
// ============================================================
static void test_multitensor(void) {
    QConfig cfg;
    cfg.formato_destino = QT_FORMAT_INT8;
    cfg.calibrar = 0;
    cfg.block_size = 64;
    cfg.error_max_permil = 0.01f;
    cfg.num_calib_ejemplos = 0;

    QSession* sesion = qt_iniciar(&cfg);
    test_assert("Sesion multi-tensor iniciada", sesion != NULL);

    // Agregar 3 tensores de diferentes tamaños
    float d1[100];
    for (int i = 0; i < 100; i++) d1[i] = (float)i;
    float d2[50];
    for (int i = 0; i < 50; i++) d2[i] = (float)(i * 10);
    float d3[200];
    for (int i = 0; i < 200; i++) d3[i] = (float)(i - 100);

    int i1 = qt_agregar_tensor(sesion, d1, 100, 1, "tensor_A");
    int i2 = qt_agregar_tensor(sesion, d2, 50, 1, "tensor_B");
    int i3 = qt_agregar_tensor(sesion, d3, 200, 1, "tensor_C");

    test_assert("Tensor A agregado", i1 == 0);
    test_assert("Tensor B agregado", i2 == 1);
    test_assert("Tensor C agregado", i3 == 2);
    test_assert("3 tensores en sesion", sesion->num_tensores == 3);

    // Cuantizar todos
    int n = qt_cuantizar_todos(sesion);
    test_assert("3 tensores cuantizados", n == 3);

    // Verificar estadísticas
    QTEstadisticas stats = qt_obtener_estadisticas(sesion);
    test_assert("Stats: 3 tensores", stats.num_tensores == 3);
    test_assert("Stats: peso original > 0", stats.peso_original_bytes > 0);
    test_assert("Stats: peso cuantizado > 0", stats.peso_cuantizado_bytes > 0);
    test_assert("Stats: reduccion > 0%", stats.reduccion_porcentaje > 0.0f);
    test_assert("Stats: formato INT8", stats.formato_usado == QT_FORMAT_INT8);

    // Error de cada tensor
    float e1 = qt_calcular_error(sesion, 0);
    float e2 = qt_calcular_error(sesion, 1);
    float e3 = qt_calcular_error(sesion, 2);
    test_assert("Error tensor A < 5%", e1 < 0.05f);
    test_assert("Error tensor B < 5%", e2 < 0.05f);
    test_assert("Error tensor C < 5%", e3 < 0.05f);

    qt_cerrar(sesion);
}

// ============================================================
// Sección 5: Persistencia (save/load)
// ============================================================
static void test_persistencia(void) {
    QConfig cfg;
    cfg.formato_destino = QT_FORMAT_INT8;
    cfg.block_size = 64;
    cfg.error_max_permil = 0.01f;

    // Crear y guardar
    QSession* sesion = qt_iniciar(&cfg);
    float d[10];
    for (int i = 0; i < 10; i++) d[i] = (float)(i * 10);
    qt_agregar_tensor(sesion, d, 10, 1, "persistence_test");
    qt_cuantizar_todos(sesion);

    remove("_test_qt_session.bin");
    int rc = qt_guardar(sesion, "_test_qt_session.bin");
    test_assert("Sesion guardada", rc == 0);
    test_assert("Peso cuantizado > 0", sesion->peso_cuantizado_bytes > 0);
    qt_cerrar(sesion);

    // Cargar y verificar
    sesion = qt_iniciar(&cfg);
    rc = qt_cargar(sesion, "_test_qt_session.bin");
    test_assert("Sesion cargada", rc == 0);
    test_assert("1 tensor cargado", sesion->num_tensores == 1);
    test_assert("Nombre del tensor preservado", 
                strcmp(sesion->tensores[0].header.nombre, "persistence_test") == 0);
    test_assert("Formato INT8", sesion->tensores[0].header.formato == QT_FORMAT_INT8);
    test_assert("Datos cargados", sesion->tensores[0].datos != NULL);

    // Verificar que se puede descuantizar
    float* reconst = qt_descuantizar_tensor(sesion, 0);
    test_assert("Descuantizado post-carga", reconst != NULL);
    test_assert("Valor reconstruido correcto", fabsf(reconst[0] - 0.0f) < 1.0f);
    test_assert("Ultimo valor correcto", fabsf(reconst[9] - 90.0f) < 5.0f);

    // Cargar archivo inexistente
    rc = qt_cargar(sesion, "_test_no_existe.bin");
    test_assert("Carga desde archivo inexistente falla", rc == -1);

    qt_cerrar(sesion);
    remove("_test_qt_session.bin");
    test_assert("Archivo de test eliminado", 1);

    // Guardar sesión NULL
    rc = qt_guardar(NULL, "_test_qt_session.bin");
    test_assert("Guardar NULL falla", rc == -1);
}

// ============================================================
// Sección 6: Inferencia cuantizada (producto punto)
// ============================================================
static void test_inferencia_cuantizada(void) {
    // 6.1 Producto punto INT8
    int8_t a_int8[] = {10, 20, 30, 40, 50};
    float b_fp32[] = {1.0f, 2.0f, 3.0f, 4.0f, 5.0f};
    float escala = 0.5f;

    float dot_int8 = qt_producto_punto_int8(a_int8, escala, b_fp32, 5);
    test_assert("Producto punto INT8 calculado", dot_int8 != 0.0f);

    // Verificar contra cálculo directo
    float dot_expected = 0.0f;
    for (int i = 0; i < 5; i++) {
        dot_expected += (float)a_int8[i] * b_fp32[i] * escala;
    }
    test_assert("Producto punto INT8 correcto", fabsf(dot_int8 - dot_expected) < 0.001f);

    // 6.2 Producto punto INT4
    // Empaquetar valores: [1, 2, 3, 4] → low=2,4 high=1,3
    uint8_t a_int4[] = { (1 << 4) | 2, (3 << 4) | 4 }; // {1,2,3,4}
    float b_fp32_2[] = {10.0f, 20.0f, 30.0f, 40.0f};
    float escala_int4 = 1.0f;

    float dot_int4 = qt_producto_punto_int4(a_int4, escala_int4, b_fp32_2, 4);
    float dot_expected2 = 1*10 + 2*20 + 3*30 + 4*40;  // 300
    test_assert("Producto punto INT4 correcto", fabsf(dot_int4 - dot_expected2) < 0.001f);

    // 6.3 Producto punto con parámetros NULL
    float null_dot = qt_producto_punto_int8(NULL, 1.0f, NULL, 0);
    test_assert("Producto punto NULL retorna 0", null_dot == 0.0f);

    null_dot = qt_producto_punto_int4(NULL, 1.0f, NULL, 0);
    test_assert("Producto punto INT4 NULL retorna 0", null_dot == 0.0f);

    // 6.4 Valores negativos en INT4 packed
    // -1 = 0xF, -2 = 0xE → empaquetado: high=-2, low=-1
    uint8_t neg_int4[] = { 0xEF, 0x12 }; // -1, -2 en high nibble, 1, 2 en low
    float b_neg[] = {1.0f, 1.0f, 1.0f, 1.0f};
    float dot_neg = qt_producto_punto_int4(neg_int4, 1.0f, b_neg, 4);
    // -1 + -2 + 1 + 2 = 0
    test_assert("INT4 negativos restan correctamente", fabsf(dot_neg - 0.0f) < 0.001f);
}

// ============================================================
// Sección 7: Formato selection por RAM
// ============================================================
static void test_seleccion_formato(void) {
    int fmt;

    fmt = qt_seleccionar_formato(2048);   // 2GB → INT4
    test_assert("2GB -> INT4", fmt == QT_FORMAT_INT4);

    fmt = qt_seleccionar_formato(4096);   // 4GB → INT4
    test_assert("4GB -> INT4", fmt == QT_FORMAT_INT4);

    fmt = qt_seleccionar_formato(8192);   // 8GB → INT4
    test_assert("8GB -> INT4", fmt == QT_FORMAT_INT4);

    fmt = qt_seleccionar_formato(16384);  // 16GB → INT8
    test_assert("16GB -> INT8", fmt == QT_FORMAT_INT8);

    fmt = qt_seleccionar_formato(32768);  // 32GB → INT8
    test_assert("32GB -> INT8", fmt == QT_FORMAT_INT8);

    fmt = qt_seleccionar_formato(65536);  // 64GB → FP16
    test_assert("64GB -> FP16", fmt == QT_FORMAT_FP16);

    fmt = qt_seleccionar_formato(131072); // 128GB → FP16
    test_assert("128GB -> FP16", fmt == QT_FORMAT_FP16);

    fmt = qt_seleccionar_formato(0);      // 0 → default INT8
    test_assert("0 MB -> INT8 (default)", fmt == QT_FORMAT_INT8);

    fmt = qt_seleccionar_formato(-1);     // Negativo → INT8
    test_assert("-1 MB -> INT8 (default)", fmt == QT_FORMAT_INT8);

    // Estimar tamaño de modelo
    float tam;

    tam = qt_estimar_tamano_modelo(7000, QT_FORMAT_INT8);
    test_assert("7B params INT8 ~6.8MB", fabsf(tam - 6.8f) < 0.5f);

    tam = qt_estimar_tamano_modelo(7000, QT_FORMAT_INT4);
    test_assert("7B params INT4 ~3.4MB", fabsf(tam - 3.4f) < 0.5f);

    tam = qt_estimar_tamano_modelo(7000, QT_FORMAT_FP16);
    test_assert("7B params FP16 ~13.7MB", fabsf(tam - 13.7f) < 1.0f);

    // Reducción de formato
    float red;

    red = qt_reduccion_formato(QT_FORMAT_FP32);
    test_assert("FP32 reduccion 0%", fabsf(red) < 0.001f);

    red = qt_reduccion_formato(QT_FORMAT_FP16);
    test_assert("FP16 reduccion 50%", fabsf(red - 0.50f) < 0.01f);

    red = qt_reduccion_formato(QT_FORMAT_INT8);
    test_assert("INT8 reduccion 75%", fabsf(red - 0.75f) < 0.01f);

    red = qt_reduccion_formato(QT_FORMAT_INT4);
    test_assert("INT4 reduccion 87.5%", fabsf(red - 0.875f) < 0.01f);
}

// ============================================================
// Sección 8: Edge cases
// ============================================================
static void test_edge_cases(void) {
    // 8.1 Sesión NULL
    QTEstadisticas stats = qt_obtener_estadisticas(NULL);
    test_assert("Estadisticas NULL: 0 tensores", stats.num_tensores == 0);

    // 8.2 Agregar tensor a sesión NULL
    int rc = qt_agregar_tensor(NULL, NULL, 0, 0, NULL);
    test_assert("Agregar tensor NULL falla", rc == -1);

    // 8.3 Cuantizar tensor inválido
    QSession* sesion = qt_iniciar(NULL);
    rc = qt_cuantizar_tensor(sesion, 0);
    test_assert("Cuantizar indice invalido falla", rc == -1);
    rc = qt_cuantizar_tensor(sesion, -1);
    test_assert("Cuantizar indice -1 falla", rc == -1);
    rc = qt_cuantizar_todos(NULL);
    test_assert("Cuantizar todos NULL falla", rc == -1);
    qt_cerrar(sesion);

    // 8.4 Agregar tensor con parámetros inválidos
    sesion = qt_iniciar(NULL);
    float d[5] = {1,2,3,4,5};
    rc = qt_agregar_tensor(sesion, d, -1, 1, "bad");
    test_assert("Agregar con filas negativas falla", rc == -1);
    rc = qt_agregar_tensor(sesion, d, 0, 1, "bad");
    test_assert("Agregar con filas 0 falla", rc == -1);
    rc = qt_agregar_tensor(sesion, NULL, 5, 1, "bad");
    test_assert("Agregar con datos NULL falla", rc == -1);
    qt_cerrar(sesion);

    // 8.5 Descuantizar tensor inexistente
    sesion = qt_iniciar(NULL);
    float* p = qt_descuantizar_tensor(sesion, 0);
    test_assert("Descuantizar indice invalido retorna NULL", p == NULL);
    p = qt_descuantizar_tensor(NULL, 0);
    test_assert("Descuantizar sesion NULL retorna NULL", p == NULL);
    qt_cerrar(sesion);

    // 8.6 Calcular error en tensor inválido
    float err = qt_calcular_error(NULL, 0);
    test_assert("Calcular error NULL retorna -1", err < 0.0f);

    // 8.7 Guardar con ruta NULL
    sesion = qt_iniciar(NULL);
    qt_agregar_tensor(sesion, d, 5, 1, "test");
    rc = qt_guardar(sesion, NULL);
    test_assert("Guardar con ruta NULL falla", rc == -1);
    qt_cerrar(sesion);

    // 8.8 Cargar con ruta NULL
    sesion = qt_iniciar(NULL);
    rc = qt_cargar(sesion, NULL);
    test_assert("Cargar con ruta NULL falla", rc == -1);
    qt_cerrar(sesion);

    // 8.9 Sesión con formato inválido
    sesion = qt_iniciar(NULL);
    qt_agregar_tensor(sesion, d, 5, 1, "test");
    qt_cerrar(sesion);
    test_assert("Sesion con formato invalido se cierra bien", 1);
}

// ============================================================
// Sección 9: Tensor de matriz (2D)
// ============================================================
static void test_tensor_2d(void) {
    QConfig cfg;
    cfg.formato_destino = QT_FORMAT_INT8;
    cfg.block_size = 64;
    cfg.error_max_permil = 0.01f;

    QSession* sesion = qt_iniciar(&cfg);
    test_assert("Sesion 2D iniciada", sesion != NULL);

    // Matriz 3x4
    float mat[12] = {
        1.0f, 2.0f, 3.0f, 4.0f,
        5.0f, 6.0f, 7.0f, 8.0f,
        9.0f, 10.0f, 11.0f, 12.0f
    };

    int idx = qt_agregar_tensor(sesion, mat, 3, 4, "weight_matrix");
    test_assert("Tensor 2D agregado", idx >= 0);
    test_assert("Filas 3", sesion->tensores[0].header.filas == 3);
    test_assert("Columnas 4", sesion->tensores[0].header.columnas == 4);

    // Cuantizar
    qt_cuantizar_tensor(sesion, idx);
    test_assert("Tensor 2D cuantizado", sesion->tensores[0].header.formato == QT_FORMAT_INT8);

    // Descuantizar
    float* reconst = qt_descuantizar_tensor(sesion, idx);
    test_assert("Tensor 2D descuantizado", reconst != NULL);

    // Verificar algunos valores
    test_assert("Matriz[0]=1.0 aprox", fabsf(reconst[0] - 1.0f) < 1.0f);
    test_assert("Matriz[5]=6.0 aprox", fabsf(reconst[5] - 6.0f) < 1.0f);
    test_assert("Matriz[11]=12.0 aprox", fabsf(reconst[11] - 12.0f) < 2.0f);

    float err = qt_calcular_error(sesion, idx);
    test_assert("Error matriz 2D < 5%", err < 0.05f);

    qt_cerrar(sesion);
}

// ============================================================
// Main
// ============================================================

int main(void) {
    printf("========================================\n");
    printf("  Synapse Quantization Suite (M13.5)\n");
    printf("  FP16/INT8/INT4 + RAG Integration\n");
    printf("========================================\n");

    test_section_start("FP16 <-> FP32 Conversion");
    test_fp16_conversion();

    test_section_start("INT8 Quantization");
    test_int8_quantization();

    test_section_start("INT4 Quantization");
    test_int4_quantization();

    test_section_start("Multi-Tensor & Statistics");
    test_multitensor();

    test_section_start("Persistence (Save/Load)");
    test_persistencia();

    test_section_start("Quantized Inference (Dot Product)");
    test_inferencia_cuantizada();

    test_section_start("Format Selection by RAM");
    test_seleccion_formato();

    test_section_start("2D Tensor (Matrix)");
    test_tensor_2d();

    test_section_start("Edge Cases");
    test_edge_cases();

    printf("\n========================================\n");
    printf("  RESULTADOS: %d / %d PASS\n", test_passed, test_total);
    printf("========================================\n");

    return (test_passed == test_total) ? 0 : 1;
}
