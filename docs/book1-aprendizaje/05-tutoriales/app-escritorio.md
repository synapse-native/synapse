# Tutorial: Aplicación de Escritorio (GUI) en Synapse

Este tutorial te enseñará a construir una aplicación de escritorio con interfaz gráfica en Synapse. Aprenderás a crear ventanas, manejar eventos y construir una experiencia de usuario completa.

Al finalizar, tendrás una aplicación de escritorio multiplataforma.

<!-- cumple Manual 2 §1, §8 -->

## 1. Visión General

Construiremos una aplicación de notas con interfaz gráfica:

- **Ventana principal** con menú y barra de herramientas
- **Editor de texto** con resaltado de sintaxis
- **Sistema de archivos** para guardar/cargar notas
- **Búsqueda** dentro de las notas
- **Atajos de teclado** y menú contextual

## 2. Estructura del Proyecto

```text
notas_app/
├── main.syn
├── lib/
│   ├── ventana.syn
│   ├── editor.syn
│   ├── archivo.syn
│   └── eventos.syn
└── notas/
    └── (archivos de notas)
```

## 3. Dependencias

Para GUI, Synapse se vincula con:
- **GTK 3** (Linux)
- **Win32 API** (Windows)
- **Cocoa** (macOS)

Las bindings se generan automáticamente con OpenSyn:

```bash
opensyn bindings --header gtk/gtk.h --lang synapse --output lib/gtk.syn
```

## 4. Modelo de Notas

### `lib/archivo.syn`

```synapse
#lang: es

importar lib.fs
importar lib.tiempo

estructura Nota:
    ruta: texto
    titulo: texto
    contenido: texto
    modificada: booleano = falso
    ultimo_acceso: texto

estructura GestorNotas:
    notas: Lista<Nota>
    directorio: texto
    
    crear(directorio: texto) -> Resultado<GestorNotas, texto>:
        si !fs.existe(directorio):
            fs.crear_directorio_recursivo(directorio)?
        
        retornar ok(GestorNotas(Lista<Nota>(), directorio))
    
    metodo cargar_todas() -> Resultado<nulo, texto>:
        intentar:
            let archivos = fs.listar(self.directorio)
            para archivo en archivos:
                si archivo.termina_con(".md"):
                    let contenido = fs.leer(archivo)
                    self.notas.agregar(Nota(
                        archivo,
                        archivo.nombre_base(),
                        contenido,
                        falso,
                        tiempo_actual().iso()
                    ))
            retornar ok()
        atrapar e:
            retornar err("Error al cargar: " + e)
    
    metodo crear(titulo: texto) -> Resultado<Nota, texto>:
        intentar:
            let ruta = self.directorio + "/" + titulo + ".md"
            fs.escribir(ruta, "")
            let nota = Nota(ruta, titulo, "", falso, tiempo_actual().iso())
            self.notas.agregar(nota)
            retornar ok(nota)
        atrapar e:
            retornar err("Error al crear: " + e)
    
    metodo guardar(nota: Nota) -> Resultado<nulo, texto>:
        intentar:
            fs.escribir(nota.ruta, nota.contenido)
            nota.modificada = falso
            retornar ok()
        atrapar e:
            retornar err("Error al guardar: " + e)
    
    metodo eliminar(nota: Nota) -> Resultado<nulo, texto>:
        intentar:
            fs.eliminar(nota.ruta)
            self.notas = self.notas.filtrar(lambda n: n.ruta != nota.ruta)
            retornar ok()
        atrapar e:
            retornar err("Error al eliminar: " + e)
    
    metodo buscar(termino: texto) -> Lista<Nota>:
        retornar self.notas.filtrar(lambda n:
            n.titulo.contiene(termino) o n.contenido.contiene(termino)
        )
```

## 5. Sistema de Eventos

### `lib/eventos.syn`

```synapse
#lang: es

// Eventos de la aplicación
tipo Evento =
    | NuevoArchivo
    | AbrirArchivo
    | Guardar
    | GuardarComo
    | Cerrar
    | Buscar
    | Salir
    | TextoCambiado(texto)
    | NotaSeleccionada(texto)
    | ClickBoton(texto)

estructura ManejadorEventos:
    callbacks: Mapa<texto, Lista<funcion(Evento) -> nulo>>
    
    crear():
        self.callbacks = Mapa<texto, Lista<funcion(Evento) -> nulo>>()
    
    metodo registrar(evento: texto, callback: funcion(Evento) -> nulo):
        si !self.callbacks.contiene(evento):
            self.callbacks[evento] = Lista<funcion(Evento) -> nulo>()
        self.callbacks[evento].agregar(callback)
    
    metodo emitir(evento: Evento):
        let nombre = nombre_evento(evento)
        si self.callbacks.contiene(nombre):
            para cb en self.callbacks[nombre]:
                intentar:
                    cb(evento)
                atrapar e:
                    log("Error en callback: ", e)

funcion nombre_evento(evento: Evento) -> texto:
    coincidir evento:
        caso NuevoArchivo: retornar "nuevo_archivo"
        caso AbrirArchivo: retornar "abrir_archivo"
        caso Guardar: retornar "guardar"
        caso TextoCambiado(_): retornar "texto_cambiado"
        caso _:
            // Otros eventos...
            retornar "desconocido"
```

## 6. Editor de Texto

### `lib/editor.syn`

```synapse
#lang: es

importar lib.fs

// Wrapper sobre el widget TextView de GTK
estructura EditorTexto:
    widget: gtk.TextView
    buffer: gtk.TextBuffer
    fuente: gtk.FontDescription
    nota_actual: Opcion<Nota> = ninguno
    
    crear() -> Resultado<EditorTexto, texto>:
        intentar:
            let widget = gtk.TextView.nuevo()
            let buffer = widget.obtener_buffer()
            let fuente = gtk.FontDescription.desde_string("Monospace 12")
            widget.modificar_fuente(fuente)
            widget.set_wrap_mode(gtk.WRAP_WORD)
            
            widget.set_size_request(600, 400)
            
            retornar ok(EditorTexto(widget, buffer, fuente, ninguno))
        atrapar e:
            retornar err("Error al crear editor: " + e)
    
    metodo cargar_nota(nota: Nota):
        self.nota_actual = algun(nota)
        self.buffer.set_text(nota.contenido)
    
    metodo obtener_contenido() -> texto:
        let inicio = self.buffer.obtener_inicio()
        let fin = self.buffer.obtener_fin()
        return self.buffer.obtener_texto(inicio, fin, falso)
    
    metodo resaltar_linea(linea: entero):
        let inicio = self.buffer.obtener_iter_en_linea(linea)
        let fin = self.buffer.obtener_iter_en_posicion(inicio, gtk.ITER_LINE_END)
        self.buffer.seleccionar(inicio, fin)
    
    metodo conectar_cambio(callback: funcion(texto) -> nulo):
        self.buffer.conectar("changed", lambda:
            callback(self.obtener_contenido())
        )
```

## 7. Ventana Principal

### `lib/ventana.syn`

```synapse
#lang: es

importar lib.fs
importar lib.archivo
importar lib.editor
importar lib.eventos

estructura VentanaPrincipal:
    ventana: gtk.Window
    gestor: GestorNotas
    editor: EditorTexto
    lista_notas: gtk.ListBox
    buscador: gtk.SearchEntry
    eventos: ManejadorEventos
    
    crear(titulo: texto, gestor: GestorNotas) -> Resultado<VentanaPrincipal, texto>:
        intentar:
            let ventana = gtk.Window.nuevo(gtk.WINDOW_TOPLEVEL)
            ventana.set_title(titulo)
            ventana.set_default_size(900, 600)
            ventana.conectar("destroy", lambda: gtk.main_quit())
            
            // Layout principal
            let grid = gtk.Grid.nuevo()
            grid.set_row_spacing(5)
            grid.set_column_spacing(5)
            grid.set_border_width(10)
            
            // Panel lateral (lista de notas)
            let panel_lateral = gtk.Box.nuevo(gtk.ORIENTATION_VERTICAL, 5)
            panel_lateral.set_size_request(200, -1)
            
            self.buscador = gtk.SearchEntry.nuevo()
            self.buscador.set_placeholder_text("Buscar notas...")
            
            self.lista_notas = gtk.ListBox.nuevo()
            self.lista_notas.set_selection_mode(gtk.SELECTION_SINGLE)
            
            let scroll_lateral = gtk.ScrolledWindow.nuevo()
            scroll_lateral.agregar(self.lista_notas)
            scroll_lateral.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
            
            panel_lateral.agregar(self.buscador)
            panel_lateral.agregar(scroll_lateral)
            
            // Editor
            self.editor = EditorTexto.crear()?
            let scroll_editor = gtk.ScrolledWindow.nuevo()
            scroll_editor.agregar(self.editor.widget)
            scroll_editor.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
            
            // Menú
            let menu = crear_menu(self)
            
            // Layout
            grid.agregar(panel_lateral, 0, 0, 1, 1)
            grid.agregar(scroll_editor, 1, 0, 1, 1)
            grid.agregar(menu, 0, 1, 2, 1)
            
            ventana.agregar(grid)
            ventana.mostrar_todos()
            
            retornar ok(VentanaPrincipal(ventana, gestor, self.editor, self.lista_notas, self.buscador, self.eventos))
        atrapar e:
            retornar err("Error al crear ventana: " + e)
    
    metodo actualizar_lista_notas():
        // Limpiar lista
        self.lista_notas.para_todo_hijo(lambda widget: widget.destruir())
        
        // Agregar notas
        para nota en self.gestor.notas:
            let label = gtk.Label.nuevo(nota.titulo)
            self.lista_notas.agregar(label)
    
    metodo mostrar():
        self.ventana.mostrar_todos()

funcion crear_menu(ventana: VentanaPrincipal) -> gtk.MenuBar:
    let menu_bar = gtk.MenuBar.nuevo()
    
    // Menú Archivo
    let menu_archivo = gtk.Menu.nuevo()
    let item_archivo = gtk.MenuItem.nuevo("Archivo")
    item_archivo.set_submenu(menu_archiva)
    
    let item_nuevo = gtk.MenuItem.nuevo("Nuevo")
    item_nuevo.conectar("activate", lambda: ventana.eventos.emitir(NuevoArchivo))
    menu_archivo.agregar(item_nuevo)
    
    let item_abrir = gtk.MenuItem.nuevo("Abrir...")
    item_abrir.conectar("activate", lambda: ventana.eventos.emitir(AbrirArchivo))
    menu_archivo.agregar(item_abrir)
    
    let item_guardar = gtk.MenuItem.nuevo("Guardar")
    item_guardar.conectar("activate", lambda: ventana.eventos.emitir(Guardar))
    menu_archivo.agregar(item_guardar)
    
    menu_archivo.agregar(gtk.SeparatorMenuItem.nuevo())
    
    let item_salir = gtk.MenuItem.nuevo("Salir")
    item_salir.conectar("activate", lambda: gtk.main_quit())
    menu_archivo.agregar(item_salir)
    
    menu_bar.agregar(item_archivo)
    
    // Menú Editar
    let menu_editar = gtk.Menu.nuevo()
    let item_editar = gtk.MenuItem.nuevo("Editar")
    item_editar.set_submenu(menu_editar)
    
    let item_buscar = gtk.MenuItem.nuevo("Buscar")
    item_buscar.conectar("activate", lambda: ventana.buscador.grab_focus())
    menu_editar.agregar(item_buscar)
    
    menu_bar.agregar(item_editar)
    
    retornar menu_bar
```

## 8. Programa Principal

### `main.syn`

```synapse
#lang: es

importar lib.gtk
importar lib.ventana
importar lib.eventos
importar lib.archivo

funcion principal() -> Resultado<nulo, texto>:
    gtk.init()?
    
    let gestor = GestorNotas.crear("notas")?
    gestor.cargar_todas()?
    
    let ventana = VentanaPrincipal.crear("Notas App", gestor)?
    
    // Registrar manejadores de eventos
    ventana.eventos.registrar("nuevo_archivo", lambda evento:
        let titulo = ventana.pedir_input("Nueva nota", "Título:")
        si titulo != "":
            let nota = gestor.crear(titulo)?
            ventana.actualizar_lista_notas()
            ventana.editor.cargar_nota(nota)
    )
    
    ventana.eventos.registrar("guardar", lambda evento:
        si ventana.editor.nota_actual.es_algun():
            let nota = ventana.editor.nota_actual.desenvolver()
            nota.contenido = ventana.editor.obtener_contenido()
            gestor.guardar(nota)?
            ventana.mostrar_mensaje("Nota guardada")
    )
    
    ventana.eventos.registrar("texto_cambiado", lambda evento:
        // Marcar como modificada
        si ventana.editor.nota_actual.es_algun():
            ventana.editor.nota_actual.desenvolver().modificada = verdadero
            ventana.actualizar_titulo()
    )
    
    // Conectar buscador
    ventana.buscador.conectar("search-changed", lambda:
        let termino = ventana.buscador.get_text()
        ventana.filtrar_notas(termino)
    )
    
    // Conectar lista de notas
    ventana.lista_notas.conectar("row-activated", lambda widget, fila:
        let nota = gestor.notas[fila.get_index()]
        ventana.editor.cargar_nota(nota)
    )
    
    // Conectar cambio en editor
    ventana.editor.conectar_cambio(lambda contenido:
        ventana.eventos.emitir(TextoCambiado(contenido))
    )
    
    ventana.mostrar()
    gtk.main()
    
    retornar ok()
```

## 9. Compilar y Ejecutar

```bash
# Generar bindings de GTK
opensyn bindings --header gtk/gtk.h --output lib/gtk.syn

# Compilar la aplicación
python main.py main.syn -o notas_app.exe

# Ejecutar
./notas_app.exe
```

## 10. Capturas de Pantalla Esperadas

La aplicación mostrará:
- **Panel izquierdo:** lista de notas existentes
- **Panel derecho:** editor de texto
- **Menú superior:** Archivo, Editar, Ver, Ayuda
- **Barra de búsqueda:** en la parte superior del panel lateral

## 11. Mejoras Posibles

1. **Resaltado de sintaxis** Markdown
2. **Vista previa** de Markdown renderizado
3. **Sistema de tags** y categorías
4. **Sincronización** con servicios en la nube
5. **Exportar** a PDF/HTML
6. **Búsqueda full-text** con indexación
7. **Atajos de teclado** personalizables
8. **Temas oscuros/claros**

## 12. Conceptos Aprendidos

- **FFI a GTK** (librería C)
- **Sistema de eventos** con callbacks
- **Gestión de memoria** automática (arena por ventana)
- **Widgets** y layout en GTK
- **Patrón MVC** (Modelo-Vista-Controlador)
- **Composición** de UI components

## Referencias

- **Manual 2 §9**: FFI e integración con C
- **Manual 2 §1**: Sintaxis de Synapse
- **Manual 2 §6**: Contratos `requiere`/`garantiza`
- **Manual 4 §6**: Arenas de componente (para UI)
- **Manual 7 §5.2**: Generación de bindings C → Synapse

// cumple Manual 2 §9
