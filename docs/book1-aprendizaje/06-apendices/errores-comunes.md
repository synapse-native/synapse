# Errores Comunes

Este apéndice recopila los errores más frecuentes que cometen los desarrolladores al usar Synapse y Syquex, junto con sus soluciones. Aprenderás a identificar y resolver problemas comunes rápidamente.

Consultar esta lista te ahorrará tiempo de depuración.

<!-- cumple Manual 2 §10, Manual 3 §7 -->

## 1. Errores Léxicos

### `ERR_LEX_MISSING_LANG`

**Causa:** El archivo no comienza con la directiva `#lang:` en la primera línea.

```synapse
// ❌ Error
funcion principal():
    log("Hola")

// ✅ Solución
#lang: es
funcion principal():
    log("Hola")
```

### `ERR_LEX_TAB_DETECTED`

**Causa:** El archivo usa tabuladores en lugar de espacios para indentación.

```synapse
// ❌ Error (usa tabs)
funcion ejemplo():
\treturnar 42

// ✅ Solución (usa 4 espacios)
funcion ejemplo():
    retornar 42
```

### Caracteres no UTF-8

**Causa:** El archivo contiene caracteres no UTF-8 (ej. Latin-1, Windows-1252).

```bash
# Convertir archivo a UTF-8
iconv -f WINDOWS-1252 -t UTF-8 archivo.syn > archivo_utf8.syn
```

## 2. Errores de Sintaxis

### `ERR_INDENT_INVALID`

**Causa:** La indentación es inconsistente.

```synapse
// ❌ Error
funcion ejemplo():
    log("Hola")
      log("Mundo")  // Indentación incorrecta

// ✅ Solución
funcion ejemplo():
    log("Hola")
    log("Mundo")
```

### `ERR_SYNTAX_EXPECTED_TOKEN`

**Causa:** Falta un token esperado (paréntesis, dos puntos, etc.).

```synapse
// ❌ Error
funcion ejemplo()
    retornar 42

// ✅ Solución
funcion ejemplo():
    retornar 42
```

### Llaves/Paréntesis no balanceados

```synapse
// ❌ Error
si condicion
    log("Hola"  // Falta cerrar paréntesis

// ✅ Solución
si condicion:
    log("Hola")
```

## 3. Errores de Ownership (Synapse)

### `ERR_MEM_USE_AFTER_MOVE`

**Causa:** Uso de una variable después de haberla movido.

```synapse
// ❌ Error
funcion ejemplo():
    let x = "Hola"
    funcion_consume(x)  // x se mueve aquí
    log(x)  // ERROR: x ya no es válido

// ✅ Solución 1: Pasar por referencia
funcion ejemplo():
    let x = "Hola"
    funcion_referencia(&x)  // Préstamo
    log(x)  // OK

// ✅ Solución 2: Clonar antes
funcion ejemplo():
    let x = "Hola"
    funcion_consume(x.clone())
    log(x)  // OK
```

### `ERR_MEM_LIFETIME_MISMATCH`

**Causa:** Un préstamo vive más que el valor prestado.

```synapse
// ❌ Error
funcion ejemplo() -> &texto:
    let s = "Hola"  // s se destruye al salir de la función
    return &s  // ERROR: s ya no existe cuando se use la referencia

// ✅ Solución: Usar 'estatico o retornar por valor
funcion ejemplo() -> texto:
    let s = "Hola"
    return s  // Move de propiedad
```

### `ERR_MEM_LIFETIME_CYCLE`

**Causa:** Ciclo en dependencias de lifetimes.

```synapse
// ❌ Error
estructura Nodo:
    siguiente: rc<Nodo>  // rc puede crear ciclos

// ✅ Solución: Usar débil
estructura Nodo:
    siguiente: débil<Nodo>  // Referencia débil rompe el ciclo
```

## 4. Errores de Tipos

### `ERR_SEM_TYPE_AMBIGUOUS`

**Causa:** El tipo no se puede inferir.

```synapse
// ❌ Error
let x = []  // Tipo ambiguo

// ✅ Solución: Anotar el tipo
let x: Lista<entero> = []
```

### `ERR_SEM_TIPO_INCOMPATIBLE`

**Causa:** Tipos incompatibles en una operación.

```syquex
// ❌ Error
let a: entero = 42
let b: texto = "Hola"
let suma = a + b  // No se puede sumar entero + texto

// ✅ Solución
let suma = a.texto() + b  // Convertir antes
```

### `ERR_SEM_EXHAUSTIVE_MATCH_REQUIRED`

**Causa:** Falta un caso en pattern matching.

```syquex
// ❌ Error
coincidir resultado:
    caso ok(v): log(v)
    // Falta caso err(...)

// ✅ Solución: Cubrir todos los casos
coincidir resultado:
    caso ok(v): log(v)
    caso err(e): log("Error: ", e)
```

## 5. Errores de Concurrencia

### `ERR_CONC_CHANNEL_CLOSED`

**Causa:** Enviar a un canal cerrado.

```syquex
// ❌ Error
let canal = Canal<entero>(10)
canal.cerrar()
canal <- 42  // ERROR: canal cerrado

// ✅ Solución: Verificar antes de enviar
si !canal.esta_cerrado():
    canal <- 42
```

### Deadlock por orden de locks

**Causa:** Adquirir locks en orden diferente en diferentes hilos.

```syquex
// ❌ Error: Puede causar deadlock
lanzar hilo_a():
    lock_a.bloquear()
    lock_b.bloquear()
    // ...

lanzar hilo_b():
    lock_b.bloquear()  // Orden inverso -> deadlock potencial
    lock_a.bloquear()
    // ...

// ✅ Solución: Usar canales en lugar de locks
lanzar productor(canal):
    canal <- dato

lanzar consumidor(canal):
    escuchar canal:
        procesar(canal ->)
```

## 6. Errores de Compilación

### `ERR_CACHE_CORRUPT`

**Causa:** Caché de compilación corrupto.

```bash
# Solución: Limpiar caché
rm -rf .cache/
python main.py archivo.syn
```

### `ERR_CACHE_VERSION_MISMATCH`

**Causa:** Caché de versión anterior.

```bash
# Solución: Limpiar caché
python main.py --clean-cache archivo.syn
```

## 7. Errores de Runtime

### Stack Overflow

**Causa:** Recursión demasiado profunda.

```syquex
// ❌ Error (recursión infinita o muy profunda)
funcion factorial(n: entero) -> entero:
    retornar n * factorial(n - 1)  // Sin caso base

// ✅ Solución: Agregar caso base
funcion factorial(n: entero) -> entero:
    si n <= 1:
        retornar 1
    retornar n * factorial(n - 1)
```

### División por cero

**Causa:** División sin verificar denominador.

```syquex
// ❌ Error
funcion dividir(a: decimal, b: decimal) -> decimal:
    retornar a / b  // Si b == 0, error

// ✅ Solución: Validar
funcion dividir(a: decimal, b: decimal) -> Resultado<decimal, texto>:
    si b == 0.0:
        retornar err("División por cero")
    retornar ok(a / b)
```

### Acceso a índice fuera de rango

**Causa:** Índice inválido en array.

```syquex
// ❌ Error
let lista = [1, 2, 3]
let valor = lista[10]  // Índice fuera de rango

// ✅ Solución: Verificar longitud
funcion obtener(lista: Lista<entero>, idx: entero) -> Resultado<entero, texto>:
    si idx < 0 o idx >= lista.len():
        retornar err("Índice fuera de rango")
    retornar ok(lista[idx])
```

## 8. Errores de Axon (Paquetes)

### `ERR_AXON_COMPROMISED`

**Causa:** El paquete descargado está corrupto o alterado.

```bash
# Solución: Re-descargar con verificación
axon install paquete --verify

# Si persiste, limpiar caché
axon cache clean
```

### `ERR_AXON_VERSION`

**Causa:** Versión incompatible del paquete.

```bash
# Solución: Verificar versión requerida
axon info paquete

# Instalar versión específica
axon install paquete@1.2.3
```

## 9. Errores Comunes de Compilación

### Olvidar el `:` después de `si`, `mientras`, `funcion`, etc.

```syquex
// ❌ Error
funcion ejemplo()
    log("Hola")

// ✅ Solución
funcion ejemplo():
    log("Hola")
```

### Usar `=` en lugar de `==` para comparación

```syquex
// ❌ Error (asignación en lugar de comparación)
si x = 5:
    log("x es 5")

// ✅ Solución
si x == 5:
    log("x es 5")
```

### Indentación incorrecta en bloques multilínea

```syquex
// ❌ Error
coincidir resultado:
caso ok(v):
log(v)

// ✅ Solución
coincidir resultado:
    caso ok(v):
        log(v)
```

## 10. Errores de FFI

### Tipos incompatibles en FFI

```syquex
// ❌ Error
externo funcion strlen(s: entero) -> entero  // strlen espera char*, no entero

// ✅ Solución
externo funcion strlen(s: &texto) -> entero
```

### Olvidar `externo` para funciones C

```syquex
// ❌ Error
funcion strlen(s: &texto) -> entero:
    retornar 0  // No llama a la función C real

// ✅ Solución
externo funcion strlen(s: &texto) -> entero
```

## 11. Errores de Concurrencia Distribuida

### Handshake Ed25519 fallido

**Causa:** Claves públicas no coinciden.

```syquex
// ❌ Error
let canal = cluster.conectar("tcp://servidor:8080", "clave-incorrecta")
// ERROR: handshake failed

// ✅ Solución: Usar la clave pública correcta
let canal = cluster.conectar("tcp://servidor:8080", "AAAA...")
```

### Timeout en canal remoto

**Causa:** El servidor remoto no responde.

```syquex
// ❌ Error
let resultado = canal_remoto.recibir()  // Bloquea indefinidamente

// ✅ Solución: Usar timeout
let resultado = await Timeout(5000, canal_remoto.recibir())
```

## 12. Tips de Depuración

### Activar logs verbose

```bash
python main.py archivo.syn --verbose
```

### Verificar el AST

```bash
python main.py --ast archivo.syn > ast.json
```

### Ejecutar paso a paso con el debugger

```bash
python main.py --debug archivo.syn
```

### Usar afirmaciones

```syquex
pruebas.afirmar(x > 0, "x debe ser positivo")
pruebas.afirmar_igual(resultado, esperado)
```

## 13. Mejores Prácticas

1. **Leer el manual** antes de codificar
2. **Usar contratos** `requiere`/`garantiza`
3. **Manejar errores** explícitamente con `Resultado`
4. **Escribir tests** para cada función
5. **Validar entradas** en funciones públicas
6. **Usar nombres descriptivos** para variables y funciones
7. **Comentar secciones complejas**
8. **Refactorizar** código duplicado

## Referencias

- **Manual 2 §10**: Taxonomía de errores (categorías y rangos)
- **Manual 3 §7**: Manejo de errores con Resultado
- **Manual 5 §6**: Patrones de concurrencia
- **Manual 9 §1**: Debug y diagnóstico

// cumple Manual 2 §10
