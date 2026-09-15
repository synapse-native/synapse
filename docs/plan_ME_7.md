# Plan ME-7: Fundamentos Críticos de Alineación

> **Fecha:** 2026-09-12
> **Manual referenciado:** Manual 2 §134 (let), Manual 2 §1.3 (comentarios), Manual 2 §5.1 (_resultado_)
> **Objetivo:** Corregir las 3 desviaciones CRITICAL fundamentales que afectan la corrección gramatical del código

---

## Desviaciones a corregir

### 1. `variable` → `let` (Manual 2 §134)

requisito: `declaracion_variable ::= "let" IDENTIFICADOR [ ":" tipo ] [ "=" expresion ] NEWLINE`
texto: La keyword para declarar variables es `let`, no `variable`.
implementacion: Cambiar `variable ultimo_tipo_tarea: entero = 0` → `let ultimo_tipo_tarea: entero = 0` en principal.syn:638.
oraculo: auditoria/verificar_alineacion.py

### 2. `#` → `//` comentarios (Manual 2 §1.3)

requisito: "Synapse soporta dos estilos de comentarios: `//` (línea) y `/* */` (bloque)."
texto: Los comentarios usan `//` para línea y `/* */` para bloque. `#` no es un comentario válido.
implementacion: Cambiar líneas 2-3 de router.syn de `# cumple...` a `// cumple...`.
oraculo: auditoria/verificar_alineacion.py

### 3. `resultado` → `_resultado_` en contratos (Manual 2 §5.1)

requisito: "La variable `_resultado_` contiene el valor que se va a retornar."
texto: En los bloques `garantiza`, la variable especial que contiene el valor de retorno es `_resultado_`.
implementacion: Reemplazar `resultado` por `_resultado_` en TODOS los bloques `garantiza:` de los 6 archivos opensyn.
oraculo: auditoria/verificar_alineacion.py

---

## Archivos afectados

| Archivo | Cambios |
|---------|---------|
| `opensyn/principal.syn` | 1 cambio (`variable` → `let`) + ~27 bloques `garantiza` |
| `opensyn/router.syn` | 2 líneas (`#` → `//`) + ~19 bloques `garantiza` |
| `opensyn/permisos.syn` | ~8 bloques `garantiza` |
| `opensyn/run_manager.syn` | ~18 bloques `garantiza` |
| `opensyn/validation_loop.syn` | ~5 bloques `garantiza` |
| `opensyn/planificador.syn` | ~9 bloques `garantiza` |

---

## Verificación

1. `python main.py opensyn/principal.syn` — compila a .exe
2. `.venv\Scripts\python.exe -m pytest tests/ -v` — 331 tests GREEN
3. `python auditoria/verificar_alineacion.py` — 0 brechas
4. Buscar `variable ` en opensyn/*.syn — 0 resultados
5. Buscar `^#` (excepto #lang:) en opensyn/*.syn — 0 resultados
6. Buscar `garantiza:\n\s+resultado[^_]` en opensyn/*.syn — 0 resultados
