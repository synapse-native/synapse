# Verificación ME — agente-opensyn (cierre MTS gate, auditoria/contrastar.py paso 4)
# Commit: pendiente de esta sesión (ver docs/reportes/R140.md)
# Scope: ME_agente_opensyn — OpenSyn agente local con herramientas TOOL,
#        banner ASCII retro + prompt estilo OpenCode/Freebuff, inyección de
#        contexto Synapse/Syquex y cliente HTTP robusto contra Ollama.

Manual 7 §1.1 — R1 CUMPLE (tests/e2e_oracle_opensyn_banner.py VERDE: banner ASCII
  "OpenSyn" presente una sola vez, encabezado v1.1.0 y contexto del repositorio
  real listado; opensyn/principal.syn inyecta reglas Synapse (.syn) y Syquex
  (.syq, @export/FFI, Manual 2) en el System Prompt de consultar_agente)

Manual 7 §2.3 — R2 CUMPLE (tests/e2e_oracle_opensyn_agente.py VERDE: el modelo,
  con el System Prompt contextual, respondió con contenido REAL del repo —
  "AGENTS.md — Protocolo de arranque obligatorio para agentes (opencode)" —;
  bucle de agente con herramientas [TOOL] listar/leer/git implementado en
  principal.syn con copias strcpy_f por regla R113; stderr de opensyn = 0 bytes
  en la prueba E2E interactiva (sin fugas de git))

Manual 7 §8 — R3 CUMPLE (hardening del cliente: runtime/core/ollama.c —
  _ollama_leer_respuesta con SO_RCVTIMEO 2 s + plazo absoluto de 300 s + corte
  temprano por Content-Length; antes un Ollama colgado dejaba el chat en
  silencio indefinido. Verificado en el binario: strings contiene el mensaje
  de timeout; prueba E2E real con Ollama + qwen-coder completó 2 consultas
  rc=0 en <300 s)

NO CUMPLE (postergado, NO es scope de este ME — registrado por el ME paralelo
  reparacion-control-calidad): las citas `// cumple Manual 2 §12` en
  opensyn/principal.syn aún no corregidas a §5 (contratos). Se respetó el
  archivo ajeno; quedan anotadas en la bitácora para su commit de corrección.
