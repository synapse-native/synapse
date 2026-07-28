#!/usr/bin/env python3
"""ci_sign.py — Helper for CI/CD signing operations.
Usage: python scripts/ci_sign.py <command> [args...]

Commands:
  generate-key       Generate Ed25519 key pair
  sign <artifact> <priv_key>  Sign a file
  verify <artifact> <sig> <pub_key>  Verify signature
  sha256 <file>     Calculate SHA-256
  sbom <artifact> <sha256> <sig> <pub>  Generate SLSA attestation
  checksum-sign <file> <priv_key>  Sign checksum file
"""
import sys
import os
import hashlib
import json

sys.path.insert(0, '.')

def generate_key():
    from nucleo.ed25519_signer import generar_par_claves
    priv, pub = generar_par_claves()
    print(f'PRIV={priv}')
    print(f'PUB={pub}')

def sign_file(artifact, priv_key):
    from nucleo.ed25519_signer import firmar_archivo, verificar_archivo, _calc_public_key
    sig = firmar_archivo(artifact, priv_key, artifact + '.sig')
    pub = _calc_public_key(bytes.fromhex(priv_key)).hex()
    valid = verificar_archivo(artifact, sig, pub)
    h = hashlib.sha256()
    with open(artifact, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    sha256 = h.hexdigest()
    print(f'SIG={sig.hex()}')
    print(f'PUB={pub}')
    print(f'VALID={valid}')
    print(f'SHA256={sha256}')

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    print(h.hexdigest())

def checksum_sign(filepath, priv_key):
    from nucleo.ed25519_signer import firmar
    with open(filepath, 'rb') as f:
        content = f.read()
    sig = firmar(content, priv_key)
    with open(filepath + '.sig', 'w') as f:
        f.write(sig)
    print(f'Checksum signed: {sig[:32]}...')

def sbom(artifact, sha256, sig, pub):
    att = {
        'version': '1.0.0',
        'buildType': 'https://synapse-lang.org/build',
        'subject': [{'name': artifact, 'digest': {'sha256': sha256}}],
        'predicateType': 'https://slsa.dev/provenance/v1',
        'predicate': {
            'builder': {'id': 'https://synapse-lang.org/builder'},
            'buildType': 'synapse-build',
            'recipe': {'type': 'synapse-compiler', 'version': os.environ.get('SYNAPSE_VERSION', '5.0.0-dev')},
            'metadata': {'completeness': {'parameters': True, 'environment': False, 'materials': False}, 'reproducible': False},
            'materials': [{'uri': 'git+https://github.com/synapse/nucleo/principal.syn', 'digest': {'sha256': sha256}}],
        },
        'signature': sig,
        'publicKey': pub,
    }
    with open(artifact + '.attestation.json', 'w') as f:
        json.dump(att, f, indent=2)
    print('SLSA attestation generated')

def verify_file(artifact, sig_path, pub_key_path):
    from nucleo.ed25519_signer import verificar_archivo
    import os
    if os.path.exists(pub_key_path):
        with open(pub_key_path) as f:
            pub_key = f.read().strip()
        with open(sig_path) as f:
            sig = f.read().strip()
        valid = verificar_archivo(artifact, sig, pub_key)
        print('SIGNATURE_VALID=YES' if valid else 'SIGNATURE_VALID=NO')
    else:
        print('SIGNATURE_VALID=NO')

if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''
    if cmd == 'generate-key':
        generate_key()
    elif cmd == 'sign':
        sign_file(sys.argv[2], sys.argv[3])
    elif cmd == 'verify':
        verify_file(sys.argv[2], sys.argv[3], sys.argv[4])
    elif cmd == 'sha256':
        sha256_file(sys.argv[2])
    elif cmd == 'checksum-sign':
        checksum_sign(sys.argv[2], sys.argv[3])
    elif cmd == 'sbom':
        sbom(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
    else:
        print(__doc__)
        sys.exit(1)
