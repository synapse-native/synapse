# Logging en Syquex

Este capítulo cubre el registro de eventos (logging) en Syquex. Aprenderás a configurar y usar diferentes niveles de log, formatos y destinos para monitorear tu aplicación.

El logging es fundamental para el diagnóstico y mantenimiento de sistemas en producción.

<!-- cumple Manual 3 §12.2 -->

## 1. Niveles de Log

Syquex proporciona 5 niveles de logging estándar:

| Nivel | Uso | Ejemplo |
|-------|-----|---------|
| `DEBUG` | Información detallada para desarrollo | Variables internas, estado de objetos |
| `INFO` | Mensajes informativos generales | Inicio de servicios, operaciones completadas |
| `ADVERTENCIA` (WARN) | Situaciones inesperadas pero no fatales | Valores inusuales, deprecated |
| `ERROR` | Errores que afectan funcionalidad | Fallos de operación, excepciones |
| `CRÍTICO` (CRITICAL) | Errores que amenazan la estabilidad | Caída del sistema, pérdida de datos |

```syquex
importar lib.logging

let logger = logging.logger("mi_app")

logger.debug("Estado interno: " + estado.texto())
logger.info("Usuario autenticado: " + usuario.nombre)
logger.advertencia("Memoria baja: " + memoria_restante.texto() + "MB")
logger.error("Falló la conexión: " + e)
logger.critico("¡Pánico del sistema! Reiniciando...")
```

## 2. Configuración de Handlers

### Console Handler (consola)

```syquex
logging.configurar({
    handlers: [
        logging.handler_consola(
            nivel: logging.INFO,
            formato: "%(timestamp)s [%(nivel)s] %(mensaje)s"
        )
    ]
})
```

### File Handler (archivo)

```syquex
let file_handler = logging.handler_archivo(
    ruta: "app.log",
    nivel: logging.DEBUG,
    formato: "%(timestamp)s | %(nivel)s | %(modulo)s | %(mensaje)s",
    rotacion: "10MB",     // Rotar cada 10MB
    copias: 5             // Mantener 5 archivos
)
```

### Network Handler (red)

```syquex
let remote_handler = logging.handler_remota(
    host: "logs.ejemplo.com",
    puerto: 514,
    protocolo: "UDP"
)
```

### Custom Handler

```syquex
estructura SlackHandler:
    webhook_url: texto
    nivel: NivelLog

    metodo emitir(registro: RegistroLog):
        let payload = {
            "text": "[" + registro.nivel.texto() + "] " + registro.mensaje,
            "username": "Syquex Bot"
        }
        await http.post(self.webhook_url, body: payload.a_json())

logging.agregar_handler(SlackHandler("https://hooks.slack.com/..."))
```

## 3. Formatos y Estructura

### Formato estándar

```syquex
logging.configurar({
    formato: "%(timestamp)s [%(hilo)s] %(modulo)s:%(linea)s - %(nivel)s - %(mensaje)s",
    fecha_formato: "%Y-%m-%d %H:%M:%S"
})
```

### Formato JSON estructurado

```syquex
logging.configurar({
    formato: logging.JSON,
    campos_extra: ["servicio", "version", "entorno"]
})

// Salida:
// {"timestamp": "2024-01-15T10:30:00Z", "nivel": "INFO", "mensaje": "Operación completada", "servicio": "api", "version": "1.2.3"}
```

### Formato personalizado

```syquex
logging.formatter_personalizado(funcion(registro) -> texto:
    retornar "[" + registro.timestamp + "] " +
           registro.nivel.texto().upper() + " " +
           registro.modulo + ": " +
           registro.mensaje
)
```

## 4. Contexto y Correlación

### Logger con contexto

```syquex
funcion procesar_solicitud(req: Request):
    let ctx = logging.contexto({
        "request_id": req.id,
        "usuario": req.usuario_id,
        "endpoint": req.ruta
    })
    
    let logger = logging.logger("api").con_contexto(ctx)
    
    logger.info("Procesando solicitud")
    // Todos los logs de este logger incluyen el contexto
```

### Correlación de traces

```syquex
// Tracer para seguir el flujo a través de múltiples servicios
let tracer = tracing.tracer("servicio-a")

async funcion manejar_operacion():
    let span = tracer.iniciar_span("procesar_pedido")
    defer span.finalizar()
    
    span.etiquetar("pedido_id", pedido.id.texto())
    
    await span.con_span("validar"):
        validar_pedido(pedido)
    
    await span.con_span("procesar_pago"):
        procesar_pago(pedido.total)
    
    span.registrar_evento("pedido_completado")
```

## 5. Rotating y Compresión

```syquex
let handler = logging.handler_archivo(
    ruta: "app.log",
    nivel: logging.DEBUG,
    rotacion: "10MB",
    copias: 10,
    compresion: "gzip",
    retencion_dias: 30
)

logging.configurar({handlers: [handler]})
```

## 6. Niveles por Módulo

```syquex
logging.configurar({
    handlers: [logging.handler_consola(logging.WARNING)],
    niveles: {
        "mi_app.core": logging.DEBUG,     // Debug solo para core
        "mi_app.api": logging.INFO,       // Info para API
        "mi_app.db": logging.WARNING,     // Solo warnings para DB
        "libreria_externa": logging.ERROR // Solo errores de librerías
    }
})
```

## 7. Redacción de Logs Seguros

### Sanitización de datos sensibles

```syquex
logging.configurar({
    filtros: [
        logging.filtro_sanitizar(["password", "api_key", "token"]),
        logging.filtro_mascarar("email", lambda s: "***@***.***")
    ]
})

// El log "password=secreto" se mostrará como "password=***"
```

### Hashing de identificadores

```syquex
logging.filtro_hash("usuario_id", lambda id: sha256(id).substring(0, 8))
```

## 8. Integración con Sistemas de Monitoreo

### Prometheus Exporter

```syquex
importar lib.monitoreo

let prometheus = monitoreo.PrometheusExporter(puerto: 9090)

prometheus.contador("peticiones_total", "Número total de peticiones")
prometheus.histograma("duracion_operacion", "Duración en segundos", bins: [0.1, 0.5, 1.0, 5.0])

funcion manejar_operacion():
    let inicio = reloj()
    // ... operación ...
    let duracion = reloj() - inicio
    
    prometheus.contador_incrementar("peticiones_total")
    prometheus.histograma_observar("duracion_operacion", duracion)
```

### Exportación a servicios externos

```syquex
logging.configurar({
    handlers: [
        logging.handler_consola(logging.INFO),
        logging.handler_datadog(
            api_key: "xxx",
            servicio: "mi-app",
            entorno: "produccion"
        )
    ]
})
```

## Ejemplo Completo

```syquex
#lang: es

importar lib.logging

estructura Servicio:
    logger: Logger
    base_datos: BaseDatos

    crear(nombre: texto, db: BaseDatos):
        self.logger = logging.logger(nombre)
        self.base_datos = db
        
        logging.configurar({
            handlers: [
                logging.handler_consola(logging.INFO,
                    formato: "%(timestamp)s [%(nivel)s] %(nombre)s: %(mensaje)s"
                ),
                logging.handler_archivo("servicio.log",
                    nivel: logging.DEBUG,
                    rotacion: "100MB",
                    copias: 5
                )
            ]
        })

    async metodo procesar(usuario_id: entero):
        self.logger.info("Procesando usuario", contexto: {"id": usuario_id})
        
        intentar:
            let usuario = await self.base_datos.obtener_usuario(usuario_id)
            self.logger.debug("Usuario obtenido", contexto: {"nombre": usuario.nombre})
            
            await self.enviar_notificacion(usuario)
            self.logger.info("Notificación enviada")
            
        atrapar e:
            self.logger.error("Falló el procesamiento", error: e)

funcion principal():
    let servicio = Servicio("api-usuarios", BaseDatos("db.sqlite"))
    await servicio.procesar(123)

// Referencias
- Manual 3 §12.1: Biblioteca estándar (lib/logging)
- Manual 9 §1: Debug y diagnóstico
