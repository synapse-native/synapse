# Verificación — ME r322_darwin_gcc

CUMPLE.

## Causa

Run `45229677100`, job `137885490205` (macos-latest). Con r321 ya no hay
símbolos duplicados, pero el C emitido no compila con clang:

```
synapse_unity.c:12753:73: error: function definition is not allowed here
 12753 | void _f8_r1_llamada_generica(struct AnalizadorSemanticoEst* e, int idx) {
synapse_unity.c:12853:1: error: call to undeclared function '_f8_r1_llamada_generica';
  ISO C99 and later do not support implicit function declarations
```

Son funciones anidadas (extensión GNU) y declaraciones implícitas: el fuente
del compilador es dialecto GCC por diseño (`nucleo/principal.syn`,
`nucleo/analizador_semantico.syn` emiten helpers C auto-contenidos dentro de la
función que los usa). `pipeline.py` ya prefería `gcc-14/13/12` de Homebrew en
darwin, pero el runner no los tiene y caía a clang sin avisar.

## Cambios

- `pipeline.py`: nuevo `_resolver_gcc_darwin()` (inyectables `env/which/run/glob`):
  `SYNAPSE_GCC_PATH` → `gcc-*` de `/opt/homebrew/bin` y `/usr/local/bin` por
  versión descendente → `gcc-20..gcc-11`, `gcc`, `cc` del PATH; descarta todo
  binario cuyo `--version` mencione `clang`. El branch darwin lo usa y avisa si
  cae a clang.
- `.github/workflows/release_matrix.yml`: paso `Install GCC (darwin)` que
  reutiliza un GCC real si existe, si no `brew install gcc`, y exporta
  `SYNAPSE_GCC_PATH` al `gcc-*` más reciente.

## Verificación

| requisito | verificación | resultado |
|---|---|---|
| Manual 9 §6.2 — CUMPLE — bootstrap en cada target | `pytest tests/auditoria/test_r322_darwin_gcc.py` | 5 passed |
| Manual 1 §3.1 — pipeline compartido | idem + `build.py --skip-test` | `S2==S3 8e9e60f83c39` |

| check | resultado |
|---|---|
| `alineacion.py --verificar --me r322_darwin_gcc` | OK, evidencia `9b81b728d54fd769` |
| `contrastar.py --plan docs/plan_ME_r322_darwin_gcc.md` | PASS |
| `verificar_alineacion.py` | SIN BRECHAS |

## Limitación declarada

En Windows no hay clang ni Homebrew: la resolución real de GCC en darwin se
valida en el run de `Release Matrix` tras el push (se declara así en el plan).
