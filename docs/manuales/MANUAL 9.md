# MANUAL 9: INSTALACIÓN, EMPAQUETADO Y DISTRIBUCIÓN

**Archivo:** `09_INSTALACION_Y_DISTRIBUCION.md`  
**Versión:** 8.0.0-industrial  
**Propósito:** Especificar el proceso de instalación, empaquetado y distribución del ecosistema completo Synapse + Syquex + OpenSyn. Este manual cubre la instalación de un solo clic (cero fricción), la generación de instaladores para Windows, Linux, macOS y WASM, la distribución a través de GitHub Releases y Axon Hub, el sistema de actualización automática, la verificación de firmas Ed25519 y el proceso de certificación de producción. El objetivo es que cualquier desarrollador pueda instalar el ecosistema completo en minutos, con una experiencia fluida y segura.

---

## 1. FILOSOFÍA DE INSTALACIÓN Y DISTRIBUCIÓN

El ecosistema Synapse sigue los siguientes principios de distribución:

| Principio | Descripción |
|-----------|-------------|
| **Instalación de un solo clic** | El usuario descarga un instalador (o ejecuta un script) y, en pocos pasos, tiene Synapse (y opcionalmente Syquex y OpenSyn) listo para usar. |
| **Cero dependencias externas** | Los binarios (`synapse.exe`, `synapse_lsp.exe`, etc.) son autocontenidos. No requieren Python, Node.js, ni otros entornos. |
| **Detección automática de hardware** | Al instalar OpenSyn, el sistema detecta RAM, VRAM y CPU para seleccionar y descargar el modelo codec más adecuado. |
| **Seguridad de la cadena de suministro** | Todos los artefactos están firmados con Ed25519. Se verifican firmas e integridad (SHA‑256) antes de la instalación. |
| **Actualizaciones sencillas** | El sistema puede actualizarse a nuevas versiones con un solo comando (`synapse update`). |
| **Offline‑first** | Los paquetes y modelos se descargan una vez y se almacenan en caché local (`~/.synapse/cache/`, `~/.opensyn/models/`). |
| **Opt‑in para IA** | OpenSyn solo se instala si el usuario lo elige explícitamente. Nunca se activa sin consentimiento. |

---

## 2. EMPAQUETADO MULTI‑TARGET

### 2.1. Artefactos Generados

El proceso de empaquetado genera artefactos para las plataformas soportadas:

| Plataforma | Formato | Contenido |
|------------|---------|-----------|
| **Windows (x86_64)** | Instalador `.exe` (Inno Setup) | `synapse.exe`, `synapse_lsp.exe`, runtime (`.dll`), bibliotecas estándar, OpenSyn (opcional), extensión VS Code (`.vsix`). |
| **Linux (x86_64, ARM64)** | Paquete `.deb` (Debian/Ubuntu), `.rpm` (Fedora/RHEL), AppImage | `synapse`, `synapse_lsp`, runtime (`.so`), bibliotecas estándar, OpenSyn (opcional). |
| **macOS (ARM64, x86_64)** | `.dmg` (para distribución), `.pkg` (para instalación) | `synapse`, `synapse_lsp`, runtime (`.dylib`), bibliotecas estándar, OpenSyn (opcional). |
| **WASM** | `.wasm` y `.wat` | Compilador `synapse` compilado a WASM (para uso en navegador). |
| **VS Code Extension** | `.vsix` | Extensión VS Code empaquetada. |

### 2.2. Estructura del Instalador

El instalador unificado incluye los siguientes directorios y archivos:

```
/ (raíz del instalador)
├── bin/
│   ├── synapse (o synapse.exe)
│   ├── synapse_lsp (o synapse_lsp.exe)
│   └── runtime/
│       ├── memory
│       ├── concurrency
│       ├── io
│       ├── http
│       ├── quantum
│       ├── ml
│       └── federated
├── std/                           # Librería estándar de Synapse
│   ├── io.syn
│   ├── math.syn
│   ├── net.syn
│   ├── json.syn
│   ├── concurrencia.syn
│   ├── cluster.syn
│   ├── debug.syn
│   ├── os.syn
│   ├── federated.syn
│   ├── quantum.syn
│   └── modelo.syn
├── lib/                           # Librería estándar de Syquex
│   ├── io.syq
│   ├── math.syq
│   ├── texto.syq
│   ├── lista.syq
│   ├── mapa.syq
│   ├── json.syq
│   ├── web.syq
│   ├── gui.syq                     # Bindings a GTK
│   ├── dom.syq
│   ├── db.syq
│   ├── tiempo.syq
│   ├── pruebas.syq
│   ├── ia.syq
│   └── ffi.syq
├── examples/                      # Ejemplos
│   ├── synapse/
│   │   ├── 01_basico.syn
│   │   ├── 02_estructuras.syn
│   │   └── 03_tensores_ia.syn
│   └── syquex/
│       ├── 01_basico.syq
│       ├── 02_web.syq
│       └── 03_gui.syq
├── docs/                          # Documentación
│   ├── 01_VISION_Y_ARQUITECTURA.md
│   ├── 02_SINTAXIS_SYNAPSE.md
│   ├── 03_SINTAXIS_SYQUEX.md
│   ├── 04_MODELO_MEMORIA_SYQUEX.md
│   ├── 05_CONCURRENCIA.md
│   ├── 06_INTEGRACION_ECOSISTEMA.md
│   ├── 07_OPENSYN_ASISTENTE.md
│   ├── 08_HERRAMIENTAS_DESARROLLO.md
│   └── 09_INSTALACION_Y_DISTRIBUCION.md
├── opensyn/                       # Solo si se incluye OpenSyn
│   ├── models/                    # Directorio para modelos (vacio al inicio)
│   ├── config.toml                # Configuración por defecto
│   ├── llama-server (o llama-server.exe)
│   └── install.sh                 # Script de instalación de OpenSyn (opcional)
└── vscode/
    └── synapse-<version>.vsix
```

### 2.3. Pipeline de Compilación (CI/CD)

El pipeline se ejecuta en GitHub Actions y sigue estos pasos:

1. **Build de los binarios** (para cada target):
   - Compilar `synapse` y `synapse_lsp` con GCC/Clang.
   - Compilar el runtime y enlazar estáticamente.
   - Generar `synapse.wasm` para WebAssembly (usando emcc).
   - Generar la extensión VS Code (`.vsix`).

2. **Pruebas**:
   - Ejecutar la suite de tests completa para cada target.
   - Verificar el bootstrap (diff 0 bytes entre Stage 2 y Stage 3).

3. **Empaquetado**:
   - **Windows:** Instalador `.exe` generado con Inno Setup.
   - **Linux:** Paquete `.deb` y `.rpm`, AppImage.
   - **macOS:** `.dmg` y `.pkg`.
   - **WASM:** Archivo `.wasm` y su correspondiente `.wat`.
   - **VS Code:** Archivo `.vsix`.

4. **Firma de artefactos**: Cada artefacto se firma con Ed25519 (clave privada del proyecto). Se generan archivos `.sig` y `.sha256`.

5. **Publicación**: Los artefactos se suben a GitHub Releases y al Axon Hub.

### 2.4. Script de Instalación (Linux/macOS)

El instalador para Unix es un script Bash que:

1. Detecta la arquitectura y el sistema operativo.
2. Descarga el paquete apropiado desde GitHub Releases (si no se ejecuta desde el paquete local).
3. Extrae los binarios en `/usr/local/bin/` (o `~/.local/bin/` para instalación de usuario).
4. Configura las variables de entorno (PATH).
5. Pregunta si instalar OpenSyn.
6. Si se elige OpenSyn, ejecuta `opensyn/install.sh` para detectar hardware y descargar el modelo.

```bash
#!/bin/bash
# install.sh - Instalador para Linux/macOS

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}=== Synapse Ecosystem Installer ===${NC}"
echo ""

# Detectar arquitectura
ARCH=$(uname -m)
OS=$(uname -s)
if [ "$OS" = "Linux" ]; then
    if [ "$ARCH" = "x86_64" ]; then
        TARGET="linux_x86_64"
    elif [ "$ARCH" = "aarch64" ]; then
        TARGET="linux_arm64"
    else
        echo -e "${RED}Arquitectura no soportada: $ARCH${NC}"
        exit 1
    fi
elif [ "$OS" = "Darwin" ]; then
    if [ "$ARCH" = "arm64" ]; then
        TARGET="darwin_arm64"
    else
        TARGET="darwin_x86_64"
    fi
else
    echo -e "${RED}Sistema operativo no soportado: $OS${NC}"
    exit 1
fi

echo -e "${YELLOW}Target detectado: $TARGET${NC}"

# Descargar el paquete más reciente desde GitHub Releases
VERSION=$(curl -s https://api.github.com/repos/synapse-lang/synapse/releases/latest | grep tag_name | cut -d '"' -f 4)
if [ -z "$VERSION" ]; then
    echo -e "${RED}Error al obtener la versión más reciente${NC}"
    exit 1
fi

URL="https://github.com/synapse-lang/synapse/releases/download/$VERSION/synapse-$VERSION-$TARGET.tar.gz"
echo -e "${YELLOW}Descargando $URL...${NC}"
curl -L -o synapse.tar.gz "$URL"

# Verificar firma
echo -e "${YELLOW}Verificando firma Ed25519...${NC}"
curl -L -o synapse.tar.gz.sig "$URL.sig"
if ! openssl dgst -sha256 -verify public_key.pem -signature synapse.tar.gz.sig synapse.tar.gz; then
    echo -e "${RED}Firma inválida. Abortando.${NC}"
    exit 1
fi

# Extraer
echo -e "${YELLOW}Extrayendo...${NC}"
tar -xzf synapse.tar.gz

# Instalar
echo -e "${YELLOW}Instalando en /usr/local/bin/...${NC}"
sudo cp synapse /usr/local/bin/
sudo cp synapse_lsp /usr/local/bin/
sudo cp -r runtime /usr/local/lib/synapse/
sudo cp -r std /usr/local/lib/synapse/
sudo cp -r lib /usr/local/lib/synapse/

# Preguntar por OpenSyn
read -p "¿Instalar OpenSyn? (y/n): " INSTALL_OPENSYN
if [ "$INSTALL_OPENSYN" = "y" ]; then
    echo -e "${YELLOW}Instalando OpenSyn...${NC}"
    chmod +x opensyn/install.sh
    ./opensyn/install.sh
fi

# Limpiar
rm -rf synapse.tar.gz synapse synapse_lsp runtime std lib opensyn

echo -e "${GREEN}✅ Instalación completada.${NC}"
echo "Ejecuta 'synapse --help' para comenzar."
```

### 2.5. Configuración de Inno Setup (Windows)

El script `installer.iss` de Inno Setup para Windows:

```pascal
[Setup]
AppName=Synapse Ecosystem
AppVersion=8.0.0
DefaultDirName={pf}\Synapse
DefaultGroupName=Synapse
UninstallDisplayIcon={app}\bin\synapse.exe
Compression=lzma2
SolidCompression=yes
OutputDir=.
OutputBaseFilename=synapse-setup

[Types]
Name: "full"; Description: "Ecosistema completo (Synapse + Syquex + OpenSyn)"
Name: "minimal"; Description: "Solo Synapse (lenguaje de sistemas)"

[Components]
Name: "synapse"; Description: "Synapse (compilador, runtime, std)"; Types: full minimal; Flags: fixed
Name: "syquex"; Description: "Syquex (lenguaje de alto nivel)"; Types: full
Name: "opensyn"; Description: "OpenSyn (asistente IA local)"; Types: full
Name: "vscode"; Description: "Extensión VS Code"; Types: full minimal

[Files]
Source: "bin\synapse.exe"; DestDir: "{app}\bin"; Components: synapse
Source: "bin\synapse_lsp.exe"; DestDir: "{app}\bin"; Components: synapse
Source: "runtime\*"; DestDir: "{app}\runtime"; Components: synapse
Source: "std\*"; DestDir: "{app}\std"; Components: synapse
Source: "lib\*"; DestDir: "{app}\lib"; Components: syquex
Source: "opensyn\*"; DestDir: "{app}\opensyn"; Components: opensyn
Source: "vscode\synapse-*.vsix"; DestDir: "{app}\vscode"; Components: vscode

[Run]
Filename: "{app}\bin\synapse.exe"; Parameters: "opensyn install"; Components: opensyn; StatusMsg: "Instalando OpenSyn..."
Filename: "code"; Parameters: "--install-extension {app}\vscode\synapse-*.vsix"; Components: vscode; StatusMsg: "Instalando extensión VS Code..."

[Registry]
Root: HKCU; Subkey: "Environment"; ValueType: expandsz; ValueName: "Path"; ValueData: "{olddata};{app}\bin"; Components: synapse
```

---

## 3. SISTEMA DE ACTUALIZACIÓN

### 3.1. Comando `synapse update`

```bash
synapse update [--version <version>] [--check]
```

- Sin argumentos: actualiza a la última versión disponible.
- `--version <version>`: actualiza a una versión específica.
- `--check`: solo verifica si hay actualizaciones disponibles, sin instalarlas.

### 3.2. Pipeline de Actualización

1. **Verificación de versión**: Consulta el endpoint de versiones en GitHub Releases (o Axon Hub).
2. **Descarga de la nueva versión**: Descarga el instalador o los binarios actualizados.
3. **Verificación de firma**: Comprueba la firma Ed25519 del artefacto.
4. **Backup de la versión anterior**: Guarda la versión actual en `~/.synapse/backup/`.
5. **Instalación de la nueva versión**: Reemplaza los binarios y archivos.
6. **Re‑instalación de OpenSyn** (si procede): Si OpenSyn está instalado, se verifica que el modelo siga siendo compatible y se re‑configura (o se actualiza).

### 3.3. Compatibilidad Hacia Atrás

Las nuevas versiones de Synapse deben ser compatibles con el código fuente de versiones anteriores (a menos que se indique explícitamente un cambio incompatible). El sistema de actualización verifica la compatibilidad y advierte al usuario antes de instalar una versión que pueda romper su código.

---

## 4. DISTRIBUCIÓN

### 4.1. GitHub Releases

Los artefactos se publican en la sección **Releases** del repositorio de GitHub. Cada release incluye:

- Notas de la versión (cambios, mejoras, correcciones de seguridad).
- Archivos de instalación para Windows, Linux, macOS y WASM.
- Archivos de firma (`.sig`) y checksums (`.sha256`).
- El SBOM (Software Bill of Materials) en formato SPDX 2.3.
- La attestación SLSA Level 3.

**Comando de creación de release** (automatizado en CI):

```bash
gh release create v8.0.0 \
    --title "Synapse Ecosystem v8.0.0" \
    --notes-file CHANGELOG.md \
    ./artifacts/*
```

### 4.2. Axon Hub (IPFS)

Los paquetes (bibliotecas, modelos, aplicaciones) se publican en el Axon Hub (descentralizado en IPFS). El comando `synapse axon publish`:

1. Empaqueta el código en un archivo TAR.
2. Firma el TAR con la clave privada del autor.
3. Publica el TAR y el manifiesto en IPFS.
4. Actualiza el índice distribuido.

### 4.3. VS Code Marketplace

La extensión VS Code se publica en el Marketplace de VS Code. El pipeline de CI/CD:

1. Construye el paquete `.vsix`.
2. Verifica la firma.
3. Publica en el Marketplace usando el token de acceso del editor.

**Comando de publicación**:

```bash
vsce publish --packagePath synapse-<version>.vsix --pat $VSCE_TOKEN
```

### 4.4. Repositorio de Modelos (OpenSyn)

Los modelos codec se distribuyen a través del Axon Hub (IPFS) y también se puede proporcionar un espejo en Hugging Face. El instalador de OpenSyn intenta descargar primero desde el Axon Hub, y si falla, desde Hugging Face.

---

## 5. INSTALACIÓN DE OPENSYN (DETALLE)

### 5.1. Detección de Hardware

El instalador de OpenSyn (`opensyn/installer.syn`) detecta hardware mediante `std.os`:

```synapse
funcion detectar_hardware() -> HardwareInfo:
    retornar HardwareInfo(
        ram_total: os.memoria_total(),
        vram_total: os.vram_total(),
        cpu_nucleos: os.cpu_nucleos(),
        arquitectura: os.arquitectura()
    )
```

### 5.2. Selección de Modelo

Según la VRAM detectada, selecciona la cuantización más adecuada:

| VRAM | Modelo | Cuantización | Tamaño aprox. |
|------|--------|--------------|---------------|
| < 4 GB | DeepSeek Coder 1.3B | Q4_K_M | ~1 GB |
| 4-6 GB | CodeLlama 7B | Q4_K_M | ~4 GB |
| 6-8 GB | CodeLlama 7B | Q5_K_M | ~5 GB |
| 8-12 GB | CodeLlama 13B | Q4_K_M | ~7 GB |
| 12+ GB | CodeLlama 34B | Q4_K_M | ~18 GB |
| Con GPU NVIDIA (CUDA) | Opt for `--n-gpu-layers` = all | - | - |

### 5.3. Descarga y Verificación

El modelo se descarga desde Hugging Face o Axon Hub, y se verifica su integridad mediante SHA‑256.

```synapse
funcion descargar_modelo(info: ModeloInfo) -> Resultado<texto, texto>:
    let ruta = os.home() + "/.opensyn/models/" + info.nombre + ".gguf"
    si os.existe_archivo(ruta):
        let hash = hash.sha256_archivo(ruta)
        si hash == info.sha256:
            io.escribir_linea("Modelo ya descargado y verificado")
            retornar ok(ruta)
    // Descargar
    net.descargar(info.url, ruta)?
    let hash = hash.sha256_archivo(ruta)
    si hash != info.sha256:
        os.eliminar(ruta)
        retornar err("Checksum incorrecto")
    retornar ok(ruta)
```

### 5.4. Configuración de `llama-server`

El instalador configura `llama-server` con los parámetros óptimos:

```toml
# ~/.opensyn/config.toml
[general]
idioma = "es"
editor = "vscode"

[modelo]
nombre = "codellama-7b-Q4_K_M"
ruta = "~/.opensyn/models/codellama-7b-Q4_K_M.gguf"
n_ctx = 4096
n_threads = 8
n_gpu_layers = 30

[server]
puerto = 8088
host = "127.0.0.1"
timeout = 30
```

### 5.5. Prueba de Humo

El instalador ejecuta una consulta simple al modelo para verificar que todo funciona:

```synapse
funcion prueba_inferencia():
    let cliente = llama_client.crear("127.0.0.1", 8088)
    let respuesta = cliente.completar("Di 'Hola' en español.")
    si respuesta == "Hola":
        io.escribir_linea("✅ Prueba de OpenSyn exitosa.")
    sino:
        io.escribir_linea("⚠️  Prueba de OpenSyn fallida. Revisa la configuración.")
```

---

## 6. CERTIFICACIÓN DE PRODUCCIÓN Y HARDENING FINAL

### 6.1. Checklist de Verificación Final (Definition of Done)

□ **Compilación sin errores**: todos los targets (Windows, Linux, macOS, WASM) compilan sin errores ni warnings.

□ **Bootstrap exitoso**: en cada target, el proceso de bootstrap de 3 etapas produce `diff 0 bytes` entre Stage 2 y Stage 3.

□ **Tests**: 184/184 tests Python pasan; 34/34 tests C nativos pasan; fuzzing: 500+ iteraciones, 0 crashes.

□ **Sanitizadores**: ASan/UBSan/TSan no reportan errores (en los targets que lo soportan).

□ **SBOM y SLSA**: generados y firmados correctamente.

□ **Documentación**: todos los manuales versionados y empaquetados.

□ **Instalador unificado**: probado en sistemas limpios (sin instalación previa) y funciona correctamente.

□ **OpenSyn**: detección de hardware, descarga de modelo y consulta de prueba exitosas.

□ **Extensión VS Code**: instalación y comandos básicos funcionan.

□ **Firmas Ed25519**: todos los artefactos distribuidos están firmados y verificados.

□ **Migración de proyectos**: scripts de migración desde versiones anteriores funcionan.

### 6.2. Validación Cruzada en CI/CD

El pipeline de CI/CD ejecuta automáticamente:

- La suite de tests completa en cada target.
- La verificación del bootstrap (diff 0 bytes).
- El fuzzing destructivo (500+ iteraciones).
- Los sanitizadores (ASan, UBSan, TSan).

### 6.3. Sellado Criptográfico Definitivo

Cada artefacto se firma con la clave privada Ed25519 del proyecto. Se generan:

- Archivo de firma (`.sig`) para cada binario/instalador.
- Archivo `.sha256` con el hash del artefacto.
- Atestación SLSA Level 3.
- SBOM SPDX 2.3.

Todos estos archivos se suben junto con los artefactos a GitHub Releases.

---

## 7. PRUEBAS OBLIGATORIAS PARA ESTA ETAPA

| Test | Comando | Criterio |
|------|---------|----------|
| Instalación en Windows (limpiamente) | Ejecutar instalador en máquina virtual Windows limpia | Instalación exitosa, PATH configurado, `synapse --version` funciona. |
| Instalación en Linux | Ejecutar script de instalación en Ubuntu/Debian | Instalación exitosa, `synapse` en PATH, `synapse build` funciona. |
| Instalación en macOS | Ejecutar script de instalación en macOS ARM | Instalación exitosa, `synapse` funciona. |
| OpenSyn en hardware limitado | Instalar OpenSyn en máquina con 4GB VRAM | Modelo Q3 seleccionado, consulta exitosa. |
| Actualización | `synapse update` desde v7.x a v8.0 | Actualización exitosa, versión correcta. |
| Firma de artefactos | Verificar firma Ed25519 de cada artefacto | 100% de los artefactos verificados. |
| SBOM y SLSA | Generación y validación de SBOM y SLSA | Archivos generados correctamente. |
| Extensión VS Code | Instalar `.vsix` en VS Code limpio | Extensión activa, comandos funcionan. |
| Desinstalación | Ejecutar desinstalador | Todo eliminado, PATH restaurado. |

---

## 8. EJEMPLO DE FLUJO DE INSTALACIÓN COMPLETO

**Escenario:** Usuario nuevo descarga el instalador de Synapse desde GitHub Releases.

1. **Ejecuta el instalador**:
   - Pantalla de bienvenida con opción "Synapse + Syquex + OpenSyn".
   - El instalador detecta hardware: 16GB RAM, 8GB VRAM, CPU 8 núcleos.
   - Recomienda modelo CodeLlama 7B Q5_K_M.
   - El usuario acepta.

2. **Descarga e instalación**:
   - Se descargan los binarios de Synapse, Syquex y el modelo (5GB aprox.).
   - Se instala la extensión VS Code.
   - Se configura el PATH.

3. **Prueba de humo**:
   - Se compila `examples/synapse/01_basico.syn`.
   - Se ejecuta el binario.
   - Se consulta a OpenSyn con un prompt de prueba.

4. **Finalización**:
   - El instalador muestra un mensaje de éxito y la ruta de instalación.
   - El usuario abre VS Code, crea un archivo `.syq` y comienza a programar con asistencia de OpenSyn.

---

## 9. SIGUIENTES PASOS

Con la instalación y distribución completas, el ecosistema Synapse + Syquex + OpenSyn está **completamente especificado** y listo para su implementación. El siguiente paso es la ejecución de las fases del roadmap (Fases 22-30) para materializar la especificación en código.

---

*Este manual proporciona la especificación completa del proceso de instalación, empaquetado y distribución del ecosistema Synapse + Syquex + OpenSyn. La implementación debe seguir estos lineamientos para garantizar una experiencia de usuario fluida, segura y profesional.*

**Fin del Manual 9**

**Fin de los 9 Manuales del Ecosistema Synapse + Syquex + OpenSyn**