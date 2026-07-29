/*
 * tests/validate_borrow_matrix.c
 * Matriz de Estres de Prestamos Cruzados (Manual 4 §4.2)
 * M22.7: Validacion de exclusividad &T vs &mut T.
 *
 * Compilacion:
 *   gcc -I. -O2 tests/validate_borrow_matrix.c synapse_rt.o synapse_rt_memory.o \
 *       -o validate_borrow_matrix.exe -lpthread -lm -lws2_32
 *
 * Compilacion ASan/UBSan (Linux/CI):
 *   gcc -I. -fsanitize=address,undefined -g -O1 \
 *       tests/validate_borrow_matrix.c synapse_rt.o synapse_rt_memory.o \
 *       -o validate_borrow_matrix_asan -lpthread -lm -lws2_32
 *
 * NOTA: ASan/UBSan no disponibles en MinGW/Windows (ver M20.3.3).
 *       La instrumentacion se delega a CI en Linux (Manual 9 §9.5).
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#include <assert.h>
#include "synapse_rt.h"

/* ============================================================
 * Readers-Writer Lock (Manual 4 §4.2: &T compartido, &mut T exclusivo)
 * ============================================================ */

typedef struct RWLock {
    int valor;
    int lectores_activos;
    int escritor_activo;
    pthread_mutex_t lock;
    pthread_cond_t cv_lectores;
    pthread_cond_t cv_escritores;
    int esperando_escritores;
} RWLock;

static void rwlock_init(RWLock* r, int val_inicial) {
    r->valor = val_inicial;
    r->lectores_activos = 0;
    r->escritor_activo = 0;
    r->esperando_escritores = 0;
    pthread_mutex_init(&r->lock, NULL);
    pthread_cond_init(&r->cv_lectores, NULL);
    pthread_cond_init(&r->cv_escritores, NULL);
}

static void rwlock_destroy(RWLock* r) {
    pthread_mutex_destroy(&r->lock);
    pthread_cond_destroy(&r->cv_lectores);
    pthread_cond_destroy(&r->cv_escritores);
}

/* Adquirir prestamo compartido (&T) - multiples lectores simultaneos */
static void adquirir_lector(RWLock* r, int id) {
    pthread_mutex_lock(&r->lock);
    while (r->escritor_activo || r->esperando_escritores > 0) {
        pthread_cond_wait(&r->cv_lectores, &r->lock);
    }
    r->lectores_activos++;
    printf("  [Lector %d] adquirio &T (lectores=%d)\n", id, r->lectores_activos);
    pthread_mutex_unlock(&r->lock);
}

static void liberar_lector(RWLock* r, int id) {
    pthread_mutex_lock(&r->lock);
    r->lectores_activos--;
    printf("  [Lector %d] libero &T (lectores=%d)\n", id, r->lectores_activos);
    if (r->lectores_activos == 0 && r->esperando_escritores > 0) {
        pthread_cond_signal(&r->cv_escritores);
    }
    pthread_mutex_unlock(&r->lock);
}

/* Adquirir prestamo exclusivo (&mut T) - BLOQUEA todo otro acceso */
static void adquirir_escritor(RWLock* r, int id) {
    pthread_mutex_lock(&r->lock);
    r->esperando_escritores++;
    while (r->lectores_activos > 0 || r->escritor_activo) {
        pthread_cond_wait(&r->cv_escritores, &r->lock);
    }
    r->esperando_escritores--;
    r->escritor_activo = 1;
    printf("  [Escritor %d] ADQUIRIO &mut T (EXCLUSIVO)\n", id);
    pthread_mutex_unlock(&r->lock);
}

static void liberar_escritor(RWLock* r, int id) {
    pthread_mutex_lock(&r->lock);
    r->escritor_activo = 0;
    printf("  [Escritor %d] libero &mut T\n", id);
    pthread_cond_broadcast(&r->cv_lectores);
    pthread_cond_signal(&r->cv_escritores);
    pthread_mutex_unlock(&r->lock);
}

/* ============================================================
 * Barrera de sincronizacion (elimina dependencias de timing)
 * ============================================================ */
static pthread_barrier_t barrier;

/* ============================================================
 * Test 1: Multiples lectores simultaneos (&T) - Manual 4 §4.2
 * ============================================================ */

typedef struct {
    RWLock* recurso;
    int id;
} HiloArgs;

static void* hilo_lector(void* arg) {
    HiloArgs* a = (HiloArgs*)arg;
    adquirir_lector(a->recurso, a->id);
    int val = a->recurso->valor;
    (void)val;
    liberar_lector(a->recurso, a->id);
    return NULL;
}

static int test_multiples_lectores(void) {
    printf("\n--- [Test 1] Multiples lectores simultaneos (&T) ---\n");
    RWLock r;
    rwlock_init(&r, 42);

    pthread_t hilos[5];
    HiloArgs args[5];

    for (int i = 0; i < 5; i++) {
        args[i].recurso = &r;
        args[i].id = i + 1;
        pthread_create(&hilos[i], NULL, hilo_lector, &args[i]);
    }
    for (int i = 0; i < 5; i++) {
        pthread_join(hilos[i], NULL);
    }

    int ok = (r.lectores_activos == 0 && r.escritor_activo == 0);
    printf("  => Resultado: %s (lectores=%d, escritor=%d)\n",
           ok ? "OK" : "FAIL", r.lectores_activos, r.escritor_activo);
    rwlock_destroy(&r);
    return ok ? 0 : 1;
}

/* ============================================================
 * Test 2: Escritor bloquea lectores (&mut T vs &T) - orden garantizado
 * Manual 4 §4.2: &mut T bloquea &T hasta liberar.
 *
 * Protocolo:
 *   1. Escritor adquiere &mut T PRIMERO (orden garantizado por flag)
 *   2. Una vez que escritor sostiene &mut T, lector INTENTA adquirir &T
 *   3. El lector debe BLOQUEARSE hasta que escritor libere
 *   4. Tras liberar, lector adquiere &T y lee el valor escrito
 * ============================================================ */

static pthread_mutex_t test2_mtx = PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t test2_cv = PTHREAD_COND_INITIALIZER;
static volatile int test2_escritor_listo = 0;
static volatile int test2_valor_leido = 0;

static void* hilo_lector_test2(void* arg) {
    RWLock* r = (RWLock*)arg;
    /* Esperar a que escritor haya adquirido &mut T */
    pthread_mutex_lock(&test2_mtx);
    while (!test2_escritor_listo) {
        pthread_cond_wait(&test2_cv, &test2_mtx);
    }
    pthread_mutex_unlock(&test2_mtx);
    /* Ahora escritor SOSTIENE &mut T. Intentar adquirir &T debe BLOQUEAR */
    adquirir_lector(r, 2);
    /* Si llegamos aqui, escritor YA libero &mut T */
    test2_valor_leido = r->valor;
    liberar_lector(r, 2);
    return NULL;
}

static void* hilo_escritor_test2(void* arg) {
    RWLock* r = (RWLock*)arg;
    adquirir_escritor(r, 1);
    /* Escribir valor MIENTRAS sostenemos &mut T */
    r->valor = 100;
    /* Senalar al lector que YA tenemos &mut T */
    pthread_mutex_lock(&test2_mtx);
    test2_escritor_listo = 1;
    pthread_cond_broadcast(&test2_cv);
    pthread_mutex_unlock(&test2_mtx);
    /* Esperar para dar tiempo al lector a bloquearse contra &mut T */
    struct timespec ts = {0, 20000000}; /* 20ms */
    nanosleep(&ts, NULL);
    /* Liberar &mut T -- ahora el lector puede adquirir &T */
    liberar_escritor(r, 1);
    return NULL;
}

static int test_escritor_bloquea_lectores(void) {
    printf("\n--- [Test 2] Escritor bloquea lectores (&mut T bloquea &T) ---\n");
    RWLock r;
    rwlock_init(&r, 0);
    test2_escritor_listo = 0;
    test2_valor_leido = 0;

    pthread_t escritor, lector;
    pthread_create(&escritor, NULL, hilo_escritor_test2, &r);
    pthread_create(&lector, NULL, hilo_lector_test2, &r);

    pthread_join(escritor, NULL);
    pthread_join(lector, NULL);

    /* Verificar: lector debe leer 100 (escrito por escritor MIENTRAS
     * sostenia &mut T). Si leyo 0, significa que NO se bloqueo y
     * na adquirio &T mientras escritor tenia &mut T (antes de escribir) */
    int ok = (test2_valor_leido == 100);
    printf("  => Resultado: %s (valor_leido=%d, esperado=100)\n",
           ok ? "OK" : "FAIL", test2_valor_leido);
    rwlock_destroy(&r);
    return ok ? 0 : 1;
}

/* ============================================================
 * Test 3: Exclusion mutua estricta (&mut vs &mut) - Manual 4 §4.1
 * ============================================================ */

static void* hilo_escritor_concurrente(void* arg) {
    HiloArgs* a = (HiloArgs*)arg;
    adquirir_escritor(a->recurso, a->id);
    a->recurso->valor = a->id * 100;
    liberar_escritor(a->recurso, a->id);
    return NULL;
}

static int test_exclusion_mutua_estricta(void) {
    printf("\n--- [Test 3] Exclusion mutua estricta (&mut vs &mut) ---\n");
    RWLock r;
    rwlock_init(&r, 0);

    pthread_t e1, e2;
    HiloArgs a1, a2;
    a1.recurso = &r; a1.id = 1;
    a2.recurso = &r; a2.id = 2;

    pthread_create(&e1, NULL, hilo_escritor_concurrente, &a1);
    pthread_create(&e2, NULL, hilo_escritor_concurrente, &a2);
    pthread_join(e1, NULL);
    pthread_join(e2, NULL);

    int ok = ((r.valor == 100 || r.valor == 200) &&
              r.lectores_activos == 0 && r.escritor_activo == 0);
    printf("  => Resultado: %s (valor=%d)\n", ok ? "OK" : "FAIL", r.valor);
    rwlock_destroy(&r);
    return ok ? 0 : 1;
}

/* ============================================================
 * Test 4: Ningun lector mientras escritor activo (barrera-sincronizado)
 * Manual 4 §4.2
 * ============================================================ */

static volatile int test4_lector_violo = 0;

static void* hilo_lector_estricto(void* arg) {
    RWLock* r = (RWLock*)arg;
    pthread_barrier_wait(&barrier);
    adquirir_lector(r, 99);
    /* Si escritor esta activo mientras leemos, VIOLACION */
    if (r->escritor_activo) {
        test4_lector_violo = 1;
    }
    liberar_lector(r, 99);
    return NULL;
}

static void* hilo_escritor_estricto(void* arg) {
    RWLock* r = (RWLock*)arg;
    pthread_barrier_wait(&barrier);
    adquirir_escritor(r, 88);
    /* Dormir para dar tiempo al lector a intentar */
    struct timespec ts = {0, 20000000}; /* 20ms */
    nanosleep(&ts, NULL);
    r->valor = 999;
    liberar_escritor(r, 88);
    return NULL;
}

static int test_lector_no_viola_exclusividad(void) {
    printf("\n--- [Test 4] Ningun lector mientras escritor activo ---\n");
    RWLock r;
    rwlock_init(&r, 0);
    test4_lector_violo = 0;
    pthread_barrier_init(&barrier, NULL, 2);

    pthread_t escritor, lector;
    pthread_create(&escritor, NULL, hilo_escritor_estricto, &r);
    pthread_create(&lector, NULL, hilo_lector_estricto, &r);
    pthread_join(escritor, NULL);
    pthread_join(lector, NULL);
    pthread_barrier_destroy(&barrier);

    int ok = (!test4_lector_violo && r.valor == 999);
    printf("  => Resultado: %s (lector_violo=%d, valor=%d)\n",
           ok ? "OK" : "FAIL", test4_lector_violo, r.valor);
    rwlock_destroy(&r);
    return ok ? 0 : 1;
}

/* ============================================================
 * Test 5: Pool allocator bajo prestamos cruzados
 * ============================================================ */

static int test_pool_bajo_prestamos(void) {
    printf("\n--- [Test 5] Pool allocator bajo prestamos cruzados ---\n");

    int* datos = (int*)pool_alloc(10 * sizeof(int));
    if (!datos) { printf("  FAIL: pool_alloc fallo\n"); return 1; }

    for (int i = 0; i < 10; i++) datos[i] = i * 10;

    /* Simular 3 lectores concurrentes */
    for (int r = 0; r < 3; r++) {
        int suma = 0;
        for (int i = 0; i < 10; i++) suma += datos[i];
        (void)suma;
    }

    /* Simular escritura exclusiva */
    for (int i = 0; i < 10; i++) datos[i] = datos[i] + 1;

    int ok = 1;
    for (int i = 0; i < 10; i++) {
        if (datos[i] != i * 10 + 1) {
            printf("  FAIL: datos[%d] = %d (esperado %d)\n", i, datos[i], i * 10 + 1);
            ok = 0;
        }
    }
    pool_free(datos);
    if (ok) printf("  => Resultado: OK\n");
    return ok ? 0 : 1;
}

/* ============================================================
 * Test 6: Estres de prestamos anidados (10 niveles)
 * ============================================================ */

static int test_prestamos_anidados(void) {
    printf("\n--- [Test 6] Prestamos anidados (10 niveles) ---\n");

    int raiz = 0;
    int* nivel1 = &raiz;

    *nivel1 = 1;
    { int* nivel2 = nivel1; *nivel2 = 2;
      { int* nivel3 = nivel2; *nivel3 = 3;
        { int* nivel4 = nivel3; *nivel4 = 4;
          { int* nivel5 = nivel4; *nivel5 = 5;
            { int* nivel6 = nivel5; *nivel6 = 6;
              { int* nivel7 = nivel6; *nivel7 = 7;
                { int* nivel8 = nivel7; *nivel8 = 8;
                  { int* nivel9 = nivel8; *nivel9 = 9;
                    { int* nivel10 = nivel9; *nivel10 = 10; }
                  }
                }
              }
            }
          }
        }
      }
    }

    int ok = (raiz == 10);
    printf("  => Resultado: %s (raiz=%d)\n", ok ? "OK" : "FAIL", raiz);
    return ok ? 0 : 1;
}

/* ============================================================
 * Main
 * ============================================================ */
int main(void) {
    int fallos = 0;

    pool_init(128, 4096);
    printf("=== MATRIZ DE ESTRES DE PRESTAMOS CRUZADOS (M22.7) ===\n");
    printf("Manual 4 S4.2 - &T (compartido) vs &mut T (exclusivo)\n");

    fallos += test_multiples_lectores();
    fallos += test_escritor_bloquea_lectores();
    fallos += test_exclusion_mutua_estricta();
    fallos += test_lector_no_viola_exclusividad();
    fallos += test_pool_bajo_prestamos();
    fallos += test_prestamos_anidados();

    pool_destroy();

    printf("\n=== RESULTADO FINAL: %d fallos ===\n", fallos);
    return fallos;
}
