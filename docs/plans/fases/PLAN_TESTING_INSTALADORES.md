# Plan de Testing en Producción — Instaladores

## Objetivo
Validar que los instaladores funcionan correctamente en entornos reales.

## Escenarios de testing

### Windows
1. **Instalación limpia**: Instalar en Windows nuevo
2. **Actualización**: Actualizar desde versión anterior
3. **Desinstalación**: Desinstalar completamente
4. **Componentes**: Probar opciones de componentes
5. **Permisos**: Probar con permisos de administrador

### Linux
1. **Instalación limpia**: Instalar en Ubuntu/Debian nuevo
2. **Actualización**: Actualizar desde versión anterior
3. **Desinstalación**: Desinstalar completamente
4. **Distribuciones**: Probar en Fedora, CentOS
5. **Permisos**: Probar con/sin sudo

### macOS
1. **Instalación limpia**: Instalar en macOS nuevo
2. **Actualización**: Actualizar desde versión anterior
3. **Gatekeeper**: Verificar que no bloquea
4. **Permisos**: Probar con permisos de administrador

## Métricas de éxito
- Instalación completa sin errores
- Ejecución correcta de Synapse
- Desinstalación limpia
- Tiempo de instalación < 5 minutos

## Herramientas
- Máquinas virtuales (VirtualBox, VMware)
- Docker para Linux
- GitHub Actions para CI/CD

## Documentación
- `docs/testing/installers-test-plan.md`
- `docs/testing/installers-test-results.md`
