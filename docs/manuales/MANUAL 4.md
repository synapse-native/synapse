# MANUAL 4: MODELO DE MEMORIA DE SYQUEX

**Archivo:** `04_MODELO_MEMORIA_SYQUEX.md`  
**Versión:** 8.0.0-industrial  
**Propósito:** Especificar en detalle el modelo de gestión de memoria de Syquex, que combina arenas por ámbito, conteo de referencias (RC), análisis de alcance automático, Cleanup Blocks para salidas tempranas y FFI Marshaling para interoperabilidad con C. Este manual describe cómo Syquex logra seguridad de memoria sin recolector de basura (GC) y sin la complejidad de ownership explícito de Rust, superando a Python en rendimiento y determinismo.

---

## 1. INTRODUCCIÓN: EL PROBLEMA DE LA MEMORIA EN LENGUAJES DE ALTO NIVEL

### 1.1. ¿Por qué Python es lento en gestión de memoria?

Python utiliza un **recolector de basura (GC) basado en conteo de referencias** con un colector de ciclos adicional. Esto causa:
- **Overhead de asignación:** Cada objeto es una estructura `PyObject` pesada en el heap.
- **Pausas impredecibles:** El colector de ciclos se ejecuta periódicamente, causando micro-pausas.
- **Fragmentación:** Asignación y liberación frecuente de objetos pequeños fragmenta la memoria.
- **GIL:** El Global Interpreter Lock limita la concurrencia real.

### 1.2. El enfoque de Syquex: Sin GC, sin manual, sin pausas

Syquex implementa un modelo de memoria **híbrido y determinista** que elimina el GC y las pausas, manteniendo la productividad del desarrollador:

1. **Arenas por Ámbito (Por Defecto):** La mayoría de los objetos se asignan en una arena de memoria contigua asociada al ámbito (función, bloque, petición HTTP). Al salir del ámbito, la arena completa se libera de un solo golpe (`arena_free()`). Esto es **O(1)** y sin fragmentación.

2. **Conteo de Referencias No Atómico (`rc<T>`):** Para objetos que deben sobrevivir al ámbito (ej. estructuras compartidas entre fibras). El conteo no usa operaciones atómicas (`fetch_add`) a menos que se detecte concurrencia (canales).

3. **Conteo de Referencias Atómico (`arc<T>`):** Para objetos compartidos entre fibras a través de canales. Usa operaciones atómicas para seguridad en concurrencia.

4. **Referencias Débiles (`débil<T>`):** Para prevenir ciclos. El compilador emite un error estático si detecta un ciclo potencial sin una anotación `débil`. No hay barredor de ciclos en runtime.

5. **Análisis de Alcance Automático:** El compilador determina el último uso de cada variable e inserta liberaciones en los puntos exactos (Cleanup Blocks).

6. **Arenas de Componente (UI/DOM):** Para aplicaciones GUI, cada componente (ventana, widget) tiene su propia arena. Al destruir el componente, toda su arena se libera en masa, resolviendo el problema de referencias cíclicas en árboles UI.

---

## 2. ARENAS POR ÁMBITO (DEFAULT)

### 2.1. Concepto

Una arena es un bloque de memoria contiguo del cual se asignan objetos mediante un **bump allocator** (incremento de puntero). La liberación es instantánea: se libera todo el bloque al salir del ámbito.

```
┌─────────────────────────────────────────────────────────────────────┐
│                         ARENA POR ÁMBITO                           │
├─────────────────────────────────────────────────────────────────────┤
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │  Inicio → [Objeto A] [Objeto B] [Objeto C] ... ← Puntero    │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  Asignación: O(1) - solo incrementa el puntero                     │
│  Liberación: O(1) - arena_free() libera todo el bloque            │
│  Fragmentación: Cero                                              │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2. Estructura de Datos (C)

```c
// runtime/core/memory.h

typedef struct Arena {
    uint8_t* inicio;        // Inicio del bloque de memoria
    uint8_t* puntero;       // Puntero actual (próxima posición libre)
    uint8_t* fin;           // Fin del bloque
    struct Arena* padre;    // Arena padre (para anidamiento)
    struct Arena* hijo;     // Primer hijo (para seguimiento)
    size_t tamano;          // Tamaño total del bloque
    bool es_global;         // Si es la arena global de la aplicación
} Arena;

// Funciones
Arena* arena_crear(size_t tamano_inicial);
Arena* arena_crear_hijo(Arena* padre, size_t tamano_inicial);
void* arena_alloc(Arena* arena, size_t tamano, size_t alineacion);
void arena_free(Arena* arena);
void arena_reset(Arena* arena);  // Reinicia el puntero sin liberar memoria
```

### 2.3. Algoritmo de Asignación

```c
void* arena_alloc(Arena* a, size_t tamano, size_t alineacion) {
    // Alinear el puntero actual a la alineación requerida
    uintptr_t addr = (uintptr_t)a->puntero;
    uintptr_t aligned = (addr + alineacion - 1) & ~(alineacion - 1);
    size_t offset = aligned - addr;
    
    // Verificar espacio disponible
    if (a->puntero + offset + tamano > a->fin) {
        // Expandir la arena si es posible (solo para arenas globales)
        if (a->es_global) {
            arena_expandir(a, tamano);
            return arena_alloc(a, tamano, alineacion);
        } else {
            // Fallback a heap (con advertencia)
            return malloc(tamano);
        }
    }
    
    a->puntero += offset + tamano;
    return (void*)aligned;
}
```

### 2.4. Anidamiento de Arenas

Las arenas pueden anidarse para reflejar la jerarquía de ámbitos:

```
Arena Global (Aplicación)
    └── Arena de Función Principal
            ├── Arena de Bucle
            │   └── Arena de Iteración
            └── Arena de Bloque
```

Cuando se libera una arena padre, todas las arenas hijas se liberan automáticamente (en cascada).

### 2.5. Ejemplo en Syquex

```syquex
funcion procesar_peticion(req):
    // Arena automática para la petición
    let datos = req.leer_cuerpo()    // asignado en la arena de la petición
    let resultado = procesar(datos)   // también en la arena
    retornar resultado
    // arena_free() al salir de la función (implícito)
```

**El usuario no escribe `arena`.** El compilador deduce que `datos` y `resultado` deben vivir en la arena del ámbito y genera la asignación correspondiente.

---

## 3. CONTEJO DE REFERENCIAS (`rc<T>` Y `arc<T>`)

### 3.1. Cuándo se Usa RC

Syquex usa `rc<T>` (no atómico) cuando el objeto **debe sobrevivir al ámbito** y **no cruza hilos**. Esto ocurre en casos como:

- Estructuras compartidas entre varias partes de una misma fibra.
- Cachés locales.
- Objetos de larga duración pero sin concurrencia.

El análisis estático del compilador determina si un objeto puede ser de ámbito (arena) o necesita RC. Si el objeto se escapa del ámbito (ej. se retorna o se asigna a una variable global), el compilador **promueve automáticamente** a `rc<T>`.

### 3.2. Estructura de Datos (C)

```c
// runtime/core/memory.h

typedef struct RcHeader {
    uint32_t ref_count;          // Conteo de referencias (no atómico)
    uint32_t weak_count;         // Conteo de referencias débiles
    void* data;                  // Datos del objeto (después del header)
    void (*destructor)(void*);   // Destructor opcional
} RcHeader;

typedef struct ArcHeader {
    atomic_uint32_t ref_count;   // Conteo atómico
    atomic_uint32_t weak_count;  // Conteo atómico de débiles
    void* data;
    void (*destructor)(void*);
} ArcHeader;

void* rc_alloc(size_t tamano, void (*destructor)(void*));
void rc_incrementar(void* ptr);
void rc_decrementar(void* ptr);
void* arc_alloc(size_t tamano, void (*destructor)(void*));
void arc_incrementar(void* ptr);
void arc_decrementar(void* ptr);
```

### 3.3. Semántica de Movimiento (Move Semantics)

Cuando un objeto `rc` se envía a través de un canal (`Canal<T>`), el compilador aplica **move semantics** (semántica de movimiento). Esto significa que:

- La variable origen se invalida (no puede usarse después del envío).
- El objeto **no** se promueve a `arc` automáticamente. En lugar de eso, la propiedad se transfiere al receptor.
- Si el objeto se comparte entre múltiples fibras (no solo enviado), el compilador promueve a `arc`.

**Esto evita la necesidad de "deep promotion" y condiciones de carrera en las cabeceras RC.**

### 3.4. Ejemplo

```syquex
estructura Dato:
    contenido: texto

funcion enviar(c: Canal<Dato>):
    let d = rc(Dato("Secreto"))  // d es rc<Dato>
    c <- d   // d se mueve, la variable d queda inválida
    // d.contenido = "Nuevo"   // ERROR: d fue movido

funcion receptor(c: Canal<Dato>):
    escuchar c:
        let d = c ->   // d es Dato (no rc, la propiedad pasó)
        log(d.contenido)  // OK
```

---

## 4. REFERENCIAS DÉBILES (`débil<T>`) Y PREVENCIÓN DE CICLOS

### 4.1. El Problema de los Ciclos

Si dos objetos `rc` se referencian mutuamente, nunca se liberan (fuga de memoria). Syquex no tiene barredor de ciclos en runtime, por lo que **la prevención de ciclos es estática**.

### 4.2. Solución: Referencias Débiles

Una referencia débil (`débil<T>`) no incrementa el contador de referencias. Cuando el objeto fuerte se destruye, la débil se invalida automáticamente.

```c
// C: débil<T> es un puntero al RcHeader con un flag de validez
typedef struct {
    RcHeader* header;
    uint32_t version;   // Versión del objeto (para detección de invalidación)
} WeakRef;
```

### 4.3. Sintaxis en Syquex

```syquex
estructura Nodo:
    valor: entero
    siguiente: débil<Nodo>   // Referencia débil para evitar ciclo

funcion crear_lista():
    let a = rc(Nodo(1, debil(nulo)))  // debil(nulo) es una referencia débil vacía
    let b = rc(Nodo(2, debil(a)))     // b tiene una débil a a
    a.siguiente = debil(b)             // a tiene una débil a b
    // Cuando a y b salen del ámbito, sus rc se decrementan y se liberan sin fugas
```

### 4.4. Detección de Ciclos en Tiempo de Compilación

El analizador de alcance de Syquex detecta ciclos potenciales:

- Si una estructura tiene un campo `rc` que apunta a una estructura que contiene un `rc` a la primera, y no hay `débil`, se emite un error.
- Si se detecta un ciclo, el compilador sugiere usar `débil` o una arena de componente.

**Error:** `ERR_MEM_CYCLE_DETECTED: Ciclo potencial en la estructura 'Nodo'. Use 'débil' para romper el ciclo.`

---

## 5. ANÁLISIS DE ALCANCE Y CLEANUP BLOCKS

### 5.1. El Problema de las Salidas Tempranas

En una función con múltiples puntos de retorno (`retornar`, `?`, `romper`), el compilador debe asegurar que la memoria se libere correctamente en todos los caminos.

```syquex
funcion procesar() -> Resultado<nulo, texto>:
    let a = crear_recurso()   // rc
    si condicion:
        retornar ok()   // <- a debe liberarse antes de retornar
    let b = crear_otro_recurso()
    // ...
    retornar ok()   // <- a y b deben liberarse
```

### 5.2. Solución: Cleanup Blocks

El compilador genera **Cleanup Blocks** en el Control Flow Graph (CFG). Cada punto de salida temprana tiene un bloque de cleanup que decrementa los contadores RC de las variables vivas.

**Algoritmo:**

1. Construir el CFG de la función.
2. Realizar análisis de liveness para cada variable en cada punto.
3. Para cada punto de salida, insertar llamadas a `rc_decrementar()` para todas las variables vivas en ese punto.
4. Para retornos con `?`, insertar cleanup antes de propagar el error.

### 5.3. Ejemplo de CFG con Cleanup Blocks

```
Función procesar():
    ┌─────────────────────────────────────────────────────────────────┐
    │   Inicio                                                       │
    │   let a = rc_alloc()                                           │
    │   si condicion:                                                │
    │       └──► Cleanup (decrementar a) ──► retornar ok()          │
    │   let b = rc_alloc()                                           │
    │   ...                                                          │
    │   Cleanup (decrementar a, b) ──► retornar ok()                │
    └─────────────────────────────────────────────────────────────────┘
```

### 5.4. Implementación en el Generador (C)

```c
// C generado para una función con `?`
Resultado_T procesar() {
    Arena* arena = arena_crear(1024);
    // Asignaciones en arena...
    int rc_flag = 0;   // Para saber qué objetos se han asignado
    
    if (condicion) {
        // Cleanup: liberar recursos
        if (rc_flag & 1) rc_decrementar(a);
        if (rc_flag & 2) rc_decrementar(b);
        arena_free(arena);
        return ok();
    }
    
    // ... código ...
    
    // Cleanup final
    if (rc_flag & 1) rc_decrementar(a);
    if (rc_flag & 2) rc_decrementar(b);
    arena_free(arena);
    return ok();
}
```

---

## 6. ARENAS DE COMPONENTE (UI/DOM)

### 6.1. El Problema de GUI y DOM

En aplicaciones GUI (GTK) o DOM (navegador), los objetos forman grafos cíclicos complejos (padre-hijo, callbacks). Liberar objetos individualmente es costoso y propenso a fugas.

### 6.2. Solución: Arenas de Componente

Cada componente (ventana, diálogo, widget) tiene su propia arena. Cuando se destruye el componente, **la arena completa se libera en masa**, independientemente de las referencias cíclicas internas.

### 6.3. Estructura de Datos (C)

```c
// runtime/core/component_arena.h

typedef struct ComponentArena {
    Arena* arena;                    // Arena subyacente
    struct ComponentArena* padre;    // Componente padre
    struct ComponentArena** hijos;   // Lista de hijos
    int num_hijos;
    int ref_count;                   // Cuenta de referencias desde el árbol UI
    bool marcado_para_liberar;
    void (*destructor)(void*);       // Destructor para el componente completo
} ComponentArena;

ComponentArena* comp_arena_crear(Arena* padre, size_t tamano_inicial);
void* comp_alloc(ComponentArena* ca, size_t tamano);
void comp_destroy(ComponentArena* ca);  // Libera el componente y todos sus hijos
```

### 6.4. Reglas de Uso

- Cada widget/componente UI tiene su propia arena.
- Los hijos heredan la arena del padre o crean una nueva.
- Cuando se destruye un componente, `comp_destroy()` libera toda la jerarquía de arenas (hijos y descendientes).
- Los callbacks de eventos capturan referencias débiles (`débil`) al widget para evitar ciclos.

### 6.5. Ejemplo en Syquex (GUI)

```syquex
estructura Ventana:
    titulo: texto
    boton: Boton
    arena: arena<Componente>

    crear(titulo):
        self.arena = arena(Componente, 4096)  // Arena propia de 4KB
        self.boton = Boton("Clic", self)      // se asigna en la arena
        self.boton.onclick = funcion():
            // Captura débil para evitar ciclo
            let ventana = debil(self)
            ventana?.cerrar()

    metodo cerrar():
        comp_destroy(self.arena)  // Libera toda la jerarquía de componentes
```

---

## 7. FFI MARSHALING Y ZERO-COPY

### 7.1. El Desafío de Pasar Datos a C

Syquex usa `texto` (longitud + puntero, sin byte nulo). Las librerías C (`libsqlite3`, `GTK`, `libcurl`) esperan cadenas terminadas en `\0` (`const char*`). Copiar cada cadena sería ineficiente.

### 7.2. Estrategia Zero‑Copy

El compilador genera código que:

1. **Añade un byte `\0` al final del texto en la arena** (sin copiar todo el buffer). Esto es posible porque la arena es contigua y el objeto `texto` ya tiene un puntero.
2. Si la función C modifica la cadena, se hace una copia en arena.
3. Para estructuras complejas, se usa marshaling automático (generado por OpenSyn).

```c
// Marshaling en C
const char* texto_a_c_string(CadenaSegura* texto, Arena* arena) {
    // Añadir byte nulo al final (en la arena)
    char* c_str = arena_alloc(arena, texto->longitud + 1);
    memcpy(c_str, texto->datos, texto->longitud);
    c_str[texto->longitud] = '\0';
    return c_str;
}
```

### 7.3. Life‑cycle Management para C Callbacks

Cuando un callback de C captura un objeto Syquex, se usa una referencia débil. Al invocar el callback, se intenta convertir la débil a fuerte. Si falla, el objeto ya fue destruido.

```syquex
externo funcion gtk_button_clicked(button: &Boton, callback: funcion(&Boton) -> nulo)

funcion conectar_boton(boton: Boton):
    let captura = debil(boton)  // captura débil
    gtk_button_clicked(&boton, funcion(b):
        let b = captura.obtener()
        si b != nulo:
            b.texto = "Clicado!"
    )
```

---

## 8. COMPARACIÓN CON OTROS MODELOS

| Modelo | Rendimiento | Seguridad | Productividad | Ejemplo |
|--------|-------------|-----------|---------------|---------|
| **GC (Python/Java)** | Bajo | Bajo (fugas, pausas) | Alto | Python |
| **RC (Swift/Objective‑C)** | Medio | Medio (ciclos) | Alto | Swift |
| **Ownership (Rust)** | Máximo | Máximo | Bajo | Rust |
| **Manual (C/C++)** | Máximo | Bajo | Bajo | C |
| **Syquex (Arenas+RC+Alcance)** | Máximo | Máximo | Alto | Syquex |

---

## 9. PRUEBAS OBLIGATORIAS PARA ESTA ETAPA

| Test | Comando | Criterio |
|------|---------|----------|
| Arena por ámbito | `pytest tests/syquex/test_arena_scope.py -v` | 100% pass, 0 fugas |
| `rc<T>` no atómico | `pytest tests/syquex/test_rc.py -v` | 0 fugas, 0 condiciones de carrera |
| `arc<T>` atómico | `pytest tests/syquex/test_arc.py -v` | 0 fugas, 0 condiciones de carrera |
| Referencias débiles | `pytest tests/syquex/test_weak.py -v` | Ciclos detectados y prevenidos |
| Análisis de alcance | `pytest tests/syquex/test_scope_analysis.py -v` | 0 falsos positivos en liberación |
| Cleanup Blocks | `pytest tests/syquex/test_cleanup_blocks.py -v` | 0 fugas en salidas tempranas |
| Arenas de componente | `pytest tests/syquex/test_component_arena.py -v` | Liberación en masa correcta |
| FFI Marshaling | `pytest tests/syquex/test_ffi_marshaling.py -v` | 0 fugas, 0 copias innecesarias |

---

## 10. SIGUIENTES PASOS

Con el modelo de memoria de Syquex definido, el siguiente manual (Manual 5) se centrará en la **Concurrencia y Comunicación** en el ecosistema (fibras, canales, sincronización, concurrencia distribuida).

---

*Este manual proporciona la especificación completa del modelo de memoria de Syquex, incluyendo arenas, conteo de referencias, análisis de alcance, Cleanup Blocks y FFI Marshaling. La implementación debe seguir fielmente estos lineamientos para garantizar la seguridad y el rendimiento.*

**Fin del Manual 4**