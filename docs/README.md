# Documentación de Synapse v8.1.0

Bienvenido a la documentación oficial del ecosistema **Synapse + Syquex + OpenSyn** v8.1.0.

## Estado del Proyecto

**FASE 30 COMPLETADA** — Instalación Unificada y Distribución Final

- ✅ 667 tests Python PASS
- ✅ Bootstrap determinista (diff=0 bytes)
- ✅ SBOM SPDX 2.3
- ✅ Firma Ed25519
- ✅ Instaladores multiplataforma

---

## Manuales de Ingeniería (Fuentes de Verdad)

| # | Manual | Versión | Descripción |
|---|--------|---------|-------------|
| 1 | [Visión General, Filosofía y Arquitectura del Ecosistema](manuales/MANUAL%201.md) | 8.0.0-industrial | Visión, los tres componentes (Synapse/Syquex/OpenSyn), hoja de ruta |
| 2 | [Sintaxis y Semántica de Synapse](manuales/MANUAL%202.md) | 8.0.0-industrial | Gramática EBNF, tipos, operadores, ownership/borrowing, AST, contratos `requiere`/`garantiza` |
| 3 | [Sintaxis y Semántica de Syquex](manuales/MANUAL%203.md) | 8.0.0-industrial | Gramática EBNF, OOP nativo, manejo de errores con `Resultado` y operador `?`, biblioteca estándar |
| 4 | [Modelo de Memoria de Syquex](manuales/MANUAL%204.md) | 8.0.0-industrial | Arenas por ámbito, conteo de referencias (RC/ARC), referencias débiles, análisis de alcance, FFI Marshaling |
| 5 | [Concurrencia y Comunicación](manuales/MANUAL%205.md) | 8.0.0-industrial | Fibras ligeras, canales tipados, `lanzar`/`escuchar`, sincronización, `std.cluster` distribuido |
| 6 | [Integración del Ecosistema](manuales/MANUAL%206.md) | 8.0.0-industrial | AST canónico unificado, FFI, serialización, bindings a otros lenguajes, runtime compartido |
| 7 | [OpenSyn — Asistente de IA Local](manuales/MANUAL%207.md) | 8.1.0-industrial | Asistente IA local, RAG quirúrgico, bucle de corrección, transpilación, bindings C→Syquex |
| 8 | [Herramientas de Desarrollo](manuales/MANUAL%208.md) | 8.2.0-industrial | LSP nativo, extensión VS Code, debugger (time-travel), CLI unificado, integración con OpenSyn |
| 9 | [Instalación, Empaquetado y Distribución](manuales/MANUAL%209.md) | 8.0.0-industrial | Instalación de un solo clic, instaladores multiplataforma, GitHub Releases, Axon Hub, Ed25519 |

Documentación adicional en [`manuales/ANEXO-MANUALES.md`](manuales/ANEXO-MANUALES.md) y [`manuales/ANEXO_INVENTARIO_ARCHIVOS.md`](manuales/ANEXO_INVENTARIO_ARCHIVOS.md).

---

## Libros (Documentación Generada con mdBook)

| Libro | Audiencia | Ubicación |
|-------|-----------|-----------|
| 📘 **Libro 1: Aprende Synapse, Syquex y OpenSyn** | Principiantes e intermedios | [`book1-aprendizaje/SUMMARY.md`](book1-aprendizaje/SUMMARY.md) |
| 📗 **Libro 2: Guía para Desarrolladores** | Avanzados y contribuidores | [`book2-desarrollo/SUMMARY.md`](book2-desarrollo/SUMMARY.md) |

Para construir el sitio localmente:
```bash
mdbook serve docs/book1-aprendizaje
mdbook serve docs/book2-desarrollo
```

---

## Estructura de la Documentación

```
docs/
├── README.md                    # Este archivo
├── SUMMARY.md                   # Índice principal
├── book.toml                    # Configuración mdBook
├── _redirects                   # Redirecciones GitHub Pages
│
├── manuales/                    # Manuales oficiales (fuentes de verdad)
│   ├── MANUAL 1.md a MANUAL 9.md
│   ├── ANEXO-MANUALES.md
│   ├── ANEXO_INVENTARIO_ARCHIVOS.md
│   └── MANUAL_TESTS_OBLIGATORIOS.md
│
├── book1-aprendizaje/          # Libro 1 (mdBook): Aprende Synapse, Syquex, OpenSyn
├── book2-desarrollo/           # Libro 2 (mdBook): Guía para Desarrolladores
│
├── gobernancia/                 # Reglas y protocolos
│   ├── GUIA_DE_GOBERNANZA.md
│   ├── METODO_TRABAJO.md
│   ├── mapa_manuales.md
│   └── ...
│
├── decisiones/                  # Decisiones arquitectónicas (D-*, R*)
├── auditorias/                  # Informes de auditoría de alineación
├── reportes/                    # Reportes de micro-entregables (R1-R138)
│
├── plans/                       # Planes de micro-entregables
│   ├── ME/                      # Planes plan_ME_*.md
│   ├── verifications/            # Verificaciones verificacion_ME_*.md
│   └── fases/                    # Planes de fase (PLAN_FASE_*.md)
│
├── repair-plans/               # Planes de reparación
├── bitacoras/                    # Bitácoras de desarrollo
├── arquitectura/                 # Especificaciones de arquitectura
│
├── historicas/                  # Documentación obsoleta (v2.x, v5.0, borradores)
│
├── guia_usuario_instaladores.md # Guía de usuario de los instaladores
└── release_notes_v8.1.0.md     # Notas de release v8.1.0
```

---

## Guías y Protocolos

| Documento | Descripción |
|-----------|-------------|
| [Guía de Gobernanza](gobernancia/GUIA_DE_GOBERNANZA.md) | Reglas del proyecto y protocolos |
| [Método de Trabajo Seguro (MTS)](gobernancia/METODO_TRABAJO.md) | Protocolo TDD con `requisito:`/`texto:`/`implementacion:`/`oraculo:` |
| [Mapa de Manuales](gobernancia/mapa_manuales.md) | Mapeo de archivos productivos a secciones obligatorias de los manuales |
| [Guía de Usuario - Instaladores](guia_usuario_instaladores.md) | Instalación multiplataforma (Windows/Linux/macOS) |

---

## Decisiones, Auditorías y Reportes

| Carpeta | Contenido |
|---------|-----------|
| [`decisiones/`](decisiones/) | Decisiones arquitectónicas (D-*, R*) |
| [`auditorias/`](auditorias/) | Informes de auditoría de alineación con manuales |
| [`reportes/`](reportes/) | Reportes de micro-entregables (ME-*) y reportes de fase |
| [`plans/`](plans/) | Planes de micro-entregables (plan_ME_*.md) y planes de fase |
| [`repair-plans/`](repair-plans/) | Planes de reparación de bugs e incidencias |
| [`bitacoras/`](bitacoras/) | Bitácoras de desarrollo del proyecto |

---

## Instalación Rápida

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

Para más detalles, consultar la [Guía de Usuario de Instaladores](guia_usuario_instaladores.md) o el [Manual 9 § Instalación](manuales/MANUAL%209.md).

---

## Recursos Externos

- [GitHub Repository](https://github.com/anomalyco/opencode)
- [Releases](https://github.com/anomalyco/opencode/releases)
- [Issues](https://github.com/anomalyco/opencode/issues)

---

*Documentación Synapse v8.1.0-industrial — Septiembre 2026*
