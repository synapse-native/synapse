requisito: Manual 3 §3 — El frontend Syquex parsea y traduce conforme al manual (EBNF frontmatter+statement+expression)
texto: Compilador Syquex debe compilar programas .syq con estructura, enumeración, constante, @export, coincidir, mientras
implementacion: tests/integration/test_syquex_cert_1.py — 10 tests que compilan fixtures .syq y verifican output
oraculo: tests/integration/test_syquex_cert_1.py

requisito: Manual 3 §5 — Análisis de alcance (arena/rc/arc/débil), tipos, contratos
texto: Compilador debe manejar variables mutables, constantes, estructuras con campos, métodos con self
implementacion: tests/integration/test_syquex_cert_2.py — 10 tests de semántica
oraculo: tests/integration/test_syquex_cert_2.py

requisito: Manual 3 §3 — Pipeline completo .syq → exe con output verificable
texto: Todo fixture .syq debe compilar y ejecutarse produciendo salida correcta
implementacion: tests/integration/test_syquex_cert_3.py — 9 tests e2e
oraculo: tests/integration/test_syquex_cert_3.py
