# Optimización en Synapse

Synapse proporciona herramientas para escribir código de alto rendimiento.
Este cubre técnicas desdeInlining hasta SIMD y allocators personalizados.

## Inlining

El compilador puede insertar el cuerpo de funciones pequeñas directamente
donde se llaman, eliminando el overhead de la llamada:

```synapse
// Forzar inline con atributo
#[inline]
fn cuadrado(x: entero) -> entero {
    x * x
}

// Nunca inline (para debugging)
#[inline(nunca)]
fn funcion_grande() {
    // ...
}

// Inline agresivo (solo si es muy pequeño)
#[inline(sempre)]
fn sumar(a: entero, b: entero) -> entero {
    a + b
}

// El compilador decide automáticamente
fn ejemplo() {
    let x = cuadrado(5) // Se inlinea automáticamente
}
```

## SIMD (Single Instruction, Multiple Data)

Procese múltiples valores en paralelo con instrucciones del procesador:

```synapse
// Usar tipos SIMD explícitos
let a: Vec4 = [1.0, 2.0, 3.0, 4.0]
let b: Vec4 = [5.0, 6.0, 7.0, 8.0]

// Operaciones vectoriales
let suma = a + b      // [6.0, 8.0, 10.0, 12.0]
let producto = a * b  // [5.0, 12.0, 21.0, 32.0]
let dot = a.punto(b)  // 70.0

// Funciones SIMD personalizadas
#[simd]
fn sumar_vectores(a: [f32; 4], b: [f32; 4]) -> [f32; 4] {
    [a.0+b.0, a.1+b.1, a.2+b.2, a.3+b.3]
}

// Loop con auto-vectorización
fn procesar_arreglo(datos: Lista<f32>) {
    let resultado = Lista::con_capacidad(datos.longitud())

    // El compilador vectoriza esto automáticamente
    for valor in datos {
        resultado.agregar(valor * 2.0 + 1.0)
    }
}
```

## Pool Allocator

Reutilice memoria pre-asignada para evitar allocations costosas:

```synapse
// Pool allocator para objetos del mismo tamaño
let pool = PoolAllocator::nuevo(
    tamano_objeto: 64,
    capacidad: 1024
)

// Asignar del pool
let obj1 = pool.asignar()
let obj2 = pool.asignar()

// Liberar al pool
pool.liberar(obj1)
pool.liberar(obj2)

// Pool genérico
struct Particula {
    x: f32, y: f32,
    vx: f32, vy: f32,
    vida: u32
}

let particulas = Pool::<Particula>::nuevo(10000)

fn actualizar_particulas() {
    for i in 0..10000 {
        let p = particulas[i]
        p.x += p.vx
        p.y += p.vy
        p.vida -= 1
    }
}
```

## Arenas Allocator

Asigne memoria en bloques y libere todo de una vez:

```synapse
// Crear arena con 1MB
let arena = Arena::nuevo(1024 * 1024)

// Asignar múltiples objetos
let datos1 = arena.allocar(100)
let datos2 = arena.allocar(200)
let datos3 = arena.allocar(300)

// Todo se libera de golpe
arena.liberar_todo()
// datos1, datos2, datos3 ahora son inválidos

// Arena temporal para scope
fn procesar() {
    let tmp = Arena::temporal()

    let buffer = tmp.allocar(4096)
    let parseado = tmp.parsear(buffer)

    // Usar parseado
    usar_datos(parseado)

    // Arena se libera automáticamente al salir del scope
}
```

## Medición de Rendimiento

```synapse
use std.tiempo

fn medir() {
    let inicio = tiempo.ahora()

    // Código a medir
    let suma = 0
    for i in 0..1_000_000 {
        suma += i
    }

    let fin = tiempo.ahora()
    let duracion = fin - inicio
    log("Duración: {duracion.milisegundos()}ms")
}

// Benchmark
fn benchmark(nombre: str, fn_ejecutar: fn()) {
    let iteraciones = 100
    let tiempos = Lista::nueva()

    for _ in 0..iteraciones {
        let inicio = tiempo.ahora()
        fn_ejecutar()
        let fin = tiempo.ahora()
        tiempos.agregar(fin - inicio)
    }

    tiempos.ordenar()
    let mediana = tiempos[iteraciones / 2]
    let promedio = tiempos.reducir(0, |a, b| a + b) / iteraciones

    log("{nombre}: mediana={mediana.ns()}ns promedio={promedio.ns()}ns")
}
```

## Consejos de Optimización

```synapse
// 1. Evitar allocations en hot paths
fn mal_ejemplo() {
    for _ in 0..10000 {
        let temp = Lista::nueva()  // Allocation cada iteración
        temp.agregar(42)
    }
}

fn bueno() {
    let temp = Lista::con_capacidad(1)
    for _ in 0..10000 {
        temp.limpiar()  // Reutilizar
        temp.agregar(42)
    }
}

// 2. Usar enteros en vez de flotantes cuando sea posible
fn calcular_posiciones(posiciones: [entero; 1000]) {
    // Más rápido que flotantes para índices
    for i in 0..1000 {
        let nueva = posiciones[i] * 2
    }
}

// 3. Prefier arreglos a listas para tamaños conocidos
fn procesar像素() {
    let buffer: [u8; 640 * 480 * 4] = [0; 640 * 480 * 4]
    // Stack allocation, sin overhead
}

// 4. Use bits cuando pueda
let permisos: u8 = 0b1010_0110
let tiene_escritura = (permisos & 0b0000_0010) != 0

// 5. Evite divisiones costosas
let x = 100
let dividido = x >> 2  // Equivalente a x / 4, más rápido
```

## Perf Profiling

```synapse
// Marcar funciones para profiling
#[perf_counter("cache_misses")]
fn acceso_aleatorio(datos: &[u8]) {
    // ...
}

#[perf_counter("instructions")]
fn compute密集() {
    // ...
}

// Habilitar profiling
fn main() {
    perfilador::iniciar()
    // ... ejecutar código ...
    perfilador::detener()
    perfilador::reporte()
}
```
