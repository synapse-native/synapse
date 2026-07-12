# Librería Estándar (Sysroot)

La librería estándar incluye:

| Módulo | Descripción |
|---|---|
| `std.io` | Entrada/salida por terminal (`escribir`, `leer_linea`) |
| `std.mem` | Gestión de memoria raw (`reserva`, `libera`) |
| `std.net` | Sockets TCP cliente (`conectar`, `enviar`, `recibir`) |
| `std.json` | Parseo de JSON (`desde_texto`, `obtener_campo`) |
| `std.toml` | Parseo de TOML |
| `std.math` | Operaciones con tensores (`crear_tensor`, `producto_punto`, `relu`) |
| `std.err` | Tipos algebraicos (`Resultado`, `Opcion`) |
| `std.tiempo` | Medición de tiempo y suspensión (`ahora_ms`, `dormir_ms`) |
| `std.cripto` | Criptografía SHA-256 (`sha256_texto`) |
| `std.http` | Servidor HTTP minimalista (`iniciar_servidor`, `aceptar`, `responder`) |

## std.tiempo

Funciones para medir tiempo de ejecución y suspender hilos:

```synapse
importar std.tiempo

inicio = ahora_ms()
dormir_ms(100)
fin = ahora_ms()
log("Tardo: ", fin - inicio, " ms")
```

`ahora_ms()` retorna el timestamp UNIX en milisegundos con precisión de sistema. `dormir_ms()` suspende el hilo actual de forma cruzada (Windows: `Sleep`, POSIX: `nanosleep`).

## std.cripto

Implementación SHA-256 según FIPS 180-4, sin dependencias externas:

```synapse
importar std.cripto

hash = sha256_texto("datos a hashear")
log("SHA-256: ", hash)
// "db2c1e2c..." (64 caracteres hexadecimales)
```

El digest se retorna como `texto` (64 caracteres hex en minúsculas). La memoria del resultado es gestionada automáticamente por el RAII del compilador.

## std.http

Servidor HTTP/1.1 minimalista, síncrono, single-thread:

```synapse
importar std.http
importar std.json

fd_srv = iniciar_servidor(8080)
mientras verdadero:
    fd_cli = aceptar(fd_srv)
    peticion = leer_peticion(fd_cli)
    responder(fd_cli, 200, "application/json", "{\"status\":\"ok\"}")
```

| Función | Descripción |
|---|---|
| `iniciar_servidor(puerto)` | Crea socket de escucha en el puerto |
| `aceptar(fd_servidor)` | Bloquea hasta recibir conexión, retorna fd del cliente |
| `leer_peticion(fd_cliente)` | Lee la petición HTTP cruda |
| `responder(fd, codigo, tipo, cuerpo)` | Envía respuesta HTTP/1.1 completa y cierra conexión |
| `cerrar_cliente(fd)` | Cierra socket del cliente |
| `cerrar_servidor(fd)` | Cierra socket del servidor |

Todas las funciones que asignan recursos requieren liberación explícita mediante transferencia de ownership:

```synapse
importar std.json

nodo = desde_texto("{\"clave\": \"valor\"}")
escribir("campo: ", obtener_campo(nodo, "clave"))
liberar_nodo(-> nodo)
```
