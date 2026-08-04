#!/usr/bin/env python3
"""ci_sbom.py — Generate SPDX SBOM for Synapse releases."""
import hashlib
import os
import json
import time
from pathlib import Path
import sys

def _version_canonica(project_root: str) -> str:
    """Lee la versión canónica del archivo VERSION (Manual 1 §6: versión unificada)."""
    version_file = Path(project_root) / 'VERSION'
    if version_file.is_file():
        v = version_file.read_text(encoding='utf-8').strip()
        if v:
            return v
    return os.environ.get('SYNAPSE_VERSION', '0.0.0-dev')


def generar_sbom_standalone(project_root, artifact_name):
    files = []
    packages = []
    
    # Directorios que NO forman parte del SBOM: entornos, builds y distribución.
    EXCLUIR = {'.git', '__pycache__', 'toolchain_gcc12', '.venv', 'venv', 'build',
               'dist', 'distbin', '.pytest_cache', '.synapse', '.axon_cache'}

    root_hash = hashlib.sha256()
    for f in sorted(Path(project_root).rglob('*')):
        if f.is_file() and not any(p in str(f).split(os.sep) for p in EXCLUIR):
            try:
                root_hash.update(f.read_bytes())
                files.append({
                    'fileName': str(f.relative_to(project_root)),
                    'checksums': [{'algorithm': 'SHA256', 'value': hashlib.sha256(f.read_bytes()).hexdigest()}]
                })
            except Exception:
                pass
    
    sbom = {
        'spdxVersion': 'SPDX-2.3',
        'dataLicense': 'CC0-1.0',
        'SPDXID': 'SPDXRef-DOCUMENT',
        'name': f'Synapse-{artifact_name}',
        'creationInfo': {
            'created': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            'creators': ['Tool: synapse-release-matrix'],
        },
        'packages': [{
            'SPDXID': 'SPDXRef-RootPackage',
            'name': artifact_name,
            'versionInfo': _version_canonica(project_root),
            'supplier': 'Organization: Synapse Lang',
            'downloadLocation': 'NOASSERTION',
            'filesAnalyzed': True,
            'checksums': [{'algorithm': 'SHA256', 'value': root_hash.hexdigest()}],
        }],
        'files': files,
        'relationships': [{
            'spdxElementId': 'SPDXRef-DOCUMENT',
            'relatedSpdxElement': 'SPDXRef-RootPackage',
            'relationshipType': 'DESCRIBES',
        }],
    }
    return json.dumps(sbom, indent=2)

if __name__ == '__main__':
    artifact_name = sys.argv[1] if len(sys.argv) > 1 else 'unknown'
    sbom = json.loads(generar_sbom_standalone('.', artifact_name))
    with open(f'{artifact_name}.spdx.json', 'w') as f:
        json.dump(sbom, f, indent=2)
    print('SBOM SPDX 2.3 generado')
