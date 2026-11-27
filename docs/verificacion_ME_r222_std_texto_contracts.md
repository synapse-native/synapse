# Verificación ME r222_std_texto_contracts

**Base:** 33320c9 (R219). **Método:** MTS + TDD + MTO. **Tests existentes:** no
modificados. **Alcance:** `std/texto.syn` + oráculo nuevo.

## Marcas por requisito

- Manual 2 §5.1 R1 `requiere` booleano antes del cuerpo: las dos definiciones de `contiene()` declaran `requiere: verdadero` sin reintroducir la precondición retirada por H-R196-1 (evidencia `std/texto.syn:13`, `std/texto.syn:14`, `std/texto.syn:105`; oráculo `tests/auditoria/test_oraculos_r222_std_texto.py`): CUMPLE

- Manual 2 §5.1 R2 `garantiza` observable sobre `_resultado_`: `cmp_texto`, `strlen_s`, `strstr_f`, `strchr_f`, `atoi_f`, `strcpy_f` y `strncpy_f` restauran sus contratos públicos (evidencia `std/texto.syn:207`, `std/texto.syn:208`, `std/texto.syn:232`, `std/texto.syn:239`; oráculo `tests/auditoria/test_oraculos_r222_std_texto.py`): CUMPLE

- Manual 6 §3.1 R3 declaraciones `externo` de C en Synapse: los envoltorios llaman a los `_syn_str*` declarados como `externo funcion` en el mismo archivo (evidencia `std/texto.syn:255`, `std/texto.syn:264`, `std/texto.syn:270`; oráculo `tests/auditoria/test_oraculos_r222_std_texto.py`): CUMPLE

- Manual 8 §1.7 R4 `contiene`/`indice_de`/`reemplazar` como builtins C expuestos en Synapse: el binding `contiene` conserva `_syn_texto_contiene` y el oráculo E2E verifica subcadena vacía y ejecución real (evidencia `std/texto.syn:13`, `std/texto.syn:15`; oráculo `tests/auditoria/test_oraculos_r222_std_texto.py`): CUMPLE

## Validación ejecutada

- Oráculo propio: `tests/auditoria/test_oraculos_r222_std_texto.py` 4/4 GREEN
  (contratos de todas las definiciones de `contiene`, envoltorios históricos,
  `contiene(texto, "")` E2E y `cmp_texto`/`strcpy_f` E2E).
- Tests de contrato existentes: `tests/unit/test_std_contracts.py` 20/20 GREEN
  (antes 17/20; no se modificó el test).
- Prueba E2E manual: programa que importa `std.texto` y ejecuta `cmp_texto`
  retorna 7; `main.py` genera y enlaza los módulos `_texto.c`, `_sistema.c`,
  `_io.c` y `_cripto.c` sin errores.
- Gates:
  - `python auditoria/contrastar.py --plan docs/plan_ME_r222_std_texto_contracts.md`:
    todos los chequeos pasan.
  - `python auditoria/alineacion.py --verificar --me r222_std_texto_contracts`:
    alineación verificada, evidencia `auditoria/evidencia/beb9f255cf3636f8.json`.
  - `python auditoria/verificar_alineacion.py`: sin brechas.

## Hallazgos

- H-R222-1 (resuelto): los envoltorios públicos `cmp_texto`, `strlen_s`,
  `strstr_f`, `strchr_f`, `atoi_f`, `strcpy_f` y `strncpy_f` se perdieron en
  `a2d0ca3` (r199); se restauraron desde `d022ad8` con contratos.
- H-R222-2 (resuelto): `contiene` quedó sin `requiere` tras H-R196-1; se añadió
  `requiere: verdadero` (sin precondición semántica) para cumplir M2 §5.1 sin
  revertir la decisión ratificada.
- H-R222-3 (observación): `std/texto.syn` conserva definiciones duplicadas de
  `contiene`/`indice_de`/`reemplazar` posteriores a `importar std.sistema`; no
  se eliminaron en este ME para no ampliar el alcance. Registrado como deuda
  de limpieza para R228.
