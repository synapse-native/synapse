# GUÍA DE GOBERNANZA — SYNAPSE v5.1.1-industrial

## 📖 FUENTES DE VERDAD ABSOLUTA
- **Manuales de Ingeniería**: `docs/manuales/MANUAL_1.md` al `MANUAL_9.md`
- **Roadmap**: `ROADMAP.md`

## 🛑 REGLAS INFRINGIBLES (CADA UNA = ERROR GRAVE)

1. **Antes de codificar, LEE el manual correspondiente.**
2. **Cada entrega DEBE referenciar:** `Manual X, Sección Y, Hito Z`.
3. **NO inventes APIs.** Si no está en los manuales, no existe.
4. **TODAS las funciones públicas** deben tener `requiere` y `garantiza` (Manual 2).
5. **Debes pasar los tests** de la sección "Tests Obligatorios" de cada manual.
6. **No se permiten arreglos ilegitimos, Hardcoding** toda reparacion de codigo debe ser con codigo real y funcional.

## 📋 PROTOCOLO DE ENTREGA (COPIA Y PEGA ESTO)
Para cada micro-entregable, Opencode debe usar este formato (sin tablas ni markdown elegante):

text
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