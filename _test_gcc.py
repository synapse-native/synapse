"""Test GCC con struct<T>."""
import subprocess
import tempfile
import os

test_c = "struct debil<NodoLista> ref = 0;\nint main() { return 0; }"

with tempfile.NamedTemporaryFile(suffix=".c", delete=False, mode="w") as f:
    f.write(test_c)
    c_path = f.name

result = subprocess.run(["gcc", "-c", c_path, "-o", "/dev/null"], capture_output=True, text=True)
print("GCC rc:", result.returncode)
if result.stderr:
    print("GCC stderr:", result.stderr[:500])

os.remove(c_path)
