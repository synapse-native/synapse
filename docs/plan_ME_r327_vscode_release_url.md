# Plan de Micro-Entregable r327_vscode_release_url

## Objetivo

Cerrar H-VSCODE-URL-1: actualizar `SYNAPSE_INSTALLER_URL` en
`vscode-synapse/extension.js` para apuntar al release oficial
`synapse-native/synapse` en lugar del fork personal v1.5.0.

## Requisito 1 — URL de instalador obsoleta

requisito: Manual 9 §4.1
texto: "□ **Instaladores multiplataforma**: se generan instaladores para Windows (.exe), Linux (.deb, .AppImage) y macOS (.dmg) desde el mismo código fuente."
implementacion: se reemplaza la URL `https://github.com/gedeon1972-svg/synapse-lang/releases/download/v1.5.0/...` por `https://github.com/synapse-native/synapse/releases/latest/download/synapse-windows-x64.zip` en `vscode-synapse/extension.js`.
oraculo: auditoria/verificar_encoding.py

## Evidencia

| check | resultado |
|---|---|
| URL actualizada a release oficial | OK |
"""