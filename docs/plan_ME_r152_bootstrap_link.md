# Plan ME r152_bootstrap_link — Reparar el enlace del bootstrap S1 (H-R151-3)

Origen: docs/plan_ME_r151_linea_base.md, hallazgo H-R151-3 (verificado con probe:
logs/r151_s1_probe.log, rc=1 en AMBAS rutas de enlace desde ba2c5ee, Fase 31).
Ratificación del Arquitecto (sesión 2026-09-20): "repara y ajusta todo, sigue MTS
y MTO, los tests deben ser TDD". Los tests de línea base (r151) NO se tocan: el
oráculo RED (test_r3_param_adt_s1) pasa a GREEN reparando el CÓDIGO (TDD).

Diagnóstico (causa raíz verificada sobre el árbol):
1. Globals F5-1 sin definición en la ruta unity/monolítica. compilador/generator/
   generator.py emite `void* _G_fn_garantizas_actuales = 0;` + `char
   _G_fn_ret_tipo_c[64];` SOLO en el bloque `tiene_principal` del modo 'modulo'
   (líneas 1830-1832); _emit_cabecera_comun (ruta 'completo'/unity, tras
   _G_lanzar_count línea 1182) NO los emite. Verificado en synapse_unity.c
   (generado hoy): definiciones de _G_lanzar_count/_G_tipo_aliases presentes, par
   F5-1 ausente → el enlace unity falla con `_G_fn_ret_tipo_c` y
   `_G_fn_garantizas_actuales` indefinidos (el modular sí los define: su error solo
   lista los 5 símbolos de R2). Los usan via asm extern nucleo/generator.syn:1202,
   3521, 3653 (gen_visitar_retornar: contratos garantiza, Manual 2 §5.1).
2. Subcomandos lint/fmt/test (ba2c5ee, Fase 31) llaman externs C que NUNCA
   existieron (`lint_archivo_c`, `lint_fix_c`, `fmt_check_c`, `fmt_write_c`,
   `ejecutar_pruebas`; `git log -S` solo encuentra ba2c5ee) → enlace modular Y
   unity rotos. Las implementaciones reales existen como .syn pero NINGUNA está
   importada por nucleo/principal.syn: nucleo/lint.syn (lint_archivo, lint_fix),
   nucleo/formatter.syn (formatear_texto, fmt_archivo), nucleo/reports.syn
   (generar_junit, generar_json, ResultadoTest). principal.syn ya documenta la
   intención (líneas 713-722: "synapse test --junit | --coverage | --json ...
   escribir_reporte ... para escribir cualquier reporte a disco").

Bloques MTS (requisito/texto/implementacion/oraculo):

## R1 — Globals F5-1 sin definición en la ruta unity ('completo')
requisito: Manual 1 §6
texto: "**Regla de hierro:** Ninguna característica nueva puede romper el *bootstrap* (etapas 0→1→2→3 con diff binario 0). El determinismo se verifica obligatoriamente en la CI mediante la comparación de los hashes SHA‑256 de las etapas 2 y 3."
implementacion: compilador/generator/generator.py — _emit_cabecera_comun emite las
definiciones `void* _G_fn_garantizas_actuales = 0;` y `char _G_fn_ret_tipo_c[64];`
después de _G_lanzar_count, en paridad EXACTA con el bloque 'modulo'
tiene_principal (líneas 1830-1832) y con el orquestador nativo
(nucleo/generator.syn:4006-4007, "definidos aqui, usados via asm() en
funciones.syn/nodos_flujo.syn"). Además `#include <time.h>` en el preludio común
(cli_test mide el tiempo real del test con clock(); Manual 1 §7.1 estilo: sin
tabs, 4 espacios). Comentario `# cumple Manual 1 §6`. El bloque 'modulo' ya
define el par (sin cambio); ni el header compartido (externs correctos) ni el
orquestador nativo se tocan.
oraculo: tests/auditoria/test_oraculos_r152.py

## R2 — Subcomandos lint/fmt/test con backend real (elimina los 5 externs fantasma)
requisito: Manual 8 §4.1
texto: "| **`synapse lint`** (Fase 31) | Ejecuta el linter nativo sobre el código fuente. |" + "| **`synapse fmt`** (Fase 31) | Ejecuta el formateador nativo sobre el código fuente. |" + "| `synapse test` | Ejecuta la suite de pruebas del proyecto actual. |"
implementacion: nucleo/principal.syn — AJUSTE POR EVIDENCIA (probe
  tests/fixtures/tmp_probe_lista.syn, 2026-09-20): el pipeline Python S1 NO
  compila llamadas a métodos `obj.metodo(...)` (13 errores de parseo), ni
  `para x en ...`, ni `Lista<T>()`; los módulos lint.syn/formatter.syn/reports.syn
  usan esa sintaxis y por tanto NO pueden entrar al unity del bootstrap
  (H-R152-4: se Documentan como módulos de referencia canónicos, sin `importar`;
  sus tests tests/nucleo/test_lint.py y test_fmt.py son estructurales y siguen
  GREEN). El backend se implementa como C embebido en el dispatch de
  principal.syn, con envoltorios .syn PÚBLICOS con contratos requiere/garantiza
  (Manual 2 §5.1):
- (1) eliminar los 5 externs fantasma y el global `_trc` muerto.
- (2) el dispatch detecta subcomando/flags en asm (patrón strcmp existente) y
  fija variables .syn _sub_id/_sub_flag/_sub_ruta (patrón del parseo de -o,
  principal.syn:893) para delegar en funciones .syn:
  * cli_lint(ruta, fix): lee el archivo (_syn_leer_archivo, patrón cache.syn),
    analiza línea a línea (indentación múltiplo de 4 — Manual 1 §7.1) e imprime
    advertencias WARN_LINT_INDENT; --fix normaliza indentación (4 espacios) y
    reescribe con fwrite.
  * cli_fmt(ruta, check): --check (Manual 8 §4.2 "Verifica formato sin modificar
    archivos") normaliza en memoria (trim + colapso de espacios internos, pauta
    lint_fix/normalizar_espacios de lint.syn) y compara byte a byte SIN escribir
    (rc 0/1); sin --check reescribe el archivo normalizado.
  * cli_test(ruta, formato): compila el archivo de pruebas con el propio
    compilador (generar_etapa ya produce el exe enlazado) y lo ejecuta con
    system(); rc propagado; tiempo medido con clock() (CLOCK_REALTIME, requiere
    <time.h> — añadido en R1); --junit/--json REALES: escribe un reporte con 1
    testsuite/testcase y summary (etiquetas y campos en PARIDAD con
    nucleo/reports.syn: generar_junit/generar_json — Manual 9 §6.2) a
    "<ruta>.junit.xml" / "<ruta>.json"; --coverage honesto: mensaje claro y rc=1
    (H-R152-1).
Comentarios // cumple Manual 8 §4.1 en los bloques nuevos.
oraculo: tests/auditoria/test_oraculos_r152.py

## R3 — Bootstrap S1 enlaza y el codegen de parámetros ADT queda verificado (RED→GREEN)
requisito: Manual 2 §4.2
texto: "tipo Resultado<T, E> = ok(T) | err(E)"
implementacion: sin cambios de código propios en este bloque — R1+R2 reparan el
enlace que el oráculo TDD test_r3_param_adt_s1 exige: construye S1 on-demand con
el MISMO comando del job bootstrap del CI (`python main.py nucleo/principal.syn
-o synapse_stage1.exe`) y compila un programa con parámetro `r: Resultado<entero,
texto>` esperando el struct instanciado Resultado_entero_texto (D-2 CERRADA en
CANON_DEUDAS: monomorfización A5; test_r3_param_adt_s2 PASA). El test es
inmutable (r151); el código se corrige hacia el test.
oraculo: tests/unit/test_r3_param_adt.py

## Oráculo global del ME
tests/auditoria/test_oraculos_r152.py + tests/unit/test_r3_param_adt.py
(la matriz tests/auditoria/test_matriz_compilacion.py se ejecuta además antes del
commit: generator.py afecta a TODAS las compilaciones — criterio de no-regresión
35/35)

## Archivos a modificar (producción)
- compilador/generator/generator.py (R1 — aplicado)
- nucleo/principal.syn (R2)
- nucleo/lint.syn, nucleo/formatter.syn, nucleo/reports.syn — NO se tocan ni se
  importan (H-R152-4: usan sintaxis no compilable por S1; permanecen como
  referencia canónica con sus tests estructurales en GREEN)

## Hallazgos
- H-R152-1 (resolución asignada): cobertura real (--coverage, Manual 8 §4.2
  "Genera informe de cobertura en HTML") exige instrumentación de aristas que no
  existe en el compilador; el flag responde con mensaje claro y rc=1 (patrón
  honesto D-R150-4/M3c). Resolución: ME futuro del runner de suites
  multi-archivo con instrumentación.
- H-R152-2 (contrato verificado): la ruta unity solo se ejercita como fallback
  del enlace modular; el oráculo verifica el CONTRATO del generador (par F5-1
  presente en el preludio 'completo' y en el 'modulo') para que la paridad no
  regrese sin detectarlo.
- H-R152-3 (nota de tipado): texto/cadena/CadenaSegura normalizan al mismo tipo
  (compilador/tipos.py:93) — los parámetros texto de cli_* admiten los valores de
  argv_str (cadena) sin conversión.
- H-R152-4 (RESOLUCIÓN ASIGNADA, hallazgo del probe): nucleo/lint.syn,
  formatter.syn y reports.syn usan sintaxis que el pipeline Python S1 no compila
  (llamadas a métodos obj.metodo(), para-en, constructor Lista<T>(), comparación
  `es ok/es err` inexistente en el parser, valor_ok sin definición). Cualquier
  intento de importarlos rompería de nuevo el bootstrap (Manual 1 §6). El módulo
  lint.syn PODADO en esta sesión se REVERSIÓN a HEAD: tests/nucleo/test_lint.py
  (inmutable) exige lint_programa/es_snake_case/lint_nombres presentes como
  texto. Resolución: ME futuro (a) soporte de métodos/genéricos en S1 o (b)
  reescritura de los módulos a sintaxis compilable; hasta entonces su backend
  vivo es el C embebido de principal.syn (R2) y los .syn son referencia canónica
  (status quo previo a ba2c5ee, consistente con el comentario
  principal.syn:716-718 que ya declaraba reports.syn "referencia/canónico").
