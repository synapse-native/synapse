"""Test validar_documento directly.

Manual 8 §1.2 — LSP diagnostic validation
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from synapse_lsp.server import validar_documento

code = "#lang: es\nfuncion principal() -> nulo:\n    x = indefinido\n"
print(f"Test code: {repr(code)}")
errs = validar_documento("test.syn", code)
print(f"Errors: {len(errs)}")
for e in errs:
    print(f"  {e}")
print("DONE")