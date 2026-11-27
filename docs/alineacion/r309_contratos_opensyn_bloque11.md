# Expediente de alineación r309_contratos_opensyn_bloque11

base: HEAD  # commit sobre el que se leyó el manual
cambio_hash: 37592a6904706b28

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## opensyn/principal.syn
- manual: 7
  seccion: 2.1
  cita: "Se ejecuta en segundo plano y se comunica con el LSP mediante un socket local."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/principal.syn:18
  oraculo: auditoria/verificar_contratos.py

- manual: 7
  seccion: 2.3
  cita: "El nodo AST actual (función, estructura, bloque, etc.)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/principal.syn:32
  oraculo: auditoria/verificar_contratos.py

- manual: 7
  seccion: 4.2
  cita: "El LSP es el responsable de orquestar el bucle de validación (descrito en la sección 6.3)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/principal.syn:489
  oraculo: auditoria/verificar_contratos.py

- manual: 7
  seccion: 7.3
  cita: "**Nota de restauración (2026-10-01):** Sección restaurada textualmente por decisión del Arquitecto (Opción A, cierre de H-R171-1) tras su eliminación involuntaria en la revisión de manuales v8.2.0 (commit 154a544); con ella, la cita `cumple Manual 7 §7.3` del oráculo R6 (tests/integration/test_permisos_opensyn.py, TestCitasCumpleManual::test_permisos_cita_r6) vuelve a resolver contra una sección real — tercera víctima de la truncación v8.2.0 en repararse (tras §5.1/R119 y §6.3/restauro_bucle_validacion)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/principal.syn:281
  oraculo: auditoria/verificar_contratos.py

- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/principal.syn:103
  oraculo: auditoria/verificar_contratos.py

## opensyn/installer.syn
- manual: 7
  seccion: 2.5
  cita: "Lee la lista de modelos disponibles y sus metadatos (URLs, hashes SHA‑256, tamaños) desde el archivo `modelos.toml` que se distribuye junto con el instalador (ver Manual 9, §5.6)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/installer.syn:5
  oraculo: auditoria/verificar_contratos.py

- manual: 9
  seccion: 5.2
  cita: "| VRAM | Modelo | Cuantización | Tamaño aprox. |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/installer.syn:6
  oraculo: auditoria/verificar_contratos.py

- manual: 9
  seccion: 5.3
  cita: "El modelo se descarga desde Hugging Face o Axon Hub, y se verifica su integridad mediante SHA‑256."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/installer.syn:7
  oraculo: auditoria/verificar_contratos.py

- manual: 9
  seccion: 5.4
  cita: "El instalador configura `llama-server` con los parámetros óptimos:"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/installer.syn:8
  oraculo: auditoria/verificar_contratos.py

- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/installer.syn:50
  oraculo: auditoria/verificar_contratos.py

## opensyn/memoria_persistente_cifrada.syn
- manual: 6
  seccion: 1.1
  cita: "El ecosistema Synapse se basa en un **Árbol de Sintaxis Abstracta (AST) canónico y unificado** denominado `SemNodo[]`."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/memoria_persistente_cifrada.syn:3
  oraculo: auditoria/verificar_contratos.py

- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/memoria_persistente_cifrada.syn:5
  oraculo: auditoria/verificar_contratos.py

## opensyn/architect_det.syn
- manual: 6
  seccion: 1.1
  cita: "El ecosistema Synapse se basa en un **Árbol de Sintaxis Abstracta (AST) canónico y unificado** denominado `SemNodo[]`."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/architect_det.syn:3
  oraculo: auditoria/verificar_contratos.py

- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/architect_det.syn:4
  oraculo: auditoria/verificar_contratos.py

