# Depuración en Synapse

La depuración es esencial para encontrar y corregir errores. Synapse
proporciona herramientas integradas y patrones para facilitar el proceso.

## Logging con `log()`

La función `log()` imprime mensajes de debug a stderr:

```synapse
// Mensaje simple
log("Iniciando programa")

// Interpolación de variables
let nombre = "Synapse"
let version = 1.0
log("Versión {nombre} {version}")

// Diferentes niveles de log
log("DEBUG: valor de x = {x}")
log("INFO: procesando archivo")
log("WARN: memoria casi llena")
log("ERROR: conexión fallida")
```

## Traces

Los traces permiten seguir la ejecución del programa:

```synapse
use std.debug

fn funcion_a() {
    debug::trace!("inicio funcion_a")
    debug::trace!("argumento recibido: {x}")

    let resultado = funcion_b(x)
    debug::trace!("funcion_b retornó: {resultado}")

    return resultado
}

fn funcion_b(valor: entero) -> entero {
    debug::trace!("inicio funcion_b con {valor}")
    // ...
    debug::trace!("fin funcion_b")
    return valor * 2
}

// Trace con contexto
fn procesar_lista(lista: Lista<entero>) {
    debug::trace!("procesar_lista: {lista.longitud()} elementos")
    for item in lista {
        debug::trace!("  procesando: {item}")
    }
}
```

## Assertions

Use assertions para verificar invariantes:

```synapse
fn dividir(a: flotante, b: flotante) -> flotante {
    assert que (b != 0.0), "División por cero"
    return a / b
}

fn accederindice(lista: Lista<entero>, indice: entero) -> entero {
    assert que (indice >= 0), "Índice negativo: {indice}"
    assert que (indice < lista.longitud()),
        "Índice fuera de rango: {indice} >= {lista.longitud()}"
    return lista[indice]
}

// Assertion con mensaje detallado
fn procesar(dato: Dato) {
    assert que (dato.valido),
        "Dato inválido: {dato.debug()}"
}
```

## Depurador

Synapse genera información de debug para depuradores externos:

```synapse
// Punto de interrupción programático
fn funcion_problematica() {
    debug::punto_de_interrupcion()
    // El depurador se detiene aquí
}

// Inspeccionar variables
fn examinar() {
    let x = 42
    debug::inspeccionar(x) // Muestra valor y tipo
    debug::inspeccionar(&x) // Muestra dirección de memoria
}

// Backtrace
fn funcion_recursiva(n: entero) {
    if n == 0 {
        debug::backtrace() // Imprime pila de llamadas
        return
    }
    funcion_recursiva(n - 1)
}
```

## Errores Comunes y Debug

### Errores de memoria

```synapse
// Problema: usar memoria liberada
let ptr = malloc(100)
free(ptr)
// ptr.escribir(0, 42) // ERROR: memoria liberada

// Solución: marcar como nulo después de free
let ptr = malloc(100)
free(ptr)
ptr = nulo
```

### Race conditions

```synapse
// Problema: acceso concurrente sin sincronizar
let contador = 0

para _ in 0..10 {
    lanzar {
        for _ in 0..1000 {
            contador += 1 // RACE CONDITION
        }
    }
}

// Solución: usar Mutex
let contador = Mutex::nuevo(0)

para _ in 0..10 {
    lanzar {
        for _ in 0..1000 {
            let mut val = contador.bloquear()
            *val += 1
        }
    }
}
```

### Deadlocks

```synapse
// Problema: deadlock por orden de locks
let mutex_a = Mutex::nuevo(0)
let mutex_b = Mutex::nuevo(0)

// Fibras 1: lock A, luego B
lanzar {
    let _a = mutex_a.bloquear()
    let _b = mutex_b.bloquear() // ESPERA
}

// Fibras 2: lock B, luego A
lanzar {
    let _b = mutex_b.bloquear()
    let _a = mutex_a.bloquear() // ESPERA para siempre
}

// Solución: siempre lock en mismo orden
```

## Logging Estructurado

```synapse
use std.log

fn ejemplo_logging() {
    log::debug!("Valor: {}", x)
    log::info!("Procesando {}", nombre)
    log::warn!("Memoria baja: {}%", uso)
    log::error!("Fallo: {}", error)
}

// Configurar nivel de log
fn main() {
    log::configurar(log::Nivel::Debug)
    // ...
}
```

## Pruebas Unitarias

```synapse
// En archivo tests/test_matematica.sin
importar matematica

fn test_sumar() {
    assert que (matematica::sumar(2, 3) == 5)
    assert que (matematica::sumar(-1, 1) == 0)
}

fn test_dividir() {
    assert que (matematica::dividir(10, 2) == 5.0)
    // Verificar error en división por cero
    assert que (matematica::dividir(10, 0) es error)
}

// Ejecutar tests
// synapse test tests/
```
