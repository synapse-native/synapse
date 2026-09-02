# Herencia en Syquex

Este capítulo cubre la herencia de clases en Syquex. Aprenderás a crear jerarquías de clases, sobrescribir métodos y utilizar la herencia de forma efectiva.

La herencia permite reutilizar y extender comportamiento de manera organizada.

<!-- cumple Manual 3 §6 -->

## 1. Herencia Simple

En Syquex, la herencia se logra mediante **composición y traits** en lugar de herencia clásica:

```syquex
// Estructura base
estructura Animal:
    nombre: texto

    crear(nombre: texto):
        self.nombre = nombre

    metodo hablar() -> texto:
        retornar self.nombre + " hace un sonido"

// "Herencia" mediante composición
estructura Perro:
    animal: Animal
    raza: texto

    crear(nombre: texto, raza: texto):
        self.animal = Animal(nombre)
        self.raza = raza

    // Sobrescribir método
    metodo hablar() -> texto:
        retornar self.animal.nombre + " ladra"

    // Método adicional
    metodo mover_cola():
        io.escribir_linea("Cola moviéndose")
```

## 2. Traits (Interfaces)

Los traits definen comportamientos compartibles:

```syquex
trait Volador:
    metodo volar() -> texto

trait Nadador:
    metodo nadar() -> texto

estructura Pato:
    nombre: texto

    // Implementar múltiples traits
    implementa Volador:
        metodo volar() -> texto:
            retornar self.nombre + " vuela"

    implementa Nadador:
        metodo nadar() -> texto:
            retornar self.nombre + " nada"
```

## 3. Sobrescritura de Métodos

```syquex
estructura Vehiculo:
    marca: texto
    crear(marca: texto):
        self.marca = marca
    metodo mover() -> texto:
        retornar "El vehículo se mueve"

estructura Auto:
    vehiculo: Vehiculo
    puertas: entero

    crear(marca: texto, puertas: entero):
        self.vehiculo = Vehiculo(marca)
        self.puertas = puertas

    metodo mover() -> texto:
        retornar self.vehiculo.marca + " avanza con " + self.puertas.texto() + " puertas"

    metodo mover() -> texto:
        // Llamar al método "padre" (manualmente)
        io.escribir_linea(self.vehiculo.mover())
        retornar self.vehiculo.marca + " acelera"
```

## 4. Herencia Múltiple (Por Traits)

```syquex
trait Serializable:
    metodo a_json() -> texto

trait Deserializable:
    metodo desde_json(datos: texto) -> Self

estructura Producto:
    nombre: texto
    precio: decimal

    implementa Serializable:
        metodo a_json() -> texto:
            retornar '{"nombre": "' + self.nombre + '", "precio": ' + self.precio.texto() + '}'

    implementa Deserializable:
        metodo desde_json(datos: texto) -> Producto:
            // Parseo simplificado
            let partes = datos.dividir(",")
            retornar Producto("producto", 0.0)
```

## 5. Polimorfismo con Traits

```syquex
funcion hacer_volador(objeto: Volador):
    io.escribir_linea(objeto.volar())

let pato = Pato("PatoLucas")
let avion = Avion("Boeing747")

hacer_volador(pato)    // "PatoLucas vuela"
hacer_volador(avion)   // "Boeing747 despega"
```

## 6. Métodos Auxiliares

```syquex
estructura Figura:
    metodo area() -> decimal:
        retornar 0.0  // Método virtual (se sobreescribe)

estructura Cuadrado:
    lado: decimal
    crear(lado: decimal):
        self.lado = lado
    metodo area() -> decimal:
        retornar self.lado * self.lado

estructura Circulo:
    radio: decimal
    crear(radio: decimal):
        self.radio = radio
    metodo area() -> decimal:
        retornar 3.14159 * self.radio * self.radio
```

## 7. Buenas Prácticas

### Prefiere Composición sobre Herencia

```syquex
// ✅ Mejor: composición
estructura Motor:
    potencia: entero

estructura Auto:
    motor: Motor
    marca: texto

// ❌ Evita: herencia profunda
// Auto -> Vehiculo -> Transporte -> Maquinaria
```

### Usa Traits para Comportamientos Compartidos

```syquex
trait Loggeable:
    metodo log(mensaje: texto):
        io.escribir_linea("[LOG] " + mensaje)

estructura ServicioWeb:
    implementa Loggeable
    // ...
```

## Ejemplo Completo

```syquex
#lang: es
importar lib.io

trait Hablar:
    metodo hablar() -> texto

estructura Gato:
    nombre: texto

    crear(nombre: texto):
        self.nombre = nombre

    implementa Hablar:
        metodo hablar() -> texto:
            retornar self.nombre + " maúlla"

estructura Perro:
    nombre: texto

    crear(nombre: texto):
        self.nombre = nombre

    implementa Hablar:
        metodo hablar() -> texto:
            retornar self.nombre + " ladra"

funcion principal():
    let gato = Gato("Misu")
    let perro = Perro("Rex")
    
    io.escribir_linea(gato.hablar())
    io.escribir_linea(perro.hablar())

// Referencias
- Manual 3 §6: Estructuras, métodos y constructores
- Manual 3 §11: Integración con AST canónico
