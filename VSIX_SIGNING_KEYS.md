# VSIX Signing Keys

## Ed25519 Key Pair for VS Code Extension Signing

**Public Key (PEM)**:
```
-----BEGIN PUBLIC KEY-----
MCowBQYDK2VwAyEAQHR4k7lmx/wEKYIx0AxyBd63nctyP2dxTRr//KF7pJc=
-----END PUBLIC KEY-----
```

**Public Key Hex** (for `openssl pkeyutl -verify`):
```
40747893b966c7fc04298231d00c7205deb79dcb723f67714d1afffca17ba497
```

## Setup

1. Add private key hex as GitHub Secret:
   - Go to GitHub → Settings → Secrets and variables → Actions
   - New repository secret
   - Name: `VSIX_SIGNING_KEY`
   - Value: `6dd9e673e70d7bc575c4d0275e3ea221fbf04314535b696097866050ff3d8a73`

2. Keep `vsix_signing_private.pem` secure and out of version control.

## Verification

```bash
# Verify signature
openssl pkeyutl -verify -pubin -inkey vsix_signing_public.pem -rawin -in synapse.vsix -sigfile synapse.vsix.sig
```
