MANUAL 4: GESTIÓN DE MEMORIA Y OWNERSHIP
Archivo: 04_MEMORIA_Y_OWNERSHIP.md
Versión: 5.0.0
Propósito: Especificar el modelo de ownership, borrowing, lifetimes, la implementación del runtime (pool allocator, watchdog) y las reglas ABI.

4.1 Modelo de Ownership (Posesión Única)
Reglas fundamentales:

Posesión Única: Cada recurso (memoria heap, canal, archivo, tensor) tiene exactamente un propietario en cada momento.

Move por defecto: Asignación (x = y) y paso de argumentos por valor transfieren la posesión (move). El origen queda invalidado.

RAII estático: Cuando el propietario sale del scope, el compilador inserta automáticamente la liberación (pool_free).

Detección de Use-After-Move: Cualquier uso de una variable movida → error en tiempo de compilación (ERR_MEM_USE_AFTER_MOVE).

Ejemplo de código válido:

synapse
funcion consumir(t: Tensor) -> nulo:
    // t es el propietario aquí
    procesar(t)
    // t se libera al salir del scope

funcion principal() -> nulo:
    t1 = crear_tensor(10)   // t1 es propietario
    consumir(t1)            // Move: t1 → t (t1 invalidado)
    // t1 no puede usarse aquí (error en compilación si se intenta)
Ejemplo de código inválido (bloqueado por el compilador):

synapse
funcion principal() -> nulo:
    t1 = crear_tensor(10)
    consumir(t1)
    imprimir(t1)  // ERROR: ERR_MEM_USE_AFTER_MOVE
4.2 Préstamo (Borrowing)
Tipo de préstamo	Sintaxis	Mutabilidad	Regla
Inmutable	&T	Solo lectura	Múltiples préstamos inmutables simultáneos permitidos.
Mutable	&mut T	Lectura + escritura	Solo un préstamo mutable a la vez, y no puede coexistir con inmutables.
Ejemplo:

synapse
funcion calcular_suma(datos: &[entero]) -> entero:
    // datos es un préstamo inmutable
    suma = 0
    para i = 0 mientras i < datos.len():
        suma = suma + datos[i]
    retornar suma

funcion modificar(datos: &mut [entero], idx: entero, valor: entero) -> nulo:
    datos[idx] = valor   // Permitido porque es &mut
Regla de elisión de lifetimes (análoga a Rust):

Si una función toma un solo préstamo y retorna un préstamo, el lifetime de retorno se asocia a ese parámetro.

Si toma &self (estructura), el lifetime de retorno se asocia a self.

4.3 Análisis de Lifetimes (Algoritmo)
Representación interna:

c
typedef enum {
    LT_ESTATICO,       // Toda la vida del programa
    LT_LOCAL,          // Scope de bloque (índice)
    LT_PARAMETRICO,    // Parámetro de función
    LT_ELIDIDO         // Inferido automáticamente
} LifetimeKind;

typedef struct {
    LifetimeKind kind;
    int index;         // Para LT_LOCAL: ID del scope
    char* nombre;      // Para LT_PARAMETRICO: nombre del parámetro
} Lifetime;
Pasos del análisis:

Recolección: Recorrer el AST para identificar variables y sus scopes.

Asignación: Asignar lifetimes a cada variable y préstamo.

Restricciones: Recolectar restricciones de uso (ej. 'a debe vivir al menos tanto como 'b).

Resolución: Resolver el grafo de restricciones (algoritmo de unificación de regiones).

Verificación: Confirmar que no hay ciclos y que ningún lifetime excede el ámbito de su propietario.

Errores posibles:

ERR_MEM_LIFETIME_MISMATCH: Un préstamo vive más que el valor prestado.

ERR_MEM_LIFETIME_CYCLE: Ciclo en la dependencia de lifetimes.

4.4 Runtime de Memoria (synapse_rt.c)
Pool Allocator (Slab):

c
#define POOL_BLOCK_SIZE 4096
#define POOL_MAX_BLOCKS 1024

typedef struct MemoryPool {
    void* blocks[POOL_MAX_BLOCKS];
    bool used[POOL_MAX_BLOCKS];
    size_t block_size;
    pthread_mutex_t mutex;
} MemoryPool;

MemoryPool g_pool;

void* pool_alloc(size_t size) {
    pthread_mutex_lock(&g_pool.mutex);
    size_t num_blocks = (size + g_pool.block_size - 1) / g_pool.block_size;
    // Buscar num_blocks contiguos libres (first-fit)
    for (int i = 0; i <= POOL_MAX_BLOCKS - num_blocks; i++) {
        bool free = true;
        for (int j = 0; j < num_blocks; j++) {
            if (g_pool.used[i + j]) { free = false; break; }
        }
        if (free) {
            for (int j = 0; j < num_blocks; j++) g_pool.used[i + j] = true;
            pthread_mutex_unlock(&g_pool.mutex);
            return g_pool.blocks[i];
        }
    }
    pthread_mutex_unlock(&g_pool.mutex);
    // Fallback a malloc (solo en modo debug se reporta)
    return malloc(size);
}

void pool_free(void* ptr) {
    pthread_mutex_lock(&g_pool.mutex);
    // Buscar ptr en g_pool.blocks
    for (int i = 0; i < POOL_MAX_BLOCKS; i++) {
        if (g_pool.blocks[i] == ptr) {
            // Liberar bloque (marcar como no usado)
            // Nota: necesita saber cuántos bloques liberar (almacenado en metadatos)
            // Implementación simplificada para ilustración.
            g_pool.used[i] = false;
            pthread_mutex_unlock(&g_pool.mutex);
            return;
        }
    }
    pthread_mutex_unlock(&g_pool.mutex);
    // Si no está en el pool, liberar con free()
    free(ptr);
}
MemoryWatchdog (Modo Debug):

c
#ifdef SYNAPSE_DEBUG_MEM

typedef struct {
    void* ptr;
    size_t size;
    const char* file;
    int line;
    bool active;
} MemRecord;

#define MAX_RECORDS 100000
MemRecord g_watchdog[MAX_RECORDS];
pthread_mutex_t g_watchdog_mutex;

void* watchdog_malloc(size_t size, const char* file, int line) {
    void* ptr = pool_alloc(size);
    pthread_mutex_lock(&g_watchdog_mutex);
    for (int i = 0; i < MAX_RECORDS; i++) {
        if (!g_watchdog[i].active) {
            g_watchdog[i].ptr = ptr;
            g_watchdog[i].size = size;
            g_watchdog[i].file = file;
            g_watchdog[i].line = line;
            g_watchdog[i].active = true;
            break;
        }
    }
    pthread_mutex_unlock(&g_watchdog_mutex);
    return ptr;
}

void watchdog_free(void* ptr) {
    pthread_mutex_lock(&g_watchdog_mutex);
    for (int i = 0; i < MAX_RECORDS; i++) {
        if (g_watchdog[i].ptr == ptr && g_watchdog[i].active) {
            g_watchdog[i].active = false;
            break;
        }
    }
    pthread_mutex_unlock(&g_watchdog_mutex);
    pool_free(ptr);
}

void watchdog_report(void) {
    int leaks = 0;
    pthread_mutex_lock(&g_watchdog_mutex);
    for (int i = 0; i < MAX_RECORDS; i++) {
        if (g_watchdog[i].active) {
            leaks++;
            fprintf(stderr, "LEAK: %zu bytes en %s:%d\n",
                    g_watchdog[i].size, g_watchdog[i].file, g_watchdog[i].line);
        }
    }
    pthread_mutex_unlock(&g_watchdog_mutex);
    if (leaks > 0) abort();
}
#endif
Regla de producción: En modo release, SYNAPSE_DEBUG_MEM no está definido, por lo que pool_alloc y pool_free se usan sin overhead de tracking.

4.5 ABI y Alineación de Memoria (Padding)
Fórmula de relleno:

P
=
(
A
−
(
O
 
mod
 
A
)
)
 
mod
 
A
P=(A−(OmodA))modA

P
P: bytes de relleno a añadir.

A
A: requisito de alineación del tipo (ej. entero → 8 bytes).

O
O: offset actual dentro de la estructura.

Directiva [empaquetado]: Para estructuras que se comunican con hardware o FFI (sin padding):

synapse
[empaquetado]
estructura CabeceraIP:
    version: caracter   // offset 0, size 1
    longitud: entero    // offset 1, size 4 (sin padding, alineación forzada a 1)
Advertencia: Acceder a campos no alineados en ARM puede generar Bus Error. Usar [empaquetado] solo para buffers crudos.