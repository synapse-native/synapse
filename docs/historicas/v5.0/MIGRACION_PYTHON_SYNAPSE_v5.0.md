# Guía de Migración: Python → Synapse v5.0

**Versión:** 5.0.0
**Fecha:** 26 Julio 2026
**Estado:** LIBERACIÓN

> **Nota sobre ejemplos:** Los ejemplos de código en esta guía representan la sintaxis objetivo de Synapse v5.0. La mayoría de los constructos están implementados en el compilador actual. Los ejemplos marcados con `[Spec v5.0]` corresponden a características de la especificación completa que pueden estar pendientes de implementación en el compilador bootstrap actual.

---

## 1. INTRODUCCIÓN

Esta guía proporciona una referencia exhaustiva para migrar código Python 3.10+ a Synapse. Está diseñada tanto para migración automatizada (vía `synapse migrate`) como para migración manual.

### 1.1 ¿Por qué migrar a Synapse?

| Aspecto | Python | Synapse |
|---------|--------|---------|
| **Rendimiento** | Interpretado (CPython) | Compilado a C nativo (GCC/Clang -O3) |
| **Memoria** | GC (recolector de basura) | Zero-GC (Ownership & Borrowing) |
| **Tipado** | Dinámico / opcional (type hints) | Estático estricto con inferencia |
| **Errores** | Excepciones en runtime | Tipos algebraicos (`Resultado<T,E>`, `Opcion<T>`) |
| **Concurrencia** | GIL (Global Interpreter Lock) | Canales tipados sin GIL |
| **Distribución** | Requiere intérprete Python | Binario estático autocontenido |
| **Distribución** | pip + virtualenv | Axon (gestor de paquetes inmutable) |

### 1.2 Migración Automática

```bash
# Migrar un archivo
synapse migrate usuario.py

# Migrar un directorio completo
synapse migrate src/ --output src_syn/

# Con opciones
synapse migrate app.py --output app.syn --add-contracts --optimize-simd

# Desde VS Code
# Click derecho en .py → Refactorizar → Migrar a Synapse
```

---

## 2. SINTAXIS BÁSICA

### 2.1 Variables y Tipos

**Python:**
```python
# Con type hint
nombre: str = "Ana"
edad: int = 30
altura: float = 1.75
activo: bool = True

# Sin type hint (no recomendado)
x = 42  # Error en migración estricta
```

**Synapse:**
```synapse
#lang: es

let nombre: texto = "Ana"
let edad: entero = 30
let altura: decimal = 1.75
let activo: booleano = verdadero

# Inferencia de tipos (cuando es inequívoco)
let x = 42          # x: entero inferido
let y = 3.14        # y: decimal inferido

# Mutabilidad directa
let contador: entero = 0
contador = contador + 1  # Reasignación permitida
```

### 2.2 Constantes

**Python:**
```python
PI = 3.14159
MAX_INTENTOS = 3
```

**Synapse:**
```synapse
constante PI = 3.14159
constante MAX_INTENTOS = 3
```

### 2.3 Comentarios

**Python:**
```python
# Comentario de línea
"""Docstring de función."""
```

**Synapse:**
```synapse
// Comentario de línea
/* Comentario de bloque */
```

---

## 3. FUNCIONES

### 3.1 Declaración Básica

**Python:**
```python
def saludar(nombre: str) -> str:
    return f"Hola, {nombre}!"
```

**Synapse:**
```synapse
funcion saludar(nombre: texto) -> texto:
    retornar "Hola, " + nombre
```

### 3.2 Múltiples Parámetros

**Python:**
```python
def sumar(a: int, b: int) -> int:
    return a + b
```

**Synapse:**
```synapse
funcion sumar(a: entero, b: entero) -> entero:
    retornar a + b
```

### 3.3 Valores por Defecto

**Python:**
```python
def conectar(host: str, puerto: int = 8080) -> bool:
    ...
```

**Synapse:**
```synapse
funcion conectar(host: texto, puerto: entero = 8080) -> booleano:
    ...
```

### 3.4 Contratos (Requiere / Garantiza)

**Python:**
```python
def dividir(a: int, b: int) -> float:
    assert b != 0, "Divisor no puede ser cero"
    return a / b
```

**Synapse:**
```synapse
funcion dividir(a: entero, b: entero) -> decimal:
    requiere:
        b != 0
    garantiza:
        _resultado_ * b - a < 0.001  // Precisión
    retornar a / b
```

### 3.5 Funciones Anidadas

**Python:**
```python
def exterior(x: int) -> int:
    def interior(y: int) -> int:
        return y * 2
    return interior(x) + 1
```

**Synapse:**
```synapse
funcion exterior(x: entero) -> entero:
    funcion interior(y: entero) -> entero:
        retornar y * 2
    retornar interior(x) + 1
```

### 3.6 Funciones Puras (Modo --safe)

```synapse
funcion pura factorial(n: entero) -> entero:
    requiere:
        n >= 0
    garantiza:
        _resultado_ >= 1
    si n <= 1:
        retornar 1
    retornar n * factorial(n - 1)
```

---

## 4. CONTROL DE FLUJO

### 4.1 Condicionales

**Python:**
```python
if edad >= 18:
    print("Adulto")
elif edad >= 13:
    print("Adolescente")
else:
    print("Niño")
```

**Synapse:**
```synapse
si edad >= 18:
    escribir_linea("Adulto")
si no edad >= 13:
    escribir_linea("Adolescente")
si no:
    escribir_linea("Niño")
```

### 4.2 Bucle While

**Python:**
```python
while contador < 10:
    print(contador)
    contador += 1
```

**Synapse:**
```synapse
mientras contador < 10:
    escribir_linea(contador)
    contador = contador + 1
```

### 4.3 Bucle For / Para

**Python:**
```python
for item in items:
    print(item)

for i in range(10):
    print(i)
```

**Synapse:**
```synapse
para item en items:
    escribir_linea(item)

para i en 0..10:
    escribir_linea(i)
```

### 4.4 Match / Coincidir

**Python:**
```python
match valor:
    case 0:
        print("Cero")
    case 1 | 2:
        print("Uno o dos")
    case _:
        print("Otro")
```

**Synapse:**
```synapse
coincidir valor:
    0 =>
        escribir_linea("Cero")
    1, 2 =>
        escribir_linea("Uno o dos")
    _ =>
        escribir_linea("Otro")
```

### 4.5 Break / Continue

**Python:**
```python
for i in range(10):
    if i == 5:
        break
    if i % 2 == 0:
        continue
    print(i)
```

**Synapse:**
```synapse
para i en 0..10:
    si i == 5:
        romper
    si i % 2 == 0:
        siguiente
    escribir_linea(i)
```

---

## 5. TIPOS DE DATOS

### 5.1 Tipos Primitivos

| Python | Synapse | Rango / Notas |
|--------|---------|---------------|
| `int` | `entero` | 64-bit signed (`int64_t`) |
| `float` | `decimal` | 64-bit (`double`) |
| `bool` | `booleano` | `verdadero` / `falso` |
| `str` | `texto` | `CadenaSegura` (longitud + datos) |
| `bytes` | `bytes` | `uint8_t[]` |
| `None` | `nulo` | Ausencia de valor |

### 5.2 Tipos Compuestos

**Python:**
```python
from typing import Optional, Union, List, Dict

resultado: Optional[str] = None
valor: Union[int, str] = 42
items: List[int] = [1, 2, 3]
mapa: Dict[str, int] = {"a": 1}
```

**Synapse:**
```synapse
let resultado: Opcion<texto> = ninguno
let valor: Entero | texto = 42    // Tipo unión
let items: Lista<entero> = [1, 2, 3]
let mapa: Diccionario<texto, entero> = {"a": 1}
```

### 5.3 Tipos Algebraicos

**Python:**
```python
from typing import Union

def procesar(valor: int) -> Union[int, str]:
    if valor >= 0:
        return valor
    return "Error: negativo"
```

**Synapse:**
```synapse
funcion procesar(valor: entero) -> Resultado<entero, texto>:
    si valor >= 0:
        retornar ok(valor)
    retornar err("Error: negativo")

// Uso obligatorio con coincidir
coincidir resultado:
    ok(valor) =>
        escribir_linea("Valor: " + valor)
    err(mensaje) =>
        escribir_linea("Error: " + mensaje)
```

### 5.4 Estructuras

**Python:**
```python
@dataclass
class Punto:
    x: float
    y: float

p = Punto(x=1.0, y=2.0)
```

**Synapse:**
```synapse
estructura Punto:
    x: decimal
    y: decimal

let p = Punto{x: 1.0, y: 2.0}
```

### 5.5 Enumeraciones

**Python:**
```python
from enum import Enum

class Color(Enum):
    ROJO = 1
    VERDE = 2
    AZUL = 3
```

**Synapse:**
```synapse
tipo Color = enum:
    rojo
    verde
    azul

// Con datos asociados
tipo ResultadoPago = enum:
    exito(transaccion_id: texto)
    fallo(codigo: entero, mensaje: texto)
```

---

## 6. OWNERSHIP Y BORROWING

### 6.1 Reglas de Posesión

```synapse
// Cada valor tiene un ÚNICO dueño
let datos: texto = "Hola, mundo"     // 'datos' es dueño
let copia = datos                      // ¡ERROR! 'datos' se movió a 'copia'
escribir_linea(datos)                  // Use-After-Move: error de compilación

// Transferencia explícita con ->
funcion consumir(-> datos: texto) -> nulo:
    escribir_linea(datos)

let mensaje = "importante"
consumir(-> mensaje)                   // mensaje transferido, ya no accesible aquí
```

### 6.2 Préstamo

```synapse
// Préstamo inmutable (&T)
funcion longitud(datos: &texto) -> entero:
    retornar datos.longitud

let nombre = "Synapse"
let largo = longitud(&nombre)           // Préstamo: nombre sigue siendo dueño
escribir_linea(nombre)                  // OK

// Préstamo mutable (&T mut)
funcion agregar_sufijo(datos: &texto) -> nulo:
    datos = datos + " v5.0"

let version = "Synapse"
agregar_sufijo(&version)            // Préstamo mutable
escribir_linea(version)                 // "Synapse v5.0"
```

### 6.2 Préstamo [Spec v5.0]

*Nota: El sistema de préstamo (borrowing) es parte de la especificación completa de Synapse v5.0. Las características `&T` y `&mut T` están en desarrollo activo.*

```synapse
// Préstamo inmutable (&T)
funcion longitud(datos: &texto) -> entero:
    retornar datos.longitud

let nombre = "Synapse"
let largo = longitud(&nombre)           // Préstamo: nombre sigue siendo dueño
escribir_linea(nombre)                  // OK

// Préstamo mutable (&T mut)
funcion agregar_sufijo(datos: &texto) -> nulo:
    datos = datos + " v5.0"

let version = "Synapse"
agregar_sufijo(&version)            // Préstamo mutable
escribir_linea(version)                 // "Synapse v5.0"
```

### 6.3 Regla de Oro

> Una variable solo puede tener UNO de los siguientes:
> - Una referencia inmutable (`&T`)
> - Múltiples referencias inmutables
> - UNA referencia mutable (`&mut T`)
> - Una combinación de ambos, NUNCA

---

## 7. CONCURRENCIA

### 7.1 Canales Tipados

**Python (asyncio):**
```python
import asyncio

async def productor(queue: asyncio.Queue):
    for i in range(10):
        await queue.put(i)

async def consumidor(queue: asyncio.Queue):
    while True:
        item = await queue.get()
        if item is None:
            break
        print(f"Recibido: {item}")
```

**Synapse:**
```synapse
importar std.concurrencia

funcion productor(canal: Canal<entero>) -> nulo:
    para i en 0..10:
        canal <- i        // Enviar al canal
    canal <- -1            // Señal de terminación

funcion consumidor(canal: Canal<entero>) -> nulo:
    mientras verdadero:
        let item = <-canal    // Recibir del canal
        si item < 0:
            romper
        escribir_linea("Recibido: " + item)

funcion principal() -> entero:
    let canal: Canal<entero> = Canal<entero>(capacidad: 10)
    lanzar productor(canal)
    lanzar consumidor(canal)
    retornar 0
```

### 7.2 Hilos

**Python:**
```python
import threading

def tarea(nombre: str):
    print(f"Hilo {nombre} iniciado")

hilo = threading.Thread(target=tarea, args=("A",))
hilo.start()
hilo.join()
```

**Synapse:**
```synapse
funcion tarea(nombre: texto) -> nulo:
    escribir_linea("Hilo " + nombre + " iniciado")

lanzar tarea("A")    // Crea hilo y ejecuta función
```

---

## 8. ENTRADA/SALIDA

### 8.1 Consola

**Python:**
```python
nombre = input("Nombre: ")
print(f"Hola, {nombre}")
```

**Synapse:**
```synapse
importar std.io

escribir("Nombre: ")
let nombre = leer_linea()
escribir_linea("Hola, " + nombre)
```

### 8.2 Archivos

**Python:**
```python
with open("datos.txt", "r") as f:
    contenido = f.read()
```

**Synapse:**
```synapse
importar std.io

let archivo = abrir("datos.txt", "r")
let contenido = leer(archivo)
cerrar(archivo)
```

---

## 9. JSON

**Python:**
```python
import json

datos = json.dumps({"nombre": "Ana", "edad": 30})
obj = json.loads(datos)
print(obj["nombre"])
```

**Synapse:**
```synapse
importar std.json

let datos = a_texto({"nombre": "Ana", "edad": 30})
let obj = desde_texto(datos)
escribir_linea(obtener_campo(obj, "nombre"))
liberar_nodo(-> obj)
```

---

## 10. RED

**Python:**
```python
import urllib.request

resp = urllib.request.urlopen("https://api.ejemplo.com")
datos = resp.read()
```

**Synapse:**
```synapse
importar std.net

let respuesta = http_get("https://api.ejemplo.com")
escribir_linea(respuesta.cuerpo)
```

---

## 11. MATEMÁTICAS

**Python:**
```python
import math

x = math.sin(3.14159)
y = math.sqrt(144)
z = abs(-42)
```

**Synapse:**
```synapse
importar std.math

let x = seno(3.14159)
let y = raiz_cuadrada(144)
let z = valor_absoluto(-42)
```

---

## 12. PRUEBAS

**Python:**
```python
def test_suma():
    assert suma(2, 3) == 5
    assert suma(-1, 1) == 0
```

**Synapse:**
```synapse
importar std.testing

funcion prueba_suma() -> nulo:
    asegurar(suma(2, 3) == 5)
    asegurar(suma(-1, 1) == 0)
```

---

## 13. ERRORES COMUNES Y SOLUCIONES

| Error Python | Causa | Solución Synapse |
|-------------|-------|-----------------|
| `AttributeError: 'NoneType' object has no attribute 'x'` | Valor `None` no esperado | Usar `Opcion<T>` y `coincidir` |
| `TypeError: unsupported operand type(s)` | Tipos incorrectos | Tipado estricto en tiempo de compilación |
| `KeyError: 'clave'` | Clave faltante en diccionario | Usar `obtener(dict, clave)` que retorna `Opcion<V>` |
| `IndexError: list index out of range` | Índice fuera de rango | Verificar `lista.longitud` antes de acceder |
| `RuntimeError: cannot join current thread` | Deadlock | Canales con capacidad finita y timeouts |
| `MemoryError` | Fuga de memoria | Ownership + RAII estático |

---

## 14. HERRAMIENTAS DE MIGRACIÓN

### 14.1 CLI

```bash
# Migrar archivo individual
synapse migrate --migrate modulo.py

# Migrar con contratos
synapse migrate modulo.py --add-contracts

# Ver AST canónico generado
synapse migrate modulo.py --output modulo.syn.json
```

### 14.2 VS Code

1. Abrir archivo `.py`
2. Click derecho → **Migrar a Synapse**
3. VS Code muestra diff interactivo
4. Aceptar → se crea `.syn` al lado

### 14.3 Verificación

Siempre verificar el código migrado con:
```bash
synapse build --safe modulo.syn    # Verificación formal
synapse --sbom modulo.syn          # Generar SBOM
```

---

## 15. REFERENCIAS

| Documento | Descripción |
|-----------|-------------|
| `docs/especificacion_opensyn.md` | Especificación completa de OpenSyn |
| `docs/api_ast_canonico.md` | Referencia del AST Canónico |
| `MANUAL_LENGUAJE.md` | Manual completo del lenguaje Synapse |
| `REFERENCIA_API_STD.md` | Referencia de la biblioteca estándar |
| `tests/` | Ejemplos de código funcional |

---

## 16. HISTORIAL DE CAMBIOS

| Versión | Fecha | Cambios |
|---------|-------|---------|
| 5.0.0 | 26 Jul 2026 | Guía completa de migración con todos los constructos del lenguaje. |

---

**Fin de la Guía de Migración Python → Synapse v5.0**
