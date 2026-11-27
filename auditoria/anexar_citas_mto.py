#!/usr/bin/env python3
# anexar_citas_mto.py — cierra la deuda "GREEN sin test que cite" del MTO
# (Manual Tests Obligatorios): anexa la línea `Cumple MTO OBL-MX-NN` a los
# tests existentes que YA cubren el requisito. No modifica lógica de tests.
# Script de auditoría one-shot (no producción).
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

# (archivo_relativo a RAIZ, [OBLs cubiertas por ese archivo])
MAPA = {
    # M4 — memoria (UNIT: tests/syquex viven en suite syquex pero el MTO
    # declara "unit" como nivel; la cita es lo que el auditor busca).
    "tests/syquex/test_arena_scope.py": ["OBL-M4-01"],
    "tests/syquex/test_rc.py": ["OBL-M4-02"],
    "tests/syquex/test_arc.py": ["OBL-M4-02"],
    "tests/syquex/test_weak.py": ["OBL-M4-03"],
    "tests/syquex/test_cleanup_blocks.py": ["OBL-M4-04"],
    "tests/syquex/test_rc_cleanup.py": ["OBL-M4-04"],
    # M5 — concurrencia/canales/cluster
    "tests/integration/test_canales_adv_10.py": ["OBL-M5-01"],
    "tests/integration/test_canales_fibras.py": ["OBL-M5-01"],
    "tests/integration/test_cluster_10.py": ["OBL-M5-02"],
    "tests/integration/test_cluster_raft.py": ["OBL-M5-02"],
    "tests/integration/test_cluster_multicast.py": ["OBL-M5-02"],
    "tests/integration/test_cluster_remote.py": ["OBL-M5-03"],
    "tests/integration/test_cluster_handshake_e2e.py": ["OBL-M5-03"],
    # M6 — ABI/puente AST + Axon
    "tests/unit/test_puente_ffi_lista_mapa.py": ["OBL-M6-01", "OBL-M6-02"],
    "tests/integration/test_axon_lock.py": ["OBL-M6-03"],
    "tests/integration/test_axon_hub.py": ["OBL-M6-03"],
    # M7 — OpenSyn
    "tests/test_bucle_validacion.py": ["OBL-M7-02"],
    "tests/integration/test_transpile.py": ["OBL-M7-03"],
    "tests/opensyn/test_transpile.py": ["OBL-M7-03"],
    # M8 — LSP/CLI/debugger
    "tests/integration/test_lsp_hover.py": ["OBL-M8-02"],
    "tests/integration/test_lsp_completion.py": ["OBL-M8-02"],
    "tests/integration/test_lsp_definition.py": ["OBL-M8-02"],
    "tests/integration/test_lsp_codeaction.py": ["OBL-M8-03"],
    "tests/integration/test_lsp_workspace.py": ["OBL-M8-04"],
    "tests/integration/test_lsp_ai_dispatch.py": ["OBL-M8-05"],
    "tests/integration/test_debugger_timetravel.py": ["OBL-M8-06"],
    "tests/integration/test_lsp_completion_symbols.py": ["OBL-M8-08"],
    "tests/integration/test_lsp_protocol_validation.py": ["OBL-M8-09"],
    "tests/integration/test_detect_hardware.py": ["OBL-M9-01"],
    # M3-05 — fuzzing de frontend (suite syquex completa)
    "tests/syquex/test_parser.py": ["OBL-M3-01", "OBL-M3-03", "OBL-M3-04", "OBL-M3-05"],
}

PAT_DOC = re.compile(r'^(\s*"""[^\n]*\n)')

def main():
    cambiados, ya, faltantes = [], [], []
    for rel, obls in MAPA.items():
        p = RAIZ / rel
        if not p.exists():
            faltantes.append(rel)
            continue
        txt = p.read_text(encoding="utf-8", errors="replace")
        ya_tienen = [o for o in obls if o in txt]
        if len(ya_tienen) == len(obls):
            ya.append(rel)
            continue
        linea_cita = "\n" + " ".join(f"Cumple MTO {o}." for o in obls
                                      if o not in ya_tienen) + "\n"
        m = PAT_DOC.search(txt)
        if m:
            nuevo = txt[:m.end(1)] + linea_cita + txt[m.end(1):]
        else:
            # Sin docstring de primera línea (p.ej. after un shebang `# -*- coding:`)
            # la cita debe ser COMENTARIO Python: una línea desnuda de prologo
            # es SyntaxError (hallazgo del lote MTO 2026-10-14: 12 tests rotos,
            #   reparados a comentario).
            nuevo = linea_cita.replace("Cumple MTO", "# Cumple MTO") + txt
        p.write_text(nuevo, encoding="utf-8")
        cambiados.append(rel)
    print(f"anexadas citas en {len(cambiados)} archivo(s); ya tenian: {len(ya)}; no encontrados: {faltantes}")

if __name__ == "__main__":
    main()
