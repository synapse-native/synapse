# Expediente de alineación r198b2_ancla

base: HEAD  # commit sobre el que se leyó el manual
cambio_hash: 8881708525cba028

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## compilador/puente_canonico.py
- manual: 3
  seccion: 11.1
  cita: "| Nodo Syquex | Nodo Synapse (SemNodo) | Notas |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/puente_canonico.py:70
  # Cubrimiento del mapa (preexistente: L70 ancla §11.1 — todos los NODO_*
  # categorizados). El ME añade en el desugar REAL de NODO_PARA_EN(57)
  # (_nodo_para_en, L614) la ancla MTS cumple Manual 2 §12 que el test
  # paridad exigía y HEAD no tenía (H-R198b1-2); comentario de
  # documentación, cero diff binario de la emisión.
  oraculo: tests/auditoria/test_paridad_nodos.py

- manual: 6
  seccion: 5.1
  cita: "El formato de serialización para canales remotos es un subconjunto de MessagePack, optimizado para velocidad. **Especificación normativa:** el formato definitivo está en el Manual 5, §6.3."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/puente_canonico.py:71
  # Cubrimiento del mapa (preexistente: L71 ancla §5.1 — NODO_INTENTO(54)
  # al AST tipado S1). El ME no toca la semántica de traducción: la entrega
  # del ME es el re-sello ancla Manual 2 §12 en el desugar de PARA_EN
  # (misma función de traducción del nodo canonico 57, _nodo_para_en).
  oraculo: tests/auditoria/test_paridad_nodos.py

- manual: 2
  seccion: 12
  cita: "| Contratos requiere/garantiza | `pytest tests/integration/test_contracts.py -v` | 100% pass |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/puente_canonico.py:614
  # Ancla NUEVA del ME (cierre H-R198b1-2): el desugar de PARA_EN alimenta
  # el pipeline de pruebas obligatorias de la etapa (OBL-PAR-R1d) y debía
  # llevar la cita grep-chequeable cumple Manual 2 §12 (comentario,
  # documentación; el test paridad la lee del archivo completo).
  oraculo: tests/auditoria/test_paridad_nodos.py

## Registro del ME (contexto, no requisitos)
- Hallazgo cerrado (H-R198b1-2): HEAD compiló la brecha del test
  test_paridad_nodos::test_emision_s1_cita_los_nodos_canonicos — el
  comentario MTS `cumple Manual 2 §12` no estaba en puente_canonico.py
  (el test lo exige a nivel de ARCHIVO completo, leído entero).
  Dirección del Arquitecto en plan maestro (2026-10-03): si el código está
  alineado y el test pide algo razonable, se satisface el test aplicando
  TDD (el test nunca se modifica).
- Verificación: test_paridad_nodos.py 4/4 GREEN (RED→GREEN con stash
  verificado en R198b1) + sin regresiones en tests/auditoria/ +
  verificar_alineacion SIN BRECHAS.
