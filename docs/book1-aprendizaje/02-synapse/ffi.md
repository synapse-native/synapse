# Interfaz con C (FFI) en Synapse

La FFI (Foreign Function Interface) permite a Synapse llamar funciones
escritas en C y otras bibliotecas nativas. Esto abre acceso a un ecosistema
masivo de código existente.

## Declarar Funciones Externas

Use la palabra clave `externo` para declarar funciones C disponibles
para el intérprete:

```synapse
// Declarar printf de C
externo fn printf(formato: cadena, ..args: anyo) -> entero

// Declarar malloc y free
externo fn malloc(tamano: entero) -> puntero
externo fn free(puntero: puntero)

// Declarar strlen
externo fn strlen(cadena: cadena) -> entero

fn principal() {
    printf("Hola desde C: %s\n", "Synapse")
    let len = strlen("hello")
    log("Longitud: {len}")
}
```

## Bindings Completos

Para usar bibliotecas C completas, cree un archivo de bindings:

```synapse
// bindings/SDL2.sin

// Constantes
externo const SDL_INIT_VIDEO: entero
externo const SDL_WINDOWPOS_CENTERED: entero

// Funciones de inicialización
externo fn SDL_Init(banderas: entero) -> entero
externo fn SDL_CreateWindow(
    titulo: cadena,
    x: entero, y: entero,
    ancho: entero, alto: entero,
    banderas: entero
) -> puntero

externo fn SDL_CreateRenderer(
    ventana: puntero,
    indice: entero,
    banderas: entero
) -> puntero

externo fn SDL_DestroyWindow(ventana: puntero)
externo fn SDL_Quit()
```

## Uso de la Biblioteca

```synapse
importar bindings.SDL2

fn main() {
    if SDL2::SDL_Init(SDL2::SDL_INIT_VIDEO) != 0 {
        log("Error inicializando SDL")
        return
    }

    let ventana = SDL2::SDL_CreateWindow(
        "Mi ventana",
        SDL2::SDL_WINDOWPOS_CENTERED,
        SDL2::SDL_WINDOWPOS_CENTERED,
        800, 600, 0
    )

    if ventana es nulo {
        log("Error creando ventana")
        SDL2::SDL_Quit()
        return
    }

    // ... usar ventana ...

    SDL2::SDL_DestroyWindow(ventana)
    SDL2::SDL_Quit()
}
```

## Manejo de Punteros

Los punteros en FFI deben manejarse con cuidado. Synapse proporciona
tipos seguros para operaciones comunes:

```synapse
externo fn malloc(tamano: entero) -> *mut u8
externo fn free(puntero: *mut u8)

fn usar_malloc() {
    let ptr = malloc(1024)

    if ptr es nulo {
        log("Error: malloc falló")
        return
    }

    // Escribir datos al puntero
    ptr.escribir(0, 42)     // Escribir byte en offset 0
    ptr.escribir(1, 100)

    // Leer datos
    let valor = ptr.leer(0)  // 42

    // Liberar memoria
    free(ptr)

    // After free, ptr es inválido
    // NUNCA acceder a ptr después de free
}
```

## Callbacks C a Synapse

También puede pasar funciones de Synapse como callbacks a funciones C:

```synapse
// Función callback para C
fn mi_callback(datos: puntero, tamano: entero) -> entero {
    let buffer = datos.como_cadena(tamano)
    log("Recibido: {buffer}")
    return 0
}

// Declarar función C que acepta callback
externo fn registrar_callback(
    fn(datos: puntero, tamano: entero) -> entero
)

fn usar_callback() {
    registrar_callback(mi_callback)
}
```

## Seguridad en FFI

FFI es inherently inseguro. Siga estas reglas:

```synapse
// 1. Validar punteros antes de usar
fn usar_puntero_c(p: puntero) {
    if p es nulo {
        log("Error: puntero nulo")
        return
    }
    // Proceder solo si es válido
}

// 2. Nunca confiar en el tamaño de datos de C
fn copiar_seguro(origen: puntero, len: entero) {
    if len < 0 || len > 1024 * 1024 {
        log("Error: tamaño inválido")
        return
    }
    // Proceder con copia segura
}

// 3. Usar bloques inseguros explícitamente
fn operacion_c() {
    inseguro {
        // Código que accede a memoria C
        let ptr = malloc(100)
        ptr.escribir(0, 1)
        free(ptr)
    }
}

// 4. Verificar errores de C
fn llamada_c() {
    let resultado = funcion_c_externa()
    if resultado < 0 {
        let errno = obtener_errno()
        log("Error de C: {errno}")
    }
}
```

## Ejemplo Completo: Lectura de Archivo con C

```synapse
externo fn fopen(nombre: cadena, modo: cadena) -> puntero
externo fn fclose(archivo: puntero) -> entero
externo fn fread(buffer: puntero, tamano: entero, count: entero, archivo: puntero) -> entero
externo fn fseek(archivo: puntero, offset: entero, whence: entero) -> entero
externo fn ftell(archivo: puntero) -> entero

fn leer_archivo_c(nombre: cadena) -> cadena {
    let archivo = fopen(nombre, "rb")
    if archivo es nulo {
        log("No se pudo abrir: {nombre}")
        return ""
    }

    // Obtener tamaño
    fseek(archivo, 0, 2) // SEEK_END
    let tamano = ftell(archivo)
    fseek(archivo, 0, 0) // SEEK_SET

    // Leer contenido
    let buffer = malloc(tamano + 1)
    let leidos = fread(buffer, 1, tamano, archivo)
    buffer.escribir(leidos, 0) // Null terminator

    fclose(archivo)

    let resultado = buffer.como_cadena(leidos)
    free(buffer)

    return resultado
}
```
