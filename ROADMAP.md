# Plan de Mejora y Estabilización — Synapse/OpenSyn

> **Basado en:** Auditoría real del código y tests ejecutados (Abril 2025)  
> **Estado actual del proyecto:** 🟢 **Maduro** — 242 tests pasando, bugs críticos corregidos, CI/CD parcial  
> **Horizonte:** 6 semanas (plan ajustado a la realidad)

---

## 0. ESTADO REAL DEL PROYECTO (Verificado con 242 tests pasando)

### ✅ Lo que ya funciona

| Componente | Estado | Tests Verificados |
|------------|--------|-------------------|
| Lexer (6 idiomas, indentación, 47 tokens) | ✅ Completamente funcional | 38 tests |
| Parser (recursive descent, AST completo) | ✅ Completamente funcional | 33 tests |
| Analizador Semántico (tabla símbolos, type checker, ownership) | ✅ Completamente funcional | 33 tests |
| Generador C (código limpio, RAII, pool allocator) | ✅ Completamente funcional | 70+ tests |
| CLI (argparse, --tokens, --dump-ast, --lang, --lsp) | ✅ Completamente funcional | Verificado |
| Operadores `<=`, `>=`, `!=` | ✅ Implementados | Verificado |
| Unario `-` y `!` | ✅ Implementados | Verificado |
| `break` / `continue` (romper/siguiente) | ✅ Implementados | Verificado |
| Estructuras (structs) y acceso a campos | ✅ Implementadas | Verificado |
| `coincidir` (match/pattern matching) | ✅ Implementado | Verificado |
| Canales (`<-`, `->`) | ✅ Implementados | Verificado |
| `inseguro` / `externo` / FFI | ✅ Implementados | Verificado |
| Contratos (`requiere` / `garantiza`) | ✅ Implementados | Verificado |
| Formato canónico `.syn.json` | ✅ Implementado | Verificado |
| Pretty printer multilingüe | ✅ Implementado | Verificado |
| CI/CD: Deploy docs | ✅ GitHub Actions | Verificado |
| CI/CD: Release binaries | ✅ GitHub Actions | Verificado |
| Bucle `para` (for loop) | ✅ Implementado | Verificado |
| Tabla de símbolos jerárquica | ✅ Implementado | Verificado |
| Booleanos y operadores lógicos | ✅ Implementado | Verificado |
| Validación estricta de tipos | ✅ Implementado | Verificado |

### ❌ Lo que realmente falta

| Elemento | Prioridad | Impacto |
|----------|-----------|---------|
| **CI/CD de tests en cada PR/push** | 🔴 Alta | Sin esto, las regresiones pasan desapercibidas |
| **Operadores compuestos (`+=`, `-=`, `*=`)** | 🟢 Baja | Azúcar sintáctico |
| **LSP: completado, hover, ir a definición** | 🟡 Media | DX avanzada |
| **Extensión VS Code** | 🟢 Baja | Atraer usuarios |
| **Ejemplos y tutoriales** | 🟡 Media | Adopción |

---

## FASE 1: CI/CD Y GARANTÍA DE CALIDAD (Semana 1)

### 1.1. Pipeline de Tests Automatizado ✅ **YA CREADO**

Se creó `.github/workflows/ci-tests.yml` que:
- Ejecuta los **242 tests** en Ubuntu, Windows y macOS
- Prueba Python 3.10, 3.11, 3.12
- Genera reporte de cobertura con pytest-cov
- Ejecuta smoke test con `run_tests.py`
- Verifica calidad de código con flake8

**Impacto:** Cada PR ejecutará automáticamente los 242 tests en 3 plataformas y 3 versiones de Python.

### 1.2. Badge de Cobertura (Recomendado)

```markdown
[![Tests](https://github.com/synapse-native/synapse/actions/workflows/ci-tests.yml/badge.svg)](https://github.com/synapse-native/synapse/actions)
```

---

## FASE 2: BUCLE `para` (FOR LOOP) — ✅ COMPLETADA

### 2.1. Sintaxis

```synapse
para i = 0; i < 10; i = i + 1:
    escribir_linea(i)
```

### 2.2. Implementación por Capas

| Capa | Cambio | Archivo |
|------|--------|---------|
| Lexer | Añadir token `PARA` (mapeo multilingüe) | `lexer.py` |
| Parser | `_parsear_para()` → `SentenciaPara` | `parser.py` |
| AST | Nueva clase `SentenciaPara` | `ast_nodes.py` |
| Semántico | Validar init, cond, incremento | `analizador_semantico.py` |
| Generador | Generar `for(init; cond; inc) { }` en C | `generator.py` |
| Tests | `test_bucle_para.syn` | `tests/` |

---

## FASE 3: LSP AVANZADO — Semanas 3-4

### 3.1. Completado (`textDocument/completion`) ✅
- Completar palabras clave según contexto
- Completar nombres de funciones y variables definidas
- Completar nombres de campos de estructuras

### 3.2. Hover (`textDocument/hover`) ✅
- Mostrar tipo de variable al pasar el mouse
- Mostrar firma de función

### 3.3. Ir a Definición (`textDocument/definition`)
- Saltar a la definición de función/variable/estructura

---

## FASE 4: ECOSISTEMA Y ADOPCIÓN — Semanas 5-6

### 4.1. Extensión VS Code
- Syntax highlighting (TextMate grammar)
- Snippets: `funcion`, `estructura`, `si`, `mientras`, `para`

### 4.2. Galería de Ejemplos

```
examples/
├── 00_hola_mundo/
├── 01_calculadora/
├── 02_estructuras/
├── 03_concurrencia/
├── 04_ffi/
├── 05_json/
└── 06_oraculo/
```

### 4.3. Documentación
- Cheatsheet de una página
- Guía de migración desde Python
- Guía de migración desde C

---

## FASE 5: RUNTIME Y BACKEND — Semana 6+

### 5.1. Mejorar `escuchar` (IPC)
- Reemplazar file polling por señales POSIX / eventos Windows

### 5.2. Canales con Buffer
- Canales asíncronos con capacidad configurable
- `cerrar_canal` explícito

### 5.3. Pool Allocator
- Alineamiento configurable (SIMD)
- Estadísticas de uso en debug

---

## CRONOGRAMA RESUMEN

```
Semana 1:  FASE 1 — CI/CD pipeline (YA CREADO)
Semana 2:  FASE 2 — Bucle `para` (for loop) ✅ COMPLETADA
Semana 3-4: FASE 3 — LSP: Completado + Hover + Definición
Semana 5:  FASE 4 — Extensión VS Code + Ejemplos
Semana 6:  FASE 5 — Runtime mejorado
```

---

## MÉTRICAS DE ÉXITO

| Métrica | Estado Actual | Objetivo (Semana 6) |
|---------|---------------|---------------------|
| Tests automatizados | **242** ✅ | > 250 |
| CI/CD tests en PR | **NO** ❌ → **SÍ** ✅ | Pasa en cada PR |
| Bugs críticos conocidos | **0** ✅ | 0 |
| Bucle `para` (for) | ✅ | ✅ |
| LSP completado/hover | Parcial | ✅ |
| Extensión VS Code | ❌ | ✅ |
| Ejemplos prácticos | 0 | > 6 |

---

## RIESGOS Y MITIGACIONES

| Riesgo | Probabilidad | Mitigación |
|--------|-------------|------------|
| Falta de tiempo para mantener el plan | Media | Priorizar Fase 0 y 1; lo demás es aspiracional |
| Refactor rompe el bootstrap | Media | Tests de regresión ANTES de refactorizar |
| La comunidad no adopta el lenguaje | Alta | Enfocar en nicho (sistemas, IA local, educación) |
| Python sigue siendo necesario | Alta | Aceptar como deuda técnica; planificar migración gradual |

---

## LLAMADO A LA ACCIÓN

1. **Arreglar los bugs de Fase 0** — es lo que impide que la gente use Synapse
2. **Escribir tests** — sin tests, cualquier cambio es una apuesta
3. **Modularizar** — el monolito de 1252 líneas no escala
4. **Poner CI/CD** — que la máquina valide lo que los humanos escriben
5. **Construir comunidad** — un lenguaje sin usuarios es un ejercicio académico

---

*"El mejor plan es aquel que se ejecuta. El peor, el que nunca se empieza."*
