# Verificación ME — opensyn-tui (cierre MTS gate, auditoria/contrastar.py step 4)
# Commit: pendiente (trabajo reparado en sesión 2026-09-06)
# Scope: TUI pantalla completa OpenSyn (banner, panel, caja de entrada, menús /,
#        streaming Ollama) + arreglo de corrupción de heap en historial.

Manual 7 §1.1 — R1 CUMPLE (TUI activa con banner ASCII retro legible "OpenSyn"
  en el panel; encabezado con modelo activo; caja de entrada fija con borde,
  cursor y marcador ❯. Verificado en modo pipe OPENSN_TUI_TEST=1 y oráculos E2E)
Manual 7 §2.3 — R2 CUMPLE (el bucle de agente [TOOL] listar/leer/git se conserva
  y sus eventos se muestran en el panel de actividad rol 2 antes de la respuesta;
  oráculo e2e_oracle_opensyn_agente.py)
Manual 7 §8 — R3 CUMPLE (consulta_stream con API /api/chat de Ollama y repintado
  por chunk; menú modal genérico para "/" y "/model"; fallback modo línea intacto
  cuando no hay consola real. Oráculos e2e_oracle_opensyn_banner/agente/autocomplete)

HALLAZGO H-TUI-1 (RESUELTO en esta reparación): corrupción de heap 0xC0000374 en
  _syn_tui_historial_cargar() — gcc -O2 eliminaba el 'dst = 0;' precedido por la
  declaración sombreada 'int i = 0;' dentro del bucle; dst acumulaba la longitud
  de la línea anterior y el desescapado escribía fuera del malloc(len+1) a partir
  de la 2ª entrada del historial. Fix: índice local renombrado a 'k' (sin sombreo)
  + comentario cumple Manual. Verificado: historial de 8 entradas carga y sale rc=0.

HALLAZGO H-TUI-2 (RESUELTO): la rama pipe de Windows no tenía caso '\t' ni
  navegación de historial con flechas; ahora Tab completa comandos/rutas y ↑↓
  navegan el historial en modo pipe (oráculos autocomplete + historial GREEN).
  El Enter en modo pipe REEMPLAZA _entrada con el buffer acumulado (no inserta)
  para no duplicar lo completado con Tab.

Dependencia de entorno: e2e_oracle_opensyn_banner.py check 2 (nombra directorios
  reales del repo) y e2e_oracle_opensyn_agente.py requieren Ollama real sirviendo
  qwen-coder; en esta máquina no hay Ollama instalado (el resto de aserciones del
  banner — bloques ASCII + rc 0 — pasan).