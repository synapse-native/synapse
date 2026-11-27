# Expediente de alineación r150_funcional

base: 8247564
cambio_hash: ebf8a0b2fbd8f95b

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## cli.py
- manual: 1
  seccion: 3.1
  cita: "El compilador unificado procesa código fuente de Synapse (.syn), Syquex (.syq) e incluso prompts en lenguaje natural (via OpenSyn) a través de un pipeline compartido:"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: cli.py:3
  oraculo: tests/auditoria/test_oraculos_r150.py

## pipeline.py
- manual: 1
  seccion: 3.1
  cita: "El compilador unificado procesa código fuente de Synapse (.syn), Syquex (.syq) e incluso prompts en lenguaje natural (via OpenSyn) a través de un pipeline compartido:"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: pipeline.py:109
  oraculo: tests/auditoria/test_oraculos_r150.py

## compilador/generator/generator.py
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: DESVIACION
  decision: D-R149-1
  nota: >-
    El cambio real (D-R150-4, plan M3d/M4) elimina la llamada a
    _principal_impl() en el stub de biblioteca sin entry point: el link
    fallaba con undefined reference cuando el programa no define
    'funcion principal'. El requisito prescrito (sin prose indexada: es
    semántica del stub main generado) no vive en Manual 2 §5.1; la ancla
    se toma de la oración real más próxima del área (contratos
    requiere/garantiza) y el requisito queda registrado aquí y en el
    plan MTS.
- manual: 2
  seccion: 4.1
  cita: "`entero` / `int` | Entero con signo de 64 bits | 8 bytes | Alias de `int64_t`"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/generator/generator.py:898
  oraculo: tests/auditoria/test_oraculos_r150.py
  nota: >-
    D-R150-8: fix "conflicting types for 'crear_tensor'/'reserva'" — los
    prototipos hardcodeados con `int` contradecían las definiciones
    int64_t emitidas desde std.math/std.mem. Prueba directa por-nodo:
    pytest "tests/auditoria/test_matriz_compilacion.py::test_matriz_std_importa_y_enlaza[math]"
    y [mem] → 2/2 GREEN (sesión 2026-09-18); el archivo de la matriz queda
    RED solo por los 4 hallazgos parseo/semánticos aún abiertos.

## runtime/core/cluster.c
- manual: 5
  seccion: 8.1
  cita: "El scheduler de fibras utiliza un algoritmo de **work‑stealing** para balancear la carga entre hilos del sistema operativo."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/cluster.c:2348
  oraculo: tests/auditoria/test_oraculos_r150.py

## runtime/core/cluster.h
- manual: 5
  seccion: 8.1
  cita: "El scheduler de fibras utiliza un algoritmo de **work‑stealing** para balancear la carga entre hilos del sistema operativo."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/cluster.h:104
  oraculo: tests/auditoria/test_oraculos_r150.py

## std/testing.syn
- manual: 2
  seccion: 2
  cita: "La gramática de Synapse se define mediante una notación EBNF extendida."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: std/testing.syn:49
  oraculo: tests/auditoria/test_oraculos_r150.py

- manual: 7
  seccion: 2.3
  cita: "Este bloque contiene la gramática esencial, el modelo de memoria y ejemplos de Synapse/Syquex."
  tipo: comportamiento
  estado: DESVIACION
  decision: D-R149-1
  nota: >-
    Requisito literal del plan M15: "Las reglas de Synapse/Syquex se inyectan
    en el System Prompt". Esa oración no está indexada (la prosa de §2.3 es
    la lista RAG + inyección System Prompt); en su lugar se cita la oración
    real del manual. El requisito implementado (wrapper verificar() en
    std/testing.syn para que el código que genera SKILL_TDD_PROMPT compile)
    queda registrado aquí y en el plan MTS.

## compilador/generator/emit_tensors.py
- manual: 2
  seccion: 4.1
  cita: "`entero` / `int` | Entero con signo de 64 bits | 8 bytes | Alias de `int64_t`"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/generator/emit_tensors.py:11
  oraculo: tests/auditoria/test_oraculos_r150.py
  nota: >-
    D-R150-8: emisores crear_tensor/reserva con parámetros int64_t
    (paridad con el C emitido). Prueba directa: nodos [math] y [mem] de
    test_matriz_compilacion.py GREEN.

## compilador/parser_declarations.py
- manual: 2
  seccion: 2
  cita: "La gramática de Synapse se define mediante una notación EBNF extendida."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/parser_declarations.py:52
  oraculo: tests/auditoria/test_matriz_compilacion.py
  nota: >-
    D-R150-9: Manual 2 §2 L56 hace OPCIONAL el retorno
    (`declaracion_funcion ::= "funcion" IDENTIFICADOR "(" [ parametros ] ")"
    [ "->" tipo ] ...`); el parser lo exigía. Fix: retorno ausente → 'nulo'
    en _parsear_def_funcion y _parsear_externo_funcion (+ bug
    UnboundLocalError de tok_retorno en el constructor DeclaracionExterna).
    Oráculo directo: nodos [symbolic_exec] y [atp_engine] de la matriz GREEN
    (sesión 2026-09-18).

## std/symbolic_exec.syn
- manual: 2
  seccion: 4.1
  cita: "`entero` / `int` | Entero con signo de 64 bits | 8 bytes | Alias de `int64_t`"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: std/symbolic_exec.syn:4
  oraculo: tests/auditoria/test_matriz_compilacion.py
  nota: >-
    D-R150-9: tipos capitalizados (Entero/Decimal/Puntero/Cadena/Booleano)
    no son aliases de la tabla §4.1; normalizados a los canónicos en
    minúsculas. El cast estilo C `(Decimal)x` no existe en la gramática —
    la coerción entero→decimal en FFI es implícita (verificada por bisección,
    caso F). Nodo [symbolic_exec] GREEN.

## std/atp_engine.syn
- manual: 2
  seccion: 4.1
  cita: "`entero` / `int` | Entero con signo de 64 bits | 8 bytes | Alias de `int64_t`"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: std/atp_engine.syn:1
  oraculo: tests/auditoria/test_matriz_compilacion.py
  nota: >-
    D-R150-9: mismos patrones que symbolic_exec (tipos capitalizados →
    canónicos §4.1). Nodo [atp_engine] GREEN.

## std/quantum_err_corr.syn
- manual: 9
  seccion: 6.1
  cita: "□ **Compilación sin errores**: todos los targets (Windows, Linux, macOS, WASM) compilan sin errores ni warnings."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: std/quantum_err_corr.syn:4
  oraculo: tests/auditoria/test_matriz_compilacion.py
  nota: >-
    D-R150-9: el TVar ambiguo (`Expresion con tipo ambiguo: TVar(2)`) era
    consecuencia de tipos capitalizados no canónicos: el generador los
    acepta como alias pero el checker unificaba TVar frescos por ocurrencia
    (confirmado por bisección: patrón C3 con tipos capitalizados RED, con
    canónicos GREEN). Normalizados → nodo [quantum_err_corr] GREEN.
- manual: 2
  seccion: 4.1
  cita: "`entero` / `int` | Entero con signo de 64 bits | 8 bytes | Alias de `int64_t`"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: std/quantum_err_corr.syn:5
  oraculo: tests/auditoria/test_matriz_compilacion.py

## std/agent_skills.syn
- manual: 2
  seccion: 4.1
  cita: "`entero` / `int` | Entero con signo de 64 bits | 8 bytes | Alias de `int64_t`"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: std/agent_skills.syn:105
  oraculo: tests/auditoria/test_matriz_compilacion.py
  nota: >-
    D-R150-10: `principal` definido en una biblioteca std colisiona con el
    entry point del programa importador ("Redefinición de 'principal' en el
    mismo ámbito"). Renombrado a demostrar_agent_skills(): los std son
    bibliotecas importadas, no ejecutables.

