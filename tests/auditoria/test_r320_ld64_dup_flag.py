# tests/auditoria/test_r320_ld64_dup_flag.py
# cumple Manual 9 §6.2: el bootstrap compila en cada target del pipeline.
"""El ld64 de macOS no conoce `--allow-multiple-definition`.

Run `45213218955`, job `137827294530` (macos-latest):

```
ld: unknown options: --allow-multiple-definition
collect2: error: ld returned 1 exit status
[!] Link modular fallo (rc=1) — intentando unity fallback
[!] No se generaron objetos modulares — usando unity fallback
ld: unknown options: --allow-multiple-definition
```

El flag GNU tolera las definiciones duplicadas que emite la compilación modular
(`desde_texto` en `_json.c` y `_toml.c`). En darwin se enlaza en unity, donde no
hay duplicados, y no se pasa el flag.
"""

from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
PIPELINE = RAIZ / "pipeline.py"
PRINCIPAL = RAIZ / "nucleo" / "principal.syn"


def test_pipeline_condiciona_el_flag_a_no_darwin():
    texto = PIPELINE.read_text(encoding="utf-8")
    assert '_ld_dup_flag = "" if sys.platform == "darwin" else " -Wl,--allow-multiple-definition"' in texto
    assert "link_flags = f'{thread_flag} -lm {linker_net} {linker_extra}{_ld_dup_flag}'.strip()" in texto
    assert '-Wl,--allow-multiple-definition\'.strip()' not in texto, "flag incondicional residual"


def test_pipeline_usa_unity_en_darwin():
    texto = PIPELINE.read_text(encoding="utf-8")
    i = texto.find("sin el flag GNU, la compilación modular")
    assert i > 0
    assert "_module_asts.clear()" in texto[i:i + 400]


def test_cache_link_tambien_condiciona():
    texto = PIPELINE.read_text(encoding="utf-8")
    assert 'link_align = "" if sys.platform == "darwin" else "-Wl,--allow-multiple-definition"' in texto


def test_enlace_nativo_de_principal_no_pasa_el_flag_en_apple():
    texto = PRINCIPAL.read_text(encoding="utf-8")
    assert '_dup_flag = \\"-Wl,--allow-multiple-definition\\";' in texto
    assert "#ifdef __APPLE__" in texto
    assert "snprintf(_cmd_tail, 1600, \\\" -o \\\\\\\"%s\\\\\\\" -lpthread -lm %s%s\\\", salida.datos, _win_libs, _dup_flag)" in texto
    assert "-lm %s-Wl,--allow-multiple-definition" not in texto
