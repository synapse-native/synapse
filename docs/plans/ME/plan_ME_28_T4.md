requisito: Manual 3 §3 — El compilador Syquex nunca crashea con entradas inválidas
texto: Fuzzing del pipeline Syquex: archivos vacíos, binarios, unicode corrupto, keywords en posiciones incorrectas, inputs aleatorios
implementacion: tests/integration/test_syquex_fuzz.py — 16 tests de fuzzing
oraculo: tests/integration/test_syquex_fuzz.py
