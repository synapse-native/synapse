# Programación Bare-Metal (Ring 0)

Synapse v5.1.1-industrial extiende su alcance más allá de las aplicaciones con sistema operativo. La directiva `#pragma: no_std` transforma el compilador en una herramienta de desarrollo de sistemas de bajo nivel, ideal para kernels, bootloaders, firmware embebido y entornos de tiempo real (RTOS).

## `#pragma: no_std`

Al colocar `#pragma: no_std` en la primera línea del archivo fuente, el compilador:

- Omite la inclusión de `<stdio.h>`, `<stdlib.h>`, `<string.h>`, `<pthread.h>` y `<assert.h>`.
- Desactiva las estructuras del runtime (`Canal`, `Tensor`, `CadenaSegura` con soporte de E/S).
- Compila con las banderas `-ffreestanding -fno-builtin`.
- Genera un punto de entrada `main(void)` sin argumentos, sin inicialización del pool de memoria y sin sincronización de hilos.
- No enlaza `synapse_rt.o` ni las librerías `-lpthread` / `-lws2_32`.

```synapse
#lang: es
#pragma: no_std

funcion principal() -> entero:
    retornar 0
```

El código C generado contendrá únicamente las cabeceras `<stdint.h>` y `<stddef.h>`, junto con las definiciones mínimas de `CadenaSegura` y `Tensor`.

## Ensamblador Inline (`asm`)

El compilador expone la palabra reservada `asm` para insertar instrucciones de ensamblador directamente en el código generado. Por seguridad, `asm` solo puede utilizarse dentro de un bloque `inseguro:`.

```synapse
#lang: es
#pragma: no_std

funcion principal() -> entero:
    inseguro:
        asm("nop")
    retornar 0
```

El generador traduce `asm("instruccion")` a `__asm__ volatile("instruccion")`. Cualquier uso de `asm` fuera de un bloque `inseguro:` produce el error semántico `ERR_SEM_ASM_FUERA_INSEGURO`.

## Asignador de Memoria Global

En modo `no_std`, las funciones de asignación dinámica (`malloc`/`free`/`calloc`/`_pool_malloc`/`pool_free`) son redirigidas automáticamente a dos hooks que debe implementar el desarrollador del sistema:

| Hook | Firma | Propósito |
|------|-------|-----------|
| `__syn_asignar` | `(tamano: entero) -> puntero` | Reservar un bloque de memoria |
| `__syn_liberar` | `(ptr: puntero) -> nulo` | Liberar un bloque de memoria |

El compilador declara estas funciones como `extern`; el desarrollador las define en el código Synapse y el vinculador las resuelve.

```synapse
#lang: es
#pragma: no_std

var memoria_estatica[1024] = 0
var indice: entero = 0

funcion __syn_asignar(tamano: entero) -> puntero:
    ptr = &memoria_estatica[indice]
    indice = indice + tamano
    retornar ptr

funcion __syn_liberar(ptr: puntero) -> nulo:
    retornar

funcion principal() -> entero:
    t = tensor(16, 16)
    retornar 0
```

### ¿Cuándo se invoca cada hook?

| Contexto | Llamada original | Llamada en `no_std` |
|----------|------------------|---------------------|
| Literal `tensor(f, c)` | `calloc(f * c, sizeof(float))` | `__syn_asignar(f * c * sizeof(float))` |
| Reasignación de variable `Tensor` | `free(v.datos)` | `__syn_liberar(v.datos)` |
| Destructor RAII (fin de ámbito) | `pool_free(v.datos)` | `__syn_liberar(v.datos)` |
| Operaciones tensoriales (`suma`, etc.) | `_pool_malloc(n) / pool_free(p)` | `__syn_asignar(n) / __syn_liberar(p)` |

## Consideraciones para el Desarrollador

1. **No hay E/S estándar**: Sin `#pragma: no_std`, las funciones `escribir`, `leer_linea`, `abrir`, `cerrar` y los canales no están disponibles. Para depuración temprana, utilice `asm("outb ...")` o rutinas de puerto serie definidas por el desarrollador.
2. **Memoria**: El asignador global (`__syn_asignar`/`__syn_liberar`) debe gestionar un heap estático o direcciones de memoria física. No hay llamadas al sistema (`sbrk`/`mmap`).
3. **Threading**: Las funciones `synapse_lanzar_hilo` y `synapse_esperar_hilos` no están declaradas. Para concurrencia en bare-metal, implemente su propio scheduler o utilice interrupciones.
4. **Pool de memoria**: La inicialización del pool (`pool_init`) no se ejecuta. Toda la asignación dinámica queda bajo control exclusivo de los hooks `__syn_asignar`/`__syn_liberar`.
