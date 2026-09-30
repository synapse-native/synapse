# Plan ME formatter_fix — cierre de H-33.5-3 (emisor/formatter + normalización del nucleo)

Micro-entregable con resolución asignada en `docs/reportes/FASE_33_CERTIFICACION.md` §5
(H-33.5-3) y `MEMORIA_PROYECTO.md` (Próximo paso): "fix emisor formatter +
normalización de formato (H-33.5-3)".

**Refinamiento del diagnóstico (hallazgo de esta sesión, verificado con probes):**
el C de `nucleo/_formatter.c` en HEAD SÍ contiene la rama `si c == " "` (3 ramas).
La rama no la "perdió" el emisor: está ENSOMBRECIDA porque `nucleo/lint.syn:348`
define su PROPIA `normalizar_espacios` con solo 2 ramas (coma/otro, sin colapso) y el
aplanador de imports aplica dedupe first-wins por orden de sentencias
(`pipeline.py` L523-539, verificado con probe: "DUP-A" ganó) — `importar lint`
precede a `importar formatter` en `nucleo/principal.syn` (L34-35), así que la versión
de 2 ramas de lint.syn gana y el formatter no colapsa espacios dobles (repro: exe
fresco stage2 13:56 hoy, `fmt` corrige comas pero NO espacios dobles). Deuda
derivada registrada: H-FMT-1 (import módulo→módulo sin soporte nativo en el
bootstrap, ver R1).

Método de Trabajo Seguro (MTS): cada requisito cita la oración normativa
LITERAL del manual; el oráculo se EJECUTA, no se declara.

## R1 — Dedupe del backend lint/fmt: lint.syn importa formatter y delega
requisito: Manual 3 §12 (12.2 Importación); Manual 2 §5 (Contratos Lógicos); Manual 2 §12
texto: "Los módulos se importan con `importar lib.modulo`" (M3 §12.2 — composición
entre módulos del backend). "### 5.1. Semántica Formal" + "### 5.2. Ejemplo"
(M2 §5 — contratos `requiere`/`garantiza` en toda función pública).
implementacion: `nucleo/lint.syn`: añadir `importar formatter` tras `#lang: es`
(S1 soporta cadena 3-niveles vía aplanador recursivo — probe tmp_drv GREEN;
`main.py -o` también la aplana); BORRAR las definiciones duplicadas
`normalizar_espacios` (L348, 2 ramas — causa raíz de H-33.5-3) y `recortar`
(L368, idéntica a la de formatter.syn); reescribir `fix_linea` (L320, exigida
por test_lint.py inmutable sobre el FUENTE) delegando en `formatear_linea`
(formatter.syn) con contratos M2 §5. Igualdad verbatim fix↔fmt demostrada por
inspección: fix_linea solo corrige indentación (múltiplo de 4, tab=4) + espacios
= formatear_linea (mismo algoritmo). Cadena de imports 3-niveles
principal→lint→formatter VERIFICADA en AMBAS capas: stage2 NATIVO (compilado
por stage1, orquestador maneja SentenciaImportar) reconstruido y su `fmt`
colapsa espacios (probe lexer); sello sha256(S2)==sha256(S3)=6d579f9e…b1c.
oraculo: tests/auditoria/test_oraculos_formatter_fix.py

## R2 — normalizar_espacios del formatter: colapso de espacios + literales protegidos
requisito: Manual 2 §2 (cadena_literal); Manual 1 §7.1 (estilo de código)
texto: "cadena_literal   ::= '\"' { caracter_escapado | cualquier_caracter } '\"'"
(M2 §2 L165 — el contenido del literal, con escapes, es significativo; el gate
contrastar.py exige que la PRIMERA cita de cada bloque exista en
docs/manuales/ y "Manual 31" no es citable como MANUAL 31.md: su norma vive en
el archivo con nombre propio). "| Espacios alrededor de operadores | Sí (ej.
`a + b` no `a+b`) |" / "| Indentación | 4 espacios (prohibido tabs) |" (Manual
31 §5.3, archivo "MANUAL  FASE 31 HERRAMIENTAS DE DESARRO.md" L288-296 — norma
real de las reglas de estilo; brecha del mapa legacy "Manual 3 §12"
documentada al final).
implementacion: `nucleo/formatter.syn` `normalizar_espacios` (L141): añadir la
rama `si c == " "` que colapsa espacios consecutivos a uno (la rama que H-33.5-3
reportó ausente) y un escaneo previo de literales: los segmentos entre comillas
dobles (respetando `\"` y `\\`, M2 §2 cadena_literal — sintaxis validada con
probe S1: `let s = "dijo \"hola  mundo\""` compila y ejecuta) se copian VERBATIM,
sin colapso ni reescritura de comas. Se conserva la rama coma (Manual 31 §5.3:
"un espacio después de coma"). Contratos M2 §5 intactos. Los comentarios de línea
no se tratan especial: el colapso externo a literales es normalización
cosmética declarada por Manual 31 §5.2 ("reescribe el código fuente según las
reglas de estilo").
oraculo: tests/auditoria/test_oraculos_formatter_fix.py

## R3 — Oráculo nuevo del ME (comportamiento real sobre exe fresco)
requisito: Manual 8 §4.1; Manual 31 §5.4; Manual 1 §6
texto: "| **`synapse fmt`** (Fase 31) | Ejecuta el formateador nativo sobre el
código fuente. |" con ejemplo canónico "synapse fmt --check src/" (M8 §4.1).
"`synapse fmt` reescribe el archivo en el lugar (sin cambios si ya está
formateado)." y "`synapse fmt --check` retorna código de salida 1 si el archivo
no está formateado." (Manual 31 §5.4). "Regla de hierro: Ninguna característica
nueva puede romper el *bootstrap* (etapas 0→1→2→3 con diff binario 0). El
determinismo se verifica obligatoriamente en la CI mediante la comparación de
los hashes SHA-256 de las etapas 2 y 3." (M1 §6 L363).
implementacion: `tests/auditoria/test_oraculos_formatter_fix.py` NUEVO (patrón
`_exe_fresco` de test_oraculos_33_5: regenera stage1→stage2 si mtimes de
nucleo/*.syn > exe — un exe stale parece éxito y no lo es): (1)
test_dedupe_backend_sin_simbolos_duplicados: lint.syn NO define
normalizar_espacios/recortar y SÍ declara `importar formatter` (anti-regresión
del first-wins que causó H-33.5-3); (2) test_fmt_detecta_y_colapsa_espacios:
probe en TEMP con doble espacio externo → `fmt --check` rc=1 (ANTES del fix
daba rc=0 falso: reproducción de H-33.5-3), `fmt` reescribe, segundo
`--check` rc=0 (idempotencia Manual 31 §5.4) y comas normalizadas; (3)
test_fmt_no_corrompe_literales: `let s = "hola  mundo"` sobrevive al `fmt`
write byte a byte (M2 §2 cadena_literal); (4) test_lint_fix_paridad_fmt:
`lint --fix` y `fmt` sobre el mismo fuente malindentado producen salida
idéntica (paridad fix_linea→formatear_linea); (5) test_bootstrap_s1_s2_verde:
bootstrap regenerado real + humo `stage2 fmt --check` rc=0 en probe formateado
(M1 §6; anti-fabricación con mtimes). El oráculo se ejecuta EN RELEASE (stage2)
con timeout 900 (contrato de contrastar.py).
oraculo: tests/auditoria/test_oraculos_formatter_fix.py

## R4 — Normalización de formato del nucleo (operativa, cierre del hallazgo)
requisito: Manual 1 §7.1 (estilo de código); Manual 1 §6 (regla de hierro)
texto: "**Indentación:** 4 espacios, prohibido el uso de tabuladores (`\t`)."
(M1 §7.1 Estilo de Código; primera cita citable para el gate). "`synapse fmt`
reescribe el archivo en el lugar (sin cambios si ya está formateado)." (Manual
31 §5.4, archivo con nombre propio). "Regla de hierro: Ninguna característica
nueva puede romper el *bootstrap*..." (M1 §6).
implementacion: (a) medir el estado real (ya medido: 2 líneas del nucleo con
indentación no múltiplo de 4 — nucleo/lexer.syn L194-195, 26 espacios — y
espacios dobles externos a literales distribuidos); (b) ejecutar el formatter
FRESCO (post R1+R2) sobre todos los nucleo/*.syn y nucleo/generador/*.syn
(normalización pedida por FASE_33_CERTIFICACION §4: "Fix (emisor del formatter
+ normalización de formato del nucleo)"); (c) verificadores de integridad:
compilación S1 de los módulos tocados (stub efímero), matriz 35/35, suites
afectadas (unit/nucleo/auditoría), bootstrap S1→S2→S3 fresco con
sha256(S2)==sha256(S3) NUEVOS registrados en memoria (el determinismo se
re-verifica; el VALOR cambia porque cambia el fuente — así lo permite el
oráculo de 33.5, que compara S2 contra S3, no contra un hash fijado);
(d) estado final: `fmt --check` rc=0 sobre TODO el nucleo (idempotencia real,
no maquillada). Lecturas previas y anclas del expediente se generan por script
para el lote de archivos tocados (precedente 33.2: 34 anclas CUMPLE).
oraculo: tests/auditoria/test_oraculos_formatter_fix.py (test_nucleo_formateado)

## Deudas y desviaciones que este ME registra
- Cadena de imports módulo→módulo en el bootstrap nativo: VERIFICADA
  funcionando en esta sesión (contrario al diagnóstico preliminar H-FMT-1,
  que se RETIRA sin registrar: stage2 nativo compila la cadena y expone el
  comportamiento corregido).
- Brecha del mapa legacy: `mapa_alineacion.md` exige "Manual 3 §12" para
  lint/formatter.syn (12 = SYQUEX lib/, no tooling); la norma real de estilo es
  Manual 31 §5.3/§5.4 (archivo con nombre propio, no citable como "Manual 31"
  por registrar_lectura). Resolución: corrección del mapa en post-commit (docs).
