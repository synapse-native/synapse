# Verificación ME — opensyn-historial-autocomplete (cierre MTS gate, auditoria/contrastar.py step 4)
# Commit: pendiente (trabajo reparado en sesión 2026-09-06)
# Scope: historial persistente ~/.opensyn/history.jsonl + navegación ↑↓ + autocompletado Tab.

Manual 7 §1.1 — R1 CUMPLE (_syn_tui_historial_cargar/guardar/anterior/siguiente;
  archivo JSONL por entrada; límite FIFO 1000; ↑↓ navegan si caja vacía o cursor
  al final; al enviar se añade y persiste. Oráculo e2e_oracle_opensyn_historial.py
  GREEN: persistencia entre ejecuciones, navegación múltiple, 3 líneas exactas)
Manual 7 §8 — R2 CUMPLE (_syn_tui_completar reactivado: Tab completa comandos
  con prefijo '/' y rutas relativas desde cwd con FindFirstFile/opendir + filtro
  por prefijo; doble Tab abre menú modal de opciones. Oráculo
  e2e_oracle_opensyn_autocomplete.py GREEN: /mo→/model, ruta→archivo_prueba.syn,
  doble Tab muestra los 8 comandos)

HALLAZGO H-HIST-1 (RESUELTO): " salir" (con espacio) no era filtrado del historial
  por el chequeo de longitud exacta; ahora se recorta espacio/tab alrededor antes
  de comparar con salir/exit (cumple Manual 7 §1.1 UX).
HALLAZGO H-HIST-2 (RESUELTO en tui.c): en modo pipe Windows el Tab caía en el
  acumulador de caracteres (se insertaba literal) y las flechas ESC[A/B] no
  navegaban; ambos casos corregidos con la misma semántica que POSIX y el
  volcado al Enter sin duplicar el texto completado.