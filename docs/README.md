# Documentación de Synapse v5.0

Bienvenido a la documentación oficial del lenguaje de programación **Synapse** v5.0.

## Documentos de Liberación (Fase 11)

| Documento | Descripción |
|-----------|-------------|
| [**Especificación OpenSyn**](especificacion_opensyn.md) | Arquitectura completa de OpenSyn: router RAG determinista, pipeline de migración Python→Synapse, LSP, detección de hardware, seguridad zero-cloud. |
| [**Guía de Migración Python → Synapse**](migracion_python_synapse.md) | Referencia exhaustiva para migrar código Python 3.10+ a Synapse. Cubre sintaxis, tipos, ownership, concurrencia, E/S y errores comunes. |
| [**API del AST Canónico**](api_ast_canonico.md) | Referencia completa del formato `.syn.json`: 30+ tipos de nodo, tokens, expresiones, contratos y ejemplo completo. |

## Documentos Técnicos Principales

| Documento | Descripción |
|-----------|-------------|
| `ROADMAP.md` | Roadmap completo del proyecto v5.0 con estado de todos los hitos |
| `MANUAL_DE_INGENIERÍA_Y_DESARROLLO.md` | Manual técnico de ingeniería y especificación del compilador |
| `MANUAL_LENGUAJE.md` | Manual completo del lenguaje Synapse |
| `ARCH_ESPECIFICACION.md` | Especificación arquitectónica detallada |
| `AXON_SPEC.md` | Especificación del gestor de paquetes Axon |
| `LSP_NATIVO.md` | Especificación del servidor LSP nativo |
| `REFERENCIA_API_STD.md` | Referencia de la biblioteca estándar |
| `GUIA_MEMORIA_Y_TIPOS.md` | Guía de ownership, borrowing y sistema de tipos |
| `GUIA_ESTILO_IDIOMATICA.md` | Guía de estilo y buenas prácticas |
| `INTERFAZ_C_FFI.md` | Especificación de la FFI con C |
| `SEGURIDAD_Y_RESPUESTA.md` | Política de seguridad y respuesta a incidentes |
| `DISEÑO_LSP.md` | Diseño detallado del LSP |
| `DISEÑO_MEMORIA.md` | Diseño del modelo de memoria |

## Documentos de la Biblioteca Estándar

La biblioteca estándar de Synapse se encuentra en `librerias/std/` e incluye:

| Módulo | Descripción |
|--------|-------------|
| `std.io` | Entrada/salida estándar y archivos |
| `std.math` | Funciones matemáticas (seno, coseno, raíz cuadrada, etc.) |
| `std.json` | Parseo y serialización JSON |
| `std.toml` | Parseo de archivos TOML |
| `std.net` | Networking: HTTP y TCP nativo |
| `std.http` | Cliente HTTP de alto nivel |
| `std.concurrencia` | Canales tipados (`Canal<T>`) y concurrencia |
| `std.cluster` | Canales remotos distribuidos (M8) |
| `std.debug` | Depuración time-travel (M9) |
| `std.cripto` | Criptografía: SHA-256 + Ed25519 |
| `std.tensor` | Operaciones con tensores y SIMD |
| `std.simd` | Aceleración SIMD (AVX2/SSE4/NEON) |
| `std.ai` | Inferencia de IA local |
| `std.modelo` | Carga y ejecución de modelos GGUF |
| `std.oraculo` | Pipeline RAG quirúrgico |
| `std.testing` | Utilidades de testing |
| `std.err` | Definiciones de error estándar |
| `std.sistema` | Llamadas al sistema operativo |
| `std.tiempo` | Funciones de tiempo y temporización |
| `std.mem` | Gestión de memoria manual |

## Nota sobre Ejemplos de Código

Los ejemplos de código en la documentación representan la **sintaxis objetivo** del lenguaje Synapse v5.0. Algunos constructos pueden corresponder a la especificación completa y estar pendientes de implementación en el compilador. Consulte `ROADMAP.md` para conocer el estado actual de implementación de cada característica.

---

*Documentación v5.0 — 26 Julio 2026*
