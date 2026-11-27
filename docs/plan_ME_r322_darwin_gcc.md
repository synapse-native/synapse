# Plan de Micro-Entregable r322_darwin_gcc

## Objetivo

Octava vuelta sobre `Release Matrix`. r321 eliminó los 23 símbolos duplicados,
pero el bootstrap de macOS sigue sin compilar (run `45229677100`, job
`137885490205`):

```
synapse_unity.c:12753:73: error: function definition is not allowed here
 12753 | void _f8_r1_llamada_generica(struct AnalizadorSemanticoEst* e, int idx) {
synapse_unity.c:12853:1: error: call to undeclared function '_f8_r1_llamada_generica';
  ISO C99 and later do not support implicit function declarations
synapse_unity.c:21796:29: error: function definition is not allowed here
 21796 | int _f8_tipo(const char* t) {
```

Ambos diagnósticos son de **clang**: funciones anidadas (extensión GNU) y
declaraciones implícitas. El C que emite el compilador es dialecto GNU, y el
propio `pipeline.py` documenta que ese dialecto exige GCC real.

`pipeline.py` ya intenta en darwin `gcc-14/13/12` de Homebrew, pero el runner
`macos-latest` no trae ninguno instalado y cae a `clang` en silencio. Además la
lista está fijada a tres versiones: cuando Homebrew publique `gcc-15` o `gcc-16`
el fallo volvería. Este ME (a) hace que darwin resuelva **cualquier** GCC real
—`SYNAPSE_GCC_PATH`, después `gcc-*` de Homebrew por versión descendente y por
último `gcc`/`cc` del PATH, siempre validando que `--version` no diga `clang`—
y (b) instala GCC en el job de macOS y exporta `SYNAPSE_GCC_PATH`.

Linux x64/ARM64 y Windows siguen fallando solo en la firma Ed25519 (H-R276-2).

## Requisito 1 — darwin resuelve un GCC real, no un shim de clang

requisito: Manual 9 §6.2
texto: "La verificación del bootstrap (diff 0 bytes)."
implementacion: `pipeline.py` gana `_resolver_gcc_darwin()`, que recibe `env/which/run` inyectables y devuelve el primer binario cuyo `--version` no menciona `clang` (prioridad: `SYNAPSE_GCC_PATH`, `gcc-*` de `/opt/homebrew/bin` y `/usr/local/bin` por versión descendente, `gcc`/`cc` del PATH); el branch darwin de `ejecutar_compilador` la usa y sólo cae a `clang` si no hay GCC.
oraculo: tests/auditoria/test_r322_darwin_gcc.py

## Requisito 2 — el job de macOS instala GCC y lo declara

requisito: Manual 9 §6.2
texto: "La suite de tests completa en cada target."
implementacion: `.github/workflows/release_matrix.yml` agrega un paso darwin-only que instala `gcc` con Homebrew y exporta a `GITHUB_ENV` la ruta del `gcc-*` más reciente como `SYNAPSE_GCC_PATH`; el resto de plataformas no ejecuta el paso.
oraculo: tests/auditoria/test_r322_darwin_gcc.py

## Evidencia

| check | resultado |
|---|---|
| `pytest tests/auditoria/test_r322_darwin_gcc.py` | 5 passed |
| `build.py --skip-test` (Windows) + `S2==S3` | OK, sha `8e9e60f83c39` (sin cambios) |
| `alineacion.py --verificar --me r322_darwin_gcc` | OK (`9b81b728d54fd769`) |
| `contrastar.py --plan docs/plan_ME_r322_darwin_gcc.md` | PASS |
| CI `Release Matrix` macOS tras el push | (se completa tras ejecutar) |
