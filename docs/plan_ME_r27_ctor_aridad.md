# Plan ME r27_ctor_aridad — validación de aridad del ctor de struct (H-R177-1)

**Fuente:** plan maestro `docs/plan_maestro_deudas.md` (mandato Arquitecto
2026-10-03: "si el código está alineado al manual y el test no, se modifica el
test aplicando TDD y método MTO"). **Base:** 95b2374 (R178). **Método:** MTS.

**TDD (probes ejecutados 2026-10-04, /tmp/probe_r27):** `Punto(1,2)` compila y
ejecuta rc=0 imprimiendo `12` en el nativo (H-R153-4b validación implícita por
emisión); `Punto(1)` (aridad inválida) compila y corre rc=0 en el nativo pero
S1 la rechaza con ERR_SEM_ARGUMENTOS_INVALIDOS (rc=7) — divergencia de
paridad. La raíz: `SemEstructuraInfo.total_campos` existe (L109) pero nunca se
puebla (registrar_estructura L794 lo fija a 0), y r153 eliminó el check en vez
de poblar la metadata.

**Decisión (ratificación en línea, mandato vigente):** M2 L67 define la
estructura como `{ campo }` en orden; H-R153-4 (S1, ratificada r153) acepta
`Struct()` o `Struct(c1..cn)` con n = campos declarados. El nativo se alinea a
esa MISMA regla poblando `total_campos` y restaurando el check; el test r27
(pre-r153: "se esperaban 0") se alinea vía TDD/MTO a la forma ratificada.
Se AGREGA cobertura del caso válido (no existía ningún test de `Punto(1,2)`
válido).

## R1 — total_campos: poblar la metadata de campos en registrar_estructura
requisito: Manual 2 §2
texto: "La gramática de Synapse se define mediante una notación EBNF extendida."
(M2 §2 L38 autoriza la notación EBNF como ley; la regla vigente L67:
`declaracion_estructura ::= "estructura" IDENTIFICADOR [ "(" IDENTIFICADOR ")" ]? ":" NEWLINE INDENT { campo } DEDENT`
— los campos declarados en orden definen la forma del struct).
implementacion: `nucleo/analizador_semantico.syn`
`registrar_estructura`: después de guardar el nombre, recorrer la cadena de
NODO_PARAMETRO de `hijo_izq` del NODO_ESTRUCTURA (patrón de registro ADT de
analizar_paso_estructuras: `tp = nodo_hijo_izq(est, idx_nodo)` + `hermano`)
y contar los campos; poblar `info_estructuras[...].total_campos` con ese
conteo (L794 `= 0` pasa a la cuenta real).
// cumple Manual 2 §2 (ME r27_ctor_aridad R1)
oraculo: tests/auditoria/test_oraculos_r27_ctor_aridad.py

## R2 — check_aridad_nativo: restaurar el check H-R153-4 con paridad exacta
requisito: Manual 2 §8.2
texto: "| Tipos de datos | `pytest tests/integration/test_fase2_nativa_hm.py -v` | 100% pass |"
(M2 §12 tabla de pruebas obligatorias — el tipo de dato de usuario debe
validarse idéntico en S1 y nativo; paridad H-R153-4: se acepta `Punto()` o
`Punto(c1, ..., cn)` con n = campos declarados; otros aridades →
ERR_SEM_ARGUMENTOS_INVALIDOS rc=7).
implementacion: `nucleo/analizador_semantico.syn` bloque NODO_LLAMADA (zona
R27/H-R153-4b): si el callee es estructura Y no es función de usuario, se
cuenta la aridad real de la llamada (recorrido `hermano` desde
`nodo_expr(est, idx)`, como el loop de análisis que sigue) y se compara contra
`info_estructuras[_i27].total_campos`; si `nargs != 0 && nargs != ncampos` →
`sem_error(est, ERR_SEM_ARGUMENTOS_INVALIDOS, idx, msg)` con mensaje paridad
S1 ("Cantidad de argumentos invalida para 'X': se esperaban N"), rc=7. El
comentario se actualiza: H-R153-4b queda SUPERADA (la metadata ahora existe).
// cumple Manual 2 §8.2 (ME r27_ctor_aridad R2)
oraculo: tests/auditoria/test_oraculos_r27_ctor_aridad.py

## R3 — test_r27_alineado: el test pasa de pre-r153 a la ley vigente (TDD/MTO)
requisito: Manual 7 §2.3
texto: "Los tests del repositorio prueban comportamiento real, no la presencia de texto en el artefacto generado."
implementacion: `tests/integration/test_fase2_nativa_hm.py`:
(a) `test_r27_struct_ctor_con_argumentos_rechazado` pasa a
`test_r27_struct_ctor_posicional_valido`: `_PROG_R27_STRUCT_CTOR_CON_ARGS`
(`Punto(1, 2)`) debe compilar rc=0 y ejecutar imprimiendo `1\n2` (los ctors
posicionales son LEGALES desde r153, H-R153-4/4b; probe TDD demuestra que el
nativo ya lo soporta);
(b) NUEVO `test_r27_struct_ctor_aridad_invalida_rechazada` con
`_PROG_R27_STRUCT_CTOR_ARIDAD_BAD` (`Punto(1)` sobre struct de 2 campos):
debe fallar rc=7 con `Cantidad de argumentos invalida para 'Punto'` (paridad
S1 semantic_types.py H-R153-4). Docstrings citan M2 L67 + H-R153-4/4b + R179.
Mapeo MTO: OBL-M2-05 (Manual 2 §12) en la cabecera del archivo.
// cumple Manual 7 §2.3 (ME r27_ctor_aridad R3)
oraculo: tests/auditoria/test_oraculos_r27_ctor_aridad.py

## R4 — oraculo_me: oráculo E2E del ME
requisito: Manual 2 §12
texto: "| Contratos requiere/garantiza | `pytest tests/integration/test_contracts.py -v` | 100% pass |"
implementacion: `tests/auditoria/test_oraculos_r27_ctor_aridad.py`:
(r1) nativo stage2 `Punto(1,2)` rc=0 + salida `1\n2` (sin ESCAPE de errores);
(r2) nativo stage2 `Punto(1)` rc=7 + mensaje paridad S1;
(r3) paridad S1: `Punto(1,2)` rc=0 vía cli pipeline; `Punto(1)` rc!=0;
(r4) `Punto()` (zero-arg) sigue compilando rc=0 en nativo (H-R153-4 forma
canónica de los módulos del compilador).
// cumple Manual 2 §12 (ME r27_ctor_aridad R4)
oraculo: tests/auditoria/test_oraculos_r27_ctor_aridad.py

## Verificación
- `rm -f nucleo/_principal.c nucleo/_principal.c.o synapse_stage1.exe && .venv/Scripts/python.exe main.py nucleo/principal.syn -o synapse_stage1.exe`
- `rm -f synapse_stage2.exe && ./synapse_stage1.exe nucleo/principal.syn -o synapse_stage2.exe` (ambos rc=0, timestamps frescos)
- Probes /tmp/probe_r27: r27_ok (12), r27_bad (rc=7 nuevo), r27_zero (rc=0)
- `.venv/Scripts/python.exe -m pytest tests/auditoria/test_oraculos_r27_ctor_aridad.py -v` → 4/4
- `.venv/Scripts/python.exe -m pytest "tests/integration/test_fase2_nativa_hm.py::test_r27_struct_ctor_posicional_valido" "tests/integration/test_fase2_nativa_hm.py::test_r27_struct_ctor_aridad_invalida_rechazada" -v` → 2/2
- Regresión: fase2 `-k "r9 or r27 or r20 or f37 or f313"`, unit 514, matriz.
