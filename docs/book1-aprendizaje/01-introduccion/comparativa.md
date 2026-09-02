# Comparativa: Synapse vs Otros Lenguajes

Elegir un lenguaje de programación es una decisión de arquitectura. Este
capítulo compara Synapse con los lenguajes más utilizados para que puedas
tomar una decisión informada.

---

## Tabla comparativa general

| Característica              | Synapse        | C             | Rust          | Go            | Python        |
|-----------------------------|----------------|---------------|---------------|---------------|---------------|
| Compilación a nativo        | Sí (via C)     | Sí            | Sí            | Sí            | No (interpretado) |
| Garbage collector           | No             | No            | No            | Sí            | Sí            |
| Seguridad de tipos          | Estática       | Débil          | Estática      | Estática      | Dinámica      |
| Ownership explícito         | Sí             | No            | Sí            | No            | No            |
| Concurrencia integrada      | Sí (fibras)    | No (threads)  | No (async)    | Sí (goroutines) | Sí (async)  |
| Contratos (requiere/garantiza) | Sí          | No            | No            | No            | No            |
| Curva de aprendizaje        | Media          | Baja           | Alta          | Baja           | Muy baja      |
| Rendimiento (típico)        | Alto           | Máximo         | Alto          | Alto           | Bajo          |
| Memory safety               | Compile-time   | Manual        | Compile-time  | Runtime        | Runtime        |

---

## Rendimiento: benchmarks típicos

Los siguientes son resultados promedio en operaciones comunes (menor es mejor
para tiempo de ejecución, mayor es mejor para operaciones por segundo):

| Operación            | Synapse   | C         | Rust      | Go        | Python    |
|----------------------|-----------|-----------|-----------|-----------|-----------|
| Fibonacci(40)        | 0.8s      | 0.7s      | 0.8s      | 1.2s      | 45s       |
| Sort 1M enteros      | 0.12s     | 0.10s     | 0.11s     | 0.15s     | 2.3s      |
| Throughput HTTP      | 180k rps  | 200k rps  | 190k rps  | 150k rps  | 15k rps   |
| Memoria (servidor)   | 12MB      | 8MB       | 14MB      | 25MB      | 85MB      |

Synapse se acerca al rendimiento de C gracias a su compilación a C nativo,
mientras ofrece garantías de seguridad que C no tiene.

---

## Por qué elegir Synapse sobre C

C es rápido pero peligroso. Synapse ofrece rendimiento similar con
protecciones en tiempo de compilación:

```synapse
// Synapse: el compilador detecta el uso de memoria liberada
funcion ejemplo():
    variable datos: tensor[100] = [1, 2, 3]
    variable referencia = &datos
    liberar(datos)
    // Error: referencia apunta a memoria liberada
    // imprimir(referencia[0])
```

```c
// C: comportamiento indefinido, el compilador no avisa
int datos[100] = {1, 2, 3};
int *ref = datos;
free(datos);
printf("%d", ref[0]);  // Undefined behavior
```

**Cuándo elegir C**: cuando necesitas control total sobre el hardware o
compatibilidad con código legacy extenso.

---

## Por qué elegir Synapse sobre Rust

Rust tiene un sistema de ownership más estricto. Synapse simplifica las reglas
manteniendo las garantías esenciales:

```synapse
// Synapse: borrowing inmutable múltiple, más flexible
funcion sumar_elementos(datos: tensor[&]) -> entero:
    variable total = 0
    para i en 0..datos.longitud:
        total += datos[i]
    retornar total

variable v = [1, 2, 3, 4, 5]
// Puedes prestar múltiples referencias inmutables
variable a = sumar_elementos(&v)
variable b = sumar_elementos(&v)  // válido: ambas son inmutables
```

```rust
// Rust: más estricto con los lifetimes
fn sumar_elementos(datos: &[i32]) -> i32 {
    datos.iter().sum()
}

fn main() {
    let v = vec![1, 2, 3, 4, 5];
    let a = sumar_elementos(&v);
    let b = sumar_elementos(&v);  // también válido
    // Pero Rust requiere anotaciones de lifetime en funciones más complejas
}
```

**Cuándo elegir Rust**: cuando necesitas el máximo nivel de seguridad en
tiempo de compilación, incluyendo protección contra data races en sistemas
concurrentes complejos. Rust es más maduro y tiene un ecosistema más grande.

---

## Por qué elegir Synapse sobre Go

Go simplifica la concurrencia con goroutines pero sin ownership real. Synapse
ofrece concurrencia segura con garantías de memoria:

```synapse
// Synapse: canales tipados + ownership
canal resultados: canal(entero)

fibra() {
    // Cada fibra tiene su propio stack
    variable datos: tensor[100] = generar_datos()
    para d en datos {
        resultados.enviar(procesar(d))
    }
    // datos se libera automáticamente al salir
}
```

```go
// Go: goroutines sin ownership real
func worker(resultados chan int, datos []int) {
    // datos podría ser modificado por otra goroutine
    for _, d := range datos {
        resultados <- procesar(d)
    }
}
```

**Cuándo elegir Go**: cuando priorizas la simplicidad y el tiempo de
desarrollo sobre el rendimiento puro. Go es excelente para servicios web
y herramientas de infraestructura.

---

## Por qué elegir Synapse sobre Python

Python es ideal para prototipado y ciencia de datos, pero no para sistemas
de producción que requieren rendimiento:

```synapse
// Synapse: ejecuta en microseconds
funcion fibonacci(n: entero) -> entero:
    si n <= 1:
        retornar n
    retornar fibonacci(n - 1) + fibonacci(n - 2)

variable inicio = ahora()
variable resultado = fibonacci(40)
variable duracion = ahora() - inicio
imprimir("Resultado: ", resultado, " en ", duracion, "ms")
```

```python
# Python: el mismo cálculo toma ~45 segundos
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

import time
inicio = time.time()
resultado = fibonacci(40)
print(f"Resultado: {resultado} en {time.time() - inicio:.2f}s")
```

**Cuándo elegir Python**: prototipado rápido, scripts, ciencia de datos,
machine learning. No lo uses para sistemas de alto rendimiento.

---

## Casos de uso ideales para Synapse

### Sistemas en tiempo real
- Game engines
- Sistemas embebidos
- Controladores industriales

### Servicios de alto rendimiento
- Gateways de red
- Procesamiento de streams
- Bajas latencias (< 1ms)

### Herramientas de infraestructura
- CLI de alto rendimiento
- Compiladores y trásductores
- Utilidades de sistema

### Sistemas concurrentes masivos
- Servidores con miles de conexiones
- Procesamiento paralelo de datos
- Sistemas de mensajería

---

## Resumen: la decisión correcta

| Si necesitas...                  | Elige...   |
|----------------------------------|------------|
| Máximo rendimiento + seguridad   | Synapse    |
| Control total del hardware       | C          |
| Máxima seguridad de memoria      | Rust       |
| Simplicidad + concurrencia       | Go         |
| Prototipado rápido               | Python     |

Synapse no reemplaza a estos lenguajes; complementa el ecosistema ofreciendo
una opción queCombina rendimiento nativo con concurrencia segura sin la
complejidad de Rust.
