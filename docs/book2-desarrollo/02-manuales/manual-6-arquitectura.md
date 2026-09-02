# MANUAL 6: INTEGRACIÓN DEL ECOSISTEMA

**Archivo:** `06_INTEGRACION_ECOSISTEMA.md`  
**Versión:** 8.0.0-industrial  
**Propósito:** Especificar la integración completa del ecosistema: cómo Synapse, Syquex y OpenSyn se interconectan, la FFI con C, la serialización de datos, la generación de bindings para otros lenguajes, el runtime compartido, y el papel de OpenSyn como asistente universal. Este manual describe la columna vertebral que hace que los tres componentes funcionen como una plataforma unificada.

---

## 1. EL AST CANÓNICO UNIFICADO (EL CORAZÓN DEL ECOSISTEMA)

### 1.1. Concepto

El ecosistema Synapse se basa en un **Árbol de Sintaxis Abstracta (AST) canónico y unificado** denominado `SemNodo[]`. Tanto Synapse como Syquex traducen su código fuente a esta representación intermedia. El backend (análisis semántico, generación de código, optimizaciones) es **compartido** y solo opera sobre `SemNodo[]`.

**Ventajas:**
- **Cero duplicación:** No hay dos implementaciones de Hindley‑Milner, generador de C/LLVM/WASM, optimizador, ATP, etc.
- **Compatibilidad binaria absoluta:** Código Synapse y Syquex se enlazan a nivel de instrucciones de máquina sin overhead FFI.
- **Mantenimiento reducido:** Los cambios en el backend benefician a ambos lenguajes.
- **Interoperabilidad natural:** Las funciones de Synapse pueden ser llamadas desde Syquex y viceversa sin conversión.

### 1.2. Estructura del `SemNodo`

```c
// nucleo/ast_nodes.h (ABI v1)

#define AST_ABI_VERSION 1
#define MAX_NODOS 65536

typedef struct {
    int tipo;                   // NODO_FUNCION, NODO_ESTRUCTURA, etc.
    int linea;
    int columna;
    char* archivo;              // Ruta del archivo fuente original
    int owner_id;               // ID del propietario (para ownership)
    int scope_id;               // ID del ámbito léxico
    bool es_owned;              // ¿Es propietario de memoria?
    bool es_prestado_inmutable; // ¿Es un préstamo inmutable?
    bool es_prestado_mutable;   // ¿Es un préstamo mutable?
    bool es_transferido;        // ¿Se transfiere mediante ->?
    bool es_exportado;          // ¿Tiene @export?
    char* export_lang;          // Lenguaje de exportación (si aplica)
    
    union {
        // Nodo: Programa
        struct {
            int num_declaraciones;
            int* declaraciones_ids;  // Índices de declaraciones
        } programa;
        
        // Nodo: Función
        struct {
            char nombre[64];
            int num_params;
            int* params_ids;      // Índices de parámetros
            int tipo_retorno_id;  // Tipo de retorno (índice en tabla de tipos)
            int contratos_id;     // Índice del bloque de contratos
            int cuerpo_id;        // Índice del bloque de cuerpo
        } funcion;
        
        // Nodo: Estructura
        struct {
            char nombre[64];
            int num_campos;
            int* campos_ids;
            bool es_empaquetado;  // Directiva [empaquetado]
        } estructura;
        
        // Nodo: Llamada a función
        struct {
            char nombre[64];
            int num_args;
            int* args_ids;
        } llamada;
        
        // Nodo: Bloque
        struct {
            int num_sentencias;
            int* sentencias_ids;
        } bloque;
        
        // ... (más uniones para todos los tipos de nodos)
    };
} SemNodo;

// Tabla de símbolos (global)
typedef struct {
    char nombre[64];
    int tipo;               // TIPO_ENTERO, TIPO_FUNCION, TIPO_ESTRUCTURA, etc.
    int scope_id;
    int owner_id;
    bool es_movido;
    int num_referencias;
    bool tiene_mut_borrow;
} Simbolo;
```

### 1.3. Traductor de Syquex a `SemNodo`

El traductor (`syquex/traductor.syq`) convierte el AST de Syquex en `SemNodo[]`. La traducción es **biyectiva en cuanto a semántica**: todo concepto de Syquex tiene un equivalente en el AST canónico.

**Mapeo de nodos clave:**

| Nodo Syquex | Nodo SemNodo | Notas |
|-------------|--------------|-------|
| `FuncionDef` | `NODO_FUNCION` | Se añade un parámetro `self` implícito para métodos. |
| `EstructuraDef` | `NODO_ESTRUCTURA` | Los métodos se traducen a funciones con `self`. |
| `ConstructorDef` | `NODO_FUNCION` especial con nombre `__init__` | Retorna la estructura. |
| `MetodoDef` | `NODO_FUNCION` con `self` como primer parámetro | El nombre se decora como `struct_metodo`. |
| `EnumeracionDef` | `NODO_TIPO_ALGEBRAICO` | Los casos se traducen a constructores. |
| `Coincidir` | `NODO_COINCIDIR` | Se genera un switch sobre el discriminante. |
| `Intento` | `NODO_INTENTO` | Se traduce al modelo de `Resultado` y `?` (Manual 3 §7). La construcción `intentar`/`atrapar` está reservada exclusivamente para envolver llamadas FFI a bibliotecas C que puedan lanzar excepciones o señales (ej. `setjmp`/`longjmp`). En código nativo Syquex, se prefiere siempre `Resultado`. |
| `Lanzar` | `NODO_LANZAR` | Se convierte en `pthread_create`. |
| `Escuchar` | `NODO_ESCUCHAR` | Se convierte en un bucle con `canal_recibir()`. |
| `Canal<T>` | `NODO_CANAL` | Se traduce a `SynapseCanal*`. |
| `Delegar` (`?`) | `NODO_DELEGAR` | Se convierte en un retorno temprano con `err(...)`. |
| `export` | `NODO_EXPORT` | Se registra para generar bindings. |
| `externo` | `NODO_EXTERNO` | Se registra como FFI. |

**Algoritmo de traducción (pseudocódigo):**

```
función traducir_programa(ast_syquex):
    inicializar tabla_simbolos
    inicializar array SemNodo
    
    para cada declaración en ast_syquex:
        si es FuncionDef:
            nodo_funcion = crear_nodo(NODO_FUNCION)
            nodo_funcion.nombre = declaración.nombre
            para cada parámetro en declaración.parametros:
                nodo_param = crear_nodo(NODO_PARAMETRO)
                nodo_param.nombre = parámetro.nombre
                nodo_param.tipo = traducir_tipo(parámetro.tipo)
                añadir nodo_param a nodo_funcion.params
            nodo_funcion.tipo_retorno = traducir_tipo(declaración.tipo_retorno)
            nodo_funcion.cuerpo = traducir_bloque(declaración.cuerpo)
            añadir nodo_funcion al array
        si es EstructuraDef:
            nodo_struct = crear_nodo(NODO_ESTRUCTURA)
            nodo_struct.nombre = declaración.nombre
            para cada campo en declaración.campos:
                nodo_campo = crear_nodo(NODO_CAMPO)
                nodo_campo.nombre = campo.nombre
                nodo_campo.tipo = traducir_tipo(campo.tipo)
                añadir nodo_campo a nodo_struct.campos
            // Traducir métodos como funciones independientes
            para cada método en declaración.metodos:
                nodo_metodo = traducir_metodo(método, nodo_struct.nombre)
                añadir nodo_metodo al array
            añadir nodo_struct al array
        // ... más casos
    fin para
    
    // Construir el nodo programa
    nodo_programa = crear_nodo(NODO_PROGRAMA)
    nodo_programa.declaraciones = array_de_nodos
    añadir nodo_programa al array
    
    retornar array SemNodo
```

**Preservación de metadatos:** El traductor conserva `archivo`, `linea` y `columna` de cada nodo original para que los errores del compilador apunten al código fuente de Syquex.

---

## 2. RUNTIME COMPARTIDO (LA CAPA DE ABAJO)

El runtime es una biblioteca en C (`.a`/`.so`) que proporciona servicios fundamentales a ambos lenguajes. Es **monolítico pero modular**, y se enlaza estáticamente al binario final.

### 2.1. Módulos del Runtime

```
runtime/
├── core/
│   ├── memory.c          # Pool allocator, TLC, Arena, RC
│   ├── concurrency.c     # Fibras, canales, mutexes, semáforos, barreras
│   ├── io.c              # File I/O, sockets (basado en libc)
│   └── component_arena.c # Arenas de componente para UI/DOM
├── net/
│   └── http.c            # Cliente/servidor HTTP (libcurl + libmicrohttpd)
├── quantum/
│   └── matrix.c          # Matrices complejas para simulación cuántica
├── ml/
│   └── gguf.c            # Carga de modelos GGUF y operaciones tensoriales
└── federated/
    └── aggregator.c      # FedAvg y orquestación distribuida
```

### 2.2. Inicialización del Runtime

Todo programa generado por Synapse o Syquex incluye una función `main()` que:

1. Inicializa el pool allocator global.
2. Inicializa el scheduler de fibras.
3. Configura el manejo de señales (shutdown hooks).
4. Llama a `principal()` (el punto de entrada del usuario).
5. Al finalizar, libera recursos y termina.

**Código generado (ejemplo):**

```c
// main.c (generado por el compilador)
#include <stdio.h>
#include <stdlib.h>
#include "runtime/core/memory.h"
#include "runtime/core/concurrency.h"

// Declaración de la función principal del usuario
extern void principal(void);

int main(int argc, char** argv) {
    // Inicializar runtime
    global_pool_init();
    scheduler_init(8);  // 8 hilos OS
    atexit(shutdown_runtime);
    
    // Ejecutar programa
    principal();
    
    // Esperar a que terminen todas las fibras
    scheduler_join();
    
    // Liberar recursos
    global_pool_free();
    return 0;
}
```

### 2.3. API del Runtime (Expuesta a los Lenguajes)

El runtime expone funciones que se invocan desde el código generado. Estas funciones son las que implementan las primitivas del lenguaje (canales, fibras, etc.).

```c
// memory.h
void* pool_alloc(size_t size);
void pool_free(void* ptr);
Arena* arena_crear(size_t size);
void* arena_alloc(Arena* arena, size_t size);
void arena_free(Arena* arena);
void* rc_alloc(size_t size);
void rc_incrementar(void* ptr);
void rc_decrementar(void* ptr);

// concurrency.h
int fibra_crear(void (*func)(void*), void* arg);
void fibra_esperar(int id);
Canal* canal_crear(size_t capacidad, size_t tipo_tamano);
void canal_enviar(Canal* canal, void* dato);
void* canal_recibir(Canal* canal, bool* cerrado);
void canal_cerrar(Canal* canal);

// io.h
CadenaSegura leer_archivo(const char* ruta);
void escribir_archivo(const char* ruta, CadenaSegura contenido);
```

---

## 3. FFI CON C (INTEROPERABILIDAD NATIVA)

### 3.1. Declaración de Funciones Externas (`externo`)

Tanto Synapse como Syquex permiten declarar funciones de C con la palabra clave `externo`.

**Synapse:**
```synapse
externo funcion strlen(s: puntero) -> entero
```

**Syquex:**
```syquex
externo funcion strlen(s: &texto) -> entero
```

**Mapeo de tipos (Synapse ↔ C ↔ Syquex):**

| Synapse | C | Syquex | Notas |
|---------|---|--------|-------|
| `entero` | `int64_t` | `entero` | Tamaño fijo de 64 bits |
| `decimal` | `double` | `decimal` | Doble precisión |
| `booleano` | `bool` | `booleano` | 1 byte |
| `texto` | `CadenaSegura` (struct) | `texto` | Longitud + buffer |
| `tensor` | `Tensor` (struct) | `tensor` | Filas, columnas, float* |
| `puntero` | `void*` | `&` / `*` | Solo en `inseguro` |
| `estructura` | `struct` | `estructura` | Paso por valor o referencia |

### 3.2. Bloque `inseguro` (Solo Synapse)

Las llamadas a FFI se consideran **inseguras** y deben encapsularse en un bloque `inseguro`.

```synapse
funcion longitud(s: texto) -> entero:
    inseguro:
        retornar strlen(s.datos)
```

**En Syquex:** El FFI es más seguro por defecto porque el compilador maneja el marshaling automáticamente, pero aún así se recomienda usar `externo` con cuidado.

### 3.3. Marshaling Automático en Syquex

Cuando se pasa un `texto` de Syquex a C, el compilador:

1. Añade un byte `\0` al final en la arena (sin copiar todo el buffer).
2. Pasa el puntero `const char*` a la función C.
3. Si la función C retorna un `char*`, lo convierte de vuelta a `texto` (copiando a la arena).

**Ejemplo (Syquex):**
```syquex
externo funcion strdup(s: &texto) -> &texto

funcion duplicar(s: texto) -> texto:
    retornar strdup(&s)  // Automáticamente convierte de vuelta a texto
```

**C generado:**
```c
CadenaSegura duplicar(CadenaSegura s) {
    // Añadir byte nulo al final en arena
    char* c_str = arena_alloc(arena_actual, s.longitud + 1);
    memcpy(c_str, s.datos, s.longitud);
    c_str[s.longitud] = '\0';
    
    // Llamar a C
    char* result = strdup(c_str);
    
    // Convertir de vuelta a CadenaSegura
    CadenaSegura res;
    res.longitud = strlen(result);
    res.datos = arena_alloc(arena_actual, res.longitud);
    memcpy(res.datos, result, res.longitud);
    free(result);  // La C malloc debe ser liberada
    return res;
}
```

---

## 4. GENERACIÓN DE BINDINGS PARA OTROS LENGUAJES (`@export`)

### 4.1. Directiva `@export`

Las funciones y estructuras pueden marcarse con `@export(lenguaje)` para generar bindings automáticos a otros lenguajes (Python, JavaScript/TypeScript, Java, etc.).

**Syquex:**
```syquex
@export(python) funcion procesar(data: Lista<Decimal>) -> Resultado<Decimal, Texto>

@export(typescript) estructura Usuario:
    nombre: Texto
    edad: Entero
```

**Synapse:**
```synapse
@export(python) fn procesar(datos: Lista<Entero>) -> Resultado<Flotante, Error>
```

### 4.2. Lenguajes Soportados

| Lenguaje | Extensión | Generación |
|----------|-----------|------------|
| Python | `.py` | Módulo con `ctypes` o `cffi` |
| TypeScript/JavaScript | `.d.ts` + `.js` | Declaraciones de tipos y wrapper |
| Java | `.java` | Clase JNI |
| C# | `.cs` | P/Invoke |
| Rust | `.rs` | `extern "C"` bindings |
| Zig | `.zig` | `extern` bindings |

### 4.3. Pipeline de Generación

1. El compilador detecta nodos con `@export` en el AST.
2. Para cada exportación, genera el código de envoltura (wrapper) en el lenguaje destino.
3. Los wrappers se guardan en el directorio `bindings/` junto al binario.
4. Los wrappers se compilan (si es necesario) como bibliotecas separadas.

**Ejemplo (Python exportado):**

**Syquex:**
```syquex
@export(python) funcion calcular_iva(monto: decimal, porcentaje: decimal) -> decimal
```

**Bindings generados (`bindings/calcular_iva.py`):**
```python
import ctypes
import os

lib = ctypes.CDLL(os.path.join(os.path.dirname(__file__), "libsynapse.so"))

# Declarar la función
calcular_iva = lib.calcular_iva
calcular_iva.argtypes = [ctypes.c_double, ctypes.c_double]
calcular_iva.restype = ctypes.c_double

def calcular_iva_python(monto, porcentaje):
    return calcular_iva(monto, porcentaje)
```

---

## 5. SERIALIZACIÓN Y COMUNICACIÓN (CANALES REMOTOS)

### 5.1. Formato de Serialización Binario

El formato de serialización para canales remotos es un subconjunto de MessagePack, optimizado para velocidad. **Especificación normativa:** el formato definitivo está en el Manual 5, §6.3. Esta sección (Manual 6, §5.1) se considera un borrador anterior y debe ignorarse o eliminarse en futuras revisiones.

| Tipo | Identificador | Datos | Tamaño total |
|------|---------------|-------|--------------|
| `nulo` | `0xC0` | - | 1 byte |
| `booleano (falso)` | `0xC2` | - | 1 byte |
| `booleano (verdadero)` | `0xC3` | - | 1 byte |
| `entero` (≤ 255) | `0x00` | valor (1 byte) | 2 bytes |
| `entero` (≤ 65535) | `0x01` | valor (2 bytes) | 3 bytes |
| `entero` (≤ 2^32-1) | `0x02` | valor (4 bytes) | 5 bytes |
| `entero` (≤ 2^64-1) | `0x03` | valor (8 bytes) | 9 bytes |
| `decimal` (32-bit) | `0x04` | float (4 bytes) | 5 bytes |
| `decimal` (64-bit) | `0x05` | double (8 bytes) | 9 bytes |
| `texto` | `0x06` | longitud (4 bytes) + datos | 5 + len |
| `tensor` | `0x07` | filas (4) + columnas (4) + datos (float*) | 8 + 4*filas*columnas |
| `estructura` | `0x08` | campos serializados secuencialmente | variable |
| `lista` | `0x09` | longitud (4) + elementos | variable |
| `mapa` | `0x0A` | num_pares (4) + (clave, valor) | variable |

### 5.2. Funciones de Serialización (C)

```c
// axon/axon_rt.c
void serializar_valor(void* valor, int tipo, uint8_t** buffer, size_t* len);
void* deserializar_valor(uint8_t* buffer, size_t len, int* tipo);
```

### 5.3. Handshake Ed25519 (Zero-Trust)

El handshake entre nodos se realiza mediante Ed25519 (TweetNaCl) y es **zero-trust**:

1. El cliente envía un mensaje `HELLO` con su clave pública y una firma de un nonce aleatorio de 32 bytes.
2. El servidor verifica la firma usando la clave pública proporcionada.
3. Si es válida, el servidor responde con su propio `HELLO` firmado.
4. Se deriva una clave de sesión (usando `crypto_kx` de libsodium o similar) para cifrar el tráfico.

**Estructura del mensaje HELLO:**
```
[nonce (32 bytes)] [clave_publica (32 bytes)] [firma (64 bytes)]
```

**Flujo:**
```
Cliente                                      Servidor
   |                                             |
   |--- HELLO (nonce, pk, firma) --------------->|
   |                                             | Verificar firma
   |<--- HELLO_RESP (nonce, pk_serv, firma_serv)-|
   |                                             |
   |--- DATOS_CIFRADOS (session_key) ----------->|
   |<--- DATOS_CIFRADOS -------------------------|
```

---

## 6. OPENSYN COMO ASISTENTE UNIVERSAL

### 6.1. Acceso al AST Unificado

OpenSyn tiene acceso al AST canónico (`SemNodo[]`) a través del LSP. Esto le permite:

- Conocer la estructura exacta del código (función actual, variables, tipos).
- Obtener diagnósticos activos (errores, warnings).
- Proporcionar sugerencias contextuales precisas.

### 6.2. Transpilación Python → Syquex

OpenSyn puede tomar código Python y generar Syquex equivalente, mapeando tipos dinámicos a estáticos.

**Flujo:**
1. OpenSyn parsea el código Python usando el módulo `ast` de Python.
2. Para cada nodo Python, determina su equivalente en Syquex:
   - `list` → `Lista<T>`
   - `dict` → `Mapa<K,V>`
   - `def` → `funcion`
   - `class` → `estructura`
   - Excepciones → `Resultado<T,E>`
3. Genera código Syquex con anotaciones de tipo inferidas.

### 6.3. Generación Automática de Bindings C → Syquex

OpenSyn puede leer archivos de cabecera C (`.h`) y generar bindings Syquex automáticamente.

**Comando:**
```bash
opensyn ai bindings --header libcurl.h --output lib/curl.syq
```

**Flujo:**
1. OpenSyn usa `libclang` o `ctypes` para parsear la cabecera C.
2. Extrae funciones, estructuras, constantes y macros.
3. Genera código Syquex con `externo` y wrappers FFI.
4. Aplica marshaling automático para tipos (cadenas, arrays, punteros).

### 6.4. Explicación y Generación de Código

- **Explicación:** OpenSyn recibe el nodo AST actual (función, estructura, etc.) y genera una explicación en lenguaje natural, en el idioma del usuario.
- **Generación de código:** OpenSyn genera código Syquex o Synapse a partir de descripciones en lenguaje natural, y lo valida con el compilador.

---

## 7. DIAGNÓSTICOS Y MANEJO DE ERRORES

### 7.1. Sistema Unificado de Errores

Todos los errores del compilador y del runtime se reportan a través del `DiagnosticManager`, que:
- Centraliza los mensajes de error en un solo lugar.
- Soporta múltiples idiomas (`#lang:`).
- Proporciona ubicación exacta (archivo, línea, columna).
- Sugiere correcciones cuando es posible.

### 7.2. Taxonomía de Errores (Extracto)

| Categoría | Ejemplos |
|-----------|----------|
| Léxicos | `ERR_LEX_MISSING_LANG`, `ERR_LEX_TAB_DETECTED` |
| Sintácticos | `ERR_SYNTAX_EXPECTED_TOKEN`, `ERR_INDENT_INVALID` |
| Semánticos | `ERR_SEM_VAR_NO_DECLARADA`, `ERR_SEM_TIPO_INCOMPATIBLE` |
| Memoria | `ERR_MEM_USE_AFTER_MOVE`, `ERR_MEM_LIFETIME_MISMATCH` |
| FFI | `ERR_FFI_UNRESOLVED_SYMBOL`, `ERR_FFI_INVALID_TYPE` |
| ATP | `ERR_ATP_TAUTOLOGY_FAILED`, `ERR_ATP_NON_TERMINATING` |
| Axon | `ERR_AXON_COMPROMISED`, `ERR_AXON_VERSION` |

### 7.3. Integración con LSP

El LSP recibe diagnósticos del compilador y los envía al editor en tiempo real. Esto incluye:
- Errores y warnings mientras se escribe.
- Información de hover (tipos, documentación).
- Autocompletado (símbolos, palabras clave, sugerencias de IA).
- Navegación (definición, referencias).

---

## 8. COMPILACIÓN Y ENLACE

### 8.1. Pipeline de Compilación Completo

```
1. [Fuente .syn/.syq] → Lexer → Parser → AST
2. [AST] → Traductor (si es .syq) → SemNodo[]
3. [SemNodo[]] → Análisis Semántico → AST validado + tabla de símbolos + contratos
4. [AST validado] → Generador → Código C / LLVM IR / WAT
5. [Código intermedio] → Backend (GCC/Clang/LLVM/emcc) → Binario
6. [Binario] → Enlace con runtime → `synapse.exe`
```

### 8.2. Enlace Estático vs Dinámico

- Por defecto, el runtime se enlaza **estáticamente** al binario final, resultando en un ejecutable autocontenido.
- Opcionalmente, se puede generar una biblioteca compartida (`.so`/`.dll`) para ser usada desde otros lenguajes.

### 8.3. Determinismo y Reproducibilidad

El compilador garantiza que el mismo código fuente produzca el mismo binario bit a bit:
- Todas las iteraciones sobre mapas/diccionarios se realizan en orden lexicográfico.
- Las funciones se emiten en orden alfabético.
- El lockfile (`axon.lock`) registra hashes SHA-256 de todas las dependencias.

---

## 9. PRUEBAS OBLIGATORIAS PARA ESTA ETAPA

| Test | Comando | Criterio |
|------|---------|----------|
| Traductor Syquex → SemNodo | `pytest tests/syquex/test_traductor.py -v` | 100% pass |
| FFI con C (llamada básica) | `pytest tests/integration/test_ffi.py -v` | 100% pass |
| Exportación a Python | `pytest tests/integration/test_export_python.py -v` | Bindings generados y ejecutables |
| Serialización/Deserialización | `pytest tests/integration/test_serialization.py -v` | 100% pass |
| Handshake Ed25519 | `pytest tests/integration/test_handshake.py -v` | 100% pass |
| Transpilación Python → Syquex | `pytest tests/integration/test_transpile.py -v` | Código generado compila correctamente |
| Diagnósticos del compilador | `pytest tests/integration/test_diagnostics.py -v` | Mensajes de error en español/inglés |

---

## 10. EJEMPLO COMPLETO DE INTEGRACIÓN

**Código Synapse (`motor_audio.syn`):**
```synapse
#lang: es
@export(python) funcion generar_sonido(frecuencia: decimal, duracion: decimal) -> tensor:
    tasa = 44100.0
    num = entero(duracion * tasa)
    resultado = tensor(num, 1)
    para i = 0 mientras i < num:
        t = decimal(i) / tasa
        resultado[i] = math.sen(2.0 * math.pi * frecuencia * t)
    retornar -> resultado
```

**Código Syquex (`app.syq`):**
```syquex
#lang: es
importar lib.io
importar lib.web
importar synapse.audio  // Importa el módulo Synapse

funcion principal() -> Resultado<nulo, texto>:
    let audio = synapse.audio.generar_sonido(440.0, 3.0)?
    io.escribir_linea("Audio generado: ", audio.filas, " muestras")
    
    // Servidor web
    let servidor = web.servidor(8080)
    servidor.get("/", funcion(req):
        retornar web.respuesta(200, "Audio: " + audio.filas.texto())
    )
    servidor.iniciar()?
    retornar ok()
```

**Flujo de compilación:**
1. `motor_audio.syn` se compila a una biblioteca compartida (`libmotor_audio.so`) con exportación Python.
2. `app.syq` se compila y enlaza con `libmotor_audio.so`.
3. El binario final (`app.exe`) incluye el servidor web y el motor de audio.

**Uso desde Python:**
```python
import motor_audio
audio = motor_audio.generar_sonido(440.0, 3.0)
print(audio.shape)
```

---

## 11. SIGUIENTES PASOS

Con la integración del ecosistema completa, el siguiente manual (Manual 7) se centrará en **OpenSyn como Asistente IA**, cubriendo la orquestación de modelos, el pipeline RAG, la generación de código, la transpilación y el fine-tuning.

---

*Este manual proporciona la especificación completa de la integración del ecosistema. La implementación debe garantizar que Synapse, Syquex y OpenSyn funcionen como una plataforma unificada, sin fricción y con máxima interoperabilidad.*

**Fin del Manual 6**