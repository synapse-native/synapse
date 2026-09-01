# plan_ME_paridad_own10b — Paridad S1/nativo en el codigo de use-after-move

Método de Trabajo Seguro (MTS, docs/METODO_TRABAJO.md). Cierra H-OWN-10b:
el compilador nativo emite ERR_SEM_VAR_MOVIDA (E-501) para uso tras move,
mientras S1 emite ERR_MEM_USE_AFTER_MOVE (Manual 2 §9). Se alinea el nativo
al codigo canonico SIN romper la deteccion (ambos ya rechazan el programa).

## Estudio previo (hallazgos que fundamentan el plan)

- Taxonomia nativa: codigos ENTEROS. `ERR_SEM_VAR_MOVIDA = 22` (emitido en
  nucleo/analizador_semantico.syn:679 con texto hardcodeado "(E-501)").
- `ERR_SEM_ACCESO_MEMORIA_MOVIDA = 23` ("Acceso prohibido a memoria movida")
  esta DEFINIDO en errores.syn/diagnostics.syn PERO NO SE EMITE en ningun lado
  (candidato natural a reutilizar como codigo canonico de use-after-move).
- `ERR_MEM_USE_AFTER_MOVE` NO existe en el nativo ni en la tabla de mapeo
  compilador/generator/generator.py:579 (S1 string -> entero nativo). Por eso
  S1 y nativo son incomparables en este codigo.
- LSP (synapse_lsp/features/diagnostics.py:8-12) tiene `_CODIGOS_OWNERSHIP`
  con los strings S1; el marcador "[ERR_LIFETIME]" se aplica si el code esta
  en ese conjunto. Para paridad, el codigo canonico debe entrar ahi.
- Emision unica de use-after-move en nativo: analizador_semantico.syn:677-679
  (funcion analizar_expr, NODO_IDENTIFICADOR ya movido). Un solo punto.

## Requisito 1 (ME-P1) — Unificar el codigo canonico (aditivo, sin tocar emision)

requisito: Manual 2 §9
texto: "uso de variable invalidada por move previo ... ERR_MEM_USE_AFTER_MOVE"
implementacion:
  - Renombrar nativo ERR_SEM_ACCESO_MEMORIA_MOVIDA (23) -> ERR_MEM_USE_AFTER_MOVE
    (mantener valor 23) en nucleo/errores.syn, nucleo/analizador_semantico.syn,
    nucleo/diagnostics.syn (mensaje: "Uso ilegal de variable ya movida '{nombre}'").
  - Anadir en compilador/generator/generator.py:579 la entrada
    "ERR_MEM_USE_AFTER_MOVE": 23 (round-trip S1<->nativo).
  - Anadir "ERR_MEM_USE_AFTER_MOVE" a _CODIGOS_OWNERSHIP en
    synapse_lsp/features/diagnostics.py.
  - NO se modifica el sitio de emision (679) ni ningun test -> tests actuales
    en verde.
oraculo: tests/unit/test_lsp_f12.py
oraculo: tests/integration/test_ownership_10.py

## Requisito 2 (ME-P2) — Cambiar emision nativa + actualizar tests (aprobado)

requisito: Manual 2 §9
texto: "uso de variable invalidada por move previo ... ERR_MEM_USE_AFTER_MOVE"
implementacion:
  - nucleo/analizador_semantico.syn:679: sem_error(est, ERR_SEM_VAR_MOVIDA,...)
    -> sem_error(est, ERR_MEM_USE_AFTER_MOVE, ...); texto "(E-501)" -> "(E-504)".
  - Actualizar ~16 assertions inmutables en tests/integration/test_fase2_nativa_hm.py
    (E-501 / ERR_SEM_VAR_MOVIDA -> E-504 / ERR_MEM_USE_AFTER_MOVE). APROBADO por
    el Arquitecto (regla 5) en el cierre de H-OWN-10.
oraculo: tests/integration/test_fase2_nativa_hm.py
oraculo: tests/integration/test_ownership_10.py

## Requisito 3 (ME-P3) — Limpieza de codigo muerto / mensajes

requisito: Manual 2 §9
texto: codigo canonico unico para use-after-move en ambos compiladores
implementacion:
  - Tras ME-P2, ERR_SEM_VAR_MOVIDA (22) ya no se emite para use-after-move:
    decidir eliminacion o alias (regla codigo muerto), actualizando diagnostics.syn.
  - Alinear mensaje S1 ERR_MEM_USE_AFTER_MOVE para quitar "por lanzar/concurrencia"
    (cubre tambien canal); verificar test_spawn / test_concurrency.
oraculo: tests/integration/test_fase2_nativa_hm.py
oraculo: tests/integration/test_ownership_10.py
oraculo: tests/integration/test_spawn.py
oraculo: tests/integration/test_concurrency_10.py

## Riesgos y validacion por ME

- ME-P1: bajo. Requiere rebuild del compilador nativo (S1->S2->S3, timeout >=900s)
  para confirmar que compila; tests S1/LSP siguen verdes.
- ME-P2: medio. Toca tests inmutables (aprobado) + rebuild nativo + bootstrap
  S2==S3 obligatorio. Oraculo: suite HM nativa (~100+ tests) + ownership S1 21/21.
- ME-P3: bajo/medio. Requiere revisar que ERR_SEM_VAR_MOVIDA no se use en otra
  ruta antes de eliminarlo.
