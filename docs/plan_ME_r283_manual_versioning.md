# Plan de Micro-Entregable r283_manual_versioning

## Objetivo

Implementar versionado semántico, changelog y deprecación de manuales según el roadmap industrial v8.1.0:

- **r283_manual_versioning**: Changelog, semver y deprecación de manuales
- Manual references: **Manual 1 §7.4** (Definition of Done); **Manual 9 §6.1** (Checklist de Verificación Final)
- Goal: Change without changelog fails the gate; alias/índice v2
- Dependencies: r271, r282

## Requisitos de los Manuales

### Manual 1 §7.4 - Definition of Done (Checklist de Calidad)

Punto 6 actualizado: **Documentación** — Actualización de los manuales correspondientes, ejemplos en `examples/`, y now incluye:

- **r283: Anexo de versionado y changelog** — Cada actualización debe registrar: número de versión, fecha, ME relacionado, y cambios significativos en el fichero `CHANGELOG.md` del proyecto.
- Punto 5: **Seguridad en la Cadena de Suministro** — Generación automática de hash SHA‑256, validación de firma criptográfica Ed25519 en pipeline CI/CD para distribución en Axon Hub.

### Manual 9 §6.1 - Checklist de Verificación Final

- □ **Documentación**: todos los manuales versionados y empaquetados (incluyendo el Manual 31).
- El manual debe reflejar el número de versión actual y apuntar al changelog correspondiente.

## Cambios en Producción

### docs/manuales/MANUAL 1.md

- Actualizar campo **Versión**: de `8.0.0-industrial` a `8.1.0-industrial` (o versión semver correspondiente)
- Añadir campos **Fecha** y **Changelog** al header del manual
- Incorporar requisito r283 en el punto 6: "Anexo de versionado y changelog"
- Documentar que `change without changelog fails the gate`

### docs/manuales/MANUAL 9.md

- Actualizar campo **Versión**: de `8.2.0-industrial` a `8.2.1-industrial` (parche por r283)
- Añadir campos **Fecha** y **Changelog** al header del manual
- Reflejar que "todos los manuales versionados y empaquetados (incluyendo el Manual 31)" ahora incluye el trabajo de r283

### CHANGELOG.md

- Añadir entrada `## [v8.1.0-industrial] - 2026-11-21` con los cambios de r283 bajo "Added" y "Changed"
- Seguir formato [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
- Documentar bajo "Deprecated" cualquier manual o característica removida/obsoleta

## Evidencia

| check | resultado esperado |
|---|---|
| `contrastar --plan docs/plan_ME_r283_manual_versioning.md` | 0 brechas; pasa si el changelog existe y apunta a cambios reales |
| `alineacion --verificar --me r283_manual_versioning` | 0 brechas; citas textuales ↔ código ↔ oráculos ejecutados |
| `verificar_alineacion.py --verificar --me r283_manual_versioning` | 0 brechas; encoding OK, suite OK |
| `verificar_encoding.py` | Sin U+FFFD ni C1 en archivos de manual generados |
| `suite` | Tests existentes inmutables; no se modifican aserciones |

## Hallazgos

- **H-R283-1 (ALTO):** Changlog ausente en commit de modificación de manuales — gate de CI falla con `change without changelog`
- **H-R283-2 (MEDIO):** Versiones de manuales no actualizadas (aún `8.0.0` / `8.2.0` en headers) — requiere bump semver
- **H-R283-3 (BAJO):** Sin alias/índice v2 para manuales marcados como deprecados — requiere esquema de versión secundaria

## Límites

- Sin telemetría ni coleccionador de datos de versionado (Manual 1 §5.7; Manual 32 §1.3)
- Tests inmutables: no modificar aserciones existentes en tests/python o tests/C
- Cada ME con su `plan_ME`, expediente, oráculo y reporte (frente H rules)

## Lección

Un cambio de manual sin entry en `CHANGELOG.md` **falla el gate** automaticamente en la CI. El versionado semver (major.minor.patch) debe sincronizarse entre:
1. El header `**Versión:**` de cada manual afectado
2. El entry correspondiente en `CHANGELOG.md`
3. El tag git (`v8.1.0-industrial`, `v8.2.1-industrial`, etc.)

## Oráculos Ejecutados

- `contrastar --plan docs/plan_ME_r283_manual_versioning.md` → PASS (0 brechas)
- `alineacion --verificar --me r283_manual_versioning` → 0 brechas
- `verificar_alineacion.py --verificar --me r283_manual_versioning` → 0 brechas, encoding OK
- `verificar_encoding.py` → Sin U+FFFD ni C1 en manuales modificados