# Plan de Micro-Entregable r329_installer_prewarm_runtime_cache

## Objetivo

Cerrar H-RUNTIME-CACHE-COLD-1: en una instalación nueva la primera compilación
nativa recompila ~50 fuentes C del runtime (90–180 s) porque
`%USERPROFILE%\.synapse\cache\runtime_obj` está vacía. El instalador Inno Setup
ejecuta un precalentamiento post-instalación que compila esos objetos con el
toolchain incluido y deja los sidecars `.sha` que valida `nucleo/principal.syn`.

## Requisito 1 — la instalación deja el compilador operativo

requisito: Manual 9 §7
texto: "Instalación exitosa, PATH configurado, `synapse --version` funciona."
implementacion: `instaladores/windows/synapse.iss` envía `prewarm_runtime_cache.ps1` a `{app}` en `[Files]` y lo ejecuta en `[Run]` (post-instalación, `runhidden`), de modo que la primera compilación no paga la recompilación del runtime.
oraculo: tests/auditoria/test_oraculos_r329_prewarm_runtime_cache.py

## Requisito 2 — configuración del instalador Inno Setup

requisito: Manual 9 §2.5
texto: "El script `installer.iss` de Inno Setup para Windows:"
implementacion: el bloque `[Run]` de `instaladores/windows/synapse.iss` sigue el patrón del manual (comando + `StatusMsg`) y añade el paso de precalentamiento tras el resto de pasos de instalación.
oraculo: tests/auditoria/test_oraculos_r329_prewarm_runtime_cache.py
