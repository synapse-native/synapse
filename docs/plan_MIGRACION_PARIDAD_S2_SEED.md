# Plan Maestro de Migración de Paridad S1 ↔ S2 y Semilla C de Bootstrap (H-PARIDAD-S1-S2)

**Fecha de formulación:** 2026-11-21  
**Autoridad:** Manual 1 §6 (Regla de hierro del bootstrap), Manual 9 §2.3/§6.2, Manual 31 §1 (Eliminación de dependencia de Python).  
**Diagnóstico:**  
Actualmente coexisten dos implementaciones del compilador: S1 en Python (`compilador/*.py`) y S2 nativo en Synapse (`nucleo/*.syn`). Además, 89 archivos de tests invocan directamente a `main.py` (S1) en lugar de a `dist/bin/synapse.exe` (S2), generando falsos verdes en el prototipo y divergencias semánticas tardías en el binario nativo.

**Objetivo Arquitectónico:**  
Erradicar la doble fuente de verdad de raíz mediante el congelamiento de S1, la parametrización de la suite de pruebas hacia S2 por defecto, la creación de una semilla C autosuficiente (`bootstrap/seed/synapse_stage0.c`) para el bootstrap sin Python, y la eventual jubilación de `compilador/*.py`.

---

## 1. Principios No Negociables

1. **Una Sola Ley Semántica (Manual 1 a 9):**  
   El compilador nativo S2 (`nucleo/*.syn`) es la implementación de producción. S1 es exclusivamente una herramienta transitoria de arranque.
2. **Cero Regresiones en Bootstrap ($S2 == S3$):**  
   Cualquier modificación debe respetar la regla de hierro de Manual 1 §6: `oraculo_r252_paridad_bootstrap.py --construir --estricto` debe confirmar que la etapa 2 y etapa 3 sean idénticas byte por byte.
3. **Determinismo y Autonomía de Entorno (Manual 31 §1):**  
   El proceso de build debe poder completarse en una máquina con solo GCC/Clang instalado, sin requerir intérprete de Python en el sistema.

---

## 2. Desglose en 3 Micro-Entregables Secuenciales

### ME 1: `r291_congelamiento_s1_harness_s2` — Congelamiento de S1 y Conmutación del Harness de Tests
* **Prioridad:** P1 (Bloquea divergencias futuras)
* **Requisitos:** Manual 9 §6.2 (validación cruzada), Manual 1 §7.4 (DoD)
* **Acciones:**
  1. Declarar formalmente en `docs/gobernancia/GUIA_DE_GOBERNANZA.md` y `AGENTS.md` el **congelamiento estricto de S1**: prohibido agregar sintaxis, operadores o características a `compilador/*.py`.
  2. Implementar en `tests/conftest.py` una fixture canónica de ejecución del compilador:
     - Por defecto resuelve y ejecuta `dist/bin/synapse.exe` (S2).
     - Si se define la variable de entorno `SYNAPSE_COMPILADOR=S1`, delega en `main.py` para pruebas comparativas.
  3. Migrar progresivamente los 89 archivos de tests que invocan `main.py` para que utilicen la fixture canónica o `dist/bin/synapse.exe`.
* **Oráculo y Verificación:**
  - `pytest tests/unit/ -k "test_compilador"` ejecutando contra `dist/bin/synapse.exe`.
  - Gate de gobernanza verificando 0 adiciones en `compilador/`.

### ME 2: `r292_semilla_c_bootstrap_nativo` — Semilla C Autosuficiente (`synapse_stage0.c`)
* **Prioridad:** P1 (Independencia del bootstrap)
* **Requisitos:** Manual 1 §6, Manual 9 §2.3, Manual 31 §1
* **Acciones:**
  1. Diseñar el generador de snapshot de bootstrap: compilar `nucleo/principal.syn` con S2 en modo C unificado (`bootstrap/seed/synapse_stage0.c`).
  2. Integrar en `bootstrap/seed/` los headers y fuentes mínimas del runtime en C para que sea 100% autocontenido.
  3. Modificar `build.py` para soportar la bandera `--desde-semilla-c`:
     ```bash
     # Paso 1: GCC compila directamente la semilla C (sin Python)
     gcc -O2 bootstrap/seed/synapse_stage0.c -I runtime/core -o synapse_stage1.exe

     # Paso 2: synapse_stage1.exe autocompila el código fuente de nucleo/
     ./synapse_stage1.exe nucleo/principal.syn -> synapse_stage2.exe

     # Paso 3: Validación del sello S2 == S3 (diff 0 bytes)
     ./synapse_stage2.exe nucleo/principal.syn -> synapse_stage3.exe
     ```
* **Oráculo y Verificación:**
  - Construcción completa en un subshell sin Python en el PATH (`PATH=toolchain_gcc12/mingw64/bin;System32`).
  - Sello determinista S2==S3 verificado.

### ME 3: `r293_jubilacion_s1_fuente_unica` — Archivo de S1 y Fuente Única
* **Prioridad:** P2 (Consolidación final)
* **Requisitos:** Manual 31 §1 (Cadena de desarrollo nativa)
* **Acciones:**
  1. Trasladar `compilador/*.py` a `docs/historicas/compilador_s1_legado/`.
  2. Reemplazar `main.py` en la raíz por un lanzador que delegue directamente en `dist/bin/synapse.exe` (o eliminarlo si ya todos los scripts invocan el binario).
  3. Actualizar `mapa_alineacion.md` retirando las reglas transitorias de `compilador/*`.
* **Oráculo y Verificación:**
  - `python auditoria/verificar_alineacion.py` con 0 brechas.
  - La suite de CI corre íntegramente sobre binarios nativos.
  - El problema de paridad S1 ↔ S2 queda **físicamente erradicado**.

---

## 3. Matriz de Impacto

| Fase | Estado de S1 | Estado de S2 | Dependencia de Python en Build | Riesgo de Paridad |
|---|---|---|:---:|:---:|
| **Actual** | Activo (89 tests lo usan) | Activo (`dist/bin`) | Alta (requerido para Stage 1) | **Alto** (divergencias silenciosas) |
| **Tras ME 1 (`r291`)** | Congelado | Principal en tests | Media (solo para Stage 1) | **Bajo** (tests detectan fallos en S2) |
| **Tras ME 2 (`r292`)** | Semilla de respaldo | Principal autónomo | **Cero (0%)** (usa semilla C) | **Mínimo** |
| **Tras ME 3 (`r293`)** | Archivado en histórico | **Única Fuente** | **Cero (0%)** | **Inexistente (0)** |
