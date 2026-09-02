# ¿Qué es Syquex?

Syquex es un lenguaje de programación de **alto nivel** del ecosistema Synapse, diseñado para ofrecer la productividad de lenguajes dinámicos como Python con el rendimiento y la seguridad de tipos de lenguajes estáticos como Rust.

## Filosofía

Si **Synapse** es el lenguaje de sistemas (bare metal, control manual de memoria), **Syquex** es su hermano de alto nivel, orientado a:

| Aspecto | Synapse | Syquex |
|---------|---------|--------|
| **Gestión de Memoria** | Manual (Ownership, Borrowing, Lifetimes) | Automática (Arenas + RC + Análisis de alcance) |
| **Curva de Aprendizaje** | Media-Alta | Baja (similar a Python) |
| **Propósito** | Motores, Kernels, IA de alto rendimiento | APIs, GUI, Automatización, Prototipado |

## Diferencias clave con Python

- **Tipado estático inferido**: No necesitas anotar tipos, pero el compilador los verifica
- **Concurrencia segura**: Fibras y canales con verificación en tiempo de compilación
- **Sin GC**: Usa arenas y conteo de referencias en lugar de un recolector de basura
- **Compilado a C nativo**: Sin runtime, sin VM, sin dependencias en el binario final

## Casos de Uso Ideales

- **APIs y microservicios**: Sintaxis limpia + rendimiento cercano a C
- **Scripting**: Ideal para automatización y herramientas CLI
- **Aplicaciones web**: Servidor HTTP integrado en la biblioteca estándar (`lib/web.syq`)
- **GUI y escritorio**: Soporte para interfaces nativas con arenas de componente
- **Procesamiento de datos**: Operaciones funcionales sobre listas y mapas

## Integración con el Ecosistema

Syquex comparte el **AST canónico unificado** con Synapse (Manual 2 §11), lo que significa:

- Comparten el 100% del backend (generación de C/LLVM/WASM)
- Compatibilidad binaria absoluta entre ambos lenguajes
- Heredan el mismo optimizador, sanitizadores y motor ATP
- OpenSyn puede generar y explicar código en ambos lenguajes

## Estructura de un Programa

Todo archivo Syquex comienza con la directiva de idioma:

```syquex
#lang: es
```

Luego puede importar módulos, definir estructuras, funciones y constantes:

```syquex
importar lib.io

estructura Usuario:
    nombre: texto
    edad: entero

    crear(nombre: texto, edad: entero):
        self.nombre = nombre
        self.edad = edad

funcion principal():
    let ana = Usuario("Ana", 28)
    io.escribir_linea("Hola, " + ana.nombre)
```

## Referencias

- **Manual 3 §1-15**: Sintaxis y semántica completa de Syquex
- **Manual 2 §11**: AST canónico unificado y exportación FFI
- **ROADMAP.md**: Fase 24 — Biblioteca estándar de Syquex

// cumple Manual 3 §1.1
