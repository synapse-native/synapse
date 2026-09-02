# Plan ME_30_T2 — Instalador Windows (Inno Setup)

## Bloque MTS (método de trabajo seguro)

### requisito:
Manual 9 §4.1: "Los artefactos se publican en la sección Releases del repositorio de GitHub. Cada release incluye: archivos de instalación para Windows, Linux, macOS y WASM."
Manual 9 §5.1: "El instalador de OpenSyn detecta hardware mediante std.os"

### texto:
Implementar script Inno Setup completo para Windows que:
1. Instale Synapse y componentes seleccionados
2. Opciones: "Solo Synapse" vs "Ecosistema completo"
3. Cree accesos directos
4. Incluya desinstalador

### implementacion:
1. Completar `instaladores/windows/synapse.iss` con:
   - Selección de componentes (Synapse, Syquex, OpenSyn)
   - Accesos directos de escritorio y menú inicio
   - Desinstalador
   - Configuración PATH

### oraculo:
- Archivo .iss existe y tiene sintaxis válida → PASS
- Incluye opciones de componentes → PASS
- Incluye accesos directos → PASS
- Incluye desinstalador → PASS

## Archivos a modificar
- `instaladores/windows/synapse.iss`

## Citas de manuales
- Manual 9 §4.1 (GitHub Releases)
- Manual 9 §5.1 (Detección de hardware)
