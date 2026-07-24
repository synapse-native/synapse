# Introducción

Synapse v2.2.0 es un lenguaje de sistemas moderno, compilado, determinista y seguro, diseñado para ofrecer el control del hardware con las garantías de un lenguaje de alto nivel. Su compilador es 100% auto-alojado (self-hosted) y genera código C directamente, sin runtime ni máquina virtual.

## Filosofía

- **Cero-cost abstractions**: toda abstracción se resuelve en tiempo de compilación.
- **Determinismo**: no hay recolector de basura ni comportamientos impredecibles.
- **Seguridad por diseño**: el sistema de ownership y el analizador semántico previenen fugas de memoria, use-after-free y data races en compilación.
- **Concurrencia sin estado compartido**: la comunicación vía canales es el mecanismo único de interacción entre hilos.

## Objetivos

- Ser un reemplazo directo de C/C++ para sistemas embebidos, redes y computación de alto rendimiento.
- Mantener compatibilidad FFI completa con C.
- Proveer un ecosistema de paquetes (Axon) con verificación criptográfica SHA-256.
- Ofrecer tooling moderno: LSP, extensión VS Code, instalador zero-friction.
