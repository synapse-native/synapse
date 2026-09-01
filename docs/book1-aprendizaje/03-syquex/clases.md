# Clases en Syquex

Este capítulo explora el sistema de clases en Syquex, incluyendo definición, constructores, métodos y propiedades. Aprenderás a modelar datos y comportamiento de forma orientada a objetos.

Las clases en Syquex combinan la simplicidad con features modernas como propiedades computadas y destructuring.

<!-- cumple Manual 3 §6 -->

## 1. Definición de Estructuras

En Syquex, el OOP se implementa mediante **estructuras** con métodos y constructores:

```syquex
estructura Persona:
    nombre: texto
    edad: entero
    activo: booleano = verdadero   // Valor por defecto

    // Constructor
    crear(nombre: texto, edad: entero):
        self.nombre = nombre
        self.edad = edad

    // Método
    metodo saludar():
        io.escribir_linea("Hola, soy " + self.nombre)

    metodo cumpleaños():
        self.edad = self.edad + 1

    // Método con retorno
    metodo es_adulto() -> booleano:
        retornar self.edad >= 18
```

## 2. Creación e Instancia

```syquex
// Usar el constructor
let ana = Persona("Ana", 28)
ana.saludar()  // "Hola, soy Ana"
ana.cumpleaños()
io.escribir_linea(ana.es_adulto().texto())
```

### Constructores Alternativos

```syquex
// Función que actúa como constructor alternativo
funcion crear_persona_desde_csv(linea: texto) -> Persona:
    let partes = linea.dividir(",")
    retornar Persona(partes[0], entero(partes[1]))
```

## 3. Métodos y Propiedades

### Métodos Públicos y Privados

```syquex
estructura Banco:
    saldo_privado: decimal  // Campo "privado" (convención)
    
    metodo depositar(cantidad: decimal):
        self.saldo_privado = self.saldo_privado + cantidad

    metodo _calcular_interes():  // Método "privado" (convención)
        retornar self.saldo_privado * 0.05
```

### Propiedades Computadas

```syquex
estructura Rectangulo:
    ancho: entero
    alto: entero

    metodo area() -> entero:
        retornar self.ancho * self.alto
```

## 4. Métodos Especiales (Dunder Methods)

Syquex soporta métodos especiales para operaciones comunes:

```syquex
estructura Vector2D:
    x: decimal
    y: decimal
    
    metodo __add__(otro: Vector2D) -> Vector2D:
        retornar Vector2D(self.x + otro.x, self.y + otro.y)
    
    metodo __str__() -> texto:
        retornar "(" + self.x.texto() + ", " + self.y.texto() + ")"

// Uso
let v1 = Vector2D(3.0, 4.0)
let v2 = Vector2D(1.0, 2.0)
let resultado = v1 + v2  // Usa __add__
io.escribir_linea(resultado)  // "(4.0, 6.0)"
```

## 5. Visibilidad y Encapsulamiento

```syquex
estructura CuentaBancaria:
    numero: texto           // Público
    _saldo: decimal         // "Privado" (convención _)
    __pin: entero           // "Muy privado" (convención __)

    crear(numero: texto, saldo_inicial: decimal, pin: entero):
        self.numero = numero
        self._saldo = saldo_inicial
        self.__pin = pin

    metodo depositar(monto: decimal, pin: entero) -> Resultado<nulo, texto>:
        si pin != self.__pin:
            retornar err("PIN incorrecto")
        self._saldo = self._saldo + monto
        retornar ok()

    metodo obtener_saldo() -> decimal:
        retornar self._saldo
```

## 6. Destructores

```syquex
estructura Archivo:
    descriptor: entero

    crear(ruta: texto):
        self.descriptor = abrir_archivo(ruta)

    metodo destruir():
        // Llamado automáticamente al salir del scope
        cerrar_archivo(self.descriptor)
```

## 7. Comparación y Hash

```syquex
estructura Usuario:
    id: entero
    nombre: texto

    metodo __eq__(otro: Usuario) -> booleano:
        retornar self.id == otro.id

    metodo __hash__() -> entero:
        retornar self.id
```

## Ejemplo Completo

```syquex
#lang: es
importar lib.io

estructura Producto:
    nombre: texto
    precio: decimal
    stock: entero = 0

    crear(nombre: texto, precio: decimal, stock: entero = 0):
        self.nombre = nombre
        self.precio = precio
        self.stock = stock

    metodo disponible() -> booleano:
        retornar self.stock > 0

    metodo aplicar_descuento(porcentaje: decimal) -> decimal:
        retornar self.precio * (1.0 - porcentaje / 100.0)

funcion principal():
    let laptop = Producto("Laptop", 1200.00, 5)
    let mouse = Producto("Mouse", 25.00)
    
    io.escribir_linea(laptop.nombre + ": $" + laptop.precio.texto())
    io.escribir_linea("Stock disponible: " + laptop.disponible().texto())
    io.escribir_linea("Con 10% dto: $" + laptop.aplicar_descuento(10).texto())

// Referencias
- Manual 3 §6: Estructuras, métodos y constructores
- Manual 3 §9: FFI y externo
- Manual 2 §4.3: Tipos compuestos
