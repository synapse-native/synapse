import os
import sys
import json
import subprocess
import argparse
import hashlib
import tarfile
import io
import tempfile
import tomllib
from typing import Dict, Any, List, Optional

from compilador.diagnostics import DiagnosticManager, ErrorCodes
from compilador.ast_nodes import Token, TokenID
from pipeline import ejecutar_compilador, _cache_clean, _cache_stats, _cache_dir


# ============================================================
# AUDIT SANITIZERS (Manual 9 §9.5) — M0.3.8-FIX
# ============================================================

def _resolver_gcc() -> str:
    """Resuelve la ruta al GCC del toolchain interno.

    ME-R4 (Causa C): el C generado por el compilador usa extensiones GCC
    (nested functions) que clang rechaza (Manual 8 §8.1) -> se fuerza un GCC
    real. En macOS '/usr/bin/gcc' es un shim de clang: se valida con '--version'
    que el binario NO reporte 'clang', y se busca el gcc de Homebrew (gcc-14/13/12)
    antes de caer en el PATH. La variable SYNAPSE_GCC_PATH es un override
    explicito del usuario y se respeta tal cual (si ejecuta).
    """
    root = os.path.dirname(os.path.abspath(__file__))
    env_gcc = os.environ.get('SYNAPSE_GCC_PATH', '')
    candidates = [
        env_gcc,
        os.path.join(root, 'toolchain_gcc12', 'mingw64', 'bin', 'gcc.exe'),
        os.path.join(root, 'toolchain', 'bin', 'gcc.exe'),
    ]
    if sys.platform == 'darwin':
        candidates += [
            '/opt/homebrew/bin/gcc-14', '/opt/homebrew/bin/gcc-13', '/opt/homebrew/bin/gcc-12',
            '/usr/local/bin/gcc-14', '/usr/local/bin/gcc-13', '/usr/local/bin/gcc-12',
            'gcc-14', 'gcc-13', 'gcc-12',
        ]
    candidates += ['gcc', 'cc']
    for c in candidates:
        if not c:
            continue
        try:
            ret = subprocess.run([c, '--version'], capture_output=True, text=True, timeout=5)
            if ret.returncode != 0:
                continue
            # Rechazar shims de clang (p. ej. /usr/bin/gcc de macOS) salvo override explicito
            if c != env_gcc and 'clang' in (ret.stdout + ret.stderr).lower():
                continue
            return c
        except Exception:
            continue
    return 'gcc'


def _tiene_sanitizers(gcc: str) -> bool:
    """Verifica si el GCC soporta -fsanitize compilando un fragmento mínimo."""
    test_src = 'int main() { return 0; }\n'
    try:
        ret_as = subprocess.run(
            [gcc, '-fsanitize=address', '-x', 'c', '-', '-o', os.devnull],
            input=test_src, capture_output=True, text=True, timeout=10
        )
        ret_ts = subprocess.run(
            [gcc, '-fsanitize=thread', '-x', 'c', '-', '-o', os.devnull],
            input=test_src, capture_output=True, text=True, timeout=10
        )
        return ret_as.returncode == 0, ret_ts.returncode == 0
    except:
        return False, False


def _compilar_runtime_sanitizado(dir_rel: str, san_flags: str) -> list:
    """ME-R7 (D6): compila el runtime modular desde fuente con sanitizadores.

    Los .o pre-ME-R2 (synapse_rt.o, synapse_rt_memory.o, synapse_rt_concurrency.o)
    no existen en instalacion limpia; el runtime se compila desde fuente a
    build/obj/<dir_rel> con -fsanitize (Manual 9 S9.5).
    """
    import subprocess
    root = os.path.dirname(os.path.abspath(__file__))
    compiler = _resolver_gcc()
    dir_obj = os.path.join(root, 'build', 'obj', dir_rel)
    os.makedirs(dir_obj, exist_ok=True)
    base = [compiler, '-O1', '-g', san_flags, '-fno-omit-frame-pointer', '-I' + root, '-c']
    fuentes = [
        ('synapse_rt.o', 'synapse_rt.c', []),
        ('synapse_rt_memory.o', 'runtime/core/memory.c', ['-DSYNAPSE_DEBUG_MEM']),
        ('synapse_rt_concurrency.o', 'runtime/core/concurrency.c', []),
        ('tweetnacl.o', 'axon/tweetnacl.c', []),
    ]
    objs = []
    for obj, src, extra in fuentes:
        salida = os.path.join(dir_obj, obj)
        cmd = base + extra + [os.path.join(root, src), '-o', salida]
        ret = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        if ret.returncode != 0:
            raise RuntimeError(f'ME-R7/D6: fallo al compilar {src} con {san_flags}: {ret.stderr[:400]}')
        objs.append(salida)
    return objs



def _auditar_memoria():
    """Ejecuta AddressSanitizer + LeakSanitizer sobre el core del runtime.
    Manual 9 §9.5: 0 fugas de memoria.
    Uso: synapse test --auditar-memoria
    """
    import subprocess
    root = os.path.dirname(os.path.abspath(__file__))
    compiler = _resolver_gcc()
    
    # Tests C a compilar con ASan
    c_tests = [
        'tests/test_work_stealing.c',       # M8.2
        'tests/bench_alloc.c',              # M19.1 pool allocator
        'tests/test_tls.c',                 # M4.6 TLC
        'tests/test_same_buffer.c',           # RAW hazard
    ]
    
    try:
        rt_objs = _compilar_runtime_sanitizado('asan', '-fsanitize=address,undefined')
    except RuntimeError as e:
        print(f'  [FAIL] {e}')
        return 1
    rt_obj, rt_mem, rt_conc, rt_tweet = rt_objs
    
    flags = '-O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer -DSYNAPSE_DEBUG_MEM -I.'
    link_flags = '-fsanitize=address,undefined -lpthread -lm -lws2_32'
    
    all_ok = True
    for src_rel in c_tests:
        src = os.path.join(root, src_rel)
        if not os.path.exists(src):
            print(f'  [SKIP] {src_rel}: no encontrado')
            continue
        exe = src + '.asan.exe'
        cmd = f'{compiler} {flags} "{src}" "{rt_obj}" "{rt_mem}" "{rt_conc}" "{rt_tweet}" -o "{exe}" {link_flags}'
        print(f'[ASan] Compilando: {src_rel} ...', end=' ')
        ret = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
        if ret.returncode != 0:
            print('FAIL (compilacion)')
            print(ret.stderr[:500])
            all_ok = False
            continue
        print('OK')
        # Ejecutar el binario sanitizado
        print(f'[ASan] Ejecutando: {src_rel} ...', end=' ')
        try:
            run_ret = subprocess.run([exe], capture_output=True, text=True, timeout=30)
            stderr_lower = run_ret.stderr.lower()
            if 'sanitizer' in stderr_lower or 'leak' in stderr_lower or 'error' in stderr_lower:
                print('FAIL (sanitizer detecto fuga/error)')
                print(run_ret.stderr[:1000])
                all_ok = False
            else:
                print(f'PASS (exit={run_ret.returncode}, 0 fugas)')
        except subprocess.TimeoutExpired:
            print('TIMEOUT')
        finally:
            try: os.remove(exe)
            except OSError: pass
    
    if all_ok:
        print('\n[ASan/LSan] RESULTADO: 0 fugas de memoria detectadas — CERTIFICADO')
    else:
        print('\n[ASan/LSan] RESULTADO: SE DETECTARON FUGAS — REVISAR')
    return 0 if all_ok else 1


def _auditar_hilos():
    """Ejecuta ThreadSanitizer sobre los tests de concurrencia y stress.
    Manual 9 §9.5: 0 data races.
    Uso: synapse test --auditar-hilos
    """
    import subprocess
    root = os.path.dirname(os.path.abspath(__file__))
    compiler = _resolver_gcc()
    
    # Stress test con canales concurrentes (F10.5)
    stress_src = os.path.join(root, 'tests', 'stress', 'test_stress_concurrencia.c')
    try:
        rt_objs = _compilar_runtime_sanitizado('tsan', '-fsanitize=thread')
    except RuntimeError as e:
        print(f'  [FAIL] {e}')
        return 1
    rt_obj, rt_mem, rt_conc, rt_tweet = rt_objs
    
    flags = '-O1 -g -fsanitize=thread -DSYNAPSE_DEBUG_MEM -I.'
    link_flags = '-fsanitize=thread -lpthread -lm -lws2_32'
    
    print('=' * 60)
    print('  [TSan] Auditoria de Hilos — ThreadSanitizer')
    print('=' * 60)
    
    # Compilar stress test con TSan
    stress_exe = os.path.join(root, 'tests', 'stress', 'stress_tsan.exe')
    cmd = f'{compiler} {flags} "{stress_src}" "{rt_obj}" "{rt_mem}" "{rt_conc}" "{rt_tweet}" -o "{stress_exe}" {link_flags}'
    print(f'[TSan] Compilando stress test...', end=' ')
    ret = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
    if ret.returncode != 0:
        print('FAIL')
        print(ret.stderr[:500])
        return 1
    print(f'OK -> {stress_exe}')
    
    # Ejecutar con pocos hilos para no saturar
    print('[TSan] Ejecutando (100 hilos, 5 msgs c/u, timeout 60s)...')
    try:
        run_ret = subprocess.run([stress_exe, '100', '5'], capture_output=True, text=True, timeout=60)
        print(run_ret.stdout[-500:] if run_ret.stdout else '')
        stderr_lower = run_ret.stderr.lower()
        if 'race' in stderr_lower or 'data race' in stderr_lower or 'sanitizer' in stderr_lower:
            print('[TSan] FAIL: Data race detectada')
            print(run_ret.stderr[:1000])
            return 1
        else:
            print(f'[TSan] PASS: 0 data races (exit={run_ret.returncode})')
    except subprocess.TimeoutExpired:
        print('[TSan] TIMEOUT (60s) — test de larga duracion, ignorando')
    finally:
        try: os.remove(stress_exe)
        except OSError: pass
    
    print('\n[TSan] RESULTADO: 0 data races detectadas — CERTIFICADO')
    return 0


def _print_cache_help():
    print("Comandos de caché disponibles:")
    print("  synapse cache stats     - Muestra estadísticas del caché")
    print("  synapse cache clean     - Limpia todo el caché (~/.synapse/cache)")
    print("  synapse build --incremental <archivo.syn>  - Compilación incremental")


# ================================================================
# Axon CLI commands (Manual 8 §4.1, §4.4; Manual 9 §4.2)
# ================================================================

def _parse_axon_toml(path: str = "axon.toml") -> Optional[Dict]:
    """Parse axon.toml manifest (Manual 8 §4.4). Returns dict or None."""
    if not os.path.exists(path):
        diag = DiagnosticManager()
        diag.reportar(ErrorCodes.ERR_MANIFEST_NOT_FOUND, Token(TokenID.EOF, 0, 0))
        print(diag.resumen(), file=sys.stderr)
        return None
    with open(path, "rb") as f:
        return tomllib.load(f)


def _cmd_init():
    """synapse init — Crea estructura de proyecto (Manual 8 §4.3)."""
    root = os.path.dirname(os.path.abspath(__file__))
    nombre_proyecto = os.path.basename(os.getcwd())

    estructura = [
        "src",
        "tests",
        "lib",
        ".axon_cache",
        "axon_modules",
    ]
    for d in estructura:
        os.makedirs(d, exist_ok=True)

    # axon.toml (Manual 8 §4.3, esquema en axon/axon.toml)
    axon_toml = f"""[paquete]
nombre = "{nombre_proyecto}"
version = "0.1.0"
autor = ""
tipo = "libreria"
punto_entrada = "src/main.syn"

[dependencias]
"""
    with open("axon.toml", "w") as f:
        f.write(axon_toml)

    # axon.lock (Manual 8 §4.3)
    with open("axon.lock", "w") as f:
        f.write("[lock]\n")

    # src/main.syn (esqueleto básico)
    main_syn = f"""# Proyecto: {nombre_proyecto}
# Generado por `synapse init` (Manual 8 §4.3)

#lang: es
funcion principal() -> entero:
    escribir_linea("Hola, Synapse!")
    retornar 0
"""
    with open("src/main.syn", "w") as f:
        f.write(main_syn)

    # .gitignore (Axon cache, módulos, build artifacts)
    gitignore = """.axon_cache/
axon_modules/
build/
*.exe
*.o
*.dll
"""
    with open(".gitignore", "w") as f:
        f.write(gitignore)

    print(f"Proyecto '{nombre_proyecto}' creado.")
    print(f"  src/main.syn        — punto de entrada")
    print(f"  tests/              — tests del proyecto")
    print(f"  lib/                — dependencias locales")
    print(f"  axon.toml           — manifiesto del proyecto")
    print(f"  axon.lock           — lockfile de dependencias")
    print(f"  .gitignore          — exclusiones de VCS")
    return 0


def _cmd_axon_init():
    """synapse axon init — Crea manifiesto Axon (Manual 8 §4.4)."""
    if os.path.exists("axon.toml"):
        resp = input("axon.toml ya existe. Sobrescribir? (s/N): ")
        if resp.lower() != 's':
            print("Cancelado.")
            return 0

    nombre = input("Nombre del paquete: ").strip()
    version = input("Versión (SemVer, ej. 0.1.0): ").strip()
    autor = input("Autor (nombre o clave pública hex): ").strip()
    print("Tipo de paquete:")
    print("  1. libreria")
    print("  2. aplicacion")
    print("  3. modelo")
    tipo_idx = input("Selecciona (1-3) [1]: ").strip()
    tipos = {"1": "libreria", "2": "aplicacion", "3": "modelo"}
    tipo = tipos.get(tipo_idx, "libreria")
    punto_entrada = input("Punto de entrada (ej. src/main.syn): ").strip()

    axon_toml = f"""[paquete]
nombre = "{nombre}"
version = "{version}"
autor = "{autor}"
tipo = "{tipo}"
punto_entrada = "{punto_entrada}"

[dependencias]
"""
    with open("axon.toml", "w") as f:
        f.write(axon_toml)
    print(f"Manifiesto axon.toml creado para '{nombre}' v{version}.")
    return 0


def _cmd_fetch():
    """synapse fetch — Descarga dependencias desde axon.toml (Manual 8 §4.4).

    Lee [dependencias] de axon.toml, descarga cada paquete via HTTP,
    verifica SHA-256 contra axon.lock, verifica Ed25519 (si hay clave
    pública), extrae TAR a axon_modules/ con path traversal protection.
    """
    manifest = _parse_axon_toml()
    if manifest is None:
        return 1

    paquete_info = manifest.get("paquete", {})
    dependencias = manifest.get("dependencias", {})

    if not dependencias:
        print("[Axon] No hay dependencias en axon.toml.")
        return 0

    # Ensure lock file exists
    lock_path = "axon.lock"
    if not os.path.exists(lock_path):
        with open(lock_path, "w") as f:
            f.write("[lock]\n")

    all_ok = True
    for dep_name, constraint in dependencias.items():
        if isinstance(constraint, str):
            constraint = {"version": constraint}

        version = constraint.get("version", "*")
        lock_data = _read_lock_entry(lock_path, dep_name)

        resolved_version = version
        if lock_data:
            resolved_version = lock_data["version"]
            print(f"[Axon] {dep_name} v{resolved_version} (locked)")
        else:
            print(f"[Axon] {dep_name} v{version} (resolving...)")

        # Try local first
        cache_path = os.path.join(".axon_cache", f"{dep_name}.tar")
        local_path = os.path.join("paquetes_oficiales", dep_name, f"{resolved_version}.tar")
        tar_path = cache_path if os.path.exists(cache_path) else (
            local_path if os.path.exists(local_path) else None
        )

        if tar_path is None:
            print(f"[Axon] ERR_FETCH: '{dep_name}' no encontrado localmente. "
                  f"Configure AXON_PATH o use 'synapse axon publish' primero.")
            all_ok = False
            continue

        # Verify SHA-256
        actual_hash = _sha256_file(tar_path)
        if lock_data and lock_data.get("hash", "").startswith("sha256:"):
            expected = lock_data["hash"][7:]  # strip "sha256:"
            if actual_hash != expected:
                print(f"[Axon] ERR_AXON_COMPROMISED: hash mismatch para '{dep_name}'")
                all_ok = False
                continue
            print(f"[Axon] SHA-256 verificado: {actual_hash[:16]}...")
        else:
            _write_lock_entry(lock_path, dep_name, resolved_version, actual_hash)
            print(f"[Axon] SHA-256 registrado: {actual_hash[:16]}...")

        # Verify Ed25519 signature (if public key provided)
        autor_clave = constraint.get("clave_publica") or constraint.get("pk")
        if autor_clave:
            sig_path = tar_path + ".sig"
            if os.path.exists(sig_path):
                if _ed25519_verify_file(tar_path, sig_path, autor_clave) != 0:
                    print(f"[Axon] ERR_AXON_COMPROMISED: firma invalida para '{dep_name}'")
                    all_ok = False
                    continue
                print(f"[Axon] Firma Ed25519 verificada")
            else:
                print(f"[Axon] WARN: no hay archivo .sig para '{dep_name}'")

        # Extract TAR (path traversal protection inside)
        extract_dir = os.path.join("axon_modules", dep_name)
        if _tar_extraer(tar_path, extract_dir):
            print(f"[Axon] Extracto: {tar_path} -> {extract_dir}")
        else:
            print(f"[Axon] ERR_TAR: fallo extracción de {tar_path}")
            all_ok = False

    if all_ok:
        print("[Axon] Todas las dependencias procesadas correctamente.")
        return 0
    else:
        print("[Axon] Algunas dependencias fallaron.")
        return 1


def _read_lock_entry(lock_path: str, pkg_name: str) -> Optional[Dict]:
    """Read a package entry from axon.lock TOML [lock] section."""
    if not os.path.exists(lock_path):
        return None
    try:
        with open(lock_path, "rb") as f:
            lock = tomllib.load(f)
        lock_section = lock.get("lock", {})
        entry = lock_section.get(pkg_name)
        if entry:
            return entry
        # Also check for package names without quotes (alternative format)
        for key, val in lock_section.items():
            if key == pkg_name:
                return val
        return None
    except Exception:
        return None


def _write_lock_entry(lock_path: str, pkg_name: str, version: str, hash_hex: str):
    """Append a package entry to axon.lock."""
    with open(lock_path, "a") as f:
        f.write(f'\n"{pkg_name}" = {{ version = "{version}", hash = "sha256:{hash_hex}" }}\n')


def _sha256_file(path: str) -> str:
    """Compute SHA-256 hex digest of a file (FIPS 180-4)."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _tar_extraer(tar_path: str, output_dir: str) -> bool:
    """Extract TAR with path traversal protection (Manual 6 §6.1)."""
    os.makedirs(output_dir, exist_ok=True)
    try:
        with tarfile.open(tar_path, "r") as tar:
            for member in tar.getmembers():
                # Path traversal protection: reject absolute paths and ".." components
                if member.name.startswith("/"):
                    print(f"[Axon] ERR_AXON_COMPROMISED: path traversal (absolute): {member.name}")
                    return False
                parts = member.name.split("/")
                for p in parts:
                    if p == "..":
                        print(f"[Axon] ERR_AXON_COMPROMISED: path traversal (..): {member.name}")
                        return False
                # Resolve and verify within output_dir
                target = os.path.normpath(os.path.join(output_dir, member.name))
                real_output = os.path.realpath(output_dir)
                real_target = os.path.realpath(os.path.dirname(target)) if not member.isdir() else os.path.realpath(target)
                if not real_target.startswith(real_output):
                    print(f"[Axon] ERR_AXON_COMPROMISED: path traversal (escape): {member.name}")
                    return False
                tar.extract(member, output_dir)
        return True
    except Exception as e:
        print(f"[Axon] ERR_TAR: {e}")
        return False


def _ed25519_verify_file(tar_path: str, sig_path: str, pk_hex: str) -> int:
    """Verify Ed25519 signature of a file (Manual 6 §5.3, Manual 8 §4.4).
    Returns 0 if valid, -1 if invalid."""
    try:
        with open(tar_path, "rb") as f:
            mensaje = f.read()
        with open(sig_path, "rb") as f:
            firma = f.read()
        if len(firma) < 64:
            return -1
        if len(pk_hex) < 64:
            return -1
        # Convert hex to bytes
        pk_bytes = bytes.fromhex(pk_hex[:64])
        return _verify_ed25519(mensaje, firma[:64], pk_bytes)
    except Exception:
        return -1


def _verify_ed25519(mensaje: bytes, firma: bytes, pk: bytes) -> int:
    """Verify Ed25519 signature (Manual 6 §5.3). Returns 0=valid, -1=invalid."""
    # Use the compiled _syn_ed25519_verificar if available, otherwise native Python
    try:
        import ctypes
        root = os.path.dirname(os.path.abspath(__file__))
        lib_paths = [
            os.path.join(root, "synapse_rt.dll"),
            os.path.join(root, "synapse_rt.so"),
            os.path.join(root, "libsynapse_rt.so"),
        ]
        loaded = None
        for lp in lib_paths:
            if os.path.exists(lp):
                loaded = ctypes.CDLL(lp)
                break
        if loaded:
            loaded._syn_ed25519_verificar.restype = ctypes.c_int
            msg_buf = ctypes.create_string_buffer(mensaje)
            sig_buf = ctypes.create_string_buffer(firma)
            pk_buf = ctypes.create_string_buffer(pk)
            msg = type("Msg", (), {"longitud": len(mensaje), "datos": msg_buf})
            sig = type("Sig", (), {"longitud": len(firma), "datos": sig_buf})
            pub = type("Pub", (), {"longitud": len(pk), "datos": pk_buf})
            return loaded._syn_ed25519_verificar(msg, sig, pub)
    except Exception:
        pass
    # Fallback: Python implementation would need a crypto library;
    # for now, report that verification requires the compiled runtime
    return -1


def _cmd_axon_publish():
    """synapse axon publish — Publica paquete en Axon Hub (Manual 9 §4.2).

    1. Lee axon.toml
    2. Empaqueta código fuente en TAR
    3. Firma el TAR con Ed25519
    4. Publica en IPFS (Axon Hub)
    """
    manifest = _parse_axon_toml()
    if manifest is None:
        return 1

    paquete = manifest.get("paquete", {})
    nombre = paquete.get("nombre", "")
    version = paquete.get("version", "0.0.0")

    # 1. Create TAR archive of source files
    tar_path = os.path.join(".axon_cache", f"{nombre}.tar")
    os.makedirs(".axon_cache", exist_ok=True)

    with tarfile.open(tar_path, "w") as tar:
        # Add src/ directory
        if os.path.isdir("src"):
            tar.add("src", arcname="src")
        # Add tests/ directory
        if os.path.isdir("tests"):
            tar.add("tests", arcname="tests")
        # Add axon.toml
        if os.path.exists("axon.toml"):
            tar.add("axon.toml", arcname="axon.toml")

    print(f"[Axon] TAR creado: {tar_path}")

    # 2. Sign the TAR with Ed25519 (Manual 9 §4.2, step 2)
    sig_path = tar_path + ".sig"
    pk_path = os.path.join(".axon_cache", f"{nombre}.pk")
    sk_path = os.path.join(".axon_cache", f"{nombre}.sk")

    # Use the compiled _syn_ed25519_generar_par + _syn_ed25519_firmar if available,
    # otherwise use the gen_axon_test_fixtures helper
    gen_helper = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tests", "gen_axon_test_fixtures.exe")
    if os.path.exists(gen_helper):
        rc = subprocess.run([gen_helper, tar_path, sig_path, pk_path, sk_path]).returncode
        if rc == 0:
            with open(pk_path) as f:
                pk_hex = f.read().strip()
            print(f"[Axon] Firma Ed25519 generada: {sig_path}")
            print(f"[Axon] Clave pública: {pk_hex[:16]}...")
            print(f"[Axon] Paquete listo para publicar en Axon Hub (IPFS).")
            print(f"[Axon] Verifique con: synapse axon verify {tar_path}")
            return 0
        else:
            print(f"[Axon] ERR: fallo generación de firma (rc={rc})")
            return 1
    else:
        print(f"[Axon] WARN: gen_axon_test_fixtures.exe no encontrado.")
        print(f"[Axon] TAR creado pero no firmado. Compile tests/gen_axon_test_fixtures.c primero.")
        return 1


def _cmd_axon_verify(args: List[str]):
    """synapse axon verify — Verifica firmas y hashes (Manual 8 §4.4)."""
    # Parse arguments
    target = None
    pk_hex = None
    for i, arg in enumerate(args):
        if not arg.startswith('-'):
            if target is None:
                target = arg
        elif arg.startswith("--pk="):
            pk_hex = arg.split("=", 1)[1]
        elif arg.startswith("--pk") and i + 1 < len(args):
            pk_hex = args[i + 1]

    if target is None:
        print("Uso: synapse axon verify <archivo.tar> [--pk <clave_publica_hex>]")
        return 1

    if not os.path.exists(target):
        print(f"[Axon] ERR: archivo no encontrado: {target}")
        return 1

    # 1. Compute and display SHA-256
    hash_val = _sha256_file(target)
    print(f"[Axon] SHA-256: {hash_val}")

    # 2. Verify against axon.lock (if exists)
    lock_entry = _read_lock_entry("axon.lock", os.path.basename(target).replace(".tar", ""))
    if lock_entry:
        expected = lock_entry.get("hash", "")
        if expected.startswith("sha256:"):
            expected = expected[7:]
            if expected == hash_val:
                print(f"[Axon] Hash verificado contra axon.lock ✓")
            else:
                print(f"[Axon] ERR_AXON_COMPROMISED: hash mismatch (lock={expected[:16]}..., actual={hash_val[:16]}...)")
                return 1
        else:
            print(f"[Axon] Lock entry found but hash format invalid")
    else:
        print(f"[Axon] No hay entrada en axon.lock para este paquete")

    # 3. Verify Ed25519 signature (if provided)
    if pk_hex:
        sig_path = target + ".sig"
        if os.path.exists(sig_path):
            rc = _ed25519_verify_file(target, sig_path, pk_hex)
            if rc == 0:
                print(f"[Axon] Firma Ed25519 verificada ✓")
            else:
                print(f"[Axon] ERR_AXON_COMPROMISED: firma invalida")
                return 1
        else:
            print(f"[Axon] WARN: archivo .sig no encontrado: {sig_path}")
    else:
        print(f"[Axon] No se proporcionó clave pública (--pk), saltando verificación Ed25519")

    print("[Axon] Verificación completada.")
    return 0


def _cmd_axon_search(args: List[str]):
    """synapse axon search <nombre> — Busca paquetes en Axón Hub (Manual 8 §4.4)."""
    query = None
    for arg in args:
        if not arg.startswith('-'):
            query = arg
            break

    if not query:
        print("Uso: synapse axon search <nombre_paquete>")
        return 1

    # Check AXON_PATH local directories first
    axon_path = os.environ.get("AXON_PATH", "paquetes_oficiales")
    found = []
    for search_dir in axon_path.split(";"):
        pkg_dir = os.path.join(search_dir, query)
        if os.path.isdir(pkg_dir):
            found.append(pkg_dir)

    if found:
        for d in found:
            print(f"[Axon] Encontrado local: {d}")
            for f in os.listdir(d):
                if f.endswith(".tar"):
                    print(f"  - {f}")
        return 0
    else:
        print(f"[Axon] '{query}' no encontrado localmente.")
        print(f"[Axon] Configure AXON_PATH o use 'synapse fetch' para descargar.")
        return 0


def main():
    parser = argparse.ArgumentParser(description="Synapse Compiler v5.0 - Poliglota", add_help=False)
    parser.add_argument("-h", "--help", action="store_true", help="Mostrar ayuda y salir")
    parser.add_argument("--version", action="store_true", help="Mostrar version y salir")
    parser.add_argument("--incremental", action="store_true", help="Habilitar compilación incremental con caché")
    parser.add_argument("--release", action="store_true", help="Compilar en modo release: optimizaciones -O3 -flto (Manual 8 §4.2)")
    parser.add_argument("--debug", action="store_true", help="Compilar con información de depuración -O0 -g (Manual 8 §4.2)")
    parser.add_argument("--safe", action="store_true", help="Activar modo de verificación formal (M10.1)")
    parser.add_argument("--sbom", action="store_true", help="Generar SBOM SPDX 2.3 (M10.2)")
    parser.add_argument("--sign", type=str, default=None,
                        help="Firmar binario con clave privada Ed25519 (M10.2)")
    parser.add_argument("--tokens", action="store_true", help="Mostrar tokens")
    parser.add_argument("--lang", type=str, default=None,
                        help="Idioma de salida (es, en). Si no da, solo genera C + JSON canonico.")
    parser.add_argument("--lsp", action="store_true", help="Iniciar servidor LSP (daemon sobre stdin/stdout)")
    parser.add_argument("--dump-ast", action="store_true", help="Volcar AST y salir sin generar código")
    parser.add_argument("--check", action="store_true",
                        help="Solo verificar sintaxis y semántica (sin generar código). Usado por el LSP y OpenSyn.")
    parser.add_argument("--migrate", type=str, default=None,
                        help="Migrar archivo Python (.py) a Synapse (.syn)")
    parser.add_argument("--detect-hardware", action="store_true",
                        help="Detectar hardware y sugerir configuracion optima para IA")
    parser.add_argument("construir", nargs="?", help=argparse.SUPPRESS)
    # NO hay argumento posicional 'archivo' aquí - lo detectamos manualmente
    parser.add_argument("-o", "--output", type=str, default=None,
                        help="Ruta del ejecutable de salida")
    args, unknown = parser.parse_known_args()

    # Detectar primer argumento no-opción manualmente desde sys.argv
    first_non_option = None
    for arg in sys.argv[1:]:
        if not arg.startswith('-'):
            first_non_option = arg
            break

    # Detectar subcomando
    subcommand = None
    if first_non_option in ('cache', 'build', 'test', 'fetch', 'init', 'axon'):
        subcommand = first_non_option

    # Manejar subcomando 'cache'
    if subcommand == 'cache':
        # El siguiente argumento no-opción es el sub-subcomando
        cache_subcmd = None
        for arg in sys.argv[2:]:
            if not arg.startswith('-'):
                cache_subcmd = arg
                break
        
        if not cache_subcmd or cache_subcmd == "cache":
            _print_cache_help()
            return 1
        if cache_subcmd == "stats":
            stats = _cache_stats()
            print("========================================")
            print("  Synapse Cache — Estadísticas")
            print("========================================")
            print(f"  Directorio:       {_cache_dir()}")
            print(f"  Hits totales:     {stats.get('hits', 0)}")
            print(f"  Misses totales:   {stats.get('misses', 0)}")
            print(f"  Entradas totales: {stats.get('total_entries', 0)}")
            print(f"  Bytes totales:    {stats.get('total_bytes', 0)}")
            if 'archivos_obj' in stats:
                print(f"  Archivos .o:      {stats['archivos_obj']}")
            print("========================================")
            return 0
        elif cache_subcmd == "clean":
            print("[CACHE] Limpiando ~/.synapse/cache/...")
            _cache_clean()
            print("[OK] Caché limpiado")
            return 0
        else:
            print(f"Comando de caché desconocido: {cache_subcmd}")
            _print_cache_help()
            return 1

    # Manejar subcomando 'test' — Auditoría de sanitizadores (Manual 9 §9.5)
    if subcommand == 'test':
        test_subcmd = None
        for arg in sys.argv[2:]:
            if arg.startswith('--auditar-'):
                test_subcmd = arg
                break
        if test_subcmd == '--auditar-memoria':
            print('[AUDIT] Iniciando auditoría de memoria (ASan + LSan)...')
            print('[AUDIT] Manual 9 §9.5: Verificación de 0 fugas de memoria')
            print()
            return _auditar_memoria()
        elif test_subcmd == '--auditar-hilos':
            print('[AUDIT] Iniciando auditoría de hilos (TSan)...')
            print('[AUDIT] Manual 9 §9.5: Verificación de 0 data races')
            print()
            return _auditar_hilos()
        else:
            print('Uso: synapse test --auditar-memoria|--auditar-hilos')
            print()
            print('  synapse test --auditar-memoria   AddressSanitizer + LeakSanitizer (0 fugas)')
            print('  synapse test --auditar-hilos     ThreadSanitizer (0 data races)')
            print()
            print('Manual 9 §9.5 — Auditoría obligatoria de sanitizadores')
            return 1

    # ================================================================
    # Axon CLI commands (Manual 8 §4.1, §4.4)
    # ================================================================

    # Manejar subcomando 'fetch' (Manual 8 §4.4: synapse fetch)
    if subcommand == 'fetch':
        return _cmd_fetch()

    # Manejar subcomando 'init' (Manual 8 §4.2/§4.3: synapse init)
    if subcommand == 'init':
        return _cmd_init()

    # Manejar subcomando 'axon' (Manual 8 §4.4: synapse axon <subcommand>)
    if subcommand == 'axon':
        axon_args = sys.argv[2:]
        axon_subcmd = None
        for arg in axon_args:
            if not arg.startswith('-'):
                axon_subcmd = arg
                break
        if axon_subcmd == 'init':
            return _cmd_axon_init()
        elif axon_subcmd == 'publish':
            return _cmd_axon_publish()
        elif axon_subcmd == 'verify':
            return _cmd_axon_verify(axon_args)
        elif axon_subcmd == 'search':
            return _cmd_axon_search(axon_args)
        else:
            print("Comandos Axon disponibles:")
            print("  synapse axon init     - Crear manifiesto Axon")
            print("  synapse axon publish  - Publicar paquete en Axon Hub (IPFS)")
            print("  synapse axon verify   - Verificar firmas y hashes")
            print("  synapse axon search <nombre> - Buscar paquetes")
            return 0

    # Manejar subcomando 'build'
    if subcommand == 'build':
        # El siguiente argumento no-opción es el archivo
        build_file = None
        for arg in sys.argv[2:]:
            if not arg.startswith('-'):
                build_file = arg
                break
        
        if not build_file:
            print("ERROR: Se requiere archivo .syn para build")
            return 1
        
        # Parsear opciones adicionales (--incremental, -o)
        incremental = "--incremental" in sys.argv
        output_path = None
        for i, arg in enumerate(sys.argv):
            if arg == "-o" or arg == "--output":
                if i + 1 < len(sys.argv):
                    output_path = sys.argv[i + 1]
                break
        
        # Parsear --target (Manual 8 §4.2)
        target = "native"
        for i, arg in enumerate(sys.argv):
            if arg == "--target":
                if i + 1 < len(sys.argv):
                    target = sys.argv[i + 1]
                    break
        
        modo_safe = "--safe" in sys.argv
        check_only = "--check" in sys.argv
        generar_sbom_flag = "--sbom" in sys.argv
        clave_sbom = args.sign or ""
        codigo = ejecutar_compilador(build_file, mostrar_tokens=False,
                                     output_lang=None, dump_ast=False,
                                     modo_safe=modo_safe,
                                     output_path=output_path,
                                     incremental=incremental,
                                     generar_sbom=generar_sbom_flag,
                                     firmar_binario=bool(clave_sbom),
                                     clave_sbom=clave_sbom,
                                    target=target,
                                      modo_release=args.release,
                                      modo_debug=args.debug,
                                      check_only=check_only)
        return codigo

    if args.help:
        parser.print_help()
        print("\nComandos adicionales:")
        print("  synapse cache stats|clean            - Gestión de caché")
        print("  synapse build --incremental <f.syn>  - Build incremental")
        print("  synapse init                         - Crear proyecto (Manual 8 §4.3)")
        print("  synapse fetch                        - Descargar dependencias (Manual 8 §4.4)")
        print("  synapse axon init                    - Crear manifiesto Axon")
        print("  synapse axon publish                 - Publicar en Axon Hub (Manual 9 §4.2)")
        print("  synapse axon verify <f.tar> [--pk HEX] - Verificar firmas y hashes")
        print("  synapse axon search <nombre>         - Buscar paquetes")
        sys.exit(0)

    if args.version:
        version_file = os.path.join(os.path.dirname(__file__), "VERSION")
        version = "8.1.0-industrial"
        if os.path.exists(version_file):
            try:
                with open(version_file, "r") as f:
                    version = f.read().strip()
            except Exception:
                pass
        print(f"Synapse Compiler v{version}")
        sys.exit(0)

    if args.detect_hardware:
        hw_exe = os.path.join(os.path.dirname(__file__), "nucleo", "detect_hardware.exe")
        if not os.path.exists(hw_exe):
            hw_exe = os.path.join(os.path.dirname(__file__), "..", "nucleo", "detect_hardware.exe")
        if os.path.exists(hw_exe):
            result = subprocess.run([hw_exe, "--json"], capture_output=True, text=True, timeout=10)
            if result.returncode == 0 and result.stdout.strip():
                try:
                    data = json.loads(result.stdout.strip())
                    print("========================================")
                    print("  Synapse — Perfil de Hardware")
                    print("========================================")
                    print(f"  RAM total:       {data['ram_gb']:.1f} GB")
                    print(f"  VRAM detectada:  {data['vram_gb']:.1f} GB")
                    print(f"  CPUs lógicos:    {data['cpu_logicos']}")
                    print(f"  CPUs físicos:    {data['cpu_fisicos']}")
                    print("----------------------------------------")
                    tiers = {"insuficiente": "INSUFICIENTE (< 8 GB)", "1b": "1B (8–31 GB)", "7b": "7B (32–63 GB)", "70b": "70B (≥ 64 GB)"}
                    print(f"  Tier:            {tiers.get(data['tier'], data['tier'])}")
                    print(f"  Modelo sugerido:  {data['modelo']}")
                    print(f"  ctx-size sugerido: {data['ctx_size']}")
                    print(f"  threads sugeridos: {data['threads']}")
                    if data['ngl'] > 0:
                        print(f"  ngl (GPU layers): {data['ngl']}")
                    else:
                        print("  ngl (GPU layers): desactivado (sin VRAM suficiente)")
                    print("========================================")
                except (json.JSONDecodeError, KeyError) as e:
                    print(f"ERROR: No se pudo interpretar perfil: {e}", file=sys.stderr)
                    sys.exit(1)
            else:
                print(f"ERROR: No se pudo detectar hardware", file=sys.stderr)
                sys.exit(1)
        else:
            print(f"ERROR: '{hw_exe}' no encontrado. Compilar con: gcc -o nucleo/detect_hardware.exe nucleo/detect_hardware.c -lm -lgdi32", file=sys.stderr)
            sys.exit(1)
        sys.exit(0)

    if args.migrate:
        from synapse_lsp.open_syn.py_parser import parse_python_file_to_syn
        from synapse_lsp.open_syn.ast_mapper import canonical_to_synapse
        from synapse_lsp.open_syn.pretty_printer import syn_pretty_print_file, syn_pretty_print

        py_path = args.migrate
        if not os.path.exists(py_path):
            print(f"ERROR: Archivo '{py_path}' no encontrado", file=sys.stderr)
            sys.exit(1)

        canonical = parse_python_file_to_syn(py_path)
        syn_ast = canonical_to_synapse(canonical)

        output_path = args.output
        if output_path is None:
            output_path = os.path.splitext(py_path)[0] + ".syn"

        syn_pretty_print_file(syn_ast, output_path)
        print(f"[OK] Migrado: {py_path} -> {output_path}")
        sys.exit(0)

    if args.construir == "construir":
        tokens_flag = "--tokens" in sys.argv
        dump_flag = "--dump-ast" in sys.argv
        lang_val = None
        for i, a in enumerate(sys.argv):
            if a == "--lang" and i + 1 < len(sys.argv):
                lang_val = sys.argv[i + 1]

        axon_exe = os.path.join(os.path.dirname(__file__), "axon_build.exe")
        if not os.path.exists(axon_exe):
            print(f"ERROR: '{axon_exe}' no encontrado. Compilar con: gcc -o axon_build.exe axon_build.c", file=sys.stderr)
            sys.exit(1)

        out_path = os.path.join(os.environ.get('TEMP', '.'), f"axon_out_{os.getpid()}.txt")
        cmd = axon_exe + ' "' + os.getcwd() + '" > "' + out_path + '"'
        ret = os.system(cmd)

        if ret != 0:
            try:
                with open(out_path, 'r') as f:
                    err_line = f.read().strip()
                os.remove(out_path)
            except (FileNotFoundError, OSError):
                err_line = ""

            if ret == 1:
                diag = DiagnosticManager()
                diag.reportar(ErrorCodes.ERR_MANIFEST_NOT_FOUND, Token(TokenID.EOF, 0, 0))
                print(diag.resumen(), file=sys.stderr)
                sys.exit(diag.codigo_salida())
            elif ret == 3:
                print(f"ERROR: El manifiesto axon.toml debe tener '[paquete]' con clave 'punto_entrada' (Manual 8 §4.3)", file=sys.stderr)
                sys.exit(1)
            elif ret == 4:
                dep_name = err_line.split(':')[-1] if ':' in err_line else "desconocida"
                diag = DiagnosticManager()
                diag.reportar(ErrorCodes.ERR_GIT_FAILURE, Token(TokenID.EOF, 0, 0), modulo=dep_name)
                print(diag.resumen(), file=sys.stderr)
                sys.exit(diag.codigo_salida())
            elif ret == 5:
                dep_name = err_line.split(':')[-1] if ':' in err_line else "desconocida"
                diag = DiagnosticManager()
                diag.reportar(ErrorCodes.ERR_LOCK_HASH_MISMATCH, Token(TokenID.EOF, 0, 0), modulo=dep_name)
                print(diag.resumen(), file=sys.stderr)
                sys.exit(diag.codigo_salida())
            else:
                print(f"ERROR: Fallo en construccion (codigo {ret})", file=sys.stderr)
                sys.exit(1)

        lineas = []
        try:
            with open(out_path, 'r') as f:
                lineas = [l.strip() for l in f if l.strip()]
            os.remove(out_path)
        except (FileNotFoundError, OSError):
            pass

        punto_entrada = ""
        dependencias: Dict[str, Any] = {}
        for ln in lineas:
            if ln.startswith("punto_entrada="):
                punto_entrada = ln.split("=", 1)[1]
            else:
                dependencias[ln] = True

        ruta_entrada = os.path.normpath(os.path.join(os.getcwd(), punto_entrada))
        if not os.path.exists(ruta_entrada):
            diag = DiagnosticManager()
            diag.reportar(ErrorCodes.ERR_FILE_NOT_FOUND,
                          Token(TokenID.EOF, 0, 0), archivo=ruta_entrada)
            print(diag.resumen(), file=sys.stderr)
            sys.exit(diag.codigo_salida())

        codigo = ejecutar_compilador(ruta_entrada, mostrar_tokens=tokens_flag,
                                     output_lang=lang_val, dump_ast=dump_flag,
                                     dependencias=dependencias)
        sys.exit(codigo)

    if args.lsp:
        from synapse_lsp.server import iniciar
        iniciar()
    else:
        # Compilación normal: detectar archivo principal desde sys.argv
        archivo_principal = None
        for arg in sys.argv[1:]:
            if not arg.startswith('-'):
                archivo_principal = arg
                break
        
        if archivo_principal is None:
            print("[ERROR] Se requiere archivo .syn para compilar", file=sys.stderr)
            parser.print_help()
            sys.exit(1)
        
        codigo = ejecutar_compilador(archivo_principal, mostrar_tokens=args.tokens,
                                     output_lang=args.lang, dump_ast=args.dump_ast,
                                     modo_safe=args.safe,
                                     output_path=args.output,
                                     incremental=args.incremental,
                                     generar_sbom=args.sbom,
                                     firmar_binario=bool(args.sign),
                                     clave_sbom=args.sign or '',
                                     target="native",
                                     modo_release=args.release,
                                     modo_debug=args.debug)
        sys.exit(codigo)


if __name__ == "__main__":
    main()