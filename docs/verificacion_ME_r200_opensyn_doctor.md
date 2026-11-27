# Verificación ME r200_opensyn_doctor — OpenSyn `doctor`

Fecha: 2026-11-06 · Verificador: `auditoria/contrastar.py` (gate MTS fase 4b)
Oráculo: `auditoria/oraculos/oraculo_r200_opensyn_doctor.py` — PASS (13 chequeos)
Binario: `dist/bin/opensyn.exe` regenerado desde `opensyn/principal.syn`.

## R1 — Manual 7 §6.1 (prueba de humo posterior a la instalación) — CUMPLE
`opensyn/principal.syn:1926` cita `cumple Manual 7 §6.1`. `cmd_doctor()` recorre
binario, recursos IA, config, `llama-server.exe`, modelo `.gguf`, perfil y estado
del servidor; devuelve 0 solo si los recursos críticos están presentes y 1 si
falta alguno, con líneas `[OK]`, `[i]` y `[FAIL]`. `principal()` atiende
`doctor|diagnostico`; `--help`, `status` y el error de servidor sin respuesta
dirigen al diagnóstico.
Oráculo: `auditoria/oraculos/oraculo_r200_opensyn_doctor.py` PASS.

## R2 — Manual 7 §2.1 (inicio del servidor de inferencia) — CUMPLE
`opensyn/principal.syn:1925` cita `cumple Manual 7 §2.1`. El diagnóstico reutiliza
`obtener_dir_exe()`, `dir_opensyn()`, `buscar_llama_server()`,
`buscar_modelo_instalado()` y `llama_server_corriendo()` con argumentos frescos;
no reutiliza valores `texto` que el callee libera. Se corrigieron también
`iniciar_llama_server()` y `cmd_status()`, que reutilizaban `dir_exe`/`dir_app`
después de que `dir_opensyn()`/`buscar_llama_server()` los consumieran.
Oráculo: layout `{app}\bin` + `{app}\opensyn\{ia,models}` PASS.

## R3 — Manual 7 §4.2 (envío del prompt al servidor) — CUMPLE
`opensyn/principal.syn:689` cita `cumple Manual 7 §4.2`. El diagnóstico no altera
`normalizar_modelo_activo()` ni el cliente HTTP; el modelo descubierto sigue
siendo el usado por `/v1/chat/completions`.
Oráculo: `auditoria/oraculos/oraculo_r200_opensyn_doctor.py` PASS.

## E2E ejecutado
- Build: `python main.py opensyn/principal.syn -o dist/bin/opensyn.exe` → rc=0.
- Layout completo temporal: `bin/opensyn.exe` + `opensyn/ia/llama-server.exe` +
  `opensyn/models/modelo-prueba.gguf` → `doctor` rc=0, reporta modelo y servidor.
- Layout incompleto (sin `llama-server`) → `doctor` rc=1 y `[FAIL]` explícito.
- `status` en layout completo descubre el modelo de `{app}\opensyn\models` sin
  usar la ruta del perfil.
- `pytest tests/integration/test_opensyn_doctor.py -v` → 4 passed.
