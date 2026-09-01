# Privacidad y Seguridad en OpenSyn

Este capítulo explica las medidas de privacidad y seguridad implementadas en OpenSyn. Aprenderás sobre el procesamiento local, la protección de datos y las mejores prácticas para usar OpenSyn de forma segura.

La privacidad es una prioridad en el diseño de OpenSyn.

<!-- cumple Manual 7 §1.1 -->

## 1. Principio de Procesamiento Local

OpenSyn es **completamente local**. A diferencia de servicios basados en la nube, todo el procesamiento de IA ocurre en el hardware del usuario:

### Sin Conexión a la Nube

- Los modelos de IA se descargan y se guardan localmente
- Todas las inferencias se ejecutan en la máquina del usuario
- **No se envía código, prompts o datos a ningún servidor externo**
- No hay telemetría, métricas de uso ni datos de depuración enviados

### Ventajas de Procesamiento Local

| Ventaja | Detalle |
|--------|---------|
| **Privacidad total** | Tu código nunca abandona tu máquina |
| **Seguridad de datos** | No hay exposición a interceptiones de red |
| **Sin dependencia de internet** | Funciona offline completo |
| **Cumplimiento normativo** | Cumple GDPR, HIPAA y otras regulaciones |
| **Latencia mínima** | Sin latencia de red, respuesta en segundos |
| **Control total** | Tú controlas qué modelo usar y con qué datos |

## 2. Protección de Código Fuente

### Contexto No Persistente

OpenSyn no almacena permanentemente tu código fuente:

```text
Flujo de datos:
1. El LSP envía el contexto (fragmento de código) al orquestador
2. El orquestador construye el prompt con el contexto
3. El modelo genera una respuesta
4. El código generado se valida con el compilador
5. El resultado se devuelve al editor
6. El contexto se descarta (no se almacena en disco)
```

### Feedback Opcional

El sistema puede almacenar pares `(instrucción, código_corregido)` en `~/.opensyn/feedback.jsonl` para mejorar futuras versiones, pero:

- Es **opcional** (puedes desactivarlo)
- Los datos se almacenan localmente
- Puedes revisar y borrar el archivo en cualquier momento

## 3. Verificación de Modelos

### Descargas Verificadas

Todos los modelos descargados se verifican con **SHA-256**:

```syquex
// Del instalador (Manual 7 §2.5)
funcion descargar_modelo(info: ModeloInfo) -> Resultado<texto, texto>:
    net.descargar(info.url, ruta)?
    let hash = hash.sha256_archivo(ruta)
    si hash != info.sha256:
        os.eliminar(ruta)
        retornar err("Checksum incorrecto")
    retornar ok(ruta)
```

### Modelos Firmados

Los modelos oficiales están firmados con Ed25519 (Manual 5 §5.1-5.3):

```bash
# Verificar firma del modelo
opensyn verify --model codellama-7b.gguf
```

## 4. Configuración de Privacidad

### Archivo de Configuración (`~/.opensyn/config.toml`)

```toml
[privacy]
telemetría = false              # Desactivar telemetría
almacenar_feedback = false      # No guardar datos de feedback
cache_local = true              # Usar caché local de respuestas
max_cache_size = 100            # Máximo 100 entradas en caché

[seguridad]
ssl_verificacion = true         # Verificar certificados SSL
sandbox_habilitado = true       # Ejecutar modelo en sandbox
acceso_red = false              # Bloquear acceso a red del modelo
```

### Modo de Máxima Seguridad

```toml
[presicion]
# Sin conexión a internet en absoluto
modo_airgap = true

# Sin almacenamiento de feedback
almacenar_feedback = false

# Sin caché
cache_local = false
```

## 5. Sandboxing y Aislamiento

### Ejecución Aislada

El servidor de inferencia (`llama-server`) se ejecuta con:
- Permisos mínimos del sistema operativo
- Sin acceso de escritura al sistema de archivos (solo lectura)
- Sin acceso a la red (excepto el socket local)
- Limitaciones de recursos (CPU, memoria)

### Configuración de Recursos

```toml
[recursos]
max_cpu_percent = 80            # Máximo 80% de CPU
max_memoria = "8GB"             # Límite de memoria
timeout_request = 30            # 30 segundos por petición
max_concurrent = 4              # Máximo 4 inferencias simultáneas
```

## 6. Mejores Prácticas de Seguridad

### 1. Nunca Compartas Tu Modelo

- Los modelos pueden contener información sensible de entrenamiento
- No compartas archivos `.gguf` sin encriptación
- Usa transferencias seguras (SCP, SFTP) si necesitas mover modelos

### 2. Mantén OpenSyn Actualizado

```bash
# Verificar actualizaciones
opensyn update --check

# Actualizar a la última versión
opensyn update --apply
```

### 3. Configura TLS para Entornos Empresariales

```toml
[server]
puerto = 8088
host = "127.0.0.1"  # Solo localhost por defecto

[seguridad]
# Para entornos con múltiples usuarios
# tls_habilitado = true
# tls_certificado = "/etc/ssl/opensyn.crt"
# tls_llave = "/etc/ssl/opensyn.key"
```

### 4. Audita Acciones

```bash
# Ver registro de auditoría local
opensyn audit --list

# Registro de comandos ejecutados
opensyn audit --commands

# Registro de modelos cargados
opensyn audit --models
```

## 7. Cumplimiento Normativo

### GDPR (Reglamento General de Protección de Datos)

OpenSyn cumple con GDPR porque:
- **No procesa datos personales en la nube**
- **El usuario es el controlador de sus datos**
- **Soporte para derecho al olvido** (eliminación de caché y feedback)
- **Transparencia total** (código abierto, todo es auditable)

### HIPAA (Health Insurance Portability)

Para entornos médicos:
- Modo `airgap` disponible
- Certificaciones de integridad de modelos
- Auditoría completa de accesos

### Cumplimiento Empresarial

```bash
# Verificar configuración de privacidad
opensyn privacy --check

# Generar informe de cumplimiento
opensyn privacy --report
```

## 8. Configuración para Entornos Aislados

### Sin Acceso a Internet

```bash
# Descargar modelo en una máquina con internet
opensyn download codellama-7b-Q4_K_M

# Transferir a máquina aislada
scp codellama-7b-Q4_K_M.gguf usuario@maquina-aislada:~/.opensyn/models/

# Verificar integridad
opensyn verify --model codellama-7b-Q4_K_M
```

### Configuración Enterprise

```toml
[enterprise]
# Política de seguridad estricta
policy_level = "paranoid"

# Todos los modelos deben ser firmados oficialmente
requiere_firma = true

# No permitir modelos personalizados
allow_custom_models = false

# Auditoría obligatoria
audit_required = true
```

## Referencias

- **Manual 7 §1.1**: ¿Qué es OpenSyn? (características de privacidad)
- **Manual 7 §3.3**: Cuantización de modelos
- **Manual 7 §6.1**: Instalación de OpenSyn
- **Manual 9 §5**: Verificación de firmas y hashes
- **Manual 5 §5**: Seguridad y autenticación

// cumple Manual 7 §1.1
