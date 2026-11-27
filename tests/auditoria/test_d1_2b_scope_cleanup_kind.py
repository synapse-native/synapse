"""Oráculo D-1.2b: tipo WeakRef y compactación de la clase RAII.

Manual 4 §4.2: `débil<T>` se representa como `WeakRef` por valor para que
`rc_weak_release(&var)` reciba el tipo correcto. Manual 4 §5.2: el cleanup de
scope debe conservar la clase de cada variable (rc/arc/débil) al compactar el
registro de variables, de lo contrario un scope posterior usa el destructor
equivocado.

El oráculo es estático: valida la fuente y el unity regenerado sin compilar.
"""
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
FUENTES = (
    RAIZ / "nucleo" / "generador" / "emision_c.syn",
    RAIZ / "nucleo" / "generator.syn",
)
COMPACTACION = "_G_scope_vars_kind[_wi] = _G_scope_vars_kind[_ri];"
WEAKREF = r'strcpy(_gen_tmp_buf, \"WeakRef\")'
RC_ARCO_VOID = r'strcpy(_gen_tmp_buf, \"void*\")'


def _texto(ruta: Path) -> str:
    return ruta.read_text(encoding="utf-8", errors="replace")


def test_compactacion_preserva_kind():
    for ruta in FUENTES:
        texto = _texto(ruta)
        assert COMPACTACION in texto, (
            f"{ruta}: la compactación de scopes no copia _G_scope_vars_kind"
        )


def test_weak_se_tipa_como_weakref():
    for ruta in FUENTES:
        texto = _texto(ruta)
        assert 'strncmp(_t, \\"weak<\\", 5)==0' in texto, (
            f"{ruta}: falta la rama weak< en traducir_tipo_c"
        )
        assert WEAKREF in texto, f"{ruta}: weak< no se traduce a WeakRef"
        assert RC_ARCO_VOID in texto, f"{ruta}: rc/arc deben seguir como void*"


def test_weak_no_cae_en_el_mapeo_void_legacy():
    for ruta in FUENTES:
        texto = _texto(ruta)
        legacy = (
            'strncmp(_t, \\"rc<\\", 3)==0 || strncmp(_t, \\"arc<\\", 4)==0 || '
            'strncmp(_t, \\"weak<\\", 5)==0'
        )
        assert legacy not in texto, (
            f"{ruta}: weak< sigue en el mapeo legacy a void*"
        )


def test_header_nativo_declara_weakref_y_destructores():
    texto = _texto(RAIZ / "nucleo" / "generator.syn")
    assert "typedef struct { RcHeader* header; uint32_t version; } WeakRef;" in texto
    assert "extern void rc_weak_release(WeakRef* w);" in texto
    assert "extern void _syn_rc_decrement(void* p);" in texto


def test_declaracion_weak_nulo_emite_weakref_cero():
    texto = _texto(RAIZ / "nucleo" / "generator.syn")
    assert 'strncmp(_var_type, \\"WeakRef\\", 7) == 0' in texto
    assert "((WeakRef){0})" in texto
