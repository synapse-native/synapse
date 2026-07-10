# Synapse: Política de Lanzamientos y Versionado (SemVer)

## 1. Versionado Semántico (MAJOR.MINOR.PATCH)
* **MAJOR (X.0.0):** Cambios que rompen la compatibilidad del código fuente. Ejemplo: cambiar la sintaxis de `lanzar` o eliminar el soporte de tipos algebraicos.
* **MINOR (0.X.0):** Características nuevas que no rompen nada (ej. nuevo módulo en `std`).
* **PATCH (0.0.X):** Corrección de bugs o mejoras de rendimiento del compilador sin cambios sintácticos.

## 2. Regla de Depreciación (Sunset Policy)
Si una característica debe ser eliminada:
1. **Ciclo Warn (Versión N):** El compilador emite una advertencia (`E-999`) al compilar código que usa la característica vieja.
2. **Ciclo Error (Versión N+1):** La característica se convierte en error de compilación.
3. **Ciclo Remoción (Versión N+2):** El código es eliminado del parser y del generador C.

## 3. Builds Reproducibles
Cada lanzamiento oficial (ej. `v1.2.0`) debe ser acompañado por un binario generado mediante el protocolo de *Bootstrap* (Etapa 1.4 del Plan Maestro). El hash SHA-256 del binario resultante debe ser publicado junto al lanzamiento para garantizar que ningún binario fue inyectado con código malicioso.