# Conceptos Básicos

## Variables

```synapse
x: entero = 42
y: decimal = 3.14
nombre: texto = "synapse"
activo: logico = verdadero
```

## Funciones

```synapse
funcion suma(a: entero, b: entero) -> entero:
    retornar a + b

funcion saludar(nombre: texto) -> nulo:
    escribir("hola ", nombre)
```

## Tipos

| Tipo | Descripción | Tamaño |
|---|---|---|
| `entero` | Entero con signo (i64) | 8 bytes |
| `decimal` | Punto flotante (f64) | 8 bytes |
| `logico` | Booleano (`verdadero`/`falso`) | 1 byte |
| `texto` | Cadena inmutable con prefijo de longitud | 16 bytes |
| `nulo` | Tipo unidad, sin valor | 0 bytes |

## Estructuras

```synapse
estructura Punto:
    x: entero
    y: entero

p = Punto()
p.x = 10
p.y = 20
```

## Control de flujo

```synapse
si x > 0:
    escribir("positivo")
sino:
    escribir("negativo o cero")

mientras x > 0:
    x = x - 1
```
