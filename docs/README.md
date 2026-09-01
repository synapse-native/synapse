# Documentación de Synapse v8.1.0

Bienvenido a la documentación oficial del ecosistema **Synapse + Syquex + OpenSyn** v8.1.0

## Estado del Proyecto

**FASE 30 COMPLETADA** — Instalación Unificada y Distribución Final

- ✅ 667 tests Python PASS
- ✅ Bootstrap determinista (diff=0 bytes)
- ✅ SBOM SPDX 2.3
- ✅ Firma Ed25519
- ✅ Instaladores multiplataforma

---

## Manuales de Ingeniería

| Manual | Descripción |
|--------|-------------|
| [**Manual 1** — Arquitectura del Lenguaje](manuales/MANUAL%201.md) | Filosofía de diseño, arquitectura general |
| [**Manual 2** — Especificación Sintáctica](manuales/MANUAL%202.md) | Gramática EBNF, tipos, operadores |
| [**Manual 3** — Arquitectura del Compilador](manuales/MANUAL%203.md) | Pipeline 5 etapas, AST, tabla de símbolos |
| [**Manual 4** — Gestión de Memoria](manuales/MANUAL%204.md) | Ownership, borrowing, lifetimes |
| [**Manual 5** — Concurrencia](manuales/MANUAL%205.md) | Canales, hilos, sincronización |
| [**Manual 6** — Gestor de Paquetes Axon](manuales/MANUAL%206.md) | Axon, Ed25519, axon.lock |
| [**Manual 7** — Herramientas de Desarrollo](manuales/MANUAL%207.md) | LSP nativo, VS Code extension |
| [**Manual 8** — Backend y Generación de Código](manuales/MANUAL%208.md) | Generación C/LLVM/WASM |
| [**Manual 9** — Bootstrap, Pruebas y QA](manuales/MANUAL%209.md) | Bootstrap 3 etapas, CI/CD |

---

## Guías

| Guía | Descripción |
|------|-------------|
| [Guía de Instaladores](guia_usuario_instaladores.md) | Instrucciones de instalación para Windows, Linux y macOS |
| [Guía de Gobernanza](GUIA_DE_GOBERNANZA.md) | Reglas del proyecto y protocolos |
| [Método de Trabajo Seguro](METODO_TRABAJO.md) | Protocolo TDD MTO |

---

## Especificaciones

| Especificación | Descripción |
|----------------|-------------|
| [Especificación OpenSyn](especificacion_opensyn.md) | Arquitectura completa de OpenSyn |
| [Mapa de Manuales](mapa_manuales.md) | Mapa de secciones por archivo |
| [Auditoría de Alineación](AUDITORIA_ALINEACION_MANUALES.md) | Estado de alineación con manuales |

---

## Roadmap

| Documento | Descripción |
|-----------|-------------|
| [Roadmap del Proyecto](../ROADMAP.md) | Roadmap completo F0–F30 |
| [Changelog v8.1.0](../CHANGELOG_v8.1.0.md) | Historial de cambios |

---

## Instalación

### Windows
```cmd
synapse-setup.exe
```

### Linux
```bash
curl -fsSL https://raw.githubusercontent.com/anomalyco/opencode/main/instaladores/linux/install.sh | bash
```

### macOS
```bash
./instaladores/macos/create_dmg.sh
```

**[Guía completa de instalación](guia_usuario_instaladores.md)**

---

## Recursos Externos

- [GitHub Repository](https://github.com/anomalyco/opencode)
- [Releases](https://github.com/anomalyco/opencode/releases)
- [Issues](https://github.com/anomalyco/opencode/issues)

---

*Documentación v8.1.0 — Septiembre 2026*
