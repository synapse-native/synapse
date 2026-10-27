# Expediente de alineación r198b_contratos

base: HEAD  # commit sobre el que se leyó el manual
cambio_hash: ca4229aa1e9364ab

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## std/sistema.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: std/sistema.syn:29
  # garantiza de _validar_ruta_segura alineado a la semántica canónica del
  # lenguaje: subcadena(t, inicio, largo) — runtime _syn_texto_subcadena fin
  # EXCLUSIVO (runtime/core/texto.c clamp, r196 builtin). La cláusula anterior
  # (subcadena(...,1,2)==":" fin-inclusivo) producía ":/" y abortaba limpio
  # (rc=0xC0000009) la postcondición de dominio. Fix: (1,2)→(1,1) en el
  # garantiza y en el `si` de resolución relativa del mismo patrón (L34-36).
  oraculo: auditoria/oraculos/oraculo_r198b_contratos.py

## opensyn/principal.syn
- manual: 7
  seccion: 2.1
  cita: "Se ejecuta en segundo plano y se comunica con el LSP mediante un socket local."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/principal.syn:207
  # Cubrimiento del mapa (preexistente, archivo infra del ciclo: L19/L21/L86
  # anclan §2.1). El fix del ME (L213: garantiza de ruta_config_absoluta
  # `longitud(resultado)` → `longitud(_resultado_)`, alias canónico M2 §5.1)
  # toca la función de la RUTA DE CONFIG que este ciclo de arranque usa.
  oraculo: auditoria/oraculos/oraculo_r198b_contratos.py

- manual: 7
  seccion: 4.2
  cita: "El LSP es el responsable de orquestar el bucle de validación (descrito en la sección 6.3)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/principal.syn:365
  # Cubrimiento del mapa (preexistente: validación del código con el
  # compilador real --check). El fix del ME en pct_contexto (L1065:
  # `longitud(_resultado_) >= 0` sobre retorno ENTERO → `_resultado_ >= 0`,
  # la cláusula del porcentaje) es justamente una cláusula que el recorrido
  # de validación compila; el C inventado por la cláusula previa NO
  # compilaba ("incompatible type for argument 1 of 'longitud'").
  oraculo: auditoria/oraculos/oraculo_r198b_contratos.py

## Registro del ME (contexto, no requisitos)
- Naturaleza del defecto (H-R196-3 cerrada): NO era el emisor de contratos —
  emitía fielmente el AST (M2 §5.1: garantiza evalúa con `_resultado_` del
  tipo REAL, en CADA `retornar`, en emit_declarations.py L781-816); las
  cláusulas del std/opensyn estaban escritas bajo semánticas no canónicas:
  (a) subcadena fin-inclusivo cuando el lenguaje S1/r196 define
  (inicio, largo) fin exclusivo (runtime/core/texto.c); (b) alias bare
  `resultado` (L212) y `longitud()` sobre retorno entero (L1061) — la
  VÍA de corrección es el precedente ratificado H-R196-1: "corregir
  contrato al manual" (el código desviado se corrige hacia el manual; el
  emisor/runtime SON la semántica canónica).
- Verificación: oraculo_r198b_contratos.py 3/3 (A1 principal.syn rc=0 —
  antes fallaba la COMPILACIÓN; A2 sandbox contratos 5/5 — antes 3✓/1✗/1E
  con abort rc=0xC0000009; A3 regresión r198 3/3) + contratos/sandbox
  44 passed (test_contracts*10 + string_utils + test_sandbox_cover_r196) +
  borrowing family 17 passed.
- Resolución de la deuda que asignó ME r198b en plan_maestro_deudas:
  CERRADA en este ME (no requería "resolver símbolo por tipos" en el
  emisor: los casos concretos eran desviaciones del código — el emisor
  emitía lo que la cláusula tenía).
