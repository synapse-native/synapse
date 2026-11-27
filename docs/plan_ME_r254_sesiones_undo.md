# Plan ME r254_sesiones_undo (reasignado de r218_sesiones_undo)

requisito: Manual 7 §4.3
texto: "Si el código generado es inválido y se agotan los intentos, el LSP muestra un mensaje y ofrece regenerar (o pedir ayuda al usuario)."
implementacion: opensyn/run_manager.syn gana deshacer_ultimo_paso; opensyn/principal.syn importa run_manager y cablea sesiones (/sesion, /reanudar, /revertir, /sesion-fin), helpers sesion_archivo/sesion_run_id_activo/sesion_activar/sesion_limpiar/sesion_marcar_paso, y marca pasos en tui_agente.
oraculo: tests/opensyn/test_sesiones_undo_comportamiento.py

requisito: Manual 7 §2.1
texto: "El orquestador es un proceso en C que gestiona el ciclo de vida del servidor de inferencia (`llama-server`)."
implementacion: sesion_marcar_paso best-effort en el bucle de herramientas de tui_agente.
oraculo: tests/opensyn/test_run_manager_comportamiento.py

requisito: Manual 7 §2.3
texto: "El pipeline RAG (Retrieval-Augmented Generation) es el cerebro de OpenSyn."
implementacion: comandos /sesion, /reanudar, /revertir integrados en tui_comando.
oraculo: tests/opensyn/test_run_manager_comportamiento.py

requisito: Manual 7 §4.2
texto: "El LSP es el responsable de orquestar el bucle de validación (descrito en la sección 6.3)."
implementacion: validacion previa (r217) se mantiene; la sesion registra cada TOOL como paso.
oraculo: tests/opensyn/test_validation_loop_comportamiento.py

requisito: Manual 7 §7.3
texto: "Cero telemetría: Verificado con monitoreo de red (sin conexiones salientes)."
implementacion: sesion persiste solo en disco local (.opensyn_session), sin red.
oraculo: tests/opensyn/test_sesiones_undo_comportamiento.py
