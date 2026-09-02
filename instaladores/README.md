# Instaladores de Synapse

## Requisitos Previos

### Windows
- Windows 10 o superior
- 4 GB de RAM mínimo
- 500 MB de espacio en disco

### Linux
- Ubuntu 20.04+, Debian 11+, Fedora 35+
- Bash 4.0+
- `curl` o `wget` para descargar dependencias

### macOS
- macOS 12.0 Monterey o superior
- Xcode Command Line Tools (para compilar)

## Instalación

### Windows

1. Descargar `synapse-8.1.0-windows.exe` desde GitHub Releases
2. Ejecutar el instalador
3. Seguir el asistente de instalación
4. Opciones:
   - **Solo Synapse**: Instala solo el intérprete
   - **Ecosistema completo**: Instala Synapse + Syquex + OpenSyn

### Linux

```bash
# Opción 1: Instalación interactiva
curl -fsSL https://raw.githubusercontent.com/anomalyco/opencode/main/instaladores/linux/install.sh | bash

# Opción 2: Instalación con opciones
./install.sh --opensyn    # Solo OpenSyn
./install.sh --ecosistema # Ecosistema completo
```

El script detectará automáticamente tu distribución (Ubuntu, Debian, Fedora, CentOS) e instalará las dependencias necesarias.

### macOS

```bash
# Crear instalador .dmg
./instaladores/macos/create_dmg.sh

# Opciones
./create_dmg.sh --opensyn    # Solo OpenSyn
./create_dmg.sh --ecosistema # Ecosistema completo
```

1. Ejecutar el script para crear el `.dmg`
2. Abrir el `.dmg`
3. Arrastrar `Synapse.app` a `Applications`

## Verificación de Integridad

Todos los instaladores verifican la integridad de los binarios usando firmas Ed25519:

```python
from instaladores.common.verificar_firma import verificar_firma

# Verificar firma
es_valido = verificar_firma('synapse.exe', firma_bytes, clave_publica)
```

## Auto-actualización

El sistema de auto-actualización verifica automáticamente nuevas versiones:

```python
from instaladores.common.auto_actualizar import verificar_version

resultado = verificar_version("8.1.0")
if resultado['nueva_disponible']:
    print(f"Nueva versión disponible: {resultado['version_remota']}")
```

## Troubleshooting

### Windows
- **Error de permisos**: Ejecutar como administrador
- **Antivirus bloquea**: Agregar excepción para `synapse.exe`

### Linux
- **Dependencias faltantes**: Ejecutar `sudo apt update` antes de instalar
- **Permiso denegado**: Usar `chmod +x install.sh`

### macOS
- **Gatekeeper bloquea**: Ir a Preferencias > Seguridad > Permitir
- **Error de permisos**: Usar `sudo` para instalar en `/usr/local`

## Estructura de Directorios

```
instaladores/
├── common/
│   ├── verificar_firma.py    # Verificación Ed25519
│   └── auto_actualizar.py    # Sistema de actualización
├── linux/
│   └── install.sh            # Instalador Bash
├── macos/
│   └── create_dmg.sh         # Creador de .dmg
├── windows/
│   └── synapse.iss           # Script Inno Setup
└── README.md                 # Este archivo
```

## Contribución

Para agregar un nuevo instalador:

1. Crear directorio en `instaladores/<plataforma>/`
2. Implementar script de instalación
3. Agregar tests en `tests/installers/`
4. Documentar en este README
5. Registrar lectura del Manual 9 §4.1

## Soporte

- Issues: https://github.com/anomalyco/opencode/issues
- Docs: https://opencode.ai/docs
