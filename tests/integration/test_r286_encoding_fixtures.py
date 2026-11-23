# cumple Manual 2 §1.2: UTF-8 sin BOM, sin U+FFFD ni controles C1 en fuentes.
"""Oráculo del ME r286_tests_paridad (H-R286-1).

Verifica la paridad de encoding de los fixtures de test: todo archivo de texto
de `tests/fixtures/` y `tests/integration/fixtures/` debe decodificar como
UTF-8 y no contener U+FFFD (reemplazo), controles C1 ni BOM.

Las dos excepciones son fixtures UTF-16 de rechazo declarados en
`auditoria/verificar_encoding.py` (H-R280-3): su contenido no es UTF-8 por
diseño y el test inmutable que los usa espera el error del lexer.
"""

from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
DIRS_FIXTURES = (
    RAIZ / "tests" / "fixtures",
    RAIZ / "tests" / "integration" / "fixtures",
)

EXTENSIONES_TEXTO = {
    ".syn", ".syq", ".c", ".h", ".json", ".txt", ".py", ".js",
    ".toml", ".yaml", ".yml", ".md", ".csv", ".idl", ".sql",
}

EXENTOS_UTF16 = {
    "tests/fixtures/test_simple.syn",
    "tests/integration/fixtures/test_simple.syn",
}


def _fixtures_texto() -> list[Path]:
    archivos: list[Path] = []
    for base in DIRS_FIXTURES:
        if not base.exists():
            continue
        archivos.extend(
            p for p in base.rglob("*")
            if p.is_file() and p.suffix.lower() in EXTENSIONES_TEXTO
        )
    return sorted(archivos)


def _relativa(p: Path) -> str:
    return p.relative_to(RAIZ).as_posix()


def test_hay_fixtures_para_auditar():
    archivos = _fixtures_texto()
    assert len(archivos) > 200, (
        f"se esperaban >200 fixtures de texto, encontrados {len(archivos)}"
    )


def test_fixtures_sin_bom():
    con_bom = [
        _relativa(p) for p in _fixtures_texto()
        if _relativa(p) not in EXENTOS_UTF16
        and p.read_bytes().startswith(b"\xef\xbb\xbf")
    ]
    assert not con_bom, f"fixtures con BOM (Manual 2 §1.2): {con_bom}"


def test_fixtures_utf8_sin_reemplazo_ni_c1():
    defectuosos: list[str] = []
    for p in _fixtures_texto():
        rel = _relativa(p)
        if rel in EXENTOS_UTF16:
            continue
        datos = p.read_bytes()
        try:
            texto = datos.decode("utf-8")
        except UnicodeDecodeError as exc:
            defectuosos.append(f"{rel}: no es UTF-8 ({exc.reason})")
            continue
        if "\ufffd" in texto:
            defectuosos.append(f"{rel}: contiene U+FFFD")
        c1 = sorted({f"U+{ord(ch):04X}" for ch in texto
                     if 0x80 <= ord(ch) <= 0x9F})
        if c1:
            defectuosos.append(f"{rel}: controles C1 {c1}")
    assert not defectuosos, "fixtures fuera de norma:\n" + "\n".join(defectuosos)


def test_exenciones_utf16_siguen_siendo_utf16():
    """Si un fixture exento deja de ser UTF-16, la exención debe retirarse."""
    for rel in sorted(EXENTOS_UTF16):
        datos = (RAIZ / rel).read_bytes()
        assert b"\x00" in datos, (
            f"{rel} ya no parece UTF-16; retirar la exención de "
            "auditoria/verificar_encoding.py y de este test"
        )
