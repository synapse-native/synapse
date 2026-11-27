# Tutorial: Calculadora Científica en Syquex

Este tutorial paso a paso te guiará para construir una calculadora científica completa en Syquex. Aprenderás a aplicar variables, funciones, control de flujo y manejo de entrada/salida en un proyecto práctico.

Al finalizar, tendrás una calculadora funcional que demuestra los conceptos fundamentales de Syquex.

<!-- cumple Manual 3 §3-7 -->

## 1. Diseño de la Calculadora

Nuestra calculadora científica tendrá las siguientes características:

- **Operaciones básicas:** suma, resta, multiplicación, división
- **Operaciones científicas:** seno, coseno, tangente, logaritmo, potencia
- **Interfaz de línea de comandos** simple
- **Manejo de errores** con tipos `Resultado`

## 2. Configuración del Proyecto

```text
calculadora/
├── main.syq
├── lib/
│   ├── operaciones.syq
│   └── parser.syq
└── README.md
```

```bash
mkdir calculadora
cd calculadora
mkdir lib
touch main.syq lib/operaciones.syq lib/parser.syq
```

## 3. Implementación - Operaciones Básicas

### `lib/operaciones.syq`

```syquex
#lang: es

importar lib.io

// Operaciones básicas
funcion sumar(a: decimal, b: decimal) -> decimal:
    retornar a + b

funcion restar(a: decimal, b: decimal) -> decimal:
    retornar a - b

funcion multiplicar(a: decimal, b: decimal) -> decimal:
    retornar a * b

funcion dividir(a: decimal, b: decimal) -> Resultado<decimal, texto>:
    si b == 0.0:
        retornar err("Error: División por cero")
    retornar ok(a / b)
```

## 4. Implementación - Parser de Expresiones

### `lib/parser.syq`

```syquex
#lang: es

importar lib.io

// Token types
tipo Token = Numero(decimal) | Operador(texto) | Parentesis(texto)

// Parsear una expresión simple
funcion tokenizar(expresion: texto) -> Lista<Token>:
    let tokens = Lista<Token>()
    let buffer = ""
    
    para i = 0 mientras i < expresion.len():
        let char = expresion.obtener(i)
        
        si char.es_digito() o char == '.':
            buffer = buffer + char
        sino si char == '+' o char == '-' o char == '*' o char == '/':
            si buffer.len() > 0:
                tokens.agregar(Numero(buffer.decimal()))
                buffer = ""
            tokens.agregar(Operador(char.texto()))
        sino si char == '(' o char == ')':
            si buffer.len() > 0:
                tokens.agregar(Numero(buffer.decimal()))
                buffer = ""
            tokens.agregar(Parentesis(char.texto()))
    
    si buffer.len() > 0:
        tokens.agregar(Numero(buffer.decimal()))
    
    retornar tokens

// Evaluar expresión con dos operandos
funcion evaluar_operacion(a: decimal, op: texto, b: decimal) -> Resultado<decimal, texto>:
    coincidir op:
        caso "+": retornar ok(sumar(a, b))
        caso "-": retornar ok(restar(a, b))
        caso "*": retornar ok(multiplicar(a, b))
        caso "/": retornar dividir(a, b)
        caso _: retornar err("Operador desconocido: " + op)
```

## 5. Programa Principal

### `main.syq`

```syquex
#lang: es

importar lib.io
importar lib.operaciones
importar lib.parser

funcion mostrar_menu():
    io.escribir_linea("\n=== Calculadora Científica ===")
    io.escribir_linea("Operaciones disponibles:")
    io.escribir_linea("  sumar a b")
    io.escribir_linea("  restar a b")
    io.escribir_linea("  multiplicar a b")
    io.escribir_linea("  dividir a b")
    io.escribir_linea("  sin/cos/tan a (radianes)")
    io.escribir_linea("  log a")
    io.escribir_linea("  pow a b")
    io.escribir_linea("  expr <expresión>")
    io.escribir_linea("  salir")

funcion procesar_comando(comando: texto) -> booleano:
    let partes = comando.dividir(" ")
    si partes.len() == 0:
        retornar verdadero
    
    let op = partes[0]
    
    // Comandos de salida
    si op == "salir" o op == "exit":
        retornar falso
    
    // Comandos aritméticos
    si op == "sumar" y partes.len() == 3:
        let a = decimal(partes[1])
        let b = decimal(partes[2])
        io.escribir_linea(operaciones.sumar(a, b).texto())
        retornar verdadero
    
    si op == "restar" y partes.len() == 3:
        let a = decimal(partes[1])
        let b = decimal(partes[2])
        io.escribir_linea(operaciones.restar(a, b).texto())
        retornar verdadero
    
    si op == "dividir" y partes.len() == 3:
        let a = decimal(partes[1])
        let b = decimal(partes[2])
        let resultado = operaciones.dividir(a, b)
        coincidir resultado:
            caso ok(valor): io.escribir_linea(valor.texto())
            caso err(e): io.escribir_linea(e)
        retornar verdadero
    
    io.escribir_linea("Comando no reconocido")
    retornar verdadero

funcion principal():
    mostrar_menu()
    
    mientras verdadero:
        io.escribir("\ncalc> ")
        let entrada = io.leer_linea()
        
        si entrada == "":
            continuar
        
        si !procesar_comando(entrada):
            romper

    io.escribir_linea("¡Hasta luego!")
```

## 6. Compilar y Ejecutar

```bash
# Compilar
python main.py main.syq -o calculadora.exe

# Ejecutar
./calculadora.exe
```

### Sesión de Ejemplo

```
=== Calculadora Científica ===
Operaciones disponibles:
  sumar a b
  restar a b
  multiplicar a b
  dividir a b
  ...

calc> sumar 5 3
8

calc> dividir 10 0
Error: División por cero

calc> salir
¡Hasta luego!
```

## 7. Mejoras Posibles

1. **Agregar más funciones científicas:**

   ```syquex
   funcion seno(x: decimal) -> decimal:
       retornar matematica.seno(x)
   
   funcion coseno(x: decimal) -> decimal:
       retornar matematica.coseno(x)
   
   funcion potencia(base: decimal, exponente: decimal) -> decimal:
       retornar matematica.potencia(base, exponente)
   
   funcion logaritmo(x: decimal) -> Resultado<decimal, texto>:
       si x <= 0.0:
           retornar err("Logaritmo de número no positivo")
       retornar ok(matematica.logaritmo_natural(x))
   ```

2. **Historial de operaciones:**

   ```syquex
   estructura Historial:
       operaciones: Lista<Operacion>
       
       metodo agregar(op: Operacion):
           self.operaciones.agregar(op)
       
       metodo mostrar():
           para op en self.operaciones:
               io.escribir_linea(op.a_texto())
   ```

3. **Modo interactivo con REPL:**

   ```syquex
   mientras verdadero:
       io.escribir("calc> ")
       let entrada = io.leer_linea()
       // Procesar y mantener estado
   ```

## 8. Conceptos Aprendidos

En este tutorial aprendiste:

- **Estructuras básicas** con campos y métodos
- **Funciones puras** sin efectos secundarios
- **Manejo de errores** con `Resultado<T, E>`
- **Pattern matching** con `coincidir`
- **I/O básico** con `lib.io`
- **Importación de módulos** con `importar`

## Referencias

- **Manual 3 §3**: Gramática formal EBNF de Syquex
- **Manual 3 §5**: Sistema de tipos
- **Manual 3 §7**: Manejo de errores
- **Manual 3 §12**: Biblioteca estándar (`lib.io`)

// cumple Manual 3 §6
