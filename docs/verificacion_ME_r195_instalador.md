# Verificación ME — r195_instalador (cierre MTS gate, auditoria/contrastar.py paso 4)
# Gates ejecutados 2026-10-23: familia instalador completa 25 passed / 0 skipped (rc=0);
# sin modificaciones de tests (los 3 skips se cierran entregando el artefacto exigido).

Manual 9 §4.1 — R1 CUMPLE (scripts/uninstall.py NUEVO: reversa de install.sh
 (/opt/synapse + symlink + log, Linux/macOS) y de installer.syn (~/.opensyn usuario,
 todas las plataformas); --list/--dry-run/--yes; E2E probado en HOME temporal con
 fixture .opensyn falso — borrado real rc=0; el test inmutable test_uninstall pasa
 2/2 sin skip)

Manual 9 §2.5 — R2 CUMPLE (synapse_lsp.exe REAL en raíz: compilado con el pipeline
 del proyecto main.py nucleo/lsp_v3.syn -o synapse_lsp.exe --release → rc=0, 304 KB,
 gcc -O3 -flto -DNDEBUG link modular; el componente LSP del .iss ahora tiene su
 artefacto; test_install_windows 5/5 sin skip)

Manual 9 §7 — R3 CUMPLE (install.sh NUEVO en raíz: delegador exec a
 instaladores/linux/install.sh sin duplicar lógica, LF, ejecutable; el test M9 §7 de
 instalación Linux pasa 4/4 sin skip; familia completa del instalador 25 passed /
 0 skipped / 0 failed, rc=0)
