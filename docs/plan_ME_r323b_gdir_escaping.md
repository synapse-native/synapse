# Plan de Micro-Entregable r323b_gdir_escaping

## Objetivo

Corregir el escape C de la extraccion del directorio del GCC en
`nucleo/principal.syn`. r323 dejo ocho barras invertidas en la fuente Synapse;
el lexer las decodifica a cuatro en C (`'\\\\'`), un literal multicaracter que
no coincide con el separador Windows. La forma correcta es cuatro barras en
Synapse, que producen `'\\'` en C (un backslash).

## Requisito 1 - separador Windows con escape C correcto

requisito: Manual 9 §6.2
texto: "La verificación del bootstrap (diff 0 bytes)."
implementacion: `nucleo/principal.syn` usa cuatro barras invertidas en la fuente para que el C emitido sea `'\\'` (un backslash) y `_gdir` se recorte tanto con `/` como con `\`; el PATH del hijo se ajusta en Windows y POSIX.
oraculo: tests/auditoria/test_r323b_gdir_escaping.py
