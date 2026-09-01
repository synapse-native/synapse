# Tutorial: API REST con Base de Datos en Syquex

Este tutorial te enseñará a construir una API REST completa en Syquex. Aprenderás a crear endpoints, manejar requests/responses, conectar a una base de datos y implementar autenticación.

Al finalizar, tendrás una API funcional lista para producción.

<!-- cumple Manual 3 §8, §12 -->

## 1. Visión General del Proyecto

Construiremos una API REST para gestión de tareas (TODO list) con:

- **Endpoints CRUD:** GET, POST, PUT, DELETE
- **Base de datos SQLite** para persistencia
- **Autenticación JWT** para endpoints protegidos
- **Manejo de errores** consistente
- **Validación de entrada**

## 2. Estructura del Proyecto

```text
api_tareas/
├── main.syq
├── lib/
│   ├── db.syq
│   ├── auth.syq
│   ├── handlers/
│   │   ├── usuarios.syq
│   │   └── tareas.syq
│   └── modelos.syq
├── tests/
└── README.md
```

## 3. Definir Modelos de Datos

### `lib/modelos.syq`

```syquex
#lang: es

estructura Usuario:
    id: entero
    nombre: texto
    email: texto
    password_hash: texto
    creado_en: texto

estructura Tarea:
    id: entero
    usuario_id: entero
    titulo: texto
    descripcion: texto
    completada: booleano = falso
    creado_en: texto

estructura LoginRequest:
    email: texto
    password: texto

estructura RegistroRequest:
    nombre: texto
    email: texto
    password: texto

estructura CrearTareaRequest:
    titulo: texto
    descripcion: texto

estructura ActualizarTareaRequest:
    titulo: texto
    descripcion: texto
    completada: booleano
```

## 4. Capa de Base de Datos

### `lib/db.syq`

```syquex
#lang: es

importar lib.modelos

estructura BaseDeDatos:
    conexion: db.Conexion
    
    crear(ruta: texto) -> Resultado<BaseDeDatos, texto>:
        let conexion = db.conectar(ruta)?
        db.ejecutar(conexion, """
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                creado_en TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)?
        db.ejecutar(conexion, """
            CREATE TABLE IF NOT EXISTS tareas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER NOT NULL,
                titulo TEXT NOT NULL,
                descripcion TEXT,
                completada BOOLEAN DEFAULT 0,
                creado_en TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
            )
        """)?
        retornar ok(BaseDeDatos(conexion))
    
    metodo registrar_usuario(req: RegistroRequest) -> Resultado<Usuario, texto>:
        si !validar_email(req.email):
            retornar err("Email inválido")
        
        si req.password.len() < 8:
            retornar err("La contraseña debe tener al menos 8 caracteres")
        
        let hash = auth.hash_password(req.password)?
        
        intentar:
            db.ejecutar(self.conexion,
                "INSERT INTO usuarios (nombre, email, password_hash) VALUES (?, ?, ?)",
                [req.nombre, req.email, hash])?
            let id = db.ultimo_id(self.conexion)?
            retornar ok(Usuario(id, req.nombre, req.email, hash, tiempo_actual().iso()))
        atrapar e:
            retornar err("Error al registrar: " + e)
    
    metodo login(req: LoginRequest) -> Resultado<Usuario, texto>:
        let resultado = db.consultar(self.conexion,
            "SELECT id, nombre, email, password_hash, creado_en FROM usuarios WHERE email = ?",
            [req.email])?
        
        si resultado.len() == 0:
            retornar err("Usuario no encontrado")
        
        let fila = resultado[0]
        si !auth.verificar_password(req.password, fila.password_hash):
            retornar err("Contraseña incorrecta")
        
        retornar ok(Usuario(fila.id, fila.nombre, fila.email, fila.password_hash, fila.creado_en))
    
    metodo crear_tarea(usuario_id: entero, req: CrearTareaRequest) -> Resultado<Tarea, texto>:
        intentar:
            db.ejecutar(self.conexion,
                "INSERT INTO tareas (usuario_id, titulo, descripcion) VALUES (?, ?, ?)",
                [usuario_id, req.titulo, req.descripcion])?
            let id = db.ultimo_id(self.conexion)?
            retornar ok(Tarea(id, usuario_id, req.titulo, req.descripcion, falso, tiempo_actual().iso()))
        atrapar e:
            retornar err("Error al crear tarea: " + e)
    
    metodo listar_tareas(usuario_id: entero) -> Resultado<Lista<Tarea>, texto>:
        intentar:
            let filas = db.consultar(self.conexion,
                "SELECT id, usuario_id, titulo, descripcion, completada, creado_en FROM tareas WHERE usuario_id = ?",
                [usuario_id])?
            let tareas = Lista<Tarea>()
            para fila en filas:
                tareas.agregar(Tarea(
                    fila.id, fila.usuario_id, fila.titulo,
                    fila.descripcion, fila.completada == 1,
                    fila.creado_en
                ))
            retornar ok(tareas)
        atrapar e:
            retornar err("Error al listar: " + e)
    
    metodo actualizar_tarea(id: entero, usuario_id: entero, req: ActualizarTareaRequest) -> Resultado<Tarea, texto>:
        intentar:
            db.ejecutar(self.conexion,
                "UPDATE tareas SET titulo = ?, descripcion = ?, completada = ? WHERE id = ? AND usuario_id = ?",
                [req.titulo, req.descripcion, req.completada, id, usuario_id])?
            retornar ok(Tarea(id, usuario_id, req.titulo, req.descripcion, req.completada, tiempo_actual().iso()))
        atrapar e:
            retornar err("Error al actualizar: " + e)
    
    metodo eliminar_tarea(id: entero, usuario_id: entero) -> Resultado<booleano, texto>:
        intentar:
            db.ejecutar(self.conexion,
                "DELETE FROM tareas WHERE id = ? AND usuario_id = ?",
                [id, usuario_id])?
            retornar ok(verdadero)
        atrapar e:
            retornar err("Error al eliminar: " + e)
```

## 5. Autenticación con JWT

### `lib/auth.syq`

```syquex
#lang: es

importar lib.modelos

constante JWT_SECRET = sistema.env("JWT_SECRET") o "cambiar-en-produccion"

funcion hash_password(password: texto) -> Resultado<texto, texto>:
    // Usar bcrypt o argon2
    retornar cripto.hash_bcrypt(password)

funcion verificar_password(password: texto, hash: texto) -> booleano:
    retornar cripto.verificar_bcrypt(password, hash)

funcion generar_token(usuario: Usuario) -> Resultado<texto, texto>:
    let payload = {
        "sub": usuario.id,
        "email": usuario.email,
        "exp": tiempo_actual().timestamp() + 86400  // 24 horas
    }
    retornar cripto.jwt_firmar(payload, JWT_SECRET)

funcion verificar_token(token: texto) -> Resultado<entero, texto>:
    let payload = cripto.jwt_verificar(token, JWT_SECRET)?
    retornar ok(payload["sub"])
```

## 6. Handlers de Endpoints

### `lib/handlers/usuarios.syq`

```syquex
#lang: es

importar lib.web
importar lib.db
importar lib.auth
importar lib.modelos

funcion manejar_registro(db: BaseDeDatos, req: web.Request) -> web.Response:
    let body = req.cuerpo.parse_json()?
    let registro = RegistroRequest(body.nombre, body.email, body.password)
    
    let resultado = db.registrar_usuario(registro)
    coincidir resultado:
        caso ok(usuario):
            let token = auth.generar_token(usuario)?
            retornar web.respuesta_json(201, {
                "usuario": usuario,
                "token": token
            })
        caso err(e):
            retornar web.respuesta_json(400, {"error": e})

funcion manejar_login(db: BaseDeDatos, req: web.Request) -> web.Response:
    let body = req.cuerpo.parse_json()?
    let login = LoginRequest(body.email, body.password)
    
    let resultado = db.login(login)
    coincidir resultado:
        caso ok(usuario):
            let token = auth.generar_token(usuario)?
            retornar web.respuesta_json(200, {
                "usuario": usuario,
                "token": token
            })
        caso err(e):
            retornar web.respuesta_json(401, {"error": e})
```

### `lib/handlers/tareas.syq`

```syquex
#lang: es

importar lib.web
importar lib.db
importar lib.auth
importar lib.modelos

funcion manejar_crear_tarea(db: BaseDeDatos, req: web.Request) -> web.Response:
    let usuario_id = auth.verificar_token(req.headers["Authorization"])?
    let body = req.cuerpo.parse_json()?
    let crear = CrearTareaRequest(body.titulo, body.descripcion)
    
    let resultado = db.crear_tarea(usuario_id, crear)
    coincidir resultado:
        caso ok(tarea):
            retornar web.respuesta_json(201, tarea)
        caso err(e):
            retornar web.respuesta_json(400, {"error": e})

funcion manejar_listar_tareas(db: BaseDeDatos, req: web.Request) -> web.Response:
    let usuario_id = auth.verificar_token(req.headers["Authorization"])?
    
    let resultado = db.listar_tareas(usuario_id)
    coincidir resultado:
        caso ok(tareas):
            retornar web.respuesta_json(200, tareas)
        caso err(e):
            retornar web.respuesta_json(500, {"error": e})

funcion manejar_actualizar_tarea(db: BaseDeDatos, req: web.Request) -> web.Response:
    let usuario_id = auth.verificar_token(req.headers["Authorization"])?
    let id = entero(req.params["id"])
    let body = req.cuerpo.parse_json()?
    let actualizar = ActualizarTareaRequest(body.titulo, body.descripcion, body.completada)
    
    let resultado = db.actualizar_tarea(id, usuario_id, actualizar)
    coincidir resultado:
        caso ok(tarea):
            retornar web.respuesta_json(200, tarea)
        caso err(e):
            retornar web.respuesta_json(400, {"error": e})

funcion manejar_eliminar_tarea(db: BaseDeDatos, req: web.Request) -> web.Response:
    let usuario_id = auth.verificar_token(req.headers["Authorization"])?
    let id = entero(req.params["id"])
    
    let resultado = db.eliminar_tarea(id, usuario_id)
    coincidir resultado:
        caso ok(_):
            retornar web.respuesta_json(204, {})
        caso err(e):
            retornar web.respuesta_json(400, {"error": e})
```

## 7. Servidor Principal

### `main.syq`

```syquex
#lang: es

importar lib.web
importar lib.db
importar lib.handlers.usuarios
importar lib.handlers.tareas

funcion principal() -> Resultado<nulo, texto>:
    let db = BaseDeDatos.crear("tareas.db")?
    let app = web.App(8080)
    
    // Endpoints públicos
    app.post("/api/registro", funcion(req): retornar usuarios.manejar_registro(db, req))
    app.post("/api/login", funcion(req): retornar usuarios.manejar_login(db, req))
    
    // Endpoints protegidos (requieren JWT)
    app.post("/api/tareas", funcion(req): retornar tareas.manejar_crear_tarea(db, req))
    app.get("/api/tareas", funcion(req): retornar tareas.manejar_listar_tareas(db, req))
    app.put("/api/tareas/:id", funcion(req): retornar tareas.manejar_actualizar_tarea(db, req))
    app.delete("/api/tareas/:id", funcion(req): retornar tareas.manejar_eliminar_tarea(db, req))
    
    io.escribir_linea("🚀 API iniciada en http://localhost:8080")
    app.iniciar()
    retornar ok()
```

## 8. Probar la API

```bash
# Registrar usuario
curl -X POST http://localhost:8080/api/registro \
  -H "Content-Type: application/json" \
  -d '{"nombre": "Ana", "email": "ana@test.com", "password": "secreto123"}'

# Login
TOKEN=$(curl -X POST http://localhost:8080/api/login \
  -H "Content-Type: application/json" \
  -d '{"email": "ana@test.com", "password": "secreto123"}' | jq -r '.token')

# Crear tarea
curl -X POST http://localhost:8080/api/tareas \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"titulo": "Comprar leche", "descripcion": "Leche descremada"}'

# Listar tareas
curl -H "Authorization: Bearer $TOKEN" http://localhost:8080/api/tareas
```

## 9. Conceptos Aprendidos

- **Arquitectura en capas:** modelos, db, auth, handlers
- **Endpoints RESTful:** GET, POST, PUT, DELETE
- **Autenticación JWT** con bearer tokens
- **Validación de entrada** y manejo de errores
- **SQL preparado** para prevenir inyecciones
- **FFI a SQLite** (Manual 3 §9)

## Referencias

- **Manual 3 §8**: Concurrencia y comunicación
- **Manual 3 §9**: FFI e integración con C
- **Manual 3 §12**: Biblioteca estándar (`lib.web`, `lib.db`)
- **Manual 3 §10**: Exportación y bindings

// cumple Manual 3 §12
