# MÉTODO DE TRABAJO SEGURO (MTS) — Mecanismo Anti-Olvido

Este documento establece la metodología obligatoria para evitar que los agentes lean el manual y luego omitan sus reglas durante la implementación.

## 1. El plan cita el requisito textualmente, no solo la sección

En `docs/plan_ME_<id>.md` cada cambio propuesto debe incluir un bloque estricto:

```markdown
requisito: Manual [N] §[S]
texto: "[Cita literal del manual]"
implementacion: [Descripción de la implementación real]
oraculo: [Ruta al test que verifica este requisito]
```

**Ejemplo:**
```markdown
requisito: Manual 8 §1.2
texto: "rechaza Content-Length inválido"
implementacion: validacion de protocolo LSP explicita (no contrato)
oraculo: tests/test_lsp_release_invalid.py
```

## 2. El código lleva la cita del manual en el sitio del cambio (grep-chequeable)

Toda función o archivo de producción modificado debe incluir un comentario de cumplimiento anclado a la construcción real:

```c
// cumple Manual 8 §1.2: leer Content-Length y validar tope maximo (rechaza DoS)
```

Un hook `contrastar.py` verifica mediante grep que cada archivo de producción modificado contiene una cita a una sección registrada ese día en el plan.

## 3. Cada requisito se convierte en un test oracle (la clave anti-olvido)

El requisito del manual se codifica como un test ejecutable (el oráculo), y el test se ejecuta en CI en modo release.
Si la validación solo existe como aserción (que se elimina en release), el test fallará en CI.

## 4. Gate contrastar (fase 4b obligatoria)

Antes de integrar, se debe ejecutar:
`python auditoria/contrastar.py --plan docs/plan_ME_<id>.md`

Este script verifica automáticamente:
1. Cada `Manual X §Y` del plan tiene un `oraculo:` (test) asociado.
2. Cada archivo de producción modificado tiene un comentario de cita (ej. `// cumple Manual X §Y`).
3. `verificar_alineacion.py` reporta 0 brechas.
4. En `docs/verificacion_ME_<id>.md` cada requisito está marcado `CUMPLE` con `archivo:linea`.

## 5. Ejecución de Oráculos en CI

El CI ejecuta la suite de tests afectada utilizando builds release. Esto asegura que la implementación real cumple el manual en el artefacto final de producción, no solo en la intención o en modo debug.
