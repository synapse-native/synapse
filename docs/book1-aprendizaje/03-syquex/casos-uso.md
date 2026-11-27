# Casos de Uso de Syquex

Syquex está diseñado para ser versátil, con especial énfasis en la **concurrencia** y el **manejo eficiente de E/S**. Este capítulo explora los escenarios donde Syquex brilla.

<!-- cumple Manual 3 §2.47 -->

## 1. Servicios Web y APIs

Syquex incluye un servidor HTTP integrado en la biblioteca estándar (`lib/web.syq`) que maneja cada conexión en una fibra separada:

```syquex
importar lib.web

servidor = web.servidor(8080)
servidor.get("/api/usuarios", funcion(req):
    retornar web.respuesta(200, "[]")
)
servidor.iniciar()
```

**Ventajas sobre Python:**
- Sin GIL (Global Interpreter Lock)
- Concurrencia a nivel de sistema operativo
- Compilado a binario nativo sin dependencias

## 2. Scripting y Automatización

La sintaxis similar a Python hace a Syquex ideal para scripts de automatización:

```syquex
importar lib.io
importar lib.fs

// Listar archivos modificados recientemente
para archivo en fs.listar("."):
    si fs.tamaño(archivo) > 1024 * 1024:
        io.escribir_linea("Archivo grande: " + archivo)
```

## 3. Procesamiento de Datos en Tiempo Real

Las listas con operaciones funcionales (`map`, `filter`, `reduce`) permiten procesar datos eficientemente:

```syquex
importar lib.lista

datos = Lista<decimal>.desde_csv("ventas.csv")
filtrados = datos.filtrar(lambda x: x > 100.0)
promedio = filtrados.promedio()
io.escribir_linea("Promedio de ventas > $100: " + promedio.texto())
```

## 4. Integración con Otros Sistemas

Syquex puede interoperar con:
- **C**: mediante `externo` (FFI automático)
- **Python**: mediante `@export(python)`
- **JavaScript/TypeScript**: mediante WASM y `@export(typescript)`
- **Java**: mediante bindings generados

```syquex
externo funcion strlen(s: &texto) -> entero
// El compilador maneja el marshaling automáticamente
```

## 5. Aplicaciones de Escritorio

Aunque aún en desarrollo (ver `docs/book1-aprendizaje/05-tutoriales/app-escritorio.md`), Syquex planea soportar GUI nativas a través de arenas de componente y binding a GTK/Qt.

## 6. Pruebas Unitarias

La biblioteca `lib/pruebas.syq` ofrece un framework de testing similar a Python's unittest:

```syquex
importar lib.pruebas

estructura TestCalculadora:
    metodo probar_suma():
        pruebas.afirmar(2 + 2 == 4)

pruebas.ejecutar()
```

## Selección de Lenguaje

| Necesidad | Lenguaje recomendado |
|-----------|---------------------|
| Control fino de memoria | Synapse |
| Productividad rápida | Syquex |
| Bare metal / embebido | Synapse |
| APIs y web services | Syquex |
| Alto rendimiento numérico | Synapse |
| Scripting y automatización | Syquex |
| Interfaz gráfica | Syquex (futuro) |
| Kernels / drivers | Synapse |

## Referencias

- **Manual 3 §2**: Filosofía de Syquex vs Synapse
- **Manual 3 §12**: Biblioteca estándar y módulos disponibles
- **Manual 3 §14**: Ejemplo completo de programa

// cumple Manual 3 §2
