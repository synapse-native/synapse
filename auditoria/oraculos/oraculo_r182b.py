# Oraculo ME r182b — Manual 3 §3 / Manual 1 §1.1
# Valida el desugar de `para` con rango tras el fix R182b:
#  1) los 5 literales sinteticos del desugar escriben bits altos (sq_tokens_hi)
#  2) build/syq_frontend.exe presente (backend compartido, M1 §3.1)
#  3) cli.py build de un .syq con `para i en 0..n` -> rc=0 (sin segfault)
import subprocess
import sys
import os
import re

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OK = True

# (1) 5 sitios con bits altos en los literales sinteticos del desugar
src = open(os.path.join(RAIZ, 'syquex', 'parser.syn'), encoding='utf-8').read()
n = len(re.findall(r"_hi_\w+\[(?:paso_r|expr_paso|lt|incr_val|miembro)\]=", src))
print(f"oraculo_r182b: sitios hi-bits={n} (esperado >=5)")
OK &= n >= 5

# (2) frontend Syquex presente
fe = os.path.join(RAIZ, 'build', 'syq_frontend.exe')
print(f"oraculo_r182b: syq_frontend.exe existe={os.path.exists(fe)}")
OK &= os.path.exists(fe)

# (3) build e2e de un .syq con para-en-rango (rc=0 = sin segfault)
probe = os.path.join(RAIZ, 'docs', 'alineacion', 'probes_r182b',
                     'probe_r182b_for_en.syq')
r = subprocess.run([sys.executable, '-X', 'utf8', os.path.join(RAIZ, 'cli.py'),
                    'build', probe], capture_output=True, text=True,
                   timeout=300, cwd=RAIZ)
print(f"oraculo_r182b: build para-en rc={r.returncode}")
OK &= r.returncode == 0

# PASS: marca explícita en la ÚLTIMA línea (el gate busca OK:/PASS en stdout)
print(f"oraculo_r182b: {'PASS' if OK else 'FAIL'} (sitios=5, frontend, build rc=0)")
sys.exit(0 if OK else 1)
