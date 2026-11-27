# Plan ME-r200 — OpenSyn `doctor` (prueba de humo y diagnóstico real)

Contexto: OpenSyn ya arranca y responde, pero ante una instalación incompleta el
usuario solo ve un error genérico. El producto necesita un diagnóstico
accionable, con código de salida verificable, que distinga entre entorno
completo, servidor inactivo (normal antes del chat) y recursos ausentes.

## Ley citada (MTS: requisito / texto / implementacion / oraculo)

requisito: Manual 7 §6.1 (Instalación de un solo clic: prueba de humo)
texto: "Al finalizar, se ejecuta una prueba de humo."
implementacion: `opensyn/principal.syn` — `cmd_doctor()` verifica binario, `{app}\opensyn`, config, `llama-server.exe`, modelo `.gguf` y perfil; devuelve 0 solo si los recursos críticos están presentes y 1 si falta alguno, con líneas `[OK]`, `[i]` y `[FAIL]`. `principal()` atiende `doctor|diagnostico`; `--help`, `status` y el error de servidor sin respuesta remiten al diagnóstico.
oraculo: auditoria/oraculos/oraculo_r200_opensyn_doctor.py — comprueba dispatcher/ayuda y ejecuta el binario en layout completo (rc=0) y sin `llama-server` (rc=1, fallo cerrado).

requisito: Manual 7 §2.1 (Orquestador: inicio del servidor de inferencia)
texto: "**Inicio:** Verifica si `llama-server` está ejecutándose en el puerto configurado (por defecto 8088). Si no, lo inicia con los parámetros adecuados."
implementacion: `opensyn/principal.syn` — `cmd_doctor()` reutiliza `obtener_dir_exe()`, `dir_opensyn()`, `buscar_llama_server()`, `buscar_modelo_instalado()` y `llama_server_corriendo()` con argumentos temporales frescos para no reutilizar `texto` consumido; reporta si el servidor está activo o se iniciará al abrir el chat. Se corrigen los llamados de `iniciar_llama_server()` y `cmd_status()` que reutilizaban rutas ya liberadas.
oraculo: auditoria/oraculos/oraculo_r200_opensyn_doctor.py — valida el layout `{app}\bin` + `{app}\opensyn\{ia,models}` y el diagnóstico de servidor/modelo.

requisito: Manual 7 §4.2 (Flujo de una Petición de IA con Validación)
texto: "El prompt se envía al servidor de inferencia (`llama-server`) mediante el cliente HTTP (`llama_client.c`)."
implementacion: `opensyn/principal.syn` — sin cambios en el envío del prompt; el diagnóstico no altera `normalizar_modelo_activo()` ni el cliente HTTP, y el modelo descubierto sigue siendo el que usa `/v1/chat/completions`.
oraculo: auditoria/oraculos/oraculo_r200_opensyn_doctor.py — el layout completo verifica que el modelo instalado se descubre y que el comando no abre la TUI.

## Fuera de alcance
- No se toca `nucleo/lsp_v3.syn` ni el trabajo unstaged de otro agente.
- No se implementa todavía firma de releases ni actualizador; quedan registrados como siguiente fase de productización.
- No se modifica el instalador en este ME.

## Pasos de regeneración (obligatorios)
1. `python main.py opensyn/principal.syn -o dist/bin/opensyn.exe`
2. Verificar mtime del exe > `opensyn/principal.syn`.
3. `.venv\Scripts\python.exe auditoria/oraculos/oraculo_r200_opensyn_doctor.py`
4. `.venv\Scripts\python.exe -m pytest tests/integration/test_opensyn_doctor.py -v`

## Gates
- `python auditoria/contrastar.py --plan docs/plan_ME_r200_opensyn_doctor.md`
- `python auditoria/alineacion.py --nuevo --me r200_opensyn_doctor` y `--verificar`
- `python auditoria/verificar_alineacion.py` — 0 brechas
- Oráculo + E2E del binario regenerado.
