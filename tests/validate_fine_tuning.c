// validate_fine_tuning.c — Validación aislada del Pipeline de Fine-Tuning (M13.4)
// ================================================================================
// Prueba: LoRA adapter initialization, training step, loss computation,
// weight persistence (save/load), RAG re-ranking integration, edge cases.
//
// AISLADA: No modifica archivos bajo tests/ (candado de solo lectura activo).
// ================================================================================

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>

// ============================================================
// Incluir implementaciones directamente (test aislado)
// ============================================================
#include "nucleo/fine_tuning.h"
#include "nucleo/synapse_rag.h"

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
// Sección 1: Inicialización de sesión de fine-tuning
// ============================================================
static void test_inicializacion(void) {
    // 1.1 Crear sesión con configuración por defecto
    FTSession* sesion = ft_iniciar(NULL, NULL);
    test_assert("ft_iniciar(NULL, NULL) retorna sesion valida", sesion != NULL);
    test_assert("Sesion inicializada con estado 0", sesion->estado == 0);
    test_assert("Sesion sin adaptadores al inicio", sesion->num_adaptadores == 0);
    test_assert("Sesion sin ejemplos al inicio", sesion->dataset.num_ejemplos == 0);
    test_assert("Sesion con paso 0", sesion->paso_actual == 0);
    test_assert("Sesion con perdida 0", sesion->perdida_actual == 0.0f);
    test_assert("Learning rate por defecto 0.0001", sesion->config.learning_rate == 0.0001f);
    test_assert("Rank por defecto 8", sesion->config.rank == 8);
    test_assert("Alpha por defecto 16.0", sesion->config.alpha == 16.0f);
    ft_cerrar(sesion);

    // 1.2 Crear sesión con configuración personalizada
    FTConfig cfg;
    cfg.learning_rate = 0.001f;
    cfg.rank = 4;
    cfg.alpha = 8.0f;
    cfg.num_epochs = 3;
    cfg.batch_size = 2;
    cfg.weight_decay = 0.01f;
    cfg.grad_clip_norm = 1.0f;

    sesion = ft_iniciar(NULL, &cfg);
    test_assert("ft_iniciar con config personalizada", sesion != NULL);
    test_assert("LR personalizado 0.001", sesion->config.learning_rate == 0.001f);
    test_assert("Rank personalizado 4", sesion->config.rank == 4);
    test_assert("Alpha personalizado 8.0", sesion->config.alpha == 8.0f);
    test_assert("Epochs personalizado 3", sesion->config.num_epochs == 3);
    test_assert("Weight decay 0.01", sesion->config.weight_decay == 0.01f);
    ft_cerrar(sesion);

    // 1.3 Cerrar sesión nula
    ft_cerrar(NULL);
    test_assert("ft_cerrar(NULL) no crash", 1);
}

// ============================================================
// Sección 2: Adaptadores LoRA
// ============================================================
static void test_adaptadores_lora(void) {
    FTSession* sesion = ft_iniciar(NULL, NULL);
    test_assert("Sesion iniciada", sesion != NULL);

    // 2.1 Agregar adaptador para atención Q
    int idx = ft_agregar_adaptador(sesion, 0, FT_LAYER_ATTN_Q, 8, 16.0f, 4096, 4096);
    test_assert("Adaptador Q agregado", idx >= 0);
    test_assert("Indice del primer adaptador es 0", idx == 0);
    test_assert("Un adaptador en sesion", sesion->num_adaptadores == 1);
    test_assert("Capa idx 0", sesion->adaptadores[0].capa_idx == 0);
    test_assert("Tipo ATTN_Q", sesion->adaptadores[0].tipo_capa == FT_LAYER_ATTN_Q);
    test_assert("Rank 8", sesion->adaptadores[0].rank == 8);
    test_assert("Alpha 16.0", sesion->adaptadores[0].alpha == 16.0f);
    test_assert("Dim in 4096", sesion->adaptadores[0].dim_in == 4096);
    test_assert("Dim out 4096", sesion->adaptadores[0].dim_out == 4096);
    test_assert("A inicializado (no nulo)", sesion->adaptadores[0].A != NULL);
    test_assert("B inicializado (no nulo)", sesion->adaptadores[0].B != NULL);
    test_assert("Activo por defecto", sesion->adaptadores[0].activo == 1);

    // 2.2 Agregar adaptador para FFN
    idx = ft_agregar_adaptador(sesion, 0, FT_LAYER_FFN_DOWN, 4, 8.0f, 4096, 11008);
    test_assert("Adaptador FFN down agregado", idx == 1);
    test_assert("Dos adaptadores en sesion", sesion->num_adaptadores == 2);
    test_assert("FFN rank 4", sesion->adaptadores[1].rank == 4);
    test_assert("FFN dim_out 11008", sesion->adaptadores[1].dim_out == 11008);

    // 2.3 Agregar adaptador con rank inválido
    idx = ft_agregar_adaptador(sesion, 0, FT_LAYER_ATTN_V, 0, 0.0f, 4096, 4096);
    test_assert("Rank 0 usa rank por defecto (8)", idx >= 0);
    test_assert("Rank por defecto aplicado", sesion->adaptadores[2].rank == 8);

    // 2.4 Agregar adaptador con parámetros inválidos
    idx = ft_agregar_adaptador(sesion, 0, FT_LAYER_ATTN_K, -1, -1.0f, 0, 0);
    test_assert("Parametros invalidos retorna -1", idx == -1);

    // 2.5 Estadísticas de adaptadores
    test_assert("Tres adaptadores total", sesion->num_adaptadores == 3);

    ft_cerrar(sesion);
    test_assert("Sesion cerrada correctamente", 1);
}

// ============================================================
// Sección 3: Dataset de fine-tuning
// ============================================================
static void test_dataset(void) {
    FTSession* sesion = ft_iniciar(NULL, NULL);
    test_assert("Sesion iniciada", sesion != NULL);

    // 3.1 Agregar ejemplo simple
    int tokens_in[] = {1, 2, 3, 4, 5};
    int tokens_out[] = {6, 7, 8, 9, 10};
    int idx = ft_agregar_ejemplo(sesion, tokens_in, 5, tokens_out, 5, 1.0f);
    test_assert("Ejemplo 1 agregado", idx >= 0);
    test_assert("Indice 0", idx == 0);
    test_assert("Un ejemplo en dataset", sesion->dataset.num_ejemplos == 1);

    // 3.2 Agregar segundo ejemplo con peso personalizado
    int tokens_in2[] = {10, 20, 30};
    int tokens_out2[] = {40, 50, 60};
    idx = ft_agregar_ejemplo(sesion, tokens_in2, 3, tokens_out2, 3, 2.5f);
    test_assert("Ejemplo 2 agregado", idx == 1);
    test_assert("Dos ejemplos en dataset", sesion->dataset.num_ejemplos == 2);
    test_assert("Peso 2.5", sesion->dataset.ejemplos[1].peso == 2.5f);

    // 3.3 Agregar con parámetros inválidos
    idx = ft_agregar_ejemplo(sesion, NULL, 0, NULL, 0, 1.0f);
    test_assert("Params invalidos retorna -1", idx == -1);

    idx = ft_agregar_ejemplo(sesion, tokens_in, -1, tokens_out, -1, 1.0f);
    test_assert("Longitud negativa retorna -1", idx == -1);

    // 3.4 Verificar datos almacenados
    test_assert("Ejemplo 1 len_in correcto", sesion->dataset.ejemplos[0].len_entrada == 5);
    test_assert("Ejemplo 1 tokens_in[0] correcto", sesion->dataset.ejemplos[0].tokens_entrada[0] == 1);
    test_assert("Ejemplo 2 len_out correcto", sesion->dataset.ejemplos[1].len_salida == 3);
    test_assert("Ejemplo 2 tokens_out[2] correcto", sesion->dataset.ejemplos[1].tokens_salida[2] == 60);

    ft_cerrar(sesion);
    test_assert("Sesion cerrada", 1);
}

// ============================================================
// Sección 4: Training step y loss
// ============================================================
static void test_entrenamiento(void) {
    FTConfig cfg;
    cfg.learning_rate = 0.01f;
    cfg.rank = 4;
    cfg.alpha = 8.0f;
    cfg.num_epochs = 1;
    cfg.batch_size = 1;
    cfg.weight_decay = 0.001f;
    cfg.grad_clip_norm = 1.0f;

    FTSession* sesion = ft_iniciar(NULL, &cfg);
    test_assert("Sesion iniciada", sesion != NULL);

    // Agregar adaptador
    ft_agregar_adaptador(sesion, 0, FT_LAYER_ATTN_Q, 4, 8.0f, 64, 64);
    test_assert("Adaptador agregado", sesion->num_adaptadores == 1);

    // Agregar ejemplo
    int tokens_in[] = {1, 2, 3};
    int tokens_out[] = {4, 5, 6};
    ft_agregar_ejemplo(sesion, tokens_in, 3, tokens_out, 3, 1.0f);
    test_assert("Ejemplo agregado", sesion->dataset.num_ejemplos == 1);

    // 4.1 Ejecutar paso de entrenamiento
    float loss = ft_paso_entrenamiento(sesion);
    test_assert("Paso de entrenamiento produce perdida positiva", loss > 0.0f);
    test_assert("Perdida menor a 10 (rango razonable)", loss < 10.0f);
    test_assert("Perdida almacenada en sesion", sesion->perdida_actual > 0.0f);
    test_assert("Paso incrementado a 1", sesion->paso_actual == 1);

    // 4.2 Ejecutar segundo paso (loss debe cambiar)
    float loss2 = ft_paso_entrenamiento(sesion);
    test_assert("Segundo paso produce perdida", loss2 > 0.0f);
    test_assert("Paso incrementado a 2", sesion->paso_actual == 2);

    // 4.3 Entrenar sin adaptadores
    FTSession* sesion_vacia = ft_iniciar(NULL, NULL);
    float loss_err = ft_paso_entrenamiento(sesion_vacia);
    test_assert("Paso sin adaptadores retorna -1", loss_err < 0.0f);
    ft_cerrar(sesion_vacia);

    // 4.4 Entrenamiento completo
    sesion->config.num_epochs = 5;
    float loss_final = ft_entrenar(sesion);
    test_assert("Entrenamiento completo produce perdida", loss_final > 0.0f);
    test_assert("Pasos incrementados correctamente", sesion->paso_actual > 2);

    ft_cerrar(sesion);
}

// ============================================================
// Sección 5: Evaluación de pérdida
// ============================================================
static void test_evaluacion_perdida(void) {
    FTSession* sesion = ft_iniciar(NULL, NULL);
    test_assert("Sesion iniciada", sesion != NULL);

    int tokens_in[] = {1, 2, 3};
    int tokens_out[] = {4, 5, 6};
    ft_agregar_ejemplo(sesion, tokens_in, 3, tokens_out, 3, 1.0f);

    // Evaluar pérdida en un ejemplo
    FTEjemplo* ej = &sesion->dataset.ejemplos[0];
    float loss = ft_evaluar_perdida(sesion, ej);
    test_assert("Evaluacion de perdida produce valor", loss > 0.0f);
    test_assert("Perdida en rango razonable", loss < 20.0f);

    // Evaluar con NULL
    loss = ft_evaluar_perdida(sesion, NULL);
    test_assert("Evaluacion NULL retorna -1", loss < 0.0f);

    ft_cerrar(sesion);
}

// ============================================================
// Sección 6: Persistencia (save/load)
// ============================================================
static void test_persistencia(void) {
    FTConfig cfg;
    cfg.learning_rate = 0.001f;
    cfg.rank = 8;
    cfg.alpha = 16.0f;
    cfg.num_epochs = 1;
    cfg.batch_size = 1;
    cfg.weight_decay = 0.0f;
    cfg.grad_clip_norm = 0.0f;

    // Crear sesión con adaptadores
    FTSession* sesion = ft_iniciar(NULL, &cfg);
    test_assert("Sesion creada para save", sesion != NULL);

    ft_agregar_adaptador(sesion, 0, FT_LAYER_ATTN_Q, 8, 16.0f, 64, 64);
    ft_agregar_adaptador(sesion, 1, FT_LAYER_FFN_DOWN, 4, 8.0f, 64, 128);
    test_assert("Dos adaptadores agregados", sesion->num_adaptadores == 2);

    // Guardar pesos
    remove("_test_ft_weights.bin");  // Clean slate
    int rc = ft_guardar_pesos(sesion, "_test_ft_weights.bin");
    test_assert("Pesos guardados exitosamente", rc == 0);
    ft_cerrar(sesion);

    // Crear nueva sesión y cargar pesos
    FTSession* sesion2 = ft_iniciar(NULL, &cfg);
    test_assert("Sesion creada para load", sesion2 != NULL);

    rc = ft_cargar_pesos(sesion2, "_test_ft_weights.bin");
    test_assert("Pesos cargados exitosamente", rc == 0);
    test_assert("Dos adaptadores cargados", sesion2->num_adaptadores == 2);
    test_assert("Adaptador 0: capa 0", sesion2->adaptadores[0].capa_idx == 0);
    test_assert("Adaptador 0: tipo ATTN_Q", sesion2->adaptadores[0].tipo_capa == FT_LAYER_ATTN_Q);
    test_assert("Adaptador 0: rank 8", sesion2->adaptadores[0].rank == 8);
    test_assert("Adaptador 1: capa 1", sesion2->adaptadores[1].capa_idx == 1);
    test_assert("Adaptador 1: tipo FFN_DOWN", sesion2->adaptadores[1].tipo_capa == FT_LAYER_FFN_DOWN);
    test_assert("Adaptador 1: rank 4", sesion2->adaptadores[1].rank == 4);
    test_assert("Adaptador 1: dim_in 64", sesion2->adaptadores[1].dim_in == 64);
    test_assert("Adaptador 1: dim_out 128", sesion2->adaptadores[1].dim_out == 128);

    // Cargar desde archivo inexistente
    rc = ft_cargar_pesos(sesion2, "_test_no_existe.bin");
    test_assert("Carga desde archivo inexistente falla", rc == -1);

    // Cargar con ruta NULL
    rc = ft_cargar_pesos(sesion2, NULL);
    test_assert("Carga con NULL falla", rc == -1);

    ft_cerrar(sesion2);

    // Guardar desde sesión NULL
    rc = ft_guardar_pesos(NULL, "_test_ft_weights.bin");
    test_assert("Guardar NULL falla", rc == -1);

    // Limpiar archivo de test
    remove("_test_ft_weights.bin");
    test_assert("Archivo de test eliminado", 1);
}

// ============================================================
// Sección 7: Control de adaptadores (aplicar/remover)
// ============================================================
static void test_control_adaptadores(void) {
    FTSession* sesion = ft_iniciar(NULL, NULL);
    test_assert("Sesion iniciada", sesion != NULL);

    ft_agregar_adaptador(sesion, 0, FT_LAYER_ATTN_Q, 8, 16.0f, 64, 64);
    ft_agregar_adaptador(sesion, 0, FT_LAYER_ATTN_V, 8, 16.0f, 64, 64);

    // 7.1 Aplicar adaptadores
    int rc = ft_aplicar_adaptadores(sesion);
    test_assert("Aplicar adaptadores exitoso", rc == 0);
    test_assert("Adaptador 0 activo", sesion->adaptadores[0].activo == 1);
    test_assert("Adaptador 1 activo", sesion->adaptadores[1].activo == 1);

    // 7.2 Remover adaptadores
    ft_remover_adaptadores(sesion);
    test_assert("Adaptador 0 inactivo", sesion->adaptadores[0].activo == 0);
    test_assert("Adaptador 1 inactivo", sesion->adaptadores[1].activo == 0);

    // 7.3 Re-aplicar
    ft_aplicar_adaptadores(sesion);
    test_assert("Adaptadores reactivados", sesion->adaptadores[0].activo == 1);

    // 7.4 Control en sesión NULL
    rc = ft_aplicar_adaptadores(NULL);
    test_assert("Aplicar NULL falla", rc == -1);
    ft_remover_adaptadores(NULL);
    test_assert("Remover NULL no crash", 1);

    ft_cerrar(sesion);
}

// ============================================================
// Sección 8: Estadísticas
// ============================================================
static void test_estadisticas(void) {
    FTConfig cfg;
    cfg.learning_rate = 0.005f;
    cfg.rank = 16;
    cfg.alpha = 32.0f;
    cfg.num_epochs = 2;
    cfg.batch_size = 1;
    cfg.weight_decay = 0.0f;
    cfg.grad_clip_norm = 0.0f;

    FTSession* sesion = ft_iniciar(NULL, &cfg);
    test_assert("Sesion iniciada", sesion != NULL);

    ft_agregar_adaptador(sesion, 0, FT_LAYER_ATTN_Q, 16, 32.0f, 64, 64);

    int tokens_in[] = {1, 2, 3};
    int tokens_out[] = {4, 5, 6};
    ft_agregar_ejemplo(sesion, tokens_in, 3, tokens_out, 3, 1.0f);

    // Entrenar un paso
    ft_paso_entrenamiento(sesion);

    // Obtener estadísticas
    FTEstadisticas stats = ft_obtener_estadisticas(sesion);
    test_assert("Stats: 1 adaptador", stats.num_adaptadores == 1);
    test_assert("Stats: 1 ejemplo", stats.num_ejemplos == 1);
    test_assert("Stats: perdida > 0", stats.perdida_promedio > 0.0f);
    test_assert("Stats: paso > 0", stats.pasos_ejecutados > 0);
    test_assert("Stats: LR 0.005", stats.learning_rate == 0.005f);
    test_assert("Stats: rank 16", stats.rank_loRA == 16);

    // Pérdida actual
    float perdida = ft_perdida_actual(sesion);
    test_assert("Perdida actual positiva", perdida > 0.0f);
    test_assert("Perdida actual coincide con stats", perdida == stats.perdida_promedio);

    // Paso actual
    int paso = ft_paso_actual(sesion);
    test_assert("Paso actual coincide con stats", paso == stats.pasos_ejecutados);

    // Estadísticas de sesión NULL
    stats = ft_obtener_estadisticas(NULL);
    test_assert("Stats NULL: 0 adaptadores", stats.num_adaptadores == 0);
    
    perdida = ft_perdida_actual(NULL);
    test_assert("Perdida NULL retorna -1", perdida < 0.0f);
    
    paso = ft_paso_actual(NULL);
    test_assert("Paso NULL retorna -1", paso == -1);

    ft_cerrar(sesion);
}

// ============================================================
// Sección 9: Integración con RAG (re-ranking)
// ============================================================
static void test_rag_integracion(void) {
    FTSession* sesion = ft_iniciar(NULL, NULL);
    test_assert("Sesion FT iniciada para RAG", sesion != NULL);

    ft_agregar_adaptador(sesion, 0, FT_LAYER_ATTN_Q, 8, 16.0f, 64, 64);

    // Crear índice RAG con algunos chunks
    RagIndex idx;
    synapse_rag_inicializar_indice(&idx, 64);

    // Agregar chunks de prueba
    RagChunk chunk1;
    memset(&chunk1, 0, sizeof(chunk1));
    chunk1.texto = strdup("fn suma(a: entero, b: entero) -> entero");
    chunk1.longitud = (int)strlen(chunk1.texto);
    chunk1.linea_inicio = 0;
    chunk1.linea_fin = 3;
    chunk1.embedding_dim = 64;
    chunk1.embedding = (float*)calloc(64, sizeof(float));
    chunk1.embedding[0] = 1.0f;  // Embedding simple
    strcpy(chunk1.tipo_nodo, "funcion");
    synapse_rag_indexar_chunk(&idx, &chunk1);
    free(chunk1.texto);
    free(chunk1.embedding);

    RagChunk chunk2;
    memset(&chunk2, 0, sizeof(chunk2));
    chunk2.texto = strdup("estructura Punto:\n    x: entero\n    y: entero");
    chunk2.longitud = (int)strlen(chunk2.texto);
    chunk2.linea_inicio = 5;
    chunk2.linea_fin = 8;
    chunk2.embedding_dim = 64;
    chunk2.embedding = (float*)calloc(64, sizeof(float));
    chunk2.embedding[1] = 0.5f;
    strcpy(chunk2.tipo_nodo, "estructura");
    synapse_rag_indexar_chunk(&idx, &chunk2);
    free(chunk2.texto);
    free(chunk2.embedding);

    test_assert("Indice RAG con 2 chunks", idx.num_chunks == 2);

    // Re-ranking con fine-tuning
    RagResultados originales;
    memset(&originales, 0, sizeof(originales));
    originales.num_resultados = 2;
    originales.resultados[0] = &idx.chunks[0];
    originales.puntuaciones[0] = 0.75f;
    originales.resultados[1] = &idx.chunks[1];
    originales.puntuaciones[1] = 0.60f;

    RagResultados ajustados;
    int n = synapse_rag_re_rankear_con_ft(sesion, &idx, "consulta",
                                           &originales, &ajustados);
    test_assert("Re-ranking produjo resultados", n > 0);
    test_assert("Numero de resultados preservado", n == 2);
    // Check that function type got boost
    test_assert("Puntuacion de funcion ajustada (boost 1.15)", 
                ajustados.puntuaciones[0] > originales.puntuaciones[0]);
    test_assert("Puntuacion de estructura ajustada (boost 1.10)",
                ajustados.puntuaciones[1] > originales.puntuaciones[1]);

    // Re-ranking con NULL
    n = synapse_rag_re_rankear_con_ft(NULL, NULL, NULL, NULL, NULL);
    test_assert("Re-ranking NULL retorna -1", n == -1);

    // Generar embedding con fine-tuning
    int dim = 0;
    float* emb = synapse_rag_generar_embedding_ft(sesion, "test code", &dim);
    test_assert("Embedding FT generado", emb != NULL);
    test_assert("Embedding dim 64", dim == 64);

    // Normalizar: verificar que la norma es ~1.0
    float norm = 0.0f;
    for (int i = 0; i < dim; i++) norm += emb[i] * emb[i];
    norm = sqrtf(norm);
    test_assert("Embedding normalizado (norma cercana a 1.0)", 
                norm > 0.9f && norm < 1.1f);
    free(emb);

    // Generar embedding NULL
    emb = synapse_rag_generar_embedding_ft(NULL, NULL, NULL);
    test_assert("Embedding NULL retorna NULL", emb == NULL);

    synapse_rag_liberar_indice(&idx);
    ft_cerrar(sesion);
}

// ============================================================
// Sección 10: Edge cases y stress
// ============================================================
static void test_edge_cases(void) {
    // 10.1 Sesión sin adaptadores, entrenar
    FTSession* sesion = ft_iniciar(NULL, NULL);
    float loss = ft_paso_entrenamiento(sesion);
    test_assert("Paso sin adaptadores retorna -1", loss < 0.0f);
    ft_cerrar(sesion);

    // 10.2 Sesión sin dataset
    sesion = ft_iniciar(NULL, NULL);
    ft_agregar_adaptador(sesion, 0, FT_LAYER_ATTN_Q, 8, 16.0f, 64, 64);
    loss = ft_paso_entrenamiento(sesion);
    test_assert("Paso sin dataset retorna -1", loss < 0.0f);
    ft_cerrar(sesion);

    // 10.3 Dataset lleno (simular)
    sesion = ft_iniciar(NULL, NULL);
    int tokens_in[] = {1, 2};
    int tokens_out[] = {3, 4};
    for (int i = 0; i < 5; i++) {
        ft_agregar_ejemplo(sesion, tokens_in, 2, tokens_out, 2, 1.0f);
    }
    test_assert("5 ejemplos agregados", sesion->dataset.num_ejemplos == 5);
    ft_cerrar(sesion);

    // 10.4 Guardar/cargar con múltiples adaptadores complejos
    sesion = ft_iniciar(NULL, NULL);
    ft_agregar_adaptador(sesion, 0, FT_LAYER_ATTN_Q, 8, 16.0f, 4096, 4096);
    ft_agregar_adaptador(sesion, 1, FT_LAYER_ATTN_K, 8, 16.0f, 4096, 4096);
    ft_agregar_adaptador(sesion, 2, FT_LAYER_ATTN_V, 8, 16.0f, 4096, 4096);
    ft_agregar_adaptador(sesion, 3, FT_LAYER_ATTN_O, 8, 16.0f, 4096, 4096);
    ft_agregar_adaptador(sesion, 0, FT_LAYER_FFN_GATE, 4, 8.0f, 4096, 11008);
    ft_agregar_adaptador(sesion, 0, FT_LAYER_FFN_UP, 4, 8.0f, 4096, 11008);
    ft_agregar_adaptador(sesion, 0, FT_LAYER_FFN_DOWN, 4, 8.0f, 11008, 4096);
    test_assert("7 adaptadores (LoRA multi-capa)", sesion->num_adaptadores == 7);

    int rc = ft_guardar_pesos(sesion, "_test_ft_complex.bin");
    test_assert("Guardado complejo exitoso", rc == 0);
    ft_cerrar(sesion);

    sesion = ft_iniciar(NULL, NULL);
    rc = ft_cargar_pesos(sesion, "_test_ft_complex.bin");
    test_assert("Carga compleja exitosa", rc == 0);
    test_assert("7 adaptadores cargados", sesion->num_adaptadores == 7);
    ft_cerrar(sesion);

    remove("_test_ft_complex.bin");
    test_assert("Adaptador 0: capa 0 ATTN_Q rank 8", 
                sesion->adaptadores[0].capa_idx == 0 &&
                sesion->adaptadores[0].tipo_capa == FT_LAYER_ATTN_Q &&
                sesion->adaptadores[0].rank == 8);
    test_assert("Adaptador 4: capa 0 FFN_GATE rank 4",
                sesion->adaptadores[4].capa_idx == 0 &&
                sesion->adaptadores[4].tipo_capa == FT_LAYER_FFN_GATE &&
                sesion->adaptadores[4].rank == 4);
    test_assert("Adaptador 6: capa 0 FFN_DOWN dim_in 11008 dim_out 4096",
                sesion->adaptadores[6].dim_in == 11008 &&
                sesion->adaptadores[6].dim_out == 4096);
    ft_cerrar(sesion);

    remove("_test_ft_complex.bin");

    // 10.5 Sesión NULL en varias funciones
    FTEstadisticas s = ft_obtener_estadisticas(NULL);
    test_assert("Estadisticas NULL: num_adaptadores 0", s.num_adaptadores == 0);
    test_assert("Estadisticas NULL: num_ejemplos 0", s.num_ejemplos == 0);
    test_assert("Estadisticas NULL: perdida 0", s.perdida_promedio == 0.0f);

    // 10.6 Evaluar pérdida con ejemplo de token fuera de rango
    sesion = ft_iniciar(NULL, NULL);
    FTEjemplo ej_bad;
    ej_bad.tokens_entrada = NULL;
    ej_bad.tokens_salida = NULL;
    ej_bad.len_entrada = 0;
    ej_bad.len_salida = 0;
    loss = ft_evaluar_perdida(sesion, &ej_bad);
    test_assert("Evaluacion con ejemplo invalido retorna -1", loss < 0.0f);
    ft_cerrar(sesion);
}

// ============================================================
// Main
// ============================================================

int main(void) {
    printf("========================================\n");
    printf("  Synapse Fine-Tuning Suite (M13.4)\n");
    printf("  LoRA adapters + training + RAG\n");
    printf("========================================\n");

    test_section_start("Session Initialization");
    test_inicializacion();

    test_section_start("LoRA Adapters");
    test_adaptadores_lora();

    test_section_start("Training Dataset");
    test_dataset();

    test_section_start("Training Step & Loss");
    test_entrenamiento();

    test_section_start("Loss Evaluation");
    test_evaluacion_perdida();

    test_section_start("Weight Persistence (Save/Load)");
    test_persistencia();

    test_section_start("Adapter Control (Apply/Remove)");
    test_control_adaptadores();

    test_section_start("Session Statistics");
    test_estadisticas();

    test_section_start("RAG Integration (Re-ranking)");
    test_rag_integracion();

    test_section_start("Edge Cases");
    test_edge_cases();

    printf("\n========================================\n");
    printf("  RESULTADOS: %d / %d PASS\n", test_passed, test_total);
    printf("========================================\n");

    return (test_passed == test_total) ? 0 : 1;
}
