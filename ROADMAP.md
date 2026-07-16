# Roadmap de Synapse

Este documento define la trayectoria técnica de Synapse hacia su estabilidad v1.0.

### Fase 1: Estabilización (Actual)
- [x] Arquitectura base de compilación (Lexer/Parser).
- [x] Generación de C nativo.
- [x] Implementación de Pool Allocator.
- [x] Operadores lógicos (`y`, `o`, `no`).
- [x] Implementación de `recuperar` (manejo de errores de sistema).
- [x] Primitiva `lanzar` (concurrencia vía pthread).

### Fase 2: Potenciación (Próximamente)
- [x] Tabla de símbolos, tipos y booleanos.
- [x] Soporte completo para el ciclo `para`.
- [ ] Optimización de tensores vectorizados para arquitectura x86/ARM.

*Meta: 250+ tests.*

### Fase 3: Ecosistema
- [ ] Integración de módulos de seguridad criptográfica (Privacidad por defecto).
- [ ] Soporte para extensiones en editores (VS Code Syntax Highlighting).

*Nota: Las características del Motor de Inferencia (MIL) avanzado se integrarán según la estabilidad del core.*
