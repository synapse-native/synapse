# Plan ME-r199 — OpenSyn operativo en instalación limpia (auto-arranque + rutas)

Contexto: el binario instalado `{app}\bin\opensyn.exe` se ejecuta directamente
(Windows resuelve `.exe` antes que `.bat`), pero `obtener_dir_exe()` devolvía ""
(cwd), `iniciar_llama_server()` no encontraba `ia/` ni `models/` y la config se
leía de rutas fijas `C:\Program Files\Synapse\...`. Resultado: `opensyn` sin
`llama-server` previo mostraba “No se pudo listar modelos (Ollama apagado?)”.
El wrapper `opensyn.bat` además buscaba `ia/` y `models/` junto al `.bat`
(`{app}\bin`) en lugar de `{app}\opensyn`.

## Ley citada (MTS: requisito / texto / implementacion / oraculo)

requisito: Manual 7 §2.1 (Orquestador: inicio del servidor de inferencia)
texto: "Verifica si `llama-server` está ejecutándose en el puerto configurado (por defecto 8088). Si no, lo inicia con los parámetros adecuados."
implementacion: `opensyn/principal.syn` — `obtener_dir_exe()` resuelve el directorio real del binario con `GetModuleFileNameA`; `dir_opensyn()` deriva `{app}\opensyn` cuando el exe vive en `{app}\bin`; `buscar_llama_server()`/`buscar_modelo_instalado()` buscan en `{app}\opensyn\ia|models`, junto al exe, cwd y `%USERPROFILE%\.opensyn\models`; `llama_server_corriendo()` sondea `/v1/models` en 8088; `iniciar_llama_server()` lanza el server con `start "" /B` vía `_syn_ejecutar_comando` y espera readiness; la config (`.synapse_config`, `config_ollama.txt`) se busca en cwd, HOME y `{app}\opensyn` (sin `C:\Program Files\Synapse` fijo); `principal()` atiende `--version`, `--help` y `status` antes de abrir la TUI.
oraculo: auditoria/oraculos/oraculo_r199_opensyn_install.py — comprueba ausencia de rutas fijas, presencia de resolución por módulo, y E2E del exe en layout temporal (auto-arranque + modelo listado).

requisito: Manual 7 §4.2 (Flujo de una Petición de IA con Validación)
texto: "El prompt se envía al servidor de inferencia (`llama-server`) mediante el cliente HTTP (`llama_client.c`)."
implementacion: `normalizar_modelo_activo()` compara por nombre base (soporta id del server como ruta completa y config con/sin `.gguf`), de modo que el modelo configurado por el instalador se usa en `/v1/chat/completions` sin caer al primero disponible; persiste el nombre base, no la ruta completa.
oraculo: auditoria/oraculos/oraculo_r199_opensyn_install.py — verifica la paridad config↔id (helper de nombre base) y que el chat usa el modelo elegido.

requisito: Manual 9 §2.5 (Configuración de Inno Setup)
texto: "El script `installer.iss` de Inno Setup para Windows:"
implementacion: `instaladores/windows/synapse.iss` añade el acceso directo `OpenSyn (IA local)` con `WorkingDir: {app}` y mantiene `opensyn.bat` junto al exe; `opensyn/opensyn.bat` resuelve `{app}\opensyn\ia|models` cuando vive en `{app}\bin`, con fallback a `%USERPROFILE%\.opensyn` y `--host 127.0.0.1`.
oraculo: auditoria/oraculos/oraculo_r199_opensyn_install.py — valida el layout instalado (exe en bin, ia/models en opensyn) y las rutas del wrapper.

## Fuera de alcance
- No se toca el ME r198b3 (fmt/lint) ni sus archivos staged.
- No se modifica `std/texto.syn` ni el refactor unstaged de otro agente.
- No se empaqueta un modelo dentro del instalador: se conserva la descarga SHA-256 existente (Manual 9 §5.3).

## Pasos de regeneración (obligatorios)
1. `python main.py opensyn/principal.syn -o dist/bin/opensyn.exe`
2. `iscc instaladores/windows/synapse.iss`
3. Verificar mtime del exe > `opensyn/principal.syn`; instalación de prueba en
   layout limpio y E2E sin `llama-server` previo y sin Ollama.

## Gates
- `python auditoria/contrastar.py --plan docs/plan_ME_r199_opensyn_install.md`
- `python auditoria/alineacion.py --nuevo --me r199_opensyn_install` y `--verificar`
- `python auditoria/verificar_alineacion.py` — 0 brechas
- Oráculo + E2E del binario regenerado.
