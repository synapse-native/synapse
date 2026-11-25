# Plan de Micro-Entregable r330_contratos_wasm

## Objetivo

Cerrar la deuda de contratos de `nucleo/wasm_backend.syn` (83 funciones) y
restaurar la validez del módulo: usaba `#` como comentario (inválido en
Synapse), tenía 4 firmas con el bloque `garantiza:` dentro de la lista de
parámetros y llamadas a conversiones inexistentes (`texto(...)`). El test
existente ignoraba los errores del pipeline, así que la deuda se medía sobre
un archivo que no compilaba. Primero se sanea el módulo y después se contratan
las funciones, para que los contratos sean verificables y no teatro.

## Requisito 1 - comentarios canónicos

requisito: Manual 2 §1.3
texto: "**Comentarios de línea:** comienzan con `//` y se extienden hasta el final de la línea."
implementacion: Se convirtieron los 158 separadores/comentarios `#` a `//` (se conserva la directiva `#lang: es`); el módulo vuelve a lexar.
oraculo: tests/auditoria/test_r330_contratos_wasm.py

## Requisito 2 - contratos en toda función pública

requisito: Manual 2 §5.1
texto: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
implementacion: Se agregó `requiere:` a las 83 funciones con invariantes reales (`est.nivel_indentacion >= 0` y `<texto>.longitud >= 0`); se sacaron los bloques de contrato de las 4 firmas multilínea y se corrigieron las conversiones y variables sin `let`. El ratchet de código muerto destapó dos funciones sin referencias en `nucleo/diagnostics.syn` (`resumen_errores` y su única llamada, `contar_errores`), que se eliminaron (Manual 1 §7.4).
oraculo: tests/auditoria/test_r330_contratos_wasm.py

## Requisito 3 - prueba obligatoria de contratos

requisito: Manual 2 §12
texto: "| Contratos requiere/garantiza | `pytest tests/integration/test_contracts.py -v` | 100% pass |"
implementacion: Oráculo nuevo que lexa, parsea y analiza el módulo con 0 errores, exige los 83 pares de contratos y ejecuta el ratchet de contratos sin deuda para el archivo.
oraculo: tests/auditoria/test_r330_contratos_wasm.py
