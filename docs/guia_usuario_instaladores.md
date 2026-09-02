# Guía de Usuario — Instaladores de Synapse

## Instalación en Windows

### Requisitos
- Windows 10 o superior (64-bit)
- 4 GB de RAM mínimo
- 500 MB de espacio en disco
- Conexión a internet (para dependencias)

### Instalación

#### Opción 1: Instalador con asistente
1. Descargar `synapse-setup.exe` desde [GitHub Releases](https://github.com/anomalyco/opencode/releases)
2. Ejecutar el instalador
3. Seguir el asistente:
   - **Selección de componentes**: Elegir "Solo Synapse" o "Ecosistema completo"
   - **Directorio de instalación**: Por defecto `C:\Program Files\Synapse`
   - **Accesos directos**: Crear acceso directo en escritorio (opcional)
   - **Actualizaciones**: Buscar actualizaciones automáticamente (opcional)
4. Hacer clic en "Instalar"
5. Esperar a que termine la instalación
6. Hacer clic en "Finalizar"

#### Opción 2: Instalación silenciosa
```cmd
synapse-setup.exe /SILENT
```

### Verificación de integridad

El instalador verifica la integridad de los binarios usando firmas Ed25519. Si la verificación falla, la instalación se detendrá.

### Desinstalación

1. Ir a **Configuración** > **Aplicaciones** > **Aplicaciones y características**
2. Buscar "Synapse Ecosystem"
3. Hacer clic en **Desinstalar**
4. Seguir el asistente de desinstalación

---

## Instalación en Linux

### Requisitos
- Ubuntu 20.04+, Debian 11+, Fedora 35+, CentOS 8+
- Bash 4.0 o superior
- `curl` o `wget`
- Python 3.8 o superior
- Conexión a internet

### Instalación

#### Opción 1: Instalación interactiva
```bash
# Descargar el instalador
curl -fsSL https://raw.githubusercontent.com/anomalyco/opencode/main/instaladores/linux/install.sh -o install.sh

# Hacer ejecutable
chmod +x install.sh

# Ejecutar
./install.sh
```

#### Opción 2: Instalación con opciones
```bash
# Solo OpenSyn
./install.sh --opensyn

# Ecosistema completo
./install.sh --ecosistema

# Ayuda
./install.sh --help
```

#### Opción 3: Instalación silenciosa
```bash
echo "2" | sudo ./install.sh  # Ecosistema completo
```

### Componentes

| Componente | Descripción |
|------------|-------------|
| `synapse` | Compilador y runtime (siempre instalado) |
| `syquex` | Lenguaje de alto nivel |
| `opensyn` | Asistente IA local |
| `lib` | Biblioteca estándar |

### Verificación de integridad

El instalador verifica la firma Ed25519 de todos los archivos antes de instalar.

### Desinstalación

```bash
# Descargar script de desinstalación
curl -fsSL https://raw.githubusercontent.com/anomalyco/opencode/main/instaladores/linux/uninstall.sh -o uninstall.sh

# Hacer ejecutable
chmod +x uninstall.sh

# Ejecutar
sudo ./uninstall.sh
```

### Logs

Los logs de instalación se guardan en `/var/log/synapse-install.log`.

---

## Instalación en macOS

### Requisitos
- macOS 12.0 Monterey o superior
- Procesador Apple Silicon (M1/M2/M3) o Intel
- Xcode Command Line Tools
- Conexión a internet

### Instalación

#### Opción 1: DMG
1. Descargar `synapse-macos.dmg` desde [GitHub Releases](https://github.com/anomalyco/opencode/releases)
2. Abrir el archivo `.dmg`
3. Arrastrar `Synapse.app` a la carpeta `Applications`
4. Abrir `Synapse.app` desde `Applications`

#### Opción 2: Desde Terminal
```bash
# Crear instalador DMG
./instaladores/macos/create_dmg.sh

# Opciones
./create_dmg.sh --opensyn    # Solo OpenSyn
./create_dmg.sh --ecosistema # Ecosistema completo
```

### Gatekeeper

Si macOS bloquea la aplicación:
1. Ir a **Preferencias del Sistema** > **Seguridad y Privacidad**
2. En la pestaña **General**, hacer clic en **Permitir** junto a "Synapse"
3. Volver a abrir `Synapse.app`

### Verificación de integridad

El instalador verifica la firma Ed25519 de los binarios antes de crear el DMG.

### Desinstalación

1. Abrir `Finder`
2. Ir a `Applications`
3. Arrastrar `Synapse.app` a la papelera
4. Vaciar la papelera

---

## Solución de Problemas

### Windows

| Problema | Solución |
|----------|----------|
| **Error de permisos** | Ejecutar el instalador como administrador |
| **Antivirus bloquea** | Agregar excepción para `synapse.exe` |
| **Instalación falla** | Verificar que no haya otra instancia de Synapse ejecutándose |

### Linux

| Problema | Solución |
|----------|----------|
| **Dependencias faltantes** | Ejecutar `sudo apt update` o `sudo dnf update` |
| **Permiso denegado** | Usar `sudo` para instalar |
| **Command not found** | Agregar `/usr/local/bin` al PATH |

### macOS

| Problema | Solución |
|----------|----------|
| **Gatekeeper bloquea** | Ir a Preferencias del Sistema > Seguridad y Privacidad |
| **Error de permisos** | Usar `sudo` para instalar en `/usr/local` |
| **App no abre** | Verificar que macOS sea 12.0 o superior |

---

## Verificación de Integridad

Todos los instaladores incluyen verificación de integridad usando firmas Ed25519:

```bash
# Verificar manualmente
python3 instaladores/common/verificar_firma.py
```

## Auto-actualización

El sistema de auto-actualización verifica nuevas versiones automáticamente:

```python
from instaladores.common.auto_actualizar import verificar_version

resultado = verificar_version("8.1.0")
if resultado['nueva_disponible']:
    print(f"Nueva versión disponible: {resultado['version_remota']}")
```

## Soporte

- **Issues**: https://github.com/anomalyco/opencode/issues
- **Documentación**: https://opencode.ai/docs
- **Comunidad**: https://discord.gg/synapse
