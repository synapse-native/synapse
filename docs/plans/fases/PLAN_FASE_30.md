# PLAN FASE 30 — Instalación Unificada y Distribución Final

## Objetivo
Crear el instalador de un solo clic que permita instalar el ecosistema completo (Synapse + Syquex + OpenSyn) o solo Synapse.

## Micro-Entregables (MEs)

### ME_30_T1: Estructura base del instalador
- **Objetivo:** Crear la estructura de directorios y archivos base para los instaladores
- **Entregables:**
  - `instaladores/` — Directorio raíz
  - `instaladores/windows/` — Scripts Inno Setup
  - `instaladores/linux/` — Scripts Bash + paquetes
  - `instaladores/macos/` — Scripts .dmg/.pkg
  - `instaladores/common/` — Scripts compartidos
- **Tests:** Verificar estructura de directorios

### ME_30_T2: Instalador Windows (Inno Setup)
- **Objetivo:** Crear script de Inno Setup para Windows
- **Entregables:**
  - `instaladores/windows/synapse.iss` — Script Inno Setup
  - Opciones: "Solo Synapse" vs "Ecosistema completo"
- **Tests:** Verificar sintaxis del script .iss

### ME_30_T3: Instalador Linux
- **Objetivo:** Crear scripts de instalación para Linux
- **Entregables:**
  - `instaladores/linux/install.sh` — Script Bash
  - `instaladores/linux/synapse.desktop` — Archivo .desktop
  - Soporte para .deb, .rpm, AppImage
- **Tests:** Verificar scripts bash

### ME_30_T4: Instalador macOS
- **Objetivo:** Crear scripts para macOS
- **Entregables:**
  - `instaladores/macos/create_dmg.sh` — Script para crear .dmg
  - `instaladores/macos/synapse.pkg` — Paquete macOS
- **Tests:** Verificar scripts macOS

### ME_30_T5: Verificación de firmas Ed25519
- **Objetivo:** Implementar verificación de firmas de artefactos
- **Entregables:**
  - `instaladores/common/verificar_firma.py` — Script de verificación
  - Integración con Ed25519 (TweetNaCl)
- **Tests:** Verificar firma de artefactos de prueba

### ME_30_T6: Pruebas de humo post-instalación
- **Objetivo:** Crear pruebas automáticas post-instalación
- **Entregables:**
  - `instaladores/common/test_humo.py` — Pruebas de humo
  - Compilar `01_basico.syn` y `01_basico.syq`
  - Consultar OpenSyn
- **Tests:** Pruebas de humo exitosas

### ME_30_T7: Mecanismo de actualización automática
- **Objetivo:** Implementar `synapse update`
- **Entregables:**
  - `std/update.syn` — Módulo de actualización
  - Verificación de versiones
  - Rollback en caso de fallo
- **Tests:** Verificar actualización y rollback

### ME_30_T8: Documentación y empaquetado final
- **Objetivo:** Documentar y empaquetar para distribución
- **Entregables:**
  - `docs/INSTALACION.md` — Guía de instalación
  - Scripts de build para CI/CD
  - Configuración de GitHub Releases
- **Tests:** Verificar documentación

## Dependencias
- FASE 29 completada (detección de hardware y gestión de modelos)
- FASE 11 (distribución y releases)

## Criterios de Aceptación
- Instalador funciona en sistemas limpios
- Instalación completa no requiere intervención manual
- Actualizaciones se aplican correctamente
- Firmas Ed25519 verificadas

## Duración Estimada
- 4 meses (1 mes por ME principal)

## Manual de Referencia
- Manual 9 §4: Distribución (GitHub Releases, Axon Hub, VS Code Marketplace)
- Manual 9 §5: Instalación de OpenSyn
