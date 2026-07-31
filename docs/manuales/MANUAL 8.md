MANUAL 8: BACKEND Y GENERACIÓN DE CÓDIGO
Archivo: 08_BACKEND_Y_GENERACION.md
Versión: 5.1.1-industrial
Propósito: Especificar la generación de código C, WASM, LLVM, las optimizaciones (PGO/LTO), la FFI y los bindings, con reglas estrictas de determinismo.

8.1 Modos de Generación y Flags
Modo	Flags C	Propósito
debug	-O0 -g -DDEBUG	Desarrollo, trazas, asserts activos.
release	-O2 -DNDEBUG	Producción estándar.
release-pgo	-O3 -fprofile-generate -DNDEBUG	Generación de perfiles.
release-pgo-use	-O3 -fprofile-use -flto -DNDEBUG	Optimización final PGO + LTO.
safe	-O2 -fsanitize=address,undefined -DSAFE_MODE	Verificación formal + sanitizadores.
wasm	emcc -O3 -s WASM=1	WebAssembly (WAT).
incremental	-O2 -fno-whole-program	Compilación con caché.
llvm	clang -O3 -emit-llvm	Generación de IR LLVM para análisis y optimización.
llvm-jit	clang -O1 (JIT)	Ejecución interactiva (REPL) con compilación en tiempo de ejecución.
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
Regla de determinismo en la emisión: Todas las funciones globales, estructuras y variables estáticas se emiten en el archivo C generado en orden alfabético estricto por su nombre. Esto garantiza que el binario intermedio (y por tanto el binario final) sea idéntico entre compilaciones, cumpliendo con el requisito de diff 0 bytes del bootstrap.

8.3 Optimización Guiada por Perfil (PGO)
Pipeline completo:

bash
synapse build --release --pgo=instrument
./instrumented_binary --benchmark
synapse build --release --pgo=use
Beneficios medidos: Reducción del binario en un 37% y mejora de velocidad ~15-20%.

8.4 Backend WebAssembly (WAT)
Mapeo de tipos: entero → i32/i64, decimal → f64, booleano → i32 (0/1).
Ejemplo WAT:

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
synapse
externo funcion strlen(s: puntero) -> entero

funcion longitud(s: texto) -> entero:
    inseguro:
        retornar strlen(s.datos)
Mapeo de tipos para FFI:

Synapse	C (pasado a la función)
entero	int64_t
decimal	double
texto	const char*
booleano	bool
estructura	struct (pasado por valor o puntero)
Generación de bindings (v5.0) — ACOTACIÓN DE ALCANCE (Regla 6: Cero Deuda Técnica):

El nivel bajo de la FFI (externo funcion + mapeo de tipos a C) está plenamente operativo y verificado en el release v5.1.1-industrial.

La generación automatizada de bindings de alto nivel (@export(python), @export(java), @export(typescript)) se declara formalmente FUERA DE ALCANCE del release industrial v5.1.1 y queda diferida al roadmap de la versión v5.2. No se implementan stubs parciales en el generador, a fin de no introducir deuda técnica ni código muerto.

synapse
@export(python) fn procesar(datos: Lista<Entero>) -> Resultado<Flotante, Error>
// (v5.2) Genera módulo Python con PyObject* wrapper.

@export(java) class Procesador { ... } // (v5.2) Genera código JNI.

@export(typescript) fn validar(id: String) -> Booleano // (v5.2) Genera .d.ts.
8.6 Backend LLVM (IR, JIT y Control Flow)
El backend LLVM permite generar IR (Intermediate Representation) y compilarlo a código nativo con optimizaciones avanzadas o ejecutarlo vía JIT.

8.6.1 Estructuras y API (C):

c
// validate_llvm_backend.c
typedef struct {
    LLVMContextRef context;
    LLVMModuleRef module;
    LLVMBuilderRef builder;
    int opt_level;  // 0, 1, 2, 3
} LLVMBackend;

LLVMBackend* llvm_backend_create(const char* name, int opt_level);
LLVMValueRef llvm_add_function(LLVMBackend* be, const char* name, LLVMTypeRef ret, LLVMTypeRef* params);
int llvm_emit_ir(LLVMBackend* be, const char* filename);
8.6.2 Control Flow y JIT:

Bucles y Condicionales (validate_llvm_control_flow.c): Construcción de CFG con bloques básicos.

JIT (validate_llvm_jit.c): Compilación y ejecución en memoria.

c
int llvm_jit_run(LLVMJIT* jit, const char* name, void** args);
8.6.3 Comandos CLI:

bash
synapse build --target llvm main.syn         # Genera .ll
synapse build --target llvm --opt-level 3    # Optimización máxima
synapse run --jit main.syn                   # Ejecuta con JIT
8.6.4 Integración con --safe (ATP): Cuando se usa --safe, el generador LLVM inserta llvm.assume para las precondiciones y llvm.verifier para las postcondiciones, delegando la verificación formal al motor ATP durante la fase de generación.

8.7 Tests Obligatorios para esta Etapa
Test	Comando	Criterio
Generación C	pytest tests/integration/test_generator.py -v	100% pass
PGO pipeline	bash nucleo/pgo_pipeline.sh	Mejora >15%
WASM	synapse build --target wasm tests/fixtures/sum.syn	Genera .wasm válido
LLVM IR	gcc -o test_llvm validate_llvm_backend.c -lLLVM && ./test_llvm --test emit_ir	PASS
LLVM JIT	./test_llvm_jit --test run_fibonacci	PASS
Determinismo (Ordenación alfabética)	synapse build --debug test.syn && md5sum test.c; synapse build --debug test.syn && md5sum test.c	Ambos md5sum deben ser idénticos