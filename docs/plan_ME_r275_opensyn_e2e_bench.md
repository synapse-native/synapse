# Plan ME r275_opensyn_e2e_bench

**Fase del roadmap:** Frente H (release industrial), Ola H2.
**Micro-entregable:** `r275_opensyn_e2e_bench`.
**Depende de:** `r273_installer_modelo_grande` (CERRADO), `r274_gates_independientes` (CERRADO).
**Manuales:** Manual 7 §7.2, §7.3, §8; Manual 9 §5.5.

---

requisito: Manual 7 §7.2
texto: "Latencia de inferencia: < 1s para prompts cortos (modelo 7B en GPU)." / "Throughput: > 100 tokens/s en GPU." / "Uso de VRAM: < 6 GB para modelo 7B Q4_K_M."
implementacion: Benchmark reproducible y opt-in que mide latencia real, tokens/s y VRAM contra `llama-server` local; el reporte R275 registra maquina, modelo, cuantizacion, fecha y los valores medidos. No se finge el umbral de GPU en una maquina CPU: se mide y se documenta la diferencia.
oraculo: auditoria/oraculos/oraculo_r275_opensyn_e2e_bench.py

requisito: Manual 7 §7.3
texto: "Cero telemetría: Verificado con monitoreo de red (sin conexiones salientes)." / "Modelos firmados: Todos los modelos descargados se verifican con SHA-256." / "Sandboxing: El servidor de inferencia se ejecuta con permisos mínimos."
implementacion: Test estatico y de ejecucion que (a) rechaza endpoints no locales en el codigo de OpenSyn salvo las descargas documentadas del instalador, y (b) monitorea el proceso `opensyn.exe doctor` para exigir que sus conexiones sean solo loopback. Test E2E del sandbox que compila y ejecuta una sonda contra `opensyn/permisos.syn`: editar dentro del workspace = ASK, editar fuera = DENY, leer dentro = ALLOW.
oraculo: tests/integration/test_opensyn_sin_red.py

requisito: Manual 7 §8
texto: "El LSP valida con `synapse check --no-emit` (compila correctamente)." / "El LSP captura el error, construye un nuevo prompt ... y envía a OpenSyn (intento 2)."
implementacion: E2E real opt-in (`OPENSYN_E2E=1` + GGUF) que arranca `llama-server` local, ejecuta un chat real contra `/v1/chat/completions` y valida un fragmento generado con `synapse check --no-emit` (valido rc=0, invalido rc!=0). El test conserva el opt-in para que un CI sin modelo no finge verde; el oraculo del plan es el runner, que resuelve la capacidad real del entorno, exporta el opt-in y falla con causa si no hay modelo (un SKIP no es evidencia).
oraculo: auditoria/oraculos/oraculo_r275_opensyn_e2e_bench.py

requisito: Manual 9 §5.5
texto: "El instalador ejecuta una consulta simple al modelo para verificar que todo funciona."
implementacion: Prueba de humo real: la consulta simple al modelo se ejecuta contra el `llama-server` levantado por el E2E y se exige respuesta no vacia; el mismo test mide la latencia de esa consulta. La ejecuta el runner, que exige la capacidad local.
oraculo: auditoria/oraculos/oraculo_r275_opensyn_e2e_bench.py

criterio_cierre: `pytest tests/integration/test_opensyn_sin_red.py -v` verde siempre; `python auditoria/oraculos/oraculo_r275_opensyn_e2e_bench.py` verde con `llama-server` y GGUF locales (rc=1 con causa si faltan, nunca verde falso). `contrastar --plan docs/plan_ME_r275_opensyn_e2e_bench.md` PASS con oraculos ejecutados. `alineacion.py --verificar --me r275_opensyn_e2e_bench` evidencia sellada. `verificar_alineacion.py` 0 brechas. Reporte `docs/reportes/R275.md` con metricas medidas.

produccion_modificada: `tests/integration/test_opensyn_e2e_local.py` y `tests/integration/test_opensyn_sin_red.py` llevan `# cumple Manual 7 §7.2, §7.3, §8; Manual 9 §5.5`. El runner `auditoria/oraculos/oraculo_r275_opensyn_e2e_bench.py` deja de ser un placeholder y ejecuta los dos oraculos.
