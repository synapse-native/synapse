# Programación de Red en Syquex

Este capítulo cubre las operaciones de red en Syquex: HTTP, WebSockets, TCP/UDP y más. Aprenderás a construir clientes y servidores de red de forma moderna y eficiente.

Syquex ofrece soporte completo para redes con API asíncrona de alto rendimiento.

<!-- cumple Manual 3 §12.3 -->

## 1. HTTP Client

```syquex
importar lib.web
importar lib.json

// GET simple
let respuesta = await web.get("https://api.ejemplo.com/usuarios")
let usuarios = respuesta.cuerpo.parse_json()

// GET con headers
let resp = await web.get("https://api.ejemplo.com/datos", headers: {
    "Authorization": "Bearer token123",
    "Accept": "application/json"
})
```

### POST y otros métodos

```syquex
// POST JSON
let nuevos_datos = {"nombre": "Ana", "email": "ana@e.com"}
let resp = await web.post("https://api.ejemplo.com/usuarios", body: nuevos_datos.a_json())

// POST con form data
let form = FormData()
form.agregar("nombre", "Ana")
form.agregar("archivo", Archivo("foto.jpg"))

let resp = await web.post("https://api.ejemplo.com/upload", body: form)
```

### Client con configuración

```syquex
let cliente = web.Cliente(
    base_url: "https://api.ejemplo.com",
    timeout: 30000,  // 30 segundos
    retries: 3,
    headers: {"User-Agent": "Syquex/1.0"}
)

let resp1 = await cliente.get("/usuarios/1")
let resp2 = await cliente.put("/usuarios/1", body: {"nombre": "Ana Actualizada"})
```

## 2. WebSockets

```syquex
let ws = await web.websocket("wss://chat.ejemplo.com/ws")

// Escuchar mensajes
escuchar ws:
    let mensaje = ws.leer()
    io.escribir_linea("Recibido: " + mensaje)

// Enviar mensajes
ws.enviar("Hola desde Syquex!")

// Cerrar conexión
ws.cerrar()
```

## 3. Servidor HTTP

```syquex
importar lib.web

estructura App:
    servidor: web.Servidor

    crear(puerto: entero = 8080):
        self.servidor = web.servidor(puerto)

    metodo get(ruta: texto, handler: funcion(req: web.Request) -> web.Respuesta):
        self.servidor.get(ruta, handler)

    metodo post(ruta: texto, handler: funcion(req: web.Request) -> web.Respuesta):
        self.servidor.post(ruta, handler)

    metodo iniciar():
        self.servidor.iniciar()

// Uso
funcion principal():
    let app = App(8080)
    
    app.get("/", funcion(req):
        retornar web.respuesta(200, "¡Hola desde Syquex!")
    )
    
    app.post("/api/usuarios", funcion(req):
        let datos = req.cuerpo.parse_json()
        // Procesar crear usuario...
        retornar web.respuesta_json(201, {"id": 123, "nombre": datos.nombre})
    )
    
    app.iniciar()
```

## 4. Middleware

```syquex
// Logging middleware
funcion logging(req: web.Request, next: funcion() -> web.Respuesta) -> web.Respuesta:
    io.escribir_linea(req.metodo + " " + req.ruta)
    let inicio = reloj()
    let resp = next()
    let duracion = reloj() - inicio
    io.escribir_linea("Tiempo: " + duracion.texto() + "ms")
    retornar resp

// Aplicar middleware
app.usar(logging)
```

## 5. TCP/UDP

```syquex
importar lib.red

// Cliente TCP
let socket = await red.tcp_conectar("localhost", 8080)
await socket.enviar("PING\n")
let respuesta = await socket.recibir(1024)
io.escribir_linea("Respuesta: " + respuesta)
socket.cerrar()

// Servidor TCP
let servidor = await red.tcp_escuchar("0.0.0.0", 8080)

escuchar servidor:
    let (cliente, addr) = await servidor.aceptar()
    lanzar async:
        await cliente.enviar("Bienvenido al servidor\n")
        await cliente.cerrar()
```

### UDP

```syquex
let socket = await red.udp_crear()
await socket.enviar_a("Hola UDP", "127.0.0.1", 9090)

let (datos, origen) = await socket.recibir()
io.escribir_linea("Recibido: " + datos + " de " + origen.texto())
```

## 6. TLS/SSL

```syquex
let config_tls = red.TLSConfig(
    certificado: "cert.pem",
    llave_privada: "key.pem",
    ca: "ca.pem"
)

let socket = await red.tcp_conectar_tls("secure.ejemplo.com", 443, config_tls)
await socket.enviar("GET / HTTP/1.1\r\nHost: secure.ejemplo.com\r\n\r\n")
```

## 7. GraphQL Client

```syquex
importar lib.graphql

let cliente = graphql.Cliente("https://api.ejemplo.com/graphql")

let query = """
{
    usuarios {
        id
        nombre
        email
    }
}
"""

let resultado = await cliente.consultar(query)
para usuario en resultado.usuarios:
    io.escribir_linea(usuario.id.texto() + ": " + usuario.nombre)
```

## 8. REST API Completa

```syquex
#lang: es
importar lib.web
importar lib.json

estructura APIRest:
    app: App

    crear(puerto: entero = 8080):
        self.app = App(puerto)
        self.configurar_rutas()

    metodo configurar_rutas():
        self.app.get("/", funcion(req):
            retornar web.respuesta_json(200, {"status": "ok", "version": "1.0"})
        )

        self.app.get("/usuarios/:id", funcion(req):
            let id = req.params["id"]
            let usuario = base_de_datos.obtener_usuario(entero(id))
            retornar web.respuesta_json(200, usuario)
        )

        self.app.post("/usuarios", funcion(req):
            let datos = req.cuerpo.parse_json()
            let usuario = base_de_datos.crear_usuario(datos)
            retornar web.respuesta_json(201, usuario)
        )

    metodo iniciar():
        self.app.iniciar()

funcion principal():
    let api = APIRest(3000)
    io.escribir_linea("API iniciada en http://localhost:3000")
    api.iniciar()
```

## Referencias

- **Manual 3 §12.1**: Biblioteca estándar con módulo Web (servidor HTTP basado en fibras)
- **Manual 3 §12.3**: FFI y marshaling automático
- **Manual 5 §11**: Concurrencia y canales para redes

// cumple Manual 3 §12
