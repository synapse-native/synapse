# tests/auditoria/test_r321_weak_darwin.py
# cumple Manual 9 §6.2: el bootstrap compila y enlaza en cada target.
"""ld64 rechaza `--allow-multiple-definition` y el C emitido redefine helpers
del runtime.

Run `45217779214`, job `137843493888` (macos-latest), tras r320:

```
duplicate symbol '_escribir_linea' in:
    .../synapse_unity.c.o
    /Users/runner/.synapse/cache/runtime_obj/io.o
duplicate symbol '_str_eq' in:
    .../synapse_unity.c.o
    /Users/runner/.synapse/cache/runtime_obj/sistema.o
ld: 23 duplicate symbols
```

GNU ld toleraba esos duplicados con `--allow-multiple-definition` (toma la
primera definición). En darwin se emiten las definiciones del fuente como
`__attribute__((weak))`, que produce el mismo resultado (gana la primera) sin
flags específicos del linker. En Windows/ELF el C emitido no cambia.
"""

from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
PY_GEN = RAIZ / "compilador" / "generator" / "emit_declarations.py"
SYN_GEN = RAIZ / "nucleo" / "generador" / "funciones.syn"


def test_generador_python_emite_weak_solo_en_darwin():
    texto = PY_GEN.read_text(encoding="utf-8")
    assert 'weak = " __attribute__((weak))" if sys.platform == "darwin" else ""' in texto
    assert 'ctx.write_line(f"{tipo}{weak} {c_name}({params}) {{")' in texto
    assert "ctx.write_line(f\"{tipo} {c_name}({params}) {{\")" not in texto, \
        "definición emitida sin el atributo condicional"


def test_generador_autohospedado_emite_weak_bajo_apple():
    texto = SYN_GEN.read_text(encoding="utf-8")
    assert 'const char* _weak_attr = \\"\\";' in texto
    assert "#ifdef __APPLE__" in texto
    assert '_weak_attr = \\" __attribute__((weak))\\";' in texto
    assert 'snprintf(_sig, 4096, \\"%s%s %s(%s)\\", _rct, _weak_attr, _fnc, _ps);' in texto


def test_firma_por_defecto_sin_atributo():
    # En win32/ELF el atributo es cadena vacía: la firma emitida es la de antes.
    texto = SYN_GEN.read_text(encoding="utf-8")
    i = texto.find('const char* _weak_attr')
    assert i > 0
    assert texto.count('#ifdef __APPLE__', i, i + 400) == 1
