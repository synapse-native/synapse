# Empezando

## ⚡ Interruptor de Soberanía

OpenSyn v1.1.0 introduce el **Interruptor de Soberanía**: la IA es 100% Opt-In.

En la primera ejecución, se te preguntará:
- **Modo Lenguaje Puro** — Compilador Synapse standalone, sin IA.
- **Modo Oráculo (IA Local)** — Orquestador autónomo con LLM local.

Tu elección se guarda en `.synapse_config`. Elimínalo para cambiar de modo.

---

## Instalación Zero-Friction (Windows)

Un solo comando:

```powershell
powershell -c "iwr -useb https://github.com/synapse-native/synapse/releases/download/v2.1.0/instalar.ps1 | iex"
```

Esto descarga el binario a `C:\Synapse\synapse.exe` y agrega el directorio al `PATH` del usuario.

## Verificación

```powershell
synapse --version
```

## Extensión VS Code

Descarga `synapse-native-1.0.0.vsix` desde el Release e instala con doble clic, o via terminal:

```bash
code --install-extension synapse-native-1.0.0.vsix
```

La extensión activa resaltado de sintaxis y el cliente LSP automáticamente al abrir archivos `.syn`.

## Primer programa

```synapse
#lang: es

funcion principal() -> nulo:
    escribir("hola mundo")
```
