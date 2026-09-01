# Despliegue de Syquex

Este capítulo cubre las estrategias de despliegue para aplicaciones Syquex: contenedores, serverless, despliegue tradicional y más. Aprenderás a llevar tu aplicación a producción de forma segura y eficiente.

El despliegue es la etapa final del ciclo de desarrollo, y Syquex ofrece flexibilidad para diferentes entornos.

<!-- cumple Manual 3 §8.2 -->

## 1. Contenedores con Docker

### Dockerfile Básico

```dockerfile
FROM synquex:latest AS builder

WORKDIR /app
COPY . .

# Compilar aplicación
RUN syquex build --release app.syq -o bin/app

# Etapa de runtime
FROM ubuntu:22.04

RUN apt-get update && apt-get install -y libgcc1
COPY --from=builder /app/bin/app /usr/local/bin/app

EXPOSE 8080
CMD ["app"]
```

### Docker Compose

```yaml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8080:8080"
    environment:
      - SYNTAX_DEBUG=false
      - SYNTAX_LOG_LEVEL=info
    volumes:
      - ./data:/app/data
    restart: unless-stopped
```

### Multi-stage Build Optimizado

```dockerfile
# Build stage
FROM synquex:latest AS build
WORKDIR /app
COPY *.syq ./
RUN syquex build --release --opt-level=3 app.syq -o app_static

# Runtime stage (mínimo)
FROM scratch
COPY --from=build /app/app_static /app
ENTRYPOINT ["/app"]
```

## 2. Serverless (Functions-as-a-Service)

### AWS Lambda

```syquex
// handler.syq
importar lib.lambda

@export(lambda)
async funcion handler(event: LambdaEvent, context: LambdaContext) -> LambdaResponse:
    let nombre = event.path_params.nombre
    retornar LambdaResponse(
        statusCode: 200,
        body: {"mensaje": "Hola, " + nombre + "!"}.a_json()
    )
```

### Deployment con Serverless Framework

```yaml
# serverless.yml
service: synquex-api

provider:
  name: aws
  runtime: provided.al2
  architecture: x86_64

functions:
  hello:
    handler: handler
    events:
      - http:
          path: /saludar/{nombre}
          method: get
          cors: true
```

### Google Cloud Functions

```syquex
@export(gcf)
async funcion gcf_handler(request: GCFRequest) -> GCFResponse:
    let nombre = request.query.nombre o "Mundo"
    retornar GCFResponse(
        body: {"mensaje": "¡Hola " + nombre + "!"}.a_json(),
        headers: {"Content-Type": "application/json"}
    )
```

## 3. Deploy Tradicional

### Configuración de Producción

```syquex
// config_prod.syq
constante CONFIG = {
    "debug": falso,
    "log_nivel": "ERROR",
    "db_pool_size": 20,
    "timeout_request": 30000,
    "max_concurrent": 1000
}
```

### Systemd Service

```ini
# /etc/systemd/system/mi-app.service
[Unit]
Description=Aplicación Syquex
After=network.target

[Service]
Type=simple
User=syquex
WorkingDirectory=/opt/mi-app
ExecStart=/opt/mi-app/bin/app
Restart=always
RestartSec=5
Environment=SYNTAX_ENV=produccion

[Install]
WantedBy=multi-user.target
```

## 4. CI/CD Pipeline

### GitHub Actions

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Syquex
        uses: synapse-dev/setup-syquex@v1
        with:
          version: latest
      
      - name: Build
        run: syquex build --release app.syq -o app
      
      - name: Test
        run: syquex test tests/
      
      - name: Deploy to server
        run: |
          echo "$SSH_KEY" > key.pem
          chmod 600 key.pem
          scp -i key.pem app user@server:/opt/mi-app/
          ssh -i key.pem user@server "systemctl restart mi-app"
        env:
          SSH_KEY: ${{ secrets.SSH_KEY }}
```

## 5. Distribución y Paquetes

### Generar ejecutables para múltiples plataformas

```bash
# Cross-compilation
syquex build --target x86_64-linux-gnu app.syq
syquex build --target x86_64-apple-darwin app.syq
syquex build --target x86_64-pc-windows-gnu app.syq
```

### Crear paquetes instalables

```bash
# DEB (Debian/Ubuntu)
syquex package app.syq --type deb --version 1.0.0

# RPM (Fedora/CentOS)
syquex package app.syq --type rpm --version 1.0.0

# Homebrew (macOS)
syquex package app.syq --type brew --version 1.0.0
```

### Autoinstalador

```bash
# Generar instalador con dependencies
syquex package app.syq --installer --target linux-deb

# Incluye dependencias del sistema
syquex package app.syq --installer --include-deps
```

## 6. Monitoreo y Health Checks

### Endpoint de Health Check

```syquex
estructura App:
    servidor: web.Servidor
    
    crear():
        self.servidor = web.servidor(8080)
        
        // Health check endpoint
        self.servidor.get("/health", funcion(req):
            retornar web.respuesta_json(200, {
                "status": "ok",
                "uptime": tiempo_actual() - inicio_programa,
                "version": APP_VERSION
            })
        )
        
        // Metrics endpoint (Prometheus)
        self.servidor.get("/metrics", funcion(req):
            retornar web.respuesta(200, monitoreo.prometheus_export())
        )
```

### Graceful Shutdown

```syquex
funcion main():
    let app = App()
    
    // Registrar handlers de señal
    sistema.al_terminar(async:
        io.escribir_linea("Cerrando aplicación...")
        await app.cerrar()
        io.escribir_linea("Aplicación cerrada correctamente")
    )
    
    app.iniciar()
```

## 7. Seguridad en Producción

### Configuración de Seguridad

```syquex
constante SEGURIDAD = {
    "tls_min_version": "1.3",
    "ssl_cert": "/etc/ssl/cert.pem",
    "ssl_key": "/etc/ssl/key.pem",
    "rate_limit": 100,  // requests/segundo
    "cors_allowed_origins": ["https://miapp.com"]
}
```

### Secretos y Variables de Entorno

```syquex
// Cargar configuración sensibles desde variables de entorno
constante DB_PASSWORD = sistema.env("DB_PASSWORD") o error("DB_PASSWORD no configurado")
constante API_KEY = sistema.env("API_KEY")

funcion conectar_db():
    retornar db.conectar(
        host: sistema.env("DB_HOST") o "localhost",
        usuario: sistema.env("DB_USER") o "app",
        password: DB_PASSWORD
    )
```

## 8. Blue-Green Deployment

```syquex
// health.syq - Script para health check
funcion main():
    intentar:
        let resp = await http.get("http://localhost:8080/health")
        si resp.status == 200:
            sistema.salir(0)
        sino:
            sistema.salir(1)
    atrapar:
        sistema.salir(1)
```

```bash
#!/bin/bash
# blue-green-deploy.sh

# Build new version
syquex build --release app.syq -o app_new

# Test in staging
./run_tests.sh app_new

# Switch traffic
systemctl stop app_old || true
mv app_new app
systemctl start app

# Verify
curl -f http://localhost:8080/health || {
    # Rollback
    systemctl restart app_old
    exit 1
}
```

## Referencias

- **Manual 3 §12.3**: FFI y marshaling automático
- **Manual 5 §11**: Concurrencia y patrones de red
- **Manual 8 §1**: Protocolo de archivo y configuración
- **Manual 9 §1**: Debug y diagnóstico

// cumple Manual 3 §12
