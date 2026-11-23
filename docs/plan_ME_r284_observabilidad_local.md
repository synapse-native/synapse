# Plan de Micro-Entregable r284_observabilidad_local

## Objetivo

Implementar diagnóstico y monitoreo local opt-in sin telemetría forzada:

- **r284_observabilidad_local**: Diagnóstico local opt-in, cero red
- Manual references: **Manual 1 §5.7** (Cero Telemetría); **Manual 7 §7.3** (Diagnóstico local); **Manual 32 §1.3** (Agente de codificación avanzado)
- Goal: Opt-in por defecto off; test de no-salida; redacción
- Dependencies: r271, r282

## Requisitos de los Manuales

### Manual 1 §5.7 - Cero Telemetría y Soberanía del Usuario

- Los binarios compilados y herramientas del ecosistema no realizan conexiones en red ocultas
- No hay recolección de datos de uso ni analíticas
- La soberanía del entorno del usuario es inviolable
- Las capacidades de IA mediante OpenSyn operan bajo principio de activación voluntaria (*opt-in*)
- Ejecutándose exclusivamente de manera local sin exportar contexto fuera del hardware

### Manual 7 §7.3 - Diagnóstico Local

- Diagnóstico local opt-in para salud del sistema
- Sin salir del hardware del usuario
- Información segura y local

### Manual 32 §1.3 - Alcance Explícitamente Descartado

- No formar parte de vectores de ataque innecesarios
- Posponer soporte MCP y herramientas externas indefinidamente

## Cambios en Producción

### nucleo/principal.syn

- Añadir subcomando `observability --help/--status/--health/--info`
- `synapse observability status`: Mostrar estado saludable (opt-in)
- `synapse observability health`: Health check detallado (opt-in)
- `synapse observability info`: Información de diagnóstico (opt-in)
- Comentarios con `// cumplé Manual 1 §5.7`, `// cumplé Manual 7 §7.3`, `// cumplé Manual 32 §1.3`

### runtime/core/debug.h

- Declarar `int _syn_health_check(void);`
- Declarar `int _syn_diagnostic_info(char* buffer, int bufsize);`
- Comentarios `// cumplé Manual 1 §5.7`, `// cumplé Manual 7 §7.3`, `// cumplé Manual 32 §1.3`

### runtime/core/debug.c

- Implementar `_syn_health_check()`: Verificación local solo, sin red; return 1 si OK
- Implementar `_syn_diagnostic_info(char* buffer, int bufsize)`: Formatear info local solo; modo opt-in, telemetry off, arena OK
- Comentarios `// cumplé Manual 1 §5.7: zero telemetría`, `// cumplé Manual 7 §7.3: diagnóstico local opt-in`, `// cumplé Manual 32 §1.3: agente codificación - memoria persistente`

### documentación

- `docs/verificacion_ME_r284_observabilidad_local.md`: Expediente de verificación
- `docs/reportes/R284.md`: Reporte del micro-entregable

## Evidencia

| check | resultado esperado |
|---|---|
| `contrastar --plan docs/plan_ME_r284_observabilidad_local.md` | PASS (0 brechas) |
| `alineacion --verificar --me r284_observabilidad_local` | 0 brechas; citas textuales ↔ código ↔ oráculos |
| `verificar_encoding.py` | Sin U+FFFD ni C1 en archivos modificados |
| test_no_salida | Tests que verifiquen cero salida red en modo off |

## Hallazgos

- **H-R284-1 (ALTO):** Changlog ausente — gate de CI falla
- **H-R284-2 (MEDIO):** Sin test de no-salida implementado — requiere test nuevo
- **H-R284-3 (BAJO):** Documenatción Manual 32 §1.3 necesita clarificación sobre "agente codificación"

## Límites

- Sin telemetría forzada (Manual 1 §5.7; Manual 32 §1.3)
- Sin GUI externa (política del plan)
- Sin MCP ni multi-proveedor (frente H rules)
- Tests inmutables salvo aprobación explícita

## Oráculos Ejecutados

- `contrastar --plan docs/plan_ME_r284_observabilidad_local.md` → PASS (0 brechas)
- `alineacion --verificar --me r284_observabilidad_local` → 0 brechas
- `verificar_encoding.py` → Sin U+FFFD ni C1