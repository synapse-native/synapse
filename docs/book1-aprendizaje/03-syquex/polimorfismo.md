# Polimorfismo en Syquex

Este capítulo explora el polimorfismo en Syquex, permitiendo que objetos de diferentes clases respondan a la misma interfaz. Aprenderás sobre interfaces, traits y dispatch dinámico.

El polimorfismo es fundamental para escribir código flexible y reutilizable.

<!-- cumple Manual 3 §6 -->

## 1. Polimorfismo con Traits

En Syquex, el polimorfismo se logra mediante **traits** (similares a interfaces en otros lenguajes):

```syquex
// Definir un trait
trait Dibujable:
    metodo dibujar() -> texto

// Implementar el trait en diferentes estructuras
estructura Circulo:
    radio: decimal
    implementa Dibujable:
        metodo dibujar() -> texto:
            retornar "○"

estructura Cuadrado:
    lado: decimal
    implementa Dibujable:
        metodo dibujar() -> texto:
            retornar "□"

estructura Triangulo:
    base: decimal
    altura: decimal
    implementa Dibujable:
        metodo dibujar() -> texto:
            retornar "△"

// Función polimórfica
funcion renderizar(objeto: Dibujable):
    io.escribir_linea("Dibujando: " + objeto.dibujar())

// Uso
funcion principal():
    renderizar(Circulo(5.0))   // "Dibujando: ○"
    renderizar(Cuadrado(3.0))  // "Dibujando: □"
    renderizar(Triangulo(4.0, 3.0))  // "Dibujando: △"
```

## 2. Dispatch Dinámico

Syquex utiliza dispatch dinámico para traits:

```syquex
trait Sonido:
    metodo hacer_sonido() -> texto

estructura Perro:
    implementa Sonido:
        metodo hacer_sonido() -> texto:
            retornar "¡Guau!"

estructura Gato:
    implementa Sonido:
        metodo hacer_sonido() -> texto:
            retornar "¡Miau!"

funcion emitir_sonido(animal: Sonido):
    // Dispatch dinámico: se llama al método correcto en runtime
    io.escribir_linea(animal.hacer_sonido())
```

## 3. Traits con Parámetros de Tipo (Generics)

```syquex
trait Almacenamiento<T>:
    metodo guardar(valor: T) -> entero
    metodo recuperar(id: entero) -> Opcion<T>

estructura AlmacenMemoria<T>:
    implementa Almacenamiento<T>:
        _datos: Mapa<entero, T>
        _next_id: entero = 0

        metodo guardar(valor: T) -> entero:
            self._next_id = self._next_id + 1
            self._datos[self._next_id] = valor
            retornar self._next_id

        metodo recuperar(id: entero) -> Opcion<T>:
            retornar self._datos.obtener(id)
```

## 4. Coerción de Tipos

```syquex
// Syquex soporta coerción implícita para tipos compatibles
let entero_val = 42
let decimal_val: decimal = entero_val  // Coerción automática

// Con conversión explícita
let texto_val = entero_val.texto()     // "42"
let entero_nuevamente = texto_val.entero()  // 42
```

## 5. Pattern Matching Polimórfico

```syquex
tipo Animal = Perro | Gato | Pajaro

funcion sonido(animal: Animal) -> texto:
    coincidir animal:
        caso Perro(nombre): "Guau"
        caso Gato(nombre): "Miau"
        caso Pajaro(canto): "PIO"
```

## 6. Traits con Métodos por Defecto

```syquex
trait Utilidad:
    metodo imprimir() -> texto:
        retornar "Valor por defecto"

    metodo describir() -> texto:
        retornar "Descripción: " + self.imprimir()

estructura MiClase:
    valor: texto
    implementa Utilidad:
        // Solo implementa imprimir, describir usa el default
        metodo imprimir() -> texto:
            retornar self.valor
```

## 7. Polimorfismo con Funciones de Orden Superior

```syquex
funcion transformar<T, U>(lista: Lista<T>, fn: funcion(T) -> U) -> Lista<U>:
    retornar lista.mapear(fn)

// La misma función trabaja con cualquier tipo
let numeros = [1, 2, 3]
let texto_list = transformar(numeros, lambda n: n.texto())

let palabras = ["hola", "mundo"]
let mayusculas = transformar(palabras, lambda s: s.mayusculas())
```

## 8. Límites de Traits (Trait Bounds)

```syquex
funcion procesar<T: Dibujable + Serializable>(objeto: T):
    io.escribir_linea(objeto.dibujar())
    archivo.escribir(objeto.a_json())
```

## Ejemplo Completo

```syquex
#lang: es
importar lib.io

trait Calculable:
    metodo area() -> decimal
    metodo perimetro() -> decimal

estructura Rectangulo:
    ancho: decimal
    alto: decimal

    implementa Calculable:
        metodo area() -> decimal:
            retornar self.ancho * self.alto
        metodo perimetro() -> decimal:
            retornar 2 * (self.ancho + self.alto)

estructura Circulo:
    radio: decimal

    implementa Calculable:
        metodo area() -> decimal:
            retornar 3.14159 * self.radio * self.radio
        metodo perimetro() -> decimal:
            retornar 2 * 3.14159 * self.radio

funcion mostrar_info(figura: Calculable):
    io.escribir_linea("Área: " + figura.area().texto())
    io.escribir_linea("Perímetro: " + figura.perimetro().texto())

funcion principal():
    mostrar_info(Rectangulo(5.0, 3.0))
    mostrar_info(Circulo(4.0))

// Referencias
- Manual 3 §6: Estructuras, métodos y constructores
- Manual 3 §5: Sistema de tipos de Syquex
- Manual 3 §2: Filosofía y diferencias con Synapse
