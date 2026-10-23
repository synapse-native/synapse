# Plan ME — r195_instalador: instalador completamente funcional y operativo

requisito: Manual 9 §4.1 (distribución Linux — reversa de instalación) + M9 §7
texto: "instaladores/linux/install.sh copia a /opt/synapse, symlink /usr/local/bin/synapse
       y log /var/log/synapse-install.log; installer.syn escribe ~/.opensyn (config.toml,
       config_ollama.txt, modelos/.gguf)" (M9 §4.1 layout de instalación; M9 §5.4 datos de
       OpenSyn en ~/.opensyn)
hallazgo H-test_TDD: tests/integration/test_uninstall.py:28 SKIP "Script de
desinstalación no encontrado (TDD)" — chequeo de existencia sin artefacto.
implementacion (scripts de soporte, exentos del gate de lectura — mapa
§Exclusiones scripts/**):
  - scripts/uninstall.py NUEVO: detecta/lista/borra ~/.opensyn (usuario, todas
    las plataformas) y /opt/synapse + symlink /usr/local/bin/synapse + log
    (sistema, Linux/macOS); --list/--dry-run/--yes; reporte OK/AVISO con exit
    0 (desinstalado o nada que desinstalar) / 1 (error de borrado); degrade
    con permisos de root documentados.
  - El test inmutable EXIGE la existencia de scripts/uninstall.py — el test no
    se modifica (regla dura).
oraculo: tests/integration/test_uninstall.py

---

## R2 — synapse_lsp.exe real en raíz (empaquetado del .iss)

requisito: Manual 9 §2.5 (configuración de Inno Setup — componente LSP) + M9 §7
texto: "instaladores/windows/synapse.iss define MyAppLspExeName 'synapse_lsp.exe'
       y lo referencia como componente del instalador Windows" (M9 §2.5)
hallazgo H: tests/integration/test_install_windows.py:33 SKIP
"synapse_lsp.exe no encontrado" — el binario que empaqueta el .iss no existía
en la raíz del árbol.
implementacion (artefacto de build, sin código nuevo):
  - Build REAL con el compilador del proyecto: .venv/Scripts/python.exe
    main.py nucleo/lsp_v3.syn -o synapse_lsp.exe --release → rc=0, exe 304504
    bytes, gcc -O3 -flto -DNDEBUG enlazado modular (5 TU del nucleo + runtime
    completo). El exé queda en el árbol de build local (artefacto, no
    fuente); el test inmutable pasa sin skip cuando está presente.
oraculo: tests/integration/test_install_windows.py

---

## R3 — install.sh del paquete en la raíz

requisito: Manual 9 §7 (instalación en Linux — install.sh debe existir en la
raíz del bundle) M9 §7
texto: "tests/integration/test_install_linux.py:25: 'install.sh debe existir'
       (RAIZ/install.sh)" — el instalador real vive en instaladores/linux/.
implementacion (delegador, sin duplicar lógica):
  - install.sh NUEVO en raíz: exec bash instaladores/linux/install.sh "$@"
    con nota MTS; LF normalizado. No toca la lógica del instalador real.
oraculo: tests/integration/test_install_linux.py

---

## Reglas transversales (vigentes del plan maestro)

1. Tests: NINGUNO modificado (los 3 skips se cierran entregando el artefacto
   que cada test exige).
2. Deuda hallada en el camino: se repara o se registra con resolución.
3. Antes de commitear: artefactos regenerados → git add selectivo (exe NUEVO
   algo; no se commitea binario: queda en el árbol local).
4. Prohibido --no-verify; los gates del pre-commit mandan.
