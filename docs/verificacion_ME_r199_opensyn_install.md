# Verificación ME r199_opensyn_install — OpenSyn operativo en instalación limpia

Fecha: 2026-11-05 · Verificador: `auditoria/contrastar.py` (gate MTS fase 4b)
Oráculo: `auditoria/oraculos/oraculo_r199_opensyn_install.py` — PASS (14 chequeos)
E2E manual: `dist/bin/opensyn.exe` en layout temporal `{app}\bin` + `{app}\opensyn\{ia,models}`;
sin `llama-server` previo arrancó el servidor (puerto 8088 LISTENING) y la TUI mostró
`Modelo activo: C:\Users\marce\.opensyn\models\deepseek-coder-1.3b-Q4_K_M.gguf`.

## R1 — Manual 7 §2.1 (Orquestador: inicio de llama-server) — CUMPLE
`opensyn/principal.syn:96` resuelve el directorio real del exe con `GetModuleFileNameA`;
`opensyn/principal.syn:235` inicia `llama-server` solo si `llama_server_corriendo()` no
responde y espera readiness vía `_syn_ollama_modelos`; `buscar_llama_server` y
`buscar_modelo_instalado` cubren `{app}\opensyn\{ia,models}`, junto al exe, cwd y
`%USERPROFILE%\.opensyn\models`, sin rutas fijas `C:\Program Files\Synapse`.
Oráculo: `auditoria/oraculos/oraculo_r199_opensyn_install.py` PASS.

## R2 — Manual 7 §4.2 (Prompt al servidor de inferencia) — CUMPLE
`opensyn/principal.syn:665` (`nombre_base_ruta`) y `:680` (`sin_extension_gguf`) comparan
el modelo configurado por nombre base, de modo que el id de `/v1/models` (ruta completa)
coincide con `model=` del instalador y se usa en `/v1/chat/completions` sin caer al primero.
Oráculo: `auditoria/oraculos/oraculo_r199_opensyn_install.py` PASS.

## R3 — Manual 9 §2.5 (Inno Setup) — CUMPLE
`instaladores/windows/synapse.iss` añade los accesos `OpenSyn (IA local)` con
`WorkingDir: "{app}"`; `opensyn/opensyn.bat` delega en `bin\opensyn.exe` y permite
resolver `{app}\opensyn\ia|models` desde el binario instalado. Si el instalador
reutiliza un GGUF del perfil (`%USERPROFILE%\.opensyn\models`) pero falta
`{app}\opensyn\ia\llama-server.exe`, descarga el servidor igualmente (fix del
bloque `if not UseExisting`).
Oráculo: `auditoria/oraculos/oraculo_r199_opensyn_install.py` PASS.

## E2E de instalación limpia (ISCC + silent install)
- Build: `ISCC.exe instaladores/windows/synapse.iss` → rc=0,
  `dist\Synapse-8.1.0-industrial-Windows-x64.exe`.
- Instalación: `/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /COMPONENTS=opensyn
  /DIR="D:\OpenSynTest_Install"` → rc=0.
- Verificado: `{app}\bin\opensyn.exe` y `{app}\opensyn\ia\llama-server.exe` existen;
  el instalador reutilizó el GGUF del perfil y aun así descargó el servidor.
- Arranque: `D:\OpenSynTest_Install\bin\opensyn.exe` sin `llama-server` previo →
  puerto 8088 LISTENING (PID 16368) y respuesta del chat (`OpenSyn> cerrar`).
- `status` desde `{app}\bin` resolvió `Recursos IA: {app}\opensyn` y el modelo
  del perfil; el servidor queda persistente tras cerrar la TUI.
