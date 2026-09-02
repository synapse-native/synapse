# GUÍA DE GOBERNANZA — SYNAPSE v8.1.0-industrial

## 📖 FUENTES DE VERDAD ABSOLUTA
- **Manuales de Ingeniería**: `docs/manuales/MANUAL 1.md` al `MANUAL 9.md`
- **Roadmap**: `ROADMAP.md`

## 🛑 REGLAS INFRINGIBLES (CADA UNA = ERROR GRAVE)

1. **Antes de codificar, LEE el manual correspondiente.**
2. **Cada entrega DEBE referenciar:** `Manual X, Sección Y, Hito Z`.
3. **NO inventes APIs.** Si no está en los manuales, no existe.
4. **TODAS las funciones públicas** deben tener `requiere` y `garantiza` (Manual 2).
5. **Debes pasar los tests** de la sección "Tests Obligatorios" de cada manual. Los test son inmodificables, solo si es necesario para endurecerlos y siempre se debe preguuntar antes.
6. **No se permiten arreglos ilegítimos, Hardcoding.** Toda reparación de código debe ser con código real y funcional.
7. **Respeta el orden del roadmap.** No adelantes fases.
8. **Cero dependencias no especificadas.** Solo Axon está autorizado.

## 📖 GATE DE LECTURA PREVIA (regla 1 mecanizada)

El pre-commit **bloquea** el commit si hay código de producción modificado sin lectura registrada (del mismo día) de las secciones exigidas en `docs/mapa_manuales.md`. Las citas se validan contra los encabezados reales de `docs/manuales/`: las secciones fabricadas se rechazan; registrar la subsección §X.Y cubre el requisito §X.

```
python auditoria/registrar_lectura.py --pendientes    # qué exige el mapa para tus cambios
python auditoria/registrar_lectura.py --registrar --archivos "<rutas>" --cita "Manual N §S" --puntos "<requisitos leidos>"
```

Obligación del agente ANTES de codificar: ejecutar `--pendientes`, leer las secciones listadas y registrar la lectura con un resumen real de los requisitos. Un archivo productivo nuevo sin entrada en el mapa también bloquea: añade primero su mapeo a `docs/mapa_manuales.md`.

## 📋 PROTOCOLO DE ENTREGA (COPIA Y PEGA ESTO)
Para cada micro-entregable, Opencode debe usar este formato (sin tablas ni markdown elegante):
--- REPORTE DE MICRO-ENTREGABLE ---
TAREA: [nombre]
FASE: [número]
MANUAL REFERENCIADO: [sección y párrafo]
HASH COMMIT: [sha256]
COMPILACIÓN: [log completo de 10 líneas]
TESTS: [lista de tests + resultado]
COBERTURA: [%]
MODIFICACIONES DE TESTS: [ninguna / justificación]
MODULARIZACIÓN: [ninguna / archivos nuevos]
RIESGOS IDENTIFICADOS: [lista]
PRÓXIMO PASO: [descripción]
--- FIN ---

## ⚠️ SI NO PUEDES CUMPLIR: DETENTE Y PREGUNTA
PREGUNTA AL ARQUITECTO: [descripción del problema]

## 📌 OBLIGACIONES ADICIONALES (v8.1.0)

- **El código generado por OpenSyn DEBE ser validado** con el compilador real (`synapse check --no-emit`) antes de mostrarse al usuario (Manual 7, sección 6.3).
- **Las reglas de Synapse/Syquex se inyectan en el System Prompt** de cada consulta de IA (Manual 7, sección 2.3). No asumas que el modelo las conoce de antemano.
- **El flag `--check`** debe estar disponible en el CLI para el bucle de validación (Manual 8, sección 4.2).