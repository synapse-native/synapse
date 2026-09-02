# cumple Manual 1 §1: infraestructura Python del compilador Synapse
# cumple Manual 8 §4: toolchain de construcción
"""
nucleo/sbom.py — Generación de SBOM (Software Bill of Materials) estándar SPDX 2.3

Responsabilidades:
  1. Escanear el árbol de dependencias del proyecto
  2. Emitir inventario SPDX 2.3 en formato JSON
  3. Calcular SHA-256 de cada artefacto
  4. Incluir metadatos de licencia, versión y origen

Uso:
  from nucleo.sbom import generar_sbom
  sbom = generar_sbom(ruta_proyecto)
  with open("sbom.spdx.json", "w") as f:
      f.write(sbom)
"""

import os
import json
import hashlib
import datetime
from datetime import timezone
from typing import List, Dict, Optional, Set
from pathlib import Path

# Extensiones de archivo fuente reconocidas
EXTENSIONES_FUENTE = {'.syn', '.py', '.c', '.h', '.toml', '.json', '.yml', '.yaml', '.md', '.sh', '.ps1', '.bat', '.iss'}
EXTENSIONES_BINARIO = {'.exe', '.o', '.so', '.dll', '.dylib', '.a', '.lib'}

# Extensiones a excluir del SBOM
EXCLUIR_EXTENSIONES = {'.pyc', '.pyo', '.pytest_cache', '.git', '.venv', '__pycache__'}
EXCLUIR_DIRECTORIOS = {'.git', '.venv', '__pycache__', '.pytest_cache', '.egg-info',
                       'toolchain_gcc12', 'node_modules', '.github'}


def sha256_archivo(ruta: str) -> str:
    """Calcula SHA-256 de un archivo."""
    h = hashlib.sha256()
    try:
        with open(ruta, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                h.update(chunk)
        return h.hexdigest()
    except (OSError, IOError):
        return ''


def sha256_texto(contenido: str) -> str:
    """Calcula SHA-256 de un texto."""
    return hashlib.sha256(contenido.encode('utf-8')).hexdigest()


def _escanear_archivos(ruta_proyecto: str, max_depth: int = 5) -> List[Dict]:
    """Escanea el directorio del proyecto para encontrar todos los archivos relevantes."""
    archivos = []
    ruta_proyecto = os.path.abspath(ruta_proyecto)

    for root, dirs, files in os.walk(ruta_proyecto):
        # Excluir directorios no deseados
        dirs[:] = [d for d in dirs if d not in EXCLUIR_DIRECTORIOS and not d.startswith('.')]

        # Calcular profundidad relativa
        try:
            rel_path = os.path.relpath(root, ruta_proyecto)
        except ValueError:
            continue  # Saltar rutas con problemas de montaje (ej. \\.\nul en Windows)
        depth = 0 if rel_path == '.' else rel_path.count(os.sep) + 1
        if depth > max_depth:
            continue

        for fname in files:
            ext = os.path.splitext(fname)[1].lower()
            if ext in EXCLUIR_EXTENSIONES:
                continue

            # Saltar nombres reservados de Windows (nul, con, prn, etc.)
            base_lower = os.path.splitext(fname)[0].lower()
            if base_lower in ('nul', 'con', 'prn', 'aux', 'com1', 'com2', 'com3', 'com4',
                               'lpt1', 'lpt2', 'lpt3', 'clock$'):
                continue

            if ext in EXTENSIONES_FUENTE or ext in EXTENSIONES_BINARIO or ext == '':
                fpath = os.path.join(root, fname)
                try:
                    rel = os.path.relpath(fpath, ruta_proyecto)
                except ValueError:
                    continue
                if rel.startswith('.'):
                    continue

                hash_val = sha256_archivo(fpath)
                try:
                    size = os.path.getsize(fpath)
                except OSError:
                    size = 0

                # Determinar tipo de archivo
                if ext in EXTENSIONES_FUENTE:
                    pkg_type = "SOURCE"
                elif ext in EXTENSIONES_BINARIO:
                    pkg_type = "BINARY"
                else:
                    pkg_type = "OTHER"

                archivos.append({
                    "fileName": rel.replace(os.sep, '/'),
                    "SHA256": hash_val,
                    "size": size,
                    "type": pkg_type,
                })

    return archivos


def _generar_packages(archivos: List[Dict], proyecto_nombre: str, proyecto_version: str) -> List[Dict]:
    """Genera la lista de paquetes SPDX a partir de los archivos escaneados."""
    packages = []

    # Paquete principal del proyecto
    hash_proyecto = sha256_texto(proyecto_nombre + proyecto_version + str(datetime.datetime.now().year))
    packages.append({
        "SPDXID": "SPDXRef-ROOT",
        "name": proyecto_nombre,
        "versionInfo": proyecto_version,
        "supplier": "Organization: Synapse Project",
        "downloadLocation": "NOASSERTION",
        "filesAnalyzed": True,
        "packageVerificationCode": {
            "packageVerificationCodeValue": hash_proyecto[:64],
        },
        "checksums": [{"algorithm": "SHA256", "checksumValue": hash_proyecto}],
        "licenseConcluded": "NOASSERTION",
        "licenseDeclared": "NOASSERTION",
        "copyrightText": "NOASSERTION",
    })

    # Paquetes individuales por archivo fuente
    for i, f in enumerate(archivos):
        pkg_id = f"SPDXRef-FILE-{i}"
        entry = {
            "SPDXID": pkg_id,
            "name": f["fileName"],
            "versionInfo": "1.0.0",
            "supplier": "NOASSERTION",
            "downloadLocation": "NOASSERTION",
            "filesAnalyzed": True,
            "checksums": [{"algorithm": "SHA256", "checksumValue": f["SHA256"]}],
            "licenseConcluded": "NOASSERTION",
            "licenseDeclared": "NOASSERTION",
            "copyrightText": "NOASSERTION",
            "primaryPackagePurpose": f["type"],
        }
        if f["size"] > 0:
            entry["size"] = f["size"]
        packages.append(entry)

    return packages


def _generar_relationships(archivos: List[Dict]) -> List[Dict]:
    """Genera las relaciones SPDX entre paquetes."""
    relationships = []
    for i, _ in enumerate(archivos):
        relationships.append({
            "spdxElementId": "SPDXRef-ROOT",
            "relatedSpdxElement": f"SPDXRef-FILE-{i}",
            "relationshipType": "CONTAINS",
        })
    return relationships


def _leer_version(ruta_proyecto: str) -> str:
    """Lee la versión desde el archivo VERSION en la raíz del proyecto."""
    version_path = os.path.join(ruta_proyecto, 'VERSION')
    try:
        with open(version_path, 'r') as f:
            return f.read().strip()
    except (OSError, IOError):
        return '8.1.0-industrial'


def generar_sbom(ruta_proyecto: str,
                 nombre: str = "synapse",
                 version: str = "",
                 creator: str = "Synapse Project",
                 namespace: str = "https://synapse-lang.org/spdx") -> str:
    """Genera un SBOM en formato SPDX 2.3 JSON.

    Args:
        ruta_proyecto: Ruta al directorio raíz del proyecto
        nombre: Nombre del proyecto
        version: Versión del proyecto
        creator: Nombre del creador/tool
        namespace: Espacio de nombres SPDX

    Returns:
        String con el SBOM en formato JSON
    """
    # Resolver version ANTES de construir cualquier estructura
    if not version:
        version = _leer_version(ruta_proyecto)
    # Escanear archivos
    archivos = _escanear_archivos(ruta_proyecto)

    # Construir documento SPDX
    doc = {
        "spdxVersion": "SPDX-2.3",
        "dataLicense": "CC0-1.0",
        "SPDXID": "SPDXRef-DOCUMENT",
        "name": f"{nombre} SBOM",
        "documentNamespace": f"{namespace}/{nombre}-{version}-sbom-{hashlib.sha256((nombre + version).encode()).hexdigest()[:12]}",
        "creationInfo": {
            "creators": [
                f"Tool: synapse-sbom-2.0",
                f"Organization: {creator}",
            ],
            "created": datetime.datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
        "packages": _generar_packages(archivos, nombre, version),
        "files": [
            {
                "fileName": f["fileName"],
                "SPDXID": f"SPDXRef-FILE-{i}",
                "checksums": [{"algorithm": "SHA256", "checksumValue": f["SHA256"]}],
            }
            for i, f in enumerate(archivos) if f["SHA256"]
        ],
        "relationships": _generar_relationships(archivos),
    }

    return json.dumps(doc, indent=2, ensure_ascii=False)


def generar_sbom_simplificado(ruta_proyecto: str) -> Dict:
    """Genera un resumen estructurado del SBOM para uso interno.

    Returns:
        Dict con metadatos del proyecto, lista de dependencias y hashes
    """
    archivos = _escanear_archivos(ruta_proyecto)

    # Leer axon.toml si existe
    axon_toml_path = os.path.join(ruta_proyecto, 'axon.toml')
    metadatos = {
        "nombre": "synapse",
        "version": _leer_version(ruta_proyecto),
        "dependencias": [],
        "hash_proyecto": "",
    }

    if os.path.exists(axon_toml_path):
        try:
            with open(axon_toml_path, 'r') as f:
                contenido = f.read()
            metadatos["hash_proyecto"] = sha256_texto(contenido)
            # Extraer nombre y version del TOML
            for linea in contenido.split('\n'):
                linea = linea.strip()
                if linea.startswith('nombre ='):
                    metadatos["nombre"] = linea.split('=')[1].strip().strip('"')
                elif linea.startswith('version ='):
                    metadatos["version"] = linea.split('=')[1].strip().strip('"')
        except (OSError, IOError):
            pass

    # Buscar dependencias en axon_modules
    axon_modules = os.path.join(ruta_proyecto, 'axon_modules')
    if os.path.isdir(axon_modules):
        for dep in os.listdir(axon_modules):
            dep_path = os.path.join(axon_modules, dep)
            if os.path.isdir(dep_path):
                dep_manifest = os.path.join(dep_path, 'axon.toml')
                dep_hash = ''
                if os.path.exists(dep_manifest):
                    try:
                        with open(dep_manifest, 'rb') as f:
                            dep_hash = hashlib.sha256(f.read()).hexdigest()
                    except OSError:
                        pass
                metadatos["dependencias"].append({
                    "nombre": dep,
                    "hash": dep_hash,
                })

    return {
        "metadatos": metadatos,
        "total_archivos": len(archivos),
        "archivos": archivos,
    }


if __name__ == '__main__':
    import sys
    import argparse
    parser_arg = argparse.ArgumentParser(description='Generar SBOM SPDX 2.3')
    parser_arg.add_argument('ruta', nargs='?', default='.', help='Ruta del proyecto')
    parser_arg.add_argument('--output', '-o', type=str, default=None,
                            help='Archivo de salida (si no se da, imprime a stdout)')
    args_sbom = parser_arg.parse_args()
    sbom = generar_sbom(args_sbom.ruta)
    if args_sbom.output:
        with open(args_sbom.output, 'w', encoding='utf-8') as f:
            f.write(sbom)
        print(f'[SBOM] Escrito: {args_sbom.output}', file=sys.stderr)
    else:
        print(sbom)
