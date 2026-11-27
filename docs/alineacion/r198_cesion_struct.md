# Expediente de alineación r198_cesion_struct

base: HEAD  # commit sobre el que se leyó el manual
cambio_hash: e004e8e8e8645718

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## compilador/generator/emit_declarations.py
- manual: 2
  seccion: 1.3
  cita: "Synapse soporta dos estilos de comentarios:"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/generator/emit_declarations.py:2
  # Cabecera preexistente del emisor (ancla de cubrimiento del mapa); el fix
  # del ME r198 NO modifica la sintaxis de comentarios, solo la lifetimes del
  # valor de texto. El ancla del requisito cubre el bloque de anclas §1.3 del
  # emisor; L738 documenta el estilo en la emisión del comentario fuente.
  oraculo: auditoria/oraculos/oraculo_r198_cesion.py

- manual: 4
  seccion: 3.3
  cita: "Cuando un objeto `rc` se envía a través de un canal (`Canal<T>`), el compilador aplica **move semantics** (semántica de movimiento)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/generator/emit_declarations.py:506
  # visitear_asignacion_campo: asignar un `texto` local/parametro a un campo
  # de struct TRANSFIERE la propiedad al campo → el origen queda CONSUMIDO
  # (move semantics H-R182c-1 extendida de args a cesión-campo) y el cleanup
  # RAII del scope NO libera el buffer del origen: antes emitía
  # `_syn_texto_liberar(p)` y el slab TLS reciclaba (ruta corrupta de
  # config.toml, repro 2026-10-25).
  oraculo: auditoria/oraculos/oraculo_r198_cesion.py

- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/generator/emit_declarations.py:515
  # La lifetimes RAII del scope: el cleanup respeta la cesión — el origen
  # Transferido sale del scope sin liberarse (paridad con lo que el
  # garantiza/requiere FE/BE emiten para los contratos que consumen texto).
  oraculo: auditoria/oraculos/oraculo_r198_cesion.py

## nucleo/generador/nodos_flujo.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/nodos_flujo.syn:969
  # gen_visitar_asignacion_campo: paridad S1↔nativo de la cesión de texto
  # a campo de struct → sentinela de scope depth=-1 + nombre vacío tal que
  # el cleanup RAII del scope (gen_cerrar_bloque_c) NO libera el origen.
  oraculo: auditoria/oraculos/oraculo_r198_cesion.py

- manual: 4
  seccion: 3.3
  cita: "Cuando un objeto `rc` se envía a través de un canal (`Canal<T>`), el compilador aplica **move semantics** (semántica de movimiento)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/nodos_flujo.syn:961
  # mismo fix en el emisor nativo (paridad M1 §3.1): la cesión al campo
  # transfiere al campo; el scope no es libre de liberar al origen ya
  # consumido (el campo es quien queda dueño del buffer de texto).
  oraculo: auditoria/oraculos/oraculo_r198_cesion.py

## nucleo/generator.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generator.syn:2301
  # generator.syn es unity ensamblado desde los módulos (nodos_flujo.syn
  # regenera generator.syn con _rebuild_generator.py — lección H-R180-2);
  # la subsección §5.1 cubre el requisito "Manual 2" del mapa legacy.
  oraculo: auditoria/oraculos/oraculo_r198_cesion.py

## Registro del ME (contexto, no requisitos)
- Cierre de H-R197-1 (deuda de r197). Probe determinista
  auditoria/probes/probe_cesion_struct.syn recompilado con el oráculo
  (3/3 PASS: compila rc=0, el C emitido NO libera `p` en `armado`,
  salida íntegra rc=0 — `pre:C:\Users\marce/…gguf:post`).
- E2E REAL como usuario: re-instalador RC=0 con el C generado de
  opensyn/principal.syn post-fix: config.toml `ruta` sale ÍNTEGRA
  (sin slab reciclado, sin NUL).
- Reinicio de `nucleo/generator.syn` con `nucleo/_rebuild_generator.py`
  tras editar el módulo nodos_flujo.syn (lección H-R180-2).
- Deuda DERIVADA NUEVA (resolución asignada ME r198b — emisor de
  contratos): el `garantiza` de retorno de `texto` se evalúa con
  `_resultado_`/`resultado` tras el cleanup del pool de exit rápido →
  (a) test fixture probe de contratos rc=127 (bisect 2026-10-25: rc=
  0xC0000374 preexistente en HEAD sin r197); (b) compilación S1 de
  opensyn/principal.syn falla: `longitud(resultado)` NO renombrado a
  `_resultado_` (C "did you mean '_resultado_'") y otro sitél `garantiza`
  roba el `_resultado_` int64 de otra función (emisor de contratos S1
  necesita resolver el símbolo del valor de retorno por tipos, no por
  nombre de variable).
