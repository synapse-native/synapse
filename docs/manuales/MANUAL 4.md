MANUAL 4: GESTIÓN DE MEMORIA Y OWNERSHIP

Archivo: 04\_MEMORIA\_Y\_OWNERSHIP.md

Versión: 5.1.1-industrial

Propósito: Especificar el modelo de ownership, borrowing, lifetimes, la implementación del runtime (pool allocator con caché por hilo, watchdog) y las reglas ABI.



4.1 Modelo de Ownership (Posesión Única)

Reglas fundamentales:



Posesión Única: Cada recurso (memoria heap, canal, archivo, tensor) tiene exactamente un propietario en cada momento.



Move por defecto: Asignación (x = y) y paso de argumentos por valor transfieren la posesión (move). El origen queda invalidado.



RAII estático: Cuando el propietario sale del scope, el compilador inserta automáticamente la liberación (pool\_free).



Detección de Use-After-Move: Cualquier uso de una variable movida → error en tiempo de compilación (ERR\_MEM\_USE\_AFTER\_MOVE).



Ejemplo de código válido:



synapse

funcion consumir(t: Tensor) -> nulo:

&#x20;   procesar(t)      // t es propietario, se libera al salir



funcion principal() -> nulo:

&#x20;   t1 = crear\_tensor(10)

&#x20;   consumir(t1)     // Move: t1 → t, t1 invalidado

&#x20;   // t1 no puede usarse aquí (error en compilación)

Ejemplo de código inválido:



synapse

funcion principal() -> nulo:

&#x20;   t1 = crear\_tensor(10)

&#x20;   consumir(t1)

&#x20;   imprimir(t1)     // ERROR: ERR\_MEM\_USE\_AFTER\_MOVE

4.2 Préstamo (Borrowing)

Tipo de préstamo	Sintaxis	Mutabilidad	Regla

Inmutable	\&T	Solo lectura	Múltiples préstamos inmutables simultáneos permitidos.

Mutable	\&mut T	Lectura + escritura	Solo un préstamo mutable a la vez, y no puede coexistir con inmutables.

Ejemplo:



synapse

funcion calcular\_suma(datos: \&\[entero]) -> entero:

&#x20;   suma = 0

&#x20;   para i = 0 mientras i < datos.len():

&#x20;       suma = suma + datos\[i]

&#x20;   retornar suma



funcion modificar(datos: \&mut \[entero], idx: entero, valor: entero) -> nulo:

&#x20;   datos\[idx] = valor

Regla de elisión de lifetimes (análoga a Rust):



Si una función toma un solo préstamo y retorna un préstamo, el lifetime de retorno se asocia a ese parámetro.



Si toma \&self (estructura), el lifetime de retorno se asocia a self.



4.3 Análisis de Lifetimes (Algoritmo)

Representación interna:



c

typedef enum {

&#x20;   LT\_ESTATICO,       // Toda la vida del programa

&#x20;   LT\_LOCAL,          // Scope de bloque (índice)

&#x20;   LT\_PARAMETRICO,    // Parámetro de función

&#x20;   LT\_ELIDIDO         // Inferido automáticamente

} LifetimeKind;



typedef struct {

&#x20;   LifetimeKind kind;

&#x20;   int index;

&#x20;   char\* nombre;

} Lifetime;

Pasos del análisis:



Recolección: Recorrer AST para identificar variables y scopes.



Asignación: Asignar lifetimes a cada variable y préstamo.



Restricciones: Recolectar restricciones de uso (ej. 'a debe vivir al menos tanto como 'b).



Resolución: Resolver el grafo de restricciones (unificación de regiones).



Verificación: Confirmar que no hay ciclos y que ningún lifetime excede el ámbito de su propietario.



Errores posibles:



ERR\_MEM\_LIFETIME\_MISMATCH: Un préstamo vive más que el valor prestado.



ERR\_MEM\_LIFETIME\_CYCLE: Ciclo en la dependencia de lifetimes.



4.4 Runtime de Memoria — Modularizado con Caché por Hilo (TLC)

Para eliminar el cuello de botella del mutex global, el runtime implementa un Pool Allocator con Caché por Hilo (Thread-Local Cache).



Estructura del pool global y caché local:



c

// runtime/core/memory.h

\#define POOL\_BLOCK\_SIZE 4096

\#define TLS\_BLOCK\_COUNT 64   // Bloques pre-asignados por hilo



typedef struct ThreadLocalPool {

&#x20;   void\* blocks\[TLS\_BLOCK\_COUNT];

&#x20;   int used\_count;

&#x20;   pthread\_mutex\_t local\_mutex; // Solo para crecimiento, casi nunca usado

} ThreadLocalPool;



typedef struct GlobalPool {

&#x20;   void\* blocks\[POOL\_MAX\_BLOCKS];

&#x20;   bool used\[POOL\_MAX\_BLOCKS];

&#x20;   size\_t block\_size;

&#x20;   pthread\_mutex\_t mutex;       // Solo para fallbacks o reabastecimiento

} GlobalPool;



// Declaración TLS (C11)

\_Thread\_local ThreadLocalPool tls\_pool;

GlobalPool g\_pool;

Algoritmo de asignación (tls\_alloc):



Verificar si tls\_pool tiene bloques libres (used\_count < TLS\_BLOCK\_COUNT).



Si sí, devolver un bloque de la lista local sin bloqueo de mutex global.



Si no (caché local vacío), adquirir el mutex global, tomar un bloque grande (ej. 4 bloques) del pool global, moverlos al TLS y devolver uno.



Si el pool global está vacío, hacer malloc de respaldo.



Algoritmo de liberación (tls\_free):



Si el puntero pertenece al TLS local (verificar rango), marcarlo como libre localmente.



Si el TLS local está lleno o el puntero es global, liberar al pool global con mutex.



Código base de implementación (C):



c

void\* tls\_alloc(size\_t size) {

&#x20;   if (tls\_pool.used\_count < TLS\_BLOCK\_COUNT) {

&#x20;       int idx = tls\_pool.used\_count++;

&#x20;       return tls\_pool.blocks\[idx];

&#x20;   }

&#x20;   // Reabastecer desde el pool global

&#x20;   pthread\_mutex\_lock(\&g\_pool.mutex);

&#x20;   // Buscar bloque libre en el pool global y moverlo al TLS

&#x20;   for (int i = 0; i < POOL\_MAX\_BLOCKS; i++) {

&#x20;       if (!g\_pool.used\[i]) {

&#x20;           g\_pool.used\[i] = true;

&#x20;           tls\_pool.blocks\[tls\_pool.used\_count++] = g\_pool.blocks\[i];

&#x20;           pthread\_mutex\_unlock(\&g\_pool.mutex);

&#x20;           return g\_pool.blocks\[i];

&#x20;       }

&#x20;   }

&#x20;   pthread\_mutex\_unlock(\&g\_pool.mutex);

&#x20;   // Fallback a malloc (solo en debug se reporta)

&#x20;   return malloc(size);

}



void tls\_free(void\* ptr) {

&#x20;   // Verificar si ptr está en el TLS local

&#x20;   for (int i = 0; i < tls\_pool.used\_count; i++) {

&#x20;       if (tls\_pool.blocks\[i] == ptr) {

&#x20;           // Marcar como libre (swap con el último)

&#x20;           tls\_pool.blocks\[i] = tls\_pool.blocks\[tls\_pool.used\_count - 1];

&#x20;           tls\_pool.used\_count--;

&#x20;           return;

&#x20;       }

&#x20;   }

&#x20;   // Si no está en TLS, liberar al pool global

&#x20;   pthread\_mutex\_lock(\&g\_pool.mutex);

&#x20;   for (int i = 0; i < POOL\_MAX\_BLOCKS; i++) {

&#x20;       if (g\_pool.blocks\[i] == ptr) {

&#x20;           g\_pool.used\[i] = false;

&#x20;           pthread\_mutex\_unlock(\&g\_pool.mutex);

&#x20;           return;

&#x20;       }

&#x20;   }

&#x20;   pthread\_mutex\_unlock(\&g\_pool.mutex);

&#x20;   free(ptr);

}

MemoryWatchdog (Modo Debug):



c

\#ifdef SYNAPSE\_DEBUG\_MEM

typedef struct {

&#x20;   void\* ptr;

&#x20;   size\_t size;

&#x20;   const char\* file;

&#x20;   int line;

&#x20;   bool active;

} MemRecord;

\#define MAX\_RECORDS 100000

MemRecord g\_watchdog\[MAX\_RECORDS];



void watchdog\_report(void) {

&#x20;   int leaks = 0;

&#x20;   for (int i = 0; i < MAX\_RECORDS; i++) {

&#x20;       if (g\_watchdog\[i].active) {

&#x20;           leaks++;

&#x20;           fprintf(stderr, "LEAK: %zu bytes en %s:%d\\n",

&#x20;                   g\_watchdog\[i].size, g\_watchdog\[i].file, g\_watchdog\[i].line);

&#x20;       }

&#x20;   }

&#x20;   if (leaks > 0) abort();

}

\#endif

4.5 ABI y Alineación de Memoria (Padding)

Fórmula de relleno: P = (A - (O mod A)) mod A, donde P son bytes de relleno, A es la alineación del tipo, O es el offset actual.

Directiva \[empaquetado]: Para estructuras que se comunican con hardware o FFI (sin padding):



synapse

\[empaquetado]

estructura CabeceraIP:

&#x20;   version: caracter   // offset 0, size 1

&#x20;   longitud: entero    // offset 1, size 4 (alineación forzada a 1)

4.6 Tests Obligatorios para esta Etapa

Test	Comando	Criterio

Ownership (move)	pytest tests/integration/test\_ownership.py -v	Detección de ERR\_MEM\_USE\_AFTER\_MOVE

Borrowing checker	pytest tests/integration/test\_borrowing.py -v	100% pass

Lifetimes	pytest tests/integration/test\_lifetimes.py -v	0 errores de compilación

Fugas de memoria	synapse test --auditar-memoria	0 leaks (AddressSanitizer)

Contención de TLC (estrés)	gcc -o test\_tls runtime/core/memory.c -lpthread \&\& ./test\_tls --threads 10000	0 bloqueos, overhead <5% vs malloc

