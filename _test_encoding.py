"""Test encoding de debil."""
import sys
sys.stdout.reconfigure(encoding="utf-8")

s1 = "débil<"
s2 = "debil<"

print("s1 bytes:", s1.encode("utf-8"))
print("s2 bytes:", s2.encode("utf-8"))
print("s1 len:", len(s1))
print("s2 len:", len(s2))

# Check what S1 context.py uses
with open("compilador/generator/context.py", "r", encoding="utf-8") as f:
    content = f.read()
    
# Find lines with debil
for i, line in enumerate(content.splitlines()):
    if "debil" in line or "débil" in line:
        print(f"context.py:{i}: {line.strip()}")
