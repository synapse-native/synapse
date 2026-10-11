# Oraculo ME r182c — Manual 5 §2.6 / Manual 3 §8.1
# Valida el arregl del ciclo de vida de canales cedidos a fibra/listener:
#  1) programa canonico M3 §8.1 (lanzar productor + escuchar + romper) rc=0
#  2) salida correcta: 42 y 100 (antes de fix: basura+segfault)
#  3) los 2 sitios de cesion marcan _canal_vars_cedidas
import subprocess, sys, os
RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import tempfile, shutil
OK = True

src = open(os.path.join(RAIZ,'compilador','generator','emit_declarations.py'), encoding='utf-8').read()
n = src.count('_canal_vars_cedidas')
print(f"oraculo_r182c: cesiones marcadas={n} (esperado >=3)")
OK &= n >= 3

probe = os.path.join(RAIZ,'docs','alineacion','probes_r182c','canal_cierre.syq')
with tempfile.TemporaryDirectory() as td:
    r = subprocess.run([sys.executable, '-X','utf8', os.path.join(RAIZ,'cli.py'),
                        'build', probe], capture_output=True, text=True,
                       timeout=600, cwd=td, env=dict(os.environ, SYNAPSE_BUILD_MODE='release'))
    print(f"oraculo_r182c: build canal_cierre rc={r.returncode}")
    OK &= r.returncode == 0
    exe = os.path.join(td, os.path.splitext(os.path.basename(probe))[0] + '.exe')
    if os.path.exists(exe):
        r2 = subprocess.run([exe], capture_output=True, text=True, timeout=15, cwd=td)
        salida = (r2.stdout or '').split()
        print(f"oraculo_r182c: rc={r2.returncode} salida={salida[:4]}")
        OK &= r2.returncode == 0
        OK &= '42' in salida and '100' in salida
    else:
        # el build deja artefactos junto a la FUENTE (M8 §4.2 R182a): verificar alli
        dsrc = os.path.dirname(probe)
        exe2 = os.path.join(dsrc, os.path.splitext(os.path.basename(probe))[0] + '.exe')
        r2 = subprocess.run([exe2], capture_output=True, text=True, timeout=15, cwd=dsrc)
        salida = (r2.stdout or '').split()
        print(f"oraculo_r182c: (fuente-dir) rc={r2.returncode} salida={salida[:4]}")
        OK &= r2.returncode == 0
        OK &= '42' in salida and '100' in salida

print(f"oraculo_r182c: {'PASS' if OK else 'FAIL'} (canales cedidos)")
sys.exit(0 if OK else 1)
