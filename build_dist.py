import os
import shutil
import stat
import zipfile

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
VERSION = "v2.1.0"
DIST_DIR = os.path.join(PROJECT_ROOT, "dist")

def remove_readonly(func, path, excinfo):
    os.chmod(path, stat.S_IWRITE)
    func(path)

def clean_create_dir(path):
    if os.path.exists(path):
        shutil.rmtree(path, onerror=remove_readonly)
    os.makedirs(path)

def generate_install_ps1(dist_path):
    ps1_content = r"""$distDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$binPath = Join-Path $distDir "bin"

$currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($currentPath -split ";" -notcontains $binPath) {
    $newPath = $currentPath + ";" + $binPath
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    Write-Host "Synapse instalado correctamente. Reinicia tu terminal."
} else {
    Write-Host "Synapse ya se encuentra en el PATH."
}
"""
    ps1_path = os.path.join(dist_path, "install.ps1")
    with open(ps1_path, "w", encoding="utf-8") as f:
        f.write(ps1_content)
    return ps1_path

def build():
    clean_create_dir(DIST_DIR)

    bin_dir = os.path.join(DIST_DIR, "bin")
    lib_dir = os.path.join(DIST_DIR, "lib")
    os.makedirs(bin_dir, exist_ok=True)
    os.makedirs(lib_dir)

    # Copy compiler executable
    shutil.copy2(os.path.join(PROJECT_ROOT, "synapse.exe"),
                 os.path.join(bin_dir, "synapse.exe"))

    # Build Axon package manager executable
    axon_py = os.path.join(PROJECT_ROOT, "axon_src", "axon.py")
    if os.path.exists(axon_py):
        import subprocess
        axon_exe = os.path.join(bin_dir, "axon.exe")
        try:
            subprocess.run(
                ["pyinstaller", "--onefile", "--distpath", bin_dir,
                 "--specpath", os.path.join(PROJECT_ROOT, "build"),
                 "--workpath", os.path.join(PROJECT_ROOT, "build"),
                 "--name", "axon", axon_py],
                check=True, capture_output=True, text=True, cwd=PROJECT_ROOT
            )
            print(f"[+] axon.exe generado en: {axon_exe}")
        except Exception as e:
            print(f"[!] PyInstaller fallo, copiando axon.py directamente: {e}")
            shutil.copy2(axon_py, os.path.join(bin_dir, "axon.py"))

    # Copy runtime object and header
    shutil.copy2(os.path.join(PROJECT_ROOT, "synapse_rt.o"),
                 os.path.join(lib_dir, "synapse_rt.o"))
    shutil.copy2(os.path.join(PROJECT_ROOT, "synapse_rt.h"),
                 os.path.join(lib_dir, "synapse_rt.h"))

    # Copy runtime headers (preserving relative structure for #include "librerias/...")
    lib_librerias = os.path.join(lib_dir, "librerias")
    shutil.copytree(os.path.join(PROJECT_ROOT, "librerias"), lib_librerias)
    # Generate install script
    generate_install_ps1(DIST_DIR)

    # Create zip package for release
    zip_name = f"synapse-{VERSION}-windows-x64.zip"
    zip_path = os.path.join(DIST_DIR, zip_name)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(DIST_DIR):
            for filename in files:
                full_path = os.path.join(root, filename)
                if full_path == zip_path:
                    continue
                rel_path = os.path.relpath(full_path, DIST_DIR)
                zipf.write(full_path, rel_path)

    print(f"Distribucion generada en: {DIST_DIR}")
    print(f"Paquete zip creado: {zip_path}")

if __name__ == "__main__":
    build()
