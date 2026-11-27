# Synapse: Protocolo de Propuestas y Evolución (RFC)

## 1. El Principio de Inmutabilidad
Synapse es un lenguaje de sistemas. Su gramática y sus garantías de memoria son inmutables por diseño. Ninguna característica nueva puede romper el *Bootstrap* o degradar el rendimiento del binario final. Cualquier propuesta debe pasar por este proceso formal.

## 2. Ciclo de Vida de una Propuesta
1. **Borrado (Draft):** El autor redacta un documento `RFC-XXX-nombre.md` describiendo:
   * **Motivación:** ¿Qué dolor del desarrollador resuelve? (Debe ser medible).
   * **Impacto:** ¿Rompe compatibilidad hacia atrás? ¿Afecta el rendimiento?
   * **Alternativas:** ¿Por qué esta solución es mejor que usar librerías existentes?
2. **Revisión (Review):** La propuesta se abre en el repositorio. Los ingenieros del *core* deben auditar:
   * **Simplicidad:** ¿Añade complejidad innecesaria al compilador?
   * **Seguridad:** ¿Introduce riesgos de memoria o condiciones de carrera?
3. **Votación (Consenso):** Se requiere el 75% de aprobación técnica del equipo núcleo.
4. **Implementación:** El autor debe proveer el código, los tests de regresión y actualizar la documentación oficial.

## 3. Filosofía del "No"
La respuesta por defecto a cualquier propuesta de *feature* es "No". El autor tiene la carga de la prueba para demostrar que la propuesta es indispensable y que no viola la simplicidad del núcleo.