# Synapse v5.0 — Guía de Despliegue Nativo

> **Documento:** `GUIA_DESPLIEGUE.md`
> **Versión:** 5.0.0 — RELEASE CANDIDATE
> **Última actualización:** 24 Julio 2026

---

## 1. El Ejecutable Único

Synapse v5.0 se distribuye como **un único binario autónomo** que integra:

| Componente | Función | Dependencias |
|-----------|---------|-------------|
| **Compilador nativo** | `.syn` → C → binario | Solo GCC/Clang + `-lpthread -lm` |
| **Axon** | Gestor de paquetes (fetch, init, lock) | Solo `tweetnacl.o` (Ed25519) |
| **Servidor LSP** | JSON-RPC 2.0 sobre stdin/stdout | Ninguna |

**No requiere Python, Node.js, ni ningún intérprete en tiempo de ejecución.**

> **Nota importante:** Python (`python main.py`) solo es necesario para la **compilación inicial** del binario.
> El binario resultante (`synapse.exe`, `synapse_lsp.exe`) es completamente autónomo y no requiere
> Python ni ningún otro intérprete para ejecutarse ni para compilar programas `.syn`.

---

## 2. Requisitos del Sistema

| Plataforma | Compilador | Flags de enlace |
|-----------|-----------|-----------------|
| **Windows** | `gcc` (MinGW-w64) | `-lpthread -lm -lws2_32` |
| **Linux** | `gcc` | `-lpthread -lm` |
| **macOS Intel** | `clang` (autodetectado) | `-lpthread -lm -Wl,-dead_strip` |
| **macOS Apple Silicon** | `clang` (autodetectado) | `-lpthread -lm -Wl,-dead_strip` |

### 2.1 Verificar requisitos

```bash
# Windows (MinGW)
gcc --version

# Linux / macOS
gcc --version    # o clang --version
```

---

## 3. Compilación desde Código Fuente

### 3.1 Clonar el repositorio

```bash
git clone https://github.com/synapse-native/synapse.git
cd synapse
```

### 3.2 Compilar los objetos del runtime

```bash
# Runtime base
gcc -c synapse_rt.c -o synapse_rt.o -lpthread -lm

# Axon (gestor de paquetes)
gcc -c axon_rt.c -o axon_rt.o -lpthread -lm

# Criptografía Ed25519
gcc -c tweetnacl.c -o tweetnacl.o
```

**Resultado esperado:**
```
synapse_rt.o   131 KB
axon_rt.o      133 KB
tweetnacl.o     19 KB
```

### 3.3 Compilar el binario único (con Python)

> **Python solo es necesario en esta etapa.** El binario resultante es autónomo.

```bash
python main.py -o synapse.exe nucleo/principal.syn
```

**Resultado esperado (compilación exitosa):**
```
[OK] Codigo C generado: synapse_unity.c
[OK] Compilando: gcc -O2 ... -o "synapse.exe" ...
[OK] Ejecutable generado: synapse.exe
synapse.exe     ~727 KB
```

**Alternativa — binario precompilado:**
Si la compilación vía `main.py` falla por errores en el código C generado (problema conocido
en el bootstrap auto-hospedado), el repositorio incluye `synapse_bootstrap.exe` (727 KB)
como binario de referencia funcional:
```bash
# Usar el binario precompilado directamente
./synapse_bootstrap.exe programa.syn
```

### 3.4 Compilar el servidor LSP nativo

```bash
python main.py -o synapse_lsp.exe nucleo/lsp.syn
```

**Resultado esperado:**
```
[OK] Ejecutable generado: synapse_lsp.exe
synapse_lsp.exe  ~888 KB
```

---

## 4. Verificación del Binario

### 4.1 Comprobar enlace de símbolos

```bash
# Windows (MinGW)
objdump -t synapse.exe | grep -E "synapse_|axon_|tweetnacl|ed25519"

# Linux / macOS
nm synapse | grep -E "synapse_|axon_|tweetnacl|ed25519"
```

Debe mostrar símbolos como:
```
_syn_ed25519_verificar
_syn_sha256_archivo
_syn_axon_verificar_firma
_syn_axon_buscar_local
_syn_tar_extraer
crypto_sign_ed25519_tweet_open
```

### 4.2 Probar compilación simple

```bash
echo '#lang: es
funcion principal() -> entero:
    retornar 42' > hola.syn

./synapse.exe hola.syn
./hola.exe
echo $?   # Debe mostrar: 42
```

### 4.3 Probar subcomando Axon

```bash
./synapse.exe axon init
./synapse.exe axon fetch --online
```

### 4.4 Probar servidor LSP

```bash
# Inicialización manual vía stdin
echo -e "Content-Length: 57\r\n\r\n{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"initialize\",\"params\":{}}" | ./synapse_lsp.exe
```

Debe responder con las capacidades del servidor.

---

## 5. Instalación en el Sistema

### 5.1 Windows

```powershell
# Copiar a un directorio en PATH
mkdir C:\tools\synapse -Force
copy synapse.exe C:\tools\synapse\
copy synapse_lsp.exe C:\tools\synapse\

# Añadir al PATH del usuario
[Environment]::SetEnvironmentVariable(
    "PATH",
    [Environment]::GetEnvironmentVariable("PATH", "User") + ";C:\tools\synapse",
    "User"
)
```

### 5.2 Linux / macOS

```bash
# Instalar en /usr/local/bin
sudo cp synapse /usr/local/bin/
sudo cp synapse_lsp /usr/local/bin/
sudo chmod +x /usr/local/bin/synapse /usr/local/bin/synapse_lsp

# Verificar
synapse hola.syn
```

---

## 6. Integración con VS Code

### 6.1 Instalar la extensión

1. Abrir VS Code
2. Ir a Extensiones (`Ctrl+Shift+X`)
3. `Install from VSIX...` → seleccionar `vscode-synapse/synapse-0.2.0.vsix`
4. Configurar ruta del binario LSP nativo en `settings.json`:

```json
{
    "synapse.lsp.nativeBinary": "C:\\tools\\synapse\\synapse_lsp.exe"
}
```

Si no se configura, la extensión auto-detecta el binario en:
1. `./synapse_lsp.exe`
2. `./nucleo/lsp_test.exe`
3. `./build/bin/synapse_lsp.exe`

---

## 7. Guía Rápida de Uso

### 7.1 Compilar un programa

```bash
synapse programa.syn              # → programa.exe + programa.syn.json
synapse programa.syn -o salida    # → salida.exe
```

### 7.2 Gestión de paquetes Axon

```bash
synapse axon init                 # Crear axon.toml
synapse axon fetch                # Resolver dependencias locales
synapse axon fetch --online       # Descargar desde HTTP
```

### 7.3 Ver tokens del lexer

```bash
synapse programa.syn --tokens
```

### 7.4 Servidor LSP

```bash
# Opción 1 (recomendada — sin Python):
synapse_lsp.exe

# Opción 2 (legado, requiere Python):
synapse --lsp
```

**La opción 1 es la recomendada.** El binario nativo (`synapse_lsp.exe`) es autónomo,
no requiere Python, y es el predeterminado para la extensión de VS Code.

### 7.5 Ver AST canónico

```bash
synapse programa.syn --dump-ast
```

---

## 7.6 Integración LSP + IA Local Nativa (llama.cpp) — v5.0

**Nuevo en v5.0:** El servidor LSP nativo integra ahora un motor de IA local totalmente autónomo
basado en **llama.cpp**, eliminando la dependencia de Ollama.

### 7.6.1 Componentes

| Componente | Archivo | Función |
|------------|---------|---------|
| **Orquestador IA** | `nucleo/ai_orchestrator.c` | Ciclo de vida de `llama-server.exe` (inicio, health-check, apagado) |
| **Cliente HTTP nativo** | `nucleo/llama_client.c` | 4 endpoints llama.cpp: `/completion`, `/slot_save`, `/slot_restore`, `/embedding` |
| **Pipeline RAG quirúrgico** | `nucleo/synapse_rag.h/c` | Extracción de nodo AST actual, línea activa, diagnósticos; prompt con presupuesto de tokens |
| **Shutdown Hooks** | `nucleo/ai_orchestrator.c` | `synapse_shutdown_hook()` — atexit + signals → terminación forzosa + liberación RAM/VRAM |

### 7.6.2 Pipeline RAG — Negociación Dinámica de Contexto

```
n_ctx del modelo (leído vía /props)
        │
        ▼
max_tokens = clamp(n_ctx * 0.3, 64, 2048)  ← 30% para inyección, 70% reservado a generación
        │
        ▼
Prompt = [CONTEXTO_ARCHIVO (11 líneas)] + [LINEA_ACTUAL] + [NODO_AST] + [DIAGNOSTICOS]
        │
        ▼
POST /completion { prompt, n_predict: max_tokens, temperature: 0.7, stop: ["\n\n\n", "```"] }
```

### 7.6.3 Shutdown Hooks — Liberación Garantizada

| Hook | Plataforma | Acción |
|------|------------|--------|
| `synapse_shutdown_hook()` | Windows | `SetConsoleCtrlHandler` → `CTRL_C_EVENT`, `CTRL_CLOSE_EVENT`, `CTRL_LOGOFF_EVENT`, `CTRL_SHUTDOWN_EVENT` → `TerminateProcess` + `EmptyWorkingSet` + `cuDevicePrimaryCtxRelease` |
| `synapse_shutdown_hook()` | POSIX | `signal(SIGINT/SIGTERM/SIGHUP)` → `SIGKILL` + `waitpid` + `malloc_trim(0)` + `cuDevicePrimaryCtxRelease` vía `dlopen` |

**Garantía:** Al cerrar el editor o LSP, `llama-server.exe` es exterminado y la VRAM liberada — **sin procesos huérfanos**.

### 7.6.4 Configuración LSP con IA Nativa

En `settings.json` de VS Code:

```json
{
    "synapse.lsp.nativeBinary": "C:\\tools\\synapse\\synapse_lsp.exe",
    "synapse.lsp.enabled": true
}
```

Comandos disponibles en la paleta:
- `Synapse: Verificar estado de IA local` → `synapse/aiStatus`
- `Synapse: Explicar código con IA local` → `synapse/aiExplain` (usa pipeline RAG quirúrgico)
- `Synapse: Generar código con IA local` → `synapse/aiComplete`

### 7.6.5 Requisitos de IA Local

| Componente | Requerido | Notas |
|------------|-----------|-------|
| `llama-server.exe` | ✅ | Binario llama.cpp (descargado por `fetch_ai_engine.py`) |
| Modelo `.gguf` | ✅ | `Llama-3.2-1B-Instruct-Q4_K_M.gguf` (~700MB) |
| VRAM mínima | ✅ | 4 GB (modelo 1.2B Q4_K_M) |
| Puerto por defecto | ✅ | `127.0.0.1:8088` |

**Auto-aprovisionamiento:** Ejecutar `python fetch_ai_engine.py --force` — descarga `llama-server.exe` (GitHub releases) + modelo (HuggingFace) y verifica SHA-256.

---

## 8. Solución de Problemas

### Error: `gcc: command not found`

**Causa:** GCC no está instalado o no está en PATH.

**Solución:**
- **Windows:** Instalar MinGW-w64 desde https://www.mingw-w64.org/
- **Linux:** `sudo apt install build-essential`
- **macOS:** `xcode-select --install`

### Error: `synapse.exe: No such file or directory`

**Causa:** El binario no se compiló o no está en el directorio actual.

**Solución:** Seguir los pasos de la sección 3.

### Error: `[!] Compilador fallo con codigo 1`

**Causa:** Error de sintaxis en el archivo `.syn` de entrada.

**Solución:** Revisar el mensaje de error de GCC. Verificar:
- `#lang: es` en la primera línea
- Indentación con 4 espacios exactos
- Llamadas a funciones correctamente escritas

### Error: `ERR_AXON_COMPROMISED`

**Causa:** La firma Ed25519 del paquete no coincide o el autor está vacío.

**Solución:** Verificar que `axon.toml` tenga:
- `autor` con 64 caracteres hexadecimales válidos
- Archivo `.sig` presente junto al `.tar`
- Paquete descargado desde fuente confiable

### Error: `ERR_AXON_NOT_FOUND`

**Causa:** El paquete no existe en la resolución local ni remota.

**Solución:** Usar `--online` para intentar descarga HTTP:
```bash
synapse axon fetch --online
```

---

## 9. Arquitectura del Despliegue

```
┌─────────────────────────────────────────────────────────────┐
│                    synapse.exe                                │
│                                                              │
│  ┌─────────────────┐  ┌────────────────────────────────┐    │
│  │  Compilador      │  │  Axon (gestor paquetes)        │    │
│  │  Nativo (.syn)   │  │  (axon_rt.o)                   │    │
│  │  - Lexer         │  │  - axon.toml parser            │    │
│  │  - Parser        │  │  - Ed25519 verificador         │    │
│  │  - Semántico     │  │  - HTTP download               │    │
│  │  - Generador C   │  │  - TAR extracción + path guard │    │
│  └─────────────────┘  │  - SemVer matching              │    │
│                        │  - axon.lock SHA-256            │    │
│  ┌────────────────────────────────────────────────┐    │    │
│  │  Runtime Nativo (synapse_rt.o)                  │    │    │
│  │  Canales │ SIMD │ SHA-256 │ JSON │ TOML │ GGUF  │    │    │
│  │  Hilos │ Sockets │ Memoria │ AI                 │    │    │
│  └────────────────────────────────────────────────┘    │    │
│                        │                              │    │
│  ┌────────────────────────────────────────────────┐    │    │
│  │  Criptografía (tweetnacl.o)                     │    │    │
│  │  Ed25519 firmas digitales │ SHA-256             │    │    │
│  └────────────────────────────────────────────────┘    │    │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│                  synapse_lsp.exe                     │
│  Servidor LSP nativo (JSON-RPC 2.0 sobre stdin/stdout│
│  Sin dependencia Python                              │
└─────────────────────────────────────────────────────┘
```

**Dependencias en tiempo de ejecución:**
| Componente | Dependencias |
|-----------|-------------|
| `synapse.exe` | GCC/Clang (para enlazado final), `-lpthread`, `-lm` |
| `synapse_lsp.exe` | **Ninguna** — binario puro sobre stdio |
| Programas compilados por Synapse | **Ninguna** — binarios nativos independientes |

---

## 10. Notas de Seguridad

- **Ejecutable único:** No se ejecutan scripts durante la instalación del paquete Axon
- **Sin red en segundo plano:** El binario solo realiza peticiones HTTP explícitas con `--online`
- **Firmas obligatorias:** Todo paquete descargado debe tener firma Ed25519 válida
- **Opt-In IA:** El puente Ollama solo se activa con comando explícito del usuario
- **Sin telemetría:** El binario no recopila datos de uso
