# Plan de Micro-Entregable r333_std_texto_strcpy

## Objetivo

El test inmutable `tests/unit/test_std_contracts.py::test_texto_strcpy_f_tiene_garantiza`
exige `strcpy_f` con contrato en `std/texto.syn`. La función se perdió en un
barrido anterior y el test quedó en rojo, tanto en local como en la suite de CI.

## Requisito 1 — contrato verificable de strcpy_f

requisito: Manual 2 §5.1
texto: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
implementacion: `std/texto.syn` restaura los envoltorios públicos `strlen_s`, `strstr_f`, `strchr_f`, `atoi_f`, `strcpy_f` y `strncpy_f` con `requiere`/`garantiza` de dominio, delegando en los `_syn_str*` ya declarados; `strcpy_f` cumple el test inmutable y los drivers de OpenSyn vuelven a compilar sin `Función no definida`. No cambia el runtime C ni el comportamiento de los builtins.
oraculo: tests/unit/test_std_contracts.py
