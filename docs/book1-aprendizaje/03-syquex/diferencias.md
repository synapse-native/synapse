# Diferencias entre Syquex y Synapse

Syquex y Synapse son dos lenguajes del mismo ecosistema, pero con enfoques distintos. Ambos comparten el mismo **AST canónico unificado** (Manual 2 §11), pero difieren en su modelo de memoria, tipado y casos de uso.

<!-- cumple Manual 3 §2 -->

## Comparativa

| Característica | Synapse | Syquex |
|----------------|---------|--------|
| **Paradigma** | Sistema/lenguaje de bajo nivel | Alto nivel, productivo |
| **Gestión de Memoria** | Ownership, Borrowing, Lifetimes (explícitos) | Arenas por ámbito + RC (automática) |
| **Sintaxis** | Similar a Rust | Similar a Python/Swift |
| **Curva de Aprendizaje** | Media-Alta | Baja |
| **Tipado** | Estático inferido (Hindley-Milner) | Estático inferido (Hindley-Milner) |
| **Concurrencia** | Fibras + Canales | Fibras + Canales (mismo modelo) |
| **Estructuras** | `estructura` (datos) | `estructura` (OOP con métodos) |
| **Manejo de errores** | `Resultado<T,E>`, `coincidir` | `Resultado<T,E>`, `coincidir`, operador `?` |
| **Préstamos** | `&T`, `&mut T` (explícitos) | Implícitos (deduidos por el compilador) |
| **FFI** | `@export` directiva | `externo` palabra clave |
| **Propósito** | Motores, kernels, IA de alto rendimiento | APIs, GUI, scripting, prototipado |

## Regla de Oro de Syquex

> El desarrollador **nunca** escribe `free`, `&`, `mut` o lifetimes explícitos. El compilador deduce todo automáticamente mediante análisis de alcance y gestión por arenas.

```syquex
// En Syquex - memoria automática
funcion ejemplo():
    let lista = [1, 2, 3]  // Gestionado por arena automáticamente
    lista.agregar(4)
```

```synapse
// En Synapse - control manual
funcion ejemplo():
    let lista = Lista<entero>()  // Debes gestionar ownership explícitamente
    lista.agregar(4)
    // lista se libera al salir del scope (RAII)
```

## AST Canónico Unificado

Ambos lenguajes comparten el mismo backend:

1. Syquex traduce su AST `.syq` al `SemNodo[]` canónico de Synapse
2. El analizador semántico de Synapse verifica tipos y ownership
3. El generador emite código C
4. GCC/Clang produce el binario final

Esto permite:
- Compartir el 100% del backend (generación de C/LLVM/WASM)
- Compatibilidad binaria absoluta entre ambos lenguajes
- Herencia del optimizador, sanitizadores y motor ATP

## Referencias

- **Manual 2 §11**: Integración con Syquex y OpenSyn
- **Manual 3 §5**: Sistema de tipos de Syquex
- **Manual 3 §11**: Integración con el AST canónico de Synapse

// cumple Manual 3 §2
