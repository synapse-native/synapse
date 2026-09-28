# Plan ME 33.4b_genericos_para_mapa — Fase 33.4 (cierre de H-R153-3)

**Fuente:** ROADMAP.md §33.4 (2026-09-26). **Base:** 66d90ac (5ff9235+docs).
**Alcance:** (1) genéricos de usuario con la forma que prescribe la ley
(`estructura Caja(T):` + instanciación `Caja(5)` con inferencia — la ley NO
define `Caja<T>` con corchetes angulares); (2) `para k en mapa` — k itera las
CLAVES y el valor se accede con `m[k]` (33.4a); el "par ordenado" del ROADMAP
se registra como DESVIACIÓN del ROADMAP respecto de la ley (M3 §3: UN
identificador), decisión D-33.4b-1; (3) módulo de prueba TDD en la matriz.
**Hecho de la sesión 33.4a (probes E2E):** `para k en m` en S1 compila pero
SEGFAULTA (cast del handle a ListaNodo*); genérico `Caja(T)` falla en el parser
S1 ("Se esperaba COLON, se encontró LPAREN"); `Caja<T>` falla ("Token
inesperado COLON").

## R1 — Parser S1: parámetro de tipo entre paréntesis
requisito: Manual 2 §2
texto: "declaracion_estructura ::= \"estructura\" IDENTIFICADOR [ \"(\" IDENTIFICADOR \")\" ]? \":\" NEWLINE INDENT { campo } DEDENT" (M2 §2 —
la estructura genérica lleva UN parámetro de tipo entre PARENTESIS, opcional).
implementacion: `compilador/parser_declarations.py` (_parsear_def_estructura
L171): tras tok_nombre, si LPAREN → IDENTIFIER → RPAREN opcional; guardar el
nombre del parámetro en el nodo (`param_generico`). Los campos pueden referir
`T` como tipo; `traducir_tipo_c`/semantic ya toleran nombres desconocidos como
struct-puntero — monomorfización en el emisor (R2).
// cumple Manual 2 §2
oraculo: tests/auditoria/test_oraculos_334b_genericos.py

## R2 — Emisor S1: monomorfización en la instanciación
requisito: Manual 2 §8.2
texto: "Synapse utiliza un algoritmo de inferencia de tipos basado en **Hindley‑Milner** (algoritmo W)." (M2 §8.2 —
la unificación resuelve el T real desde el argumento del constructor; no hay
instanciación explícita `Caja<T>` en la gramática: el tipo se INFERE).
implementacion: `compilador/generator/emit_declarations.py`
(visitar_estructura L192): si `param_generico` → registrar plantilla en
`ctx._genericas[nodo.nombre] = campos` y NO emitir typedef (T no tiene tipo C
aún). `compilador/generator/emit_expressions.py` (instanciación de struct con
ctor, ~L430): si el nombre está en `_genericas` → resolver T = tipo del
argumento; nombre monomorfizado `Caja_T`; emitir typedef `typedef struct
Caja_T {...} Caja_T;` (lazy, antes de la primera función que lo usa — los
typedefs de struct se emiten en la fase de declaraciones: encolar en
`ctx._typedefs_genericos` y volcarlos en emit_declarations) + emitir el
constructor con el campo asignado. Registro global determinista (orden
alfabético, M1 §7.1).
// cumple Manual 2 §8.2
oraculo: tests/auditoria/test_oraculos_334b_genericos.py

## R3 — S1: `para k en mapa` itera las claves
requisito: Manual 2 §4.3
texto: "**Mapas:** `Mapa<K,V>` (diccionario, definido en la biblioteca estándar)." (M2 §4.3 —
mismo contrato runtime que 33.4a; M3 §5.2: Mapa soporta `[]`, `keys()`,
`values()`, `iter()` → en modo es: `claves()`/`valores()`; el runtime ya
tiene _syn_mapa_claves (lista de char* reales de los pares OCUPADO).
implementacion: `compilador/generator/emit_control.py` (_emitir_para_en
L93+): rama `tipo_iterable.startswith('Mapa<')` ANTES del fallback: handle →
`_syn_mapa_claves` → for i < _syn_lista_longitud →
`k = (CadenaSegura){(int)strlen((char*)(intptr_t)slot),
(char*)(intptr_t)slot}` (la variable es texto con la CLAVE; el valor con
`m[k]`, 33.4a). Externs `_syn_mapa_claves`/`_syn_lista_liberar` en
context.py/generator.py + liberar la lista de claves al salir del bloque
(RAII, M2 §9.1).
// cumple Manual 2 §4.3
oraculo: tests/auditoria/test_oraculos_334b_genericos.py

## R4 — Nativo: genérico + para-en Mapa + métodos claves()/valores()
requisito: Manual 2 §2; Manual 2 §4.3
texto: "estructura Caja(T):" (M2 §2; "**Mapas:** `Mapa<K,V>` (diccionario, definido en la biblioteca estándar)." (M2 §4.3)
implementacion: `nucleo/parser_analisis.syn`/`nucleo/analizador_semantico.syn`
(parseo de `estructura`): aceptar `( IDENTIFICADOR )` opcional tras el nombre
y registrar el parámetro; `nucleo/generador/expr_eval.syn` (instanciación
struct con args): unificar T con el tipo del argumento y emitir typedef
monomorfizado; `nucleo/generador/emit_control.syn` (nodos_flujo/emit_control
— donde vive el emisor de PARA_EN): misma rama Mapa que S1
(_syn_mapa_claves + slots char* → CadenaSegura); métodos `claves()`/`valores()`
de Mapa → extern _syn_mapa_claves/_syn_mapa_valores (tipo Lista<texto> /
Lista<entero>) en el resolutor de métodos.
// cumple Manual 2 §2
oraculo: tests/auditoria/test_oraculos_334b_genericos.py

## R5 — Módulo de prueba TDD en la matriz + bootstrap
requisito: Manual 1 §6
texto: "**Regla de hierro:** Ninguna característica nueva puede romper el *bootstrap* (etapas 0→1→2→3 con diff binario 0)." (M1 §6 —
el módulo de prueba ejercita las extensiones SIN tocar los .syn del nucleo).
implementacion: `tests/nucleo/test_modulos_compilan.py`: módulo .syn nuevo
(estructura genérica Caja(T) instanciada + `para k en m` + `m[k]` +
`m.claves()`) — RED primero (parser rechaza), GREEN tras R1-R4; unity
regenerada con _rebuild_generator.py; bootstrap stage1→stage2; matriz 35/35;
unit sin regresión.
// cumple Manual 1 §6
oraculo: tests/auditoria/test_oraculos_334b_genericos.py

## Decisión registrada en este plan
- **D-33.4b-1 (desviación del ROADMAP hacia la ley):** el ROADMAP §33.4 pide
  "`para k en mapa` con par ordenado"; la ley (M3 §3, bucle_para_rango con UN
  IDENTIFICADOR) no define pares. Se implementa k=claves + m[k] para valores
  (+ claves()/valores() de M3 §5.2). Pendiente de ratificación del Arquitecto.

## Criterios de aceptación (33.4b)
- Probe E2E S1 y nativo: `estructura Caja(T)` + `Caja(5)` + `c.valor` → rc=0.
- Probe E2E `para k en m` + `m[k]` + `m.claves()` → rc=0, SIN segfault.
- test_modulos_compilan.py GREEN con el módulo nuevo; matriz 35/35;
  bootstrap verde; unit 514/514 sin regresión.
