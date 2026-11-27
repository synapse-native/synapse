# Tutorial: CLI de Gestión de Tareas en Syquex

Este tutorial guía la creación de una herramienta de línea de comandos para gestionar tareas en Syquex. Aprenderás a parsear argumentos, persistir datos y crear una interfaz de usuario en terminal.

Al finalizar, tendrás un CLI completo para organizar tus tareas diarias.

<!-- cumple Manual 3 §7, §12 -->

## 1. Visión General

Construiremos un CLI (Command Line Interface) para gestionar tareas con:

- **Comandos:** add, list, complete, delete, update
- **Persistencia en JSON** (sin base de datos)
- **Colores en la terminal** para mejor UX
- **Argumentos de línea de comandos** con `lib.cli`

## 2. Estructura del Proyecto

```text
cli_tareas/
├── main.syq
├── lib/
│   ├── tareas.syq
│   ├── storage.syq
│   └── cli.syq
└── tareas.json
```

## 3. Modelo de Tareas

### `lib/tareas.syq`

```syquex
#lang: es

importar lib.io
importar lib.tiempo

estructura Tarea:
    id: entero
    titulo: texto
    descripcion: texto = ""
    completada: booleano = falso
    creada_en: texto
    completada_en: texto = ""

estructura GestorTareas:
    tareas: Lista<Tarea>
    proximo_id: entero = 1
    
    crear():
        self.tareas = Lista<Tarea>()
    
    metodo agregar(titulo: texto, descripcion: texto = "") -> Tarea:
        let tarea = Tarea(
            self.proximo_id,
            titulo,
            descripcion,
            falso,
            tiempo_actual().iso(),
            ""
        )
        self.tareas.agregar(tarea)
        self.proximo_id = self.proximo_id + 1
        retornar tarea
    
    metodo listar(solo_pendientes: booleano = falso) -> Lista<Tarea>:
        si solo_pendientes:
            retornar self.tareas.filtrar(lambda t: !t.completada)
        retornar self.tareas
    
    metodo completar(id: entero) -> Resultado<Tarea, texto>:
        para i = 0 mientras i < self.tareas.len():
            si self.tareas[i].id == id:
                let tarea = self.tareas[i]
                tarea.completada = verdadero
                tarea.completada_en = tiempo_actual().iso()
                retornar ok(tarea)
        retornar err("Tarea no encontrada: " + id.texto())
    
    metodo eliminar(id: entero) -> Resultado<booleano, texto>:
        para i = 0 mientras i < self.tareas.len():
            si self.tareas[i].id == id:
                self.tareas.eliminar(i)
                retornar ok(verdadero)
        retornar err("Tarea no encontrada: " + id.texto())
    
    metodo actualizar(id: entero, titulo: texto, descripcion: texto) -> Resultado<Tarea, texto>:
        para i = 0 mientras i < self.tareas.len():
            si self.tareas[i].id == id:
                let tarea = self.tareas[i]
                tarea.titulo = titulo
                tarea.descripcion = descripcion
                retornar ok(tarea)
        retornar err("Tarea no encontrada: " + id.texto())
```

## 4. Persistencia en JSON

### `lib/storage.syq`

```syquex
#lang: es

importar lib.fs
importar lib.tareas

constante ARCHIVO_TAREAS = "tareas.json"

funcion cargar() -> GestorTareas:
    let gestor = GestorTareas()
    
    si !fs.existe(ARCHIVO_TAREAS):
        retornar gestor
    
    intentar:
        let contenido = fs.leer(ARCHIVO_TAREAS)
        let datos = contenido.parse_json()
        
        para tarea_data en datos.tareas:
            gestor.tareas.agregar(Tarea(
                tarea_data.id,
                tarea_data.titulo,
                tarea_data.descripcion o "",
                tarea_data.completada,
                tarea_data.creada_en,
                tarea_data.completada_en o ""
            ))
        gestor.proximo_id = datos.proximo_id o 1
    atrapar e:
        io.escribir_linea("Error al cargar tareas: " + e)
    
    retornar gestor

funcion guardar(gestor: GestorTareas) -> Resultado<booleano, texto>:
    let datos = {
        "tareas": gestor.tareas,
        "proximo_id": gestor.proximo_id
    }
    intentar:
        fs.escribir(ARCHIVO_TAREAS, datos.a_json(pretty: verdadero))
        retornar ok(verdadero)
    atrapar e:
        retornar err("Error al guardar: " + e)
```

## 5. Interfaz de Línea de Comandos

### `lib/cli.syq`

```syquex
#lang: es

importar lib.io
importar lib.cli
importar lib.tareas
importar lib.storage

// Códigos de color ANSI
constante COLOR_VERDE = "\u001b[32m"
constante COLOR_ROJO = "\u001b[31m"
constante COLOR_AMARILLO = "\u001b[33m"
constante COLOR_AZUL = "\u001b[34m"
constante COLOR_RESET = "\u001b[0m"
constante NEGRITA = "\u001b[1m"

funcion imprimir_tarea(tarea: Tarea):
    let estado = si tarea.completada:
        COLOR_VERDE + "✓ Completada" + COLOR_RESET
    sino:
        COLOR_AMARILLO + "○ Pendiente" + COLOR_RESET
    
    io.escribir_linea(
        NEGRITA + "[" + tarea.id.texto() + "]" + COLOR_RESET + " " +
        tarea.titulo + " - " + estado
    )
    si tarea.descripcion != "":
        io.escribir_linea("  " + tarea.descripcion)

funcion comando_agregar(args: Lista<texto>) -> Resultado<booleano, texto>:
    si args.len() < 1:
        retornar err("Uso: add <título> [descripción]")
    
    let titulo = args[0]
    let descripcion = si args.len() > 1: args[1] sino: ""
    
    let gestor = cargar()
    let tarea = gestor.agregar(titulo, descripcion)
    guardar(gestor)?
    
    io.escribir_linea(COLOR_VERDE + "✓ Tarea agregada:" + COLOR_RESET)
    imprimir_tarea(tarea)
    retornar ok(verdadero)

funcion comando_listar(args: Lista<texto>) -> Resultado<booleano, texto>:
    let solo_pendientes = args.contiene("--pending")
    let gestor = cargar()
    let tareas = gestor.listar(solo_pendientes)
    
    si tareas.vacio():
        io.escribir_linea("No hay tareas" + (si solo_pendientes: " pendientes" sino: ""))
        retornar ok(verdadero)
    
    io.escribir_linea(NEGRITA + "=== Tareas ===" + COLOR_RESET)
    para tarea en tareas:
        imprimir_tarea(tarea)
    io.escribir_linea("\nTotal: " + tareas.len().texto() + " tareas")
    retornar ok(verdadero)

funcion comando_completar(args: Lista<texto>) -> Resultado<booleano, texto>:
    si args.len() < 1:
        retornar err("Uso: complete <id>")
    
    let id = entero(args[0])
    let gestor = cargar()
    let resultado = gestor.completar(id)
    
    coincidir resultado:
        caso ok(tarea):
            guardar(gestor)?
            io.escribir_linea(COLOR_VERDE + "✓ Tarea completada:" + COLOR_RESET)
            imprimir_tarea(tarea)
        caso err(e):
            io.escribir_linea(COLOR_ROJO + "✗ " + e + COLOR_RESET)
    
    retornar ok(verdadero)

funcion comando_eliminar(args: Lista<texto>) -> Resultado<booleano, texto>:
    si args.len() < 1:
        retornar err("Uso: delete <id>")
    
    let id = entero(args[0])
    let gestor = cargar()
    let resultado = gestor.eliminar(id)
    
    coincidir resultado:
        caso ok(_):
            guardar(gestor)?
            io.escribir_linea(COLOR_VERDE + "✓ Tarea eliminada" + COLOR_RESET)
        caso err(e):
            io.escribir_linea(COLOR_ROJO + "✗ " + e + COLOR_RESET)
    
    retornar ok(verdadero)

funcion comando_ayuda(args: Lista<texto>) -> Resultado<booleano, texto>:
    io.escribir_linea(NEGRITA + "CLI de Gestión de Tareas" + COLOR_RESET)
    io.escribir_linea("\nComandos disponibles:")
    io.escribir_linea("  " + COLOR_AZUL + "add" + COLOR_RESET + " <título> [descripción]  - Agregar nueva tarea")
    io.escribir_linea("  " + COLOR_AZUL + "list" + COLOR_RESET + " [--pending]              - Listar tareas")
    io.escribir_linea("  " + COLOR_AZUL + "complete" + COLOR_RESET + " <id>                     - Marcar como completada")
    io.escribir_linea("  " + COLOR_AZUL + "delete" + COLOR_RESET + " <id>                     - Eliminar tarea")
    io.escribir_linea("  " + COLOR_AZUL + "update" + COLOR_RESET + " <id> <título> [desc]     - Actualizar tarea")
    io.escribir_linea("  " + COLOR_AZUL + "help" + COLOR_RESET + "                            - Mostrar esta ayuda")
    retornar ok(verdadero)
```

## 6. Punto de Entrada

### `main.syq`

```syquex
#lang: es

importar lib.cli
importar lib.tareas
importar lib.io

funcion principal() -> entero:
    let args = sistema.argv()
    
    si args.len() < 2:
        cli.comando_ayuda(Lista<texto>())
        retornar 0
    
    let comando = args[1]
    let argumentos = Lista<texto>()
    para i = 2 mientras i < args.len():
        argumentos.agregar(args[i])
    
    let resultado = coincidir comando:
        caso "add": cli.comando_agregar(argumentos)
        caso "list": cli.comando_listar(argumentos)
        caso "complete": cli.comando_completar(argumentos)
        caso "delete": cli.comando_eliminar(argumentos)
        caso "help": cli.comando_ayuda(argumentos)
        caso _: retornar err("Comando desconocido: " + comando)
    
    coincidir resultado:
        caso ok(_): retornar 0
        caso err(e):
            io.escribir_linea(cli.COLOR_ROJO + "Error: " + e + cli.COLOR_RESET)
            retornar 1
```

## 7. Compilar y Usar

```bash
# Compilar
python main.py main.syq -o tareas_cli.exe

# Uso
./tareas_cli.exe help
./tareas_cli.exe add "Comprar leche"
./tareas_cli.exe add "Estudiar Syquex" "Manual 3"
./tareas_cli.exe list
./tareas_cli.exe complete 1
./tareas_cli.exe list --pending
./tareas_cli.exe delete 1
```

### Sesión de Ejemplo

```text
$ tareas_cli help
CLI de Gestión de Tareas

Comandos disponibles:
  add <título> [descripción]  - Agregar nueva tarea
  list [--pending]              - Listar tareas
  complete <id>                     - Marcar como completada
  delete <id>                     - Eliminar tarea
  ...

$ tareas_cli add "Comprar leche" "Leche descremada"
✓ Tarea agregada:
[1] Comprar leche - ○ Pendiente
  Leche descremada

$ tareas_cli list
=== Tareas ===
[1] Comprar leche - ○ Pendiente
  Leche descremada

Total: 1 tareas

$ tareas_cli complete 1
✓ Tarea completada:
[1] Comprar leche - ✓ Completada
```

## 8. Mejoras Posibles

1. **Categorías y prioridades**
2. **Fechas de vencimiento** con recordatorios
3. **Exportar/importar** en diferentes formatos
4. **Modo interactivo** con prompts
5. **Configuración de usuario** en archivo YAML

## 9. Conceptos Aprendidos

- **Argumentos CLI** y parsing básico
- **Persistencia en JSON** sin base de datos
- **Colores ANSI** en terminal
- **Estructuras con métodos** (OOP)
- **Patrón Resultado** para errores

## Referencias

- **Manual 3 §5.2**: Tipos de colecciones (`Lista`)
- **Manual 3 §6**: Estructuras y métodos
- **Manual 3 §7**: Manejo de errores
- **Manual 3 §12**: Biblioteca estándar (`lib.io`, `lib.fs`, `lib.cli`)

// cumple Manual 3 §12
