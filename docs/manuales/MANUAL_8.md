MANUAL 8: BACKEND Y GENERACIÓN DE CÓDIGO
Archivo: 08_BACKEND_Y_GENERACION.md
Versión: 5.0.0
Propósito: Especificar la generación de código C, WASM, las optimizaciones (PGO/LTO), la FFI y los bindings.

8.1 Modos de Generación y Flags
Modo	Flags C	Propósito
debug	-O0 -g -DDEBUG	Desarrollo, trazas, asserts activos.
release	-O2 -DNDEBUG	Producción estándar.
release-pgo	-O3 -fprofile-generate -DNDEBUG	Generación de perfiles (ejecutar benchmark luego).
release-pgo-use	-O3 -fprofile-use -flto -DNDEBUG	Optimización final con PGO + LTO.
safe	-O2 -fsanitize=address,undefined -DSAFE_MODE	Verificación formal + sanitizadores.
wasm	emcc -O3 -s WASM=1	WebAssembly (WAT).
incremental	-O2 -fno-whole-program	Compilación con caché.
8.2 Mapeo AST → C (Tabla de traducción)
Nodo AST	C Generado (ejemplo)
NODO_PROGRAMA	#include <stdio.h> + funciones.
NODO_FUNCION	int mi_funcion(int a, char* b) { ... }
NODO_ASIGNACION	int x = 42;
NODO_SI	if (cond) { ... } else { ... }
NODO_MIENTRAS	while (cond) { ... }
NODO_PARA	for (int i=0; i<10; i++) { ... }
NODO_LLAMADA	procesar(x, y);
NODO_RETORNAR	return valor; (con verificación de contrato previa)
NODO_CONTRATO	assert(precond && "Fallo de requiere");
NODO_CANAL	SynapseCanal* c = canal_crear(sizeof(T), 100);
NODO_LANZAR	pthread_create(&tid, NULL, (void*)funcion, args);
NODO_ESTRUCTURA	struct Punto { int x; int y; };
NODO_ASM	asm("mov eax, 1"); (escapado)
NODO_EXTERNO	Declaración extern int write_posix(...);
8.3 Optimización Guiada por Perfil (PGO)
Pipeline completo:

bash
# Paso 1: Instrumentación
synapse build --release --pgo=instrument
# Paso 2: Ejecutar benchmark
./instrumented_binary --benchmark
# Paso 3: Usar perfil
synapse build --release --pgo=use
Beneficios medidos: Reducción del binario en un 37% y mejora de velocidad ~15-20%.

8.4 Backend WebAssembly (WAT)
Mapeo de tipos:

Synapse	WASM
entero	i32 / i64
decimal	f64
booleano	i32 (0/1)
Ejemplo de generación WAT (pseudocódigo):

wat
(module
  (func $sumar (param $a i32) (param $b i32) (result i32)
    local.get $a
    local.get $b
    i32.add
  )
  (export "sumar" (func $sumar))
)
8.5 FFI (Interfaz con C)
Declaración de función externa:

synapse
externo funcion strlen(s: puntero) -> entero

funcion longitud(s: texto) -> entero:
    inseguro:   // Obligatorio
        retornar strlen(s.datos)   // s.datos es el char* subyacente
Mapeo de tipos para FFI:

Synapse	C (pasado a la función)
entero	int64_t
decimal	double
texto	const char* (el generador extrae datos)
booleano	bool
estructura	struct (pasado por valor o puntero)
Generación de bindings (v5.0):

synapse
@export(python)
fn procesar(datos: Lista<Entero>) -> Resultado<Flotante, Error>
// Genera módulo Python con PyObject* wrapper.

@export(java)
class Procesador { ... }
// Genera código JNI con firmas.

@export(typescript)
fn validar(id: String) -> Booleano
// Genera .d.ts con definiciones.