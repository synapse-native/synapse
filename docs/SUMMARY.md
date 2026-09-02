# Documentación Synapse v8.1.0-industrial

[Presentación](./README.md)

---

# Libros Disponibles (mdBook)

## [📘 Libro 1: Aprende Synapse, Syquex y OpenSyn](./book1-aprendizaje/SUMMARY.md)

Aprende el ecosistema Synapse desde cero hasta nivel avanzado.

- **PARTE I:** Introducción
- **PARTE II:** Synapse (Lenguaje de Sistemas)
- **PARTE III:** Syquex (Lenguaje de Alto Nivel)
- **PARTE IV:** OpenSyn (Asistente IA)
- **PARTE V:** Tutoriales Completos
- **APÉNDICES:** Referencia rápida, glosario, errores comunes, recursos

## [📗 Libro 2: Guía para Desarrolladores](./book2-desarrollo/SUMMARY.md)

Guía técnica para contribuidores y estudiantes avanzados.

- Visión general del proyecto
- Manuales de ingeniería
- Anexos (API AST, tests obligatorios, inventario)
- Especificaciones técnicas
- Guía para contribuir
- Referencia (benchmarks, release notes)

---

# Fuentes de Verdad

## Manuales de Ingeniería

Los manuales son la **fuente de verdad absoluta** del proyecto. Toda la implementación del
compilador, biblioteca estándar y herramientas debe seguir fielmente sus especificaciones.

| # | Manual | Versión |
|---|--------|---------|
| 1 | [Visión General, Filosofía y Arquitectura del Ecosistema](manuales/MANUAL%201.md) | 8.0.0 |
| 2 | [Sintaxis y Semántica de Synapse](manuales/MANUAL%202.md) | 8.0.0 |
| 3 | [Sintaxis y Semántica de Syquex](manuales/MANUAL%203.md) | 8.0.0 |
| 4 | [Modelo de Memoria de Syquex](manuales/MANUAL%204.md) | 8.0.0 |
| 5 | [Concurrencia y Comunicación](manuales/MANUAL%205.md) | 8.0.0 |
| 6 | [Integración del Ecosistema](manuales/MANUAL%206.md) | 8.0.0 |
| 7 | [OpenSyn — Asistente de IA Local](manuales/MANUAL%207.md) | 8.1.0 |
| 8 | [Herramientas de Desarrollo](manuales/MANUAL%208.md) | 8.2.0 |
| 9 | [Instalación, Empaquetado y Distribución](manuales/MANUAL%209.md) | 8.0.0 |

Anexos: [`ANEXO-MANUALES.md`](manuales/ANEXO-MANUALES.md) ·
[`ANEXO_INVENTARIO_ARCHIVOS.md`](manuales/ANEXO_INVENTARIO_ARCHIVOS.md) ·
[`MANUAL_TESTS_OBLIGATORIOS.md`](manuales/MANUAL_TESTS_OBLIGATORIOS.md)

---

# Documentación de Soporte

## Gobernanza y Protocolos

- [Guía de Gobernanza](gobernancia/GUIA_DE_GOBERNANZA.md) — Reglas del proyecto y protocolo de entrega
- [Método de Trabajo Seguro (MTS)](gobernancia/METODO_TRABAJO.md) — Mecanismo anti-olvido con `requisito:`/`texto:`/`implementacion:`/`oraculo:`
- [Mapa de Manuales](gobernancia/mapa_manuales.md) — Qué secciones leer por archivo de producción
- [Guía de Usuario - Instaladores](guia_usuario_instaladores.md) — Instalación multiplataforma
- [Release Notes v8.1.0](release_notes_v8.1.0.md) — Notas de la release industrial

## Decisiones, Auditorías y Reportes

- [Decisiones Arquitectónicas](decisiones/) — Decisiones D-*, canon de deudas, módulos D-9
- [Auditorías](auditorias/) — Auditoría de alineación con manuales
- [Reportes](reportes/) — Reportes de micro-entregables (ME-*) y fases (FASE_*)
- [Planes](plans/) — Planes de micro-entregables (`plans/ME/`), verificaciones (`plans/verifications/`), planes de fase (`plans/fases/`)
- [Repair Plans](repair-plans/) — Planes de reparación de bugs
- [Bitácoras](bitacoras/) — Bitácoras de desarrollo del proyecto

---

# Referencia Rápida

## Enlaces Importantes

- [Guía de Instaladores](guia_usuario_instaladores.md)
- [Roadmap del Proyecto](../ROADMAP.md)
- [Contribuir](../CONTRIBUTING.md)
- [GitHub Repository](https://github.com/anomalyco/opencode)

## Documentos Populares

| Documento | Descripción |
|-----------|-------------|
| [Introducción a Synapse](book1-aprendizaje/01-introduccion/que-es-synapse.md) | ¿Qué es Synapse? |
| [Instalación](book1-aprendizaje/02-synapse/instalacion.md) | Cómo instalar Synapse |
| [Sintaxis Synapse](book1-aprendizaje/02-synapse/variables.md) | Variables y tipos |
| [Sintaxis Syquex](book1-aprendizaje/03-syquex/variables.md) | Variables y tipos |
| [OpenSyn](book1-aprendizaje/04-opensyn/que-es-opensyn.md) | El asistente IA |
| [Tutoriales](book1-aprendizaje/05-tutoriales/calculadora.md) | Calculadora científica |
| [Manuales](book2-desarrollo/02-manuales/manual-1-vision-general.md) | Especificaciones técnicas |

---

*Documentación Synapse v8.1.0-industrial — Septiembre 2026*
