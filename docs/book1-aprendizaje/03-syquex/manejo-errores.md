# Manejo de Errores en Syquex

Este capítulo explora el sistema de manejo de errores en Syquex, incluyendo tipos de error, propagación y recuperación. Aprenderás a escribir código robusto que maneje errores de forma elegante.

Un buen manejo de errores es esencial para la confiabilidad del software.

<!-- cumple Manual 3 §7 -->

## 1. Filosofía del Manejo de Errores

Syquex sigue el principio de **"No hay excepciones"** — en lugar de excepciones de Python/Java, usa **tipos `Resultado<T, E>`** con propagación explícita pero ergonómica.

### ¿Por qué no excepciones?

1. **Visibilidad**: El tipo de retorno `Resultado` hace explícito que una operación puede fallar
2. **No hay costos ocultos**: No hay tablas de excepciones ni stack unwinding
3. **Thread-safe**: Los errores son valores, no estados globales
4. **Compilación estricta**: El compilador fuerza a manejar todos los errores posibles

## 2. Tipo `Resultado<T, E>`

```syquex
// Resultado tiene dos variantes:
tipo Resultado<T, E> = ok(T) | err(E)

// T = tipo de valor exitoso
// E = tipo de error (generalmente texto)
```

### Creación de Resultados

```syquex
funcion abrir_archivo(ruta: texto) -> Resultado<Archivo, texto>:
    si !fs.existe(ruta):
        retornar err("Archivo no existe: " + ruta)
    retornar ok(fs.abrir(ruta))

funcion dividir(a: decimal, b: decimal) -> Resultado<decimal, texto>:
    si b == 0.0:
        retornar err("División por cero")
    retornar ok(a / b)
```

## 3. Pattern Matching con `coincidir`

Obligatorio para tipos `Resultado`:

```syquex
funcion main():
    let resultado = dividir(10.0, 0.0)
    coincidir resultado:
        caso ok(valor):
            io.escribir_linea("Resultado: " + valor.texto())
        caso err(mensaje):
            io.escribir_linea("Error: " + mensaje)
```

## 4. Propagación con el Operador `?`

El operador `?` simplifica la propagación de errores:

```syquex
funcion calcular_promedio(numeros: Lista<decimal>) -> Resultado<decimal, texto>:
    si numeros.vacio():
        retornar err("Lista vacía")
    
    let suma = numeros.reducir(lambda acc, x: acc + x, 0.0)?
    retornar ok(suma / numeros.len().decimal())

funcion procesar(archivo: texto) -> Resultado<texto, texto>:
    let contenido = fs.leer(archivo)?
    let datos = contenido.parse_json()?
    retornar ok(datos.nombre)
```

### Propagación con transformación

```syquex
funcion obtener_usuario(id: entero) -> Resultado<Usuario, texto>:
    let json = await api.get("/usuarios/" + id.texto())?
    let usuario = json.parse_usuario()?
    retornar ok(usuario)
```

## 5. `intentar` y `atrapar`

Para operaciones que pueden lanzar errores no tipados:

```syquex
funcion operacion_riesgosa() -> Resultado<nulo, texto>:
    intentar:
        let datos = fs.leer("config.json")
        // Procesamiento que podría fallar
        procesar_datos(datos)
    atrapar e:
        retornar err("Fallo: " + e.texto())
    retornar ok()
```

### Intentar/Recuperar con valor

```syquex
funcion valor_seguro(clave: texto) -> texto:
    intentar:
        retornar fs.leer(clave + ".json")
    atrapar e:
        retornar "{}"  // Valor por defecto
```

## 6. Tipos de Error Personalizados

```syquex
// Usar ADTs para errores tipados
tipo ErrorUsuario = 
    | UsuarioNoEncontrado(entero)
    | EmailInvalido(texto)
    | ContrasenaDebil

funcion registrar_usuario(email: texto, password: texto) -> Resultado<Usuario, ErrorUsuario>:
    si !email.es_valido():
        retornar err(EmailInvalido(email))
    
    si password.len() < 8:
        retornar err(ContrasenaDebil())
    
    let usuario = Usuario.crear(email, password)
    retornar ok(usuario)

funcion main():
    let resultado = registrar_usuario("ana@", "123")
    coincidir resultado:
        caso ok(u): io.escribir_linea("Usuario creado: " + u.nombre)
        caso err(EmailInvalido(email)): io.escribir_linea("Email inválido: " + email)
        caso err(ContrasenaDebil()): io.escribir_linea("La contraseña es muy débil")
        caso err(UsuarioNoEncontrado(id)): io.escribir_linea("ID no encontrado: " + id.texto())
```

## 7. Recovery y Retry

### Patrón de Recovery

```syquex
funcion con_recuperacion<T>(operacion: funcion() -> Resultado<T, texto>) -> T:
    let intentos = 3
    para i en 1..intentos:
        intentar:
            retornar operacion()
        atrapar e:
            io.escribir_linea("Intento " + i.texto() + " falló: " + e)
            await sleep(100 * i)  // Backoff lineal
    
    retornar valor_por_defecto<T>()
```

### Retry con Exponencial Backoff

```syquex
async funcion retry<T>(
    operacion: funcion() -> Resultado<T, texto>,
    max_intentos: entero = 3
) -> Resultado<T, texto>:
    para intento en 1..max_intentos:
        let resultado = operacion()
        coincidir resultado:
            caso ok(valor): retornar ok(valor)
            caso err(e):
                io.escribir_linea("Intento " + intento.texto() + " falló: " + e)
                let delay = 100 * (2 ^ (intento - 1))  // 100, 200, 400ms
                await sleep(delay)
    
    retornar err("Agotados " + max_intentos.texto() + " intentos")
```

## 8. Resultados Combinados (`Promise.all`, `Promise.race`)

```syquex
// Esperar todas las operaciones (falla si alguna falla)
async funcion cargar_todos(urls: Lista<texto>) -> Resultado<Lista<texto>, texto>:
    let promesas = urls.mapear(async lambda url:
        await http.get(url)
    )
    
    intentar:
        let respuestas = await Promise.all(promesas)
        retornar ok(respuestas.mapear(lambda r: r.cuerpo))
    atrapar e:
        retornar err("Falló una de las peticiones: " + e)

// Primera respuesta exitrosa
async funcion primero_exitoso(urls: Lista<texto>) -> texto:
    let promesas = urls.mapear(async lambda url:
        await http.get(url)
    )
    
    intentar:
        let respuesta = await Promise.race(promesas)
        retornar respuesta.cuerpo
    atrapar e:
        retornar "Error"
```

## 9. Logging de Errores

```syquex
importar lib.logging

let logger = logging.logger("mi_app")

funcion operacion():
    let resultado = api.llamada()
    coincidir resultado:
        caso ok(valor):
            logger.info("Operación exitosa: " + valor.texto())
        caso err(e):
            logger.error("Operación falló: " + e, contexto: {
                "endpoint": "api.endpoint",
                "timestamp": tiempo_actual()
            })
            retornar err(e)
```

## 10. Buenas Prácticas

### 1. Siempre manejar errores explícitamente

```syquex
// ✅ Bien: manejo explícito
let resultado = dividir(10, 0)
coincidir resultado:
    caso ok(v): io.escribir_linea(v.texto())
    caso err(e): io.escribir_linea("Error: " + e)

// ❌ Mal: ignorar errores (el compilador lo advierte)
let _ = dividir(10, 0)  // Advertencia del compilador
```

### 2. Usar tipos de error descriptivos

```syquex
// ✅ Bien: tipos específicos
tipo ErrorValidacion = CampoInvalido(texto) | CamposFaltantes(Lista<texto>)

// ❌ Mal: solo texto
funcion validar(dato: texto) -> Resultado<nulo, texto>
```

### 3. Propagar con `?` cuando es apropiado

```syquex
funcion procesar_cadena(cadena: texto) -> Resultado<entero, texto>:
    let entero_str = cadena.split(",")
    let numeros = entero_str.mapear(lambda s: s.entero())
    let suma = numeros.reducir(lambda a, b: a + b, 0)?
    retornar ok(suma)
```

## Ejemplo Completo

```syquex
#lang: es

importar lib.io

tipo ErrorRed = 
    | ErrorConexion(texto)
    | TiempoAgotado
    | RespuestaInvalida

funcion fetch_data(url: texto) -> Resultado<Lista<entero>, ErrorRed>:
    intentar:
        let resp = await http.get(url)
        let datos = resp.parse_json()
        retornar ok(datos.numeros)
    atrapar e:
        si e.contiene("timeout"):
            retornar err(TiempoAgotado)
        retornar err(ErrorConexion(url))

funcion main():
    let resultado = await fetch_data("https://api.ejemplo.com/datos")
    coincidir resultado:
        caso ok(datos):
            io.escribir_linea("Datos recibidos: " + datos.len().texto())
        caso err(TiempoAgotado):
            io.escribir_linea("La conexión tomó demasiado tiempo")
        caso err(ErrorConexion(url)):
            io.escribir_linea("No se pudo conectar a: " + url)
```

## Referencias

- **Manual 3 §7**: Manejo de errores con `Resultado`, `Opcion` y `?`
- **Manual 3 §5.4**: Tipos algebraicos (`Resultado`, `Opcion`)
- **Manual 2 §10**: Verificación de tipos exhaustivos
- **Manual 9 §1**: Debug y diagnóstico de errores en runtime

// cumple Manual 3 §7
