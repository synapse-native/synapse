# Synapse LSP Client — Extensión para VS Code

Cliente LSP oficial para el lenguaje Synapse. Proporciona diagnósticos en
tiempo real (errores de sintaxis, semántica) y, en el futuro, autocompletado,
definiciones e información al pasar el ratón.

## Requisitos

- **VS Code** ≥ 1.85.0
- **Node.js** ≥ 18
- **Synapse** — el binario `synapse` debe estar disponible en el PATH del
  sistema o su ruta debe configurarse manualmente (ver más abajo).

## Compilación e instalación

Desde la carpeta `editor/vscode/`:

```bash
npm install                # instala dependencias (vscode-languageclient, etc.)
npm run compile            # compila TypeScript → out/extension.js
npm run package            # genera el .vsix (requiere @vscode/vsce)
```

Para instalar localmente desde el `.vsix`:

```bash
code --install-extension synapse-lsp-client-1.0.0.vsix
```

O copia la carpeta `editor/vscode/` a `~/.vscode/extensions/synapse-lsp-client/`
y reinicia VS Code.

## Configuración

| Propiedad | Tipo | Valor por defecto | Descripción |
|-----------|------|-------------------|-------------|
| `synapse.lsp.path` | string | `"synapse"` | Ruta al ejecutable de Synapse. Usa `"synapse"` si está en el PATH. |
| `synapse.lsp.args` | string[] | `["--lsp"]` | Argumentos adicionales para el servidor LSP. |

### Ejemplo: ruta personalizada en Windows

```json
"synapse.lsp.path": "D:\\proyecto_synapse\\synapse.exe"
```

### Ejemplo: ruta personalizada en Linux/macOS

```json
"synapse.lsp.path": "/usr/local/bin/synapse"
```

## Comandos

- `Synapse: Restart LSP Server` — reinicia el servidor LSP (útil tras cambiar
  la configuración sin recargar la ventana).

## Estructura de archivos

```
editor/vscode/
├── package.json          # Manifiesto de la extensión
├── tsconfig.json         # Configuración de TypeScript
├── README_EXT.md         # Este archivo
└── src/
    └── extension.ts       # Código de activación del cliente LSP
```

## Depuración

El canal de salida "Synapse LSP Trace" muestra todos los mensajes
JSON-RPC intercambiados entre VS Code y el servidor LSP de Synapse.

Para ver la salida estándar del daemon, abre el panel "Salida" y selecciona
"Synapse LSP" en el menú desplegable.