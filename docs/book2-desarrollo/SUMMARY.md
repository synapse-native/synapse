# Desarrollo del Ecosistema Synapse

[Presentación](./presentacion.md)

---

# PARTE I: VISIÓN GENERAL DEL PROYECTO

- [Roadmap y Estado Actual](./01-vision-general/roadmap.md)
- [Arquitectura del Sistema](./01-vision-general/arquitectura.md)
- [Estructura del Repositorio](./01-vision-general/repositorio.md)

---

# PARTE II: MANUALES DE INGENIERÍA

## Manual 1: Arquitectura del Lenguaje

- [Visión General](./02-manuales/manual-1-vision-general.md)
- [Pilares del Ecosistema](./02-manuales/manual-1-pilares.md)
- [Arquitectura del Compilador](./02-manuales/manual-1-arquitectura.md)

## Manual 2: Especificación Sintáctica

- [Gramática EBNF](./02-manuales/manual-2-gramatica.md)
- [Sistema de Tipos](./02-manuales/manual-2-tipos.md)
- [Contratos](./02-manuales/manual-2-contratos.md)

## Manual 3: Arquitectura del Compilador

- [Pipeline de 5 Etapas](./02-manuales/manual-3-pipeline.md)
- [AST](./02-manuales/manual-3-ast.md)
- [Tabla de Símbolos](./02-manuales/manual-3-simbolos.md)

## Manual 4: Gestión de Memoria

- [Ownership](./02-manuales/manual-4-ownership.md)
- [Borrowing](./02-manuales/manual-4-borrowing.md)
- [Lifetimes](./02-manuales/manual-4-lifetimes.md)
- [Pool Allocator](./02-manuales/manual-4-pool.md)

## Manual 5: Concurrencia

- [Canales](./02-manuales/manual-5-canales.md)
- [Hilos](./02-manuales/manual-5-hilos.md)
- [Sincronización](./02-manuales/manual-5-sincronizacion.md)

## Manual 6: Gestor de Paquetes Axon

- [Arquitectura](./02-manuales/manual-6-arquitectura.md)
- [Seguridad](./02-manuales/manual-6-seguridad.md)
- [axon.lock](./02-manuales/manual-6-lock.md)

## Manual 7: Herramientas de Desarrollo

- [LSP Nativo](./02-manuales/manual-7-lsp.md)
- [VS Code Extension](./02-manuales/manual-7-vscode.md)
- [CLI](./02-manuales/manual-7-cli.md)

## Manual 8: Backend y Generación de Código

- [Generación C](./02-manuales/manual-8-generacion-c.md)
- [LLVM](./02-manuales/manual-8-llvm.md)
- [WASM](./02-manuales/manual-8-wasm.md)

## Manual 9: Bootstrap, Pruebas y QA

- [Bootstrap 3 Etapas](./02-manuales/manual-9-bootstrap.md)
- [CI/CD](./02-manuales/manual-9-cicd.md)
- [Sanitizadores](./02-manuales/manual-9-sanitizadores.md)

---

# PARTE III: ANEXOS Y REFERENCIAS

- [Anexo de Manuales](./03-anexos/anexo-manuales.md)
- [Inventario de Archivos](./03-anexos/inventario-archivos.md)
- [Tests Obligatorios](./03-anexos/tests-obligatorios.md)
- [API AST Canónico](./03-anexos/api-ast.md)

---

# PARTE IV: ESPECIFICACIONES TÉCNICAS

- [Especificación OpenSyn](./04-especificaciones/especificacion-opensyn.md)
- [Migración Python → Synapse](./04-especificaciones/migracion-python.md)
- [Guía de Estilo](./04-especificaciones/guia-estilo.md)
- [Índice de Errores](./04-especificaciones/indice-errores.md)

---

# PARTE V: CONTRIBUIR

- [Guía de Contribución](./05-contribuir/guia-contribucion.md)
- [CI/CD y Automatización](./05-contribuir/cicd.md)
- [Testing](./05-contribuir/testing.md)
- [Proceso de Revisión](./05-contribuir/revision.md)

---

# PARTE VI: REFERENCIA TÉCNICA

- [Benchmark Results](./06-referencia/benchmarks.md)
- [Release Notes](./06-referencia/release-notes.md)
- [Recursos Externos](./06-referencia/recursos.md)

---

# APÉNDICES

- [Glosario Técnico](./06-referencia/glosario.md)
- [Configuración del Entorno](./06-referencia/configuracion-entorno.md)
- [Solución de Problemas](./06-referencia/solucion-problemas.md)
- [FAQ](./06-referencia/faq.md)
