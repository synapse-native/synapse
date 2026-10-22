# cumple Manual 6 §1: oráculo H-R144-3 — catálogo real, sin placeholder
"""ME r194_deuda_gobernanza (R2/H-R144-3): verificador del catálogo de modelos.

El protocolo del catálogo (opensyn/modelos.toml, Manual 9 §5.6): el campo
`sha256` de cada modelo DEBE ser el LFS oid (X-Linked-ETag) del archivo real
remoto en HuggingFace, así el descargador puede validar integridad sin
confiar ciegamente en la red.

Evidencia comiteada: auditoria/evidencia/r194_catalogo_etag.txt — captura
HTTP HEAD (H-R144-3, 5/5) que empareja cada URL con su X-Linked-ETag.

Sin red en CI: el oráculo contrasta el toml contra esa captura (URL→ETag
exacto) y rechaza placeholders: sha256 vacío, todo-ceros, no-hex o claves
nunca capturadas. Si el toml cambia sin re-captura, FALLA (rc=1); regenerar
la captura con un HEAD por URL y actualizar el transcript.

Ejecución: .venv/Scripts/python.exe auditoria/evidencia/r194_catalogo_verificar.py
"""
import re
import sys
import tomllib
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
TOML = RAIZ / "opensyn" / "modelos.toml"
TRANSCRIPT = RAIZ / "auditoria" / "evidencia" / "r194_catalogo_etag.txt"


def main() -> int:
    if not TOML.exists() or not TRANSCRIPT.exists():
        print("FALLO: falta opensyn/modelos.toml o el transcript r194_catalogo_etag.txt")
        return 1

    texto = TRANSCRIPT.read_text(encoding="utf-8")
    pares = dict(re.findall(
        r"URL=(\S+)\nX-Linked-ETag:\s*\"?([0-9a-f]{64})\"?", texto))
    if not pares:
        print("FALLO: el transcript no contiene pares URL/X-Linked-ETag")
        return 1

    modelos = tomllib.loads(TOML.read_text(encoding="utf-8"))["modelos"]
    problemas, verificados = [], 0
    for nombre, m in sorted(modelos.items()):
        url, sha = m.get("url", ""), m.get("sha256", m.get("hash_modelo", ""))
        sha = (sha or "").strip().lower()
        if not sha or sha in ("placeholder", "none", "null", "0" * 64) \
                or not re.fullmatch(r"[0-9a-f]{64}", sha):
            problemas.append(f"{nombre}: sha256 sin capturar/placeholder")
        elif url in pares and pares[url] == sha:
            verificados += 1
        else:
            problemas.append(f"{nombre}: sha256 no coincide con X-Linked-ETag "
                             f"de la captura (toml={sha[:12]}… remoto={(pares.get(url) or 'SIN CAPTURA')[:12]}…)")
    urls_capturadas = len(pares)
    esperadas = len(modelos)
    if urls_capturadas < esperadas:
        problemas.append(f"captura incompleta: {urls_capturadas}/{esperadas} URLs")

    if problemas:
        for p in problemas:
            print(f"FALLO: {p}")
        return 1
    print(f"OK: catalogo real verificado H-R144-3 - {verificados}/{esperadas} "
          f"modelos con sha256 == LFS oid remoto ({urls_capturadas}/5 URLs capturadas)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
