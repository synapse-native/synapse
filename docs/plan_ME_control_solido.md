# Plan MTS — ME-control_solido: endurecimiento del sistema de control

> Método de Trabajo Seguro (`docs/gobernancia/METODO_TRABAJO.md`): cada requisito
> se cita con su bloque estricto. Auditoría previa: informe de debilidades
> H1–H14 (gate de bitácora muerto en CI, oráculos nunca ejecutados, citas
> decorativas, MTO sin verificación de estados, sello no bloqueante, limpieza
> destructiva del hook, `.syq` fuera del alcance, base CI vacía, D-9 sin
> cobertura C/opensyn, vínculo plan↔código laxo).

requisito: Manual 7 §2.3
texto: "Los tests validan comportamiento real, no la presencia de texto en el artefacto generado"
implementacion: contrastar.py EJECUTA cada oráculo del plan con pytest en modo
  release (SYNAPSE_BUILD_MODE=release); SKIP / "no tests ran" / rc!=0 => FAIL.
  auditar_calidad_tests.py añade patrón SNIFF_AMP (assert de literal sobre
  cualquier variable) y SIN_OBL (todo test incremental cita su OBL del MTO).
  El CI ya no pasa --sin-oraculos a alineacion.py; el pre-commit corre oráculos
  por defecto (ALINEACION_ORACULOS=1). CI: auditoria/auditar_calidad_tests.py
  --solo-mto valida el MTO (entradas OBL con Manual §, secciones reales,
  GREEN sin test citador visible como deuda).
oraculo: tests/auditoria/test_gate_mts_oraculos.py

requisito: Manual 2 §12
texto: "Toda función pública nueva debe tener requiere/garantiza (Manual 2 §12)"
implementacion: trazabilidad endurecida — verificar_alineacion.py valida citas
  anti-fabricación + AVISO de cita decorativa (no cubre el requisito puntual del
  mapa), .syq entra en PROD_EXTS, base CI vacía degrada a HEAD~1 (nonnull_base),
  parser de bitácora con fecha completa (no hardcodea 2026), escaneo D-9 ampliado
  a opensyn/syquex/runtime-core con .c aceptado en MODULOS_D9, contraste
  plan↔archivo ESTRICTO (cada archivo productivo cubre un requisito del plan),
  MTO añadido como paso bloqueante del pre-commit.
oraculo: tests/auditoria/test_gate_mts_oraculos.py

requisito: Manual 8 §1.2
texto: "El LSP lee cabeceras HTTP-like de la entrada estándar" (convención del
  repo para work de gates: cambios en el protocolo/gates exigen oráculo
  ejecutable en modo release)
implementacion: registro permanente de la validación MTO (nueva entrada OBL-M6-04
  en el MTO según su propia regla de mantenimiento) + verificador
  auditar_calidad_tests.py --solo-mto como gate del pre-commit y del CI.
oraculo: tests/auditoria/test_gate_mts_oraculos.py

requisito: Manual 6 §5
texto: "Serialización y comunicación (canales remotos): los registros de
  evidencia y expedientes deben quedar atados al contenido que se integra"
implementacion: alineacion.py — mismatch de cambio_hash ahora BLOQUEA (la
  evidencia no queda desanclada del código); sello de lectura previa validado
  por frescura (expira al día siguiente, fecha futura rechazada, sello posterior
  al código detectado vía fecha del commit base) y BLOQUEANTE en pre-commit
  (--exigir-sello); en CI la evidencia auditoria/evidencia/<hash>.json debe
  estar COMITEADA en HEAD con el mismo cambio_hash y sin oráculos fallidos.
oraculo: tests/auditoria/test_gate_mts_oraculos.py

## Deuda detectada que requiere ratificación del Arquitecto (no corregible aquí)

- El MTO cita 10 secciones renumeradas que ya no existen (Manual 7 §6.3/§7,
  Manual 8 §6.3, Manual 9 §9) — es un manual; corregirlo exige aprobación
  (regla 5). Hoy: AVISO visible en --solo-mto.
- 30 entradas GREEN del MTO sin ningún test que cite su OBL (deuda heredada).
- 15 SNIFF_AMP en tests heredados (asserts de literal sin ejecutar artefacto,
  p.ej. tests/integration/test_reports.py) — desviación Manual 7 §2.3
  preexistente; activable como FATAL con --estricto-sniff al ratificar.
- tests/test_auditoria_alineacion.py::test_seccion_es_de_manual falla por
  construcción del propio test (busca "§" en una cadena sin §) — INMUTABLE
  sin aprobación: requiere decisión del Arquitecto.
