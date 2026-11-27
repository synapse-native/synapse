# Manejo de Archivos en Syquex

Este capítulo cubre las operaciones de archivos en Syquex: lectura, escritura, directorios y metadatos. Aprenderás a trabajar con el sistema de archivos de forma segura y eficiente.

Syquex proporciona una API moderna y segura para operaciones de archivos.

<!-- cumple Manual 3 §12 -->

## 1. Lectura de Archivos

### Leer archivo completo

```syquex
importar lib.fs

// Leer todo el contenido como texto
let contenido = fs.leer("ruta/al/archivo.txt")
io.escribir_linea(contenido)

// Leer como lista de líneas
let lineas = fs.leer_lines("ruta/al/archivo.txt")
para i, linea en lineas.enumerar():
    io.escribir_linea((i + 1).texto() + ": " + linea)
```

### Leer con manejo de errores

```syquex
funcion leer_seguro(ruta: texto) -> Resultado<texto, texto>:
    si !fs.existe(ruta):
        retornar err("Archivo no existe: " + ruta)
    
    intentar:
        let contenido = fs.leer(ruta)
        retornar ok(contenido)
    atrapar e:
        retornar err("Error de lectura: " + e)

// Uso
let resultado = leer_seguro("config.json")
coincidir resultado:
    caso ok(contenido): io.escribir_linea(contenido)
    caso err(e): io.escribir_linea("Error: " + e)
```

## 2. Escritura de Archivos

```syquex
// Escribir (sobrescribir)
fs.escribir("salida.txt", "Hola, mundo!")

// Escribir en modo append
fs.agregar("registro.log", "Operación completada\n")

// Escribir líneas
let lineas = ["Línea 1", "Línea 2", "Línea 3"]
fs.escribir_lines("datos.txt", lineas)

// Escribir JSON
fs.escribir_json("config.json", {"nombre": "Ana", "edad": 28})
```

## 3. Directorios

```syquex
// Crear directorio
fs.crear_directorio("proyecto/nuevo")

// Crear directorio recursivamente
fs.crear_directorio_recursivo("proyecto/nuevo/subdirectorio")

// Listar contenido
let archivos = fs.listar("proyecto/")
para archivo en archivos:
    io.escribir_linea(
        si fs.es_directorio(archivo): "[DIR]" sino: "[FILE]" + " " + archivo
    )

// Eliminar directorio
fs.eliminar_directorio("proyecto/viejo")  // Solo si está vacío
fs.eliminar_directorio_recursivo("proyecto/viejo")  // Con contenido
```

## 4. Metadatos y Permisos

```syquex
let info = fs.info("archivo.txt")

io.escribir_linea("Tamaño: " + info.tamaño.texto() + " bytes")
io.escribir_linea("Creado: " + info.creado.texto())
io.escribir_linea("Modificado: " + info.modificado.texto())
io.escribir_linea("Permisos: " + info.permisos.texto())

// Cambiar permisos
fs.cambiar_permisos("script.sh", 0o755)
```

## 5. Rutas y Paths

```syquex
// Unir rutas de forma segura
let ruta = fs.unir("home", "user", "documentos")
// Resultado: home/user/documentos (o home\user\documentos en Windows)

// Obtener extensiones
let ext = fs.extension("archivo.tar.gz")  // ".gz"

// Nombre base y directorio padre
let nombre = fs.nombre_base("ruta/al/archivo.txt")  // "archivo.txt"
let padre = fs.directorio_padre("ruta/al/archivo.txt")  // "ruta/al/"

// Normalizar ruta
let normalizado = fs.normalizar("ruta/./al/../archivo.txt")  // "ruta/archivo.txt"
```

## 6. Operaciones Avanzadas

### Copiar y Mover

```syquex
// Copiar archivo
fs.copiar("origen.txt", "destino.txt")

// Mover archivo
fs.mover("temporal.txt", "final.txt")

// Copiar directorio (recursivo)
fs.copiar_directorio("proyecto/", "backup/proyecto/")
```

### Streams de Archivos

```syquex
// Abrir stream para lectura/escritura eficiente
async funcion procesar_grande(ruta: texto):
    let stream = await fs.abrir_stream(ruta)
    let buffer = Lista<texto>(1024)
    
    mientras true:
        let bloque = await stream.leer(1024 * 1024)  // 1MB
        si bloque.vacio():
            romper
        procesar_bloque(bloque)
    
    stream.cerrar()
```

### File Watchers

```syquex
let watcher = fs.watch("directorio/")

escuchar watcher:
    let evento = watcher ->
    coincidir evento.tipo:
        caso "creado": io.escribir_linea("Nuevo: " + evento.ruta)
        caso "modificado": io.escribir_linea("Modificado: " + evento.ruta)
        caso "eliminado": io.escribir_linea("Eliminado: " + evento.ruta)
```

## 7. Manejo de Rutas Relativas y Absolutas

```syquex
// Convertir a ruta absoluta
let absoluta = fs.absoluta("archivo.txt", directorio_inicio: "proyecto")

// Ruta relativa desde un punto
let relativa = fs.relativa("/home/user/docs/archivo.txt", "/home/user/")

// Current working directory
let cwd = fs.directorio_actual()
io.escribir_linea("Directorio actual: " + cwd)
```

## Ejemplo Completo

```syquex
#lang: es
importar lib.fs
importar lib.io

estructura ArchivoConfig:
    ruta: texto
    datos: Mapa<texto, texto>

    metodo cargar() -> Resultado<ArchivoConfig, texto>:
        intentar:
            let contenido = fs.leer(self.ruta)
            let datos = contenido.parse_json()
            retornar ok(ArchivoConfig(self.ruta, datos))
        atrapar e:
            retornar err("No se pudo cargar la configuración: " + e)

    metodo guardar():
        fs.escribir(self.ruta, self.datos.a_json())

funcion principal():
    let config = ArchivoConfig("config.json", Mapa<texto, texto>())
    let resultado = config.cargar()
    
    coincidir resultado:
        caso ok(cfg):
            io.escribir_linea("Configuración cargada")
        caso err(e):
            io.escribir_linea("Error: " + e)
```

## Referencias

- **Manual 3 §12.1**: Módulos incluidos (IO, Web, DOM, JSON, Lista, Mapa, DB, Tiempo, Pruebas, IA, FFI)
- **Manual 3 §12.3**: FFI y marshaling automático
- **Manual 2 §9.2**: Préstamos y lifetimes (referencias a recursos)

// cumple Manual 3 §12
