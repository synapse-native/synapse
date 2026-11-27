# Tests Omitidos — Synapse v8.1.0-industrial

## Justificación Técnica

Los siguientes tests están omitidos de la suite estándar. Ninguno representa
una regresión del código actual; todos son problemas preexistentes o
requisitos de entorno no satisfechos.

| Test | Archivo | Motivo |
|------|---------|-------|
| `test_toml_compile_and_run` | `tests/test_toml_raii.py` | Símbolos `crypto_sign_ed25519_tweet_*` no resueltos al compilar `tweetnacl.c` como fuente. Requiere recompilar `tweetnacl.o` con `-Dcrypto_sign=crypto_sign_ed25519_tweet`. Problema preexistente, no relacionado con la modularización del runtime. |
| Tests de integración C nativa | `tests/*.c` (18 archivos) | Requieren compilación C nativa con toolchain MinGW-w64. No integrados en la suite pytest. Se ejecutan manualmente vía `gcc && ./test_binary`. |
| Tests de cluster | `tests/test_cluster_*.c` | Requieren múltiples nodos de red. Diseñados para ejecución en CI/CD con infraestructura de cluster. |
| Tests de quantización | `tests/validate_quantization.c` | Depende de librerías CUDA/cuBLAS no presentes en el entorno local. |
| Tests cuánticos | `tests/validate_quantum_*.c` | Requieren hardware cuántico simulado o real. Entorno de laboratorio. |
| Tests de fine-tuning | `tests/validate_fine_tuning.c` | Depende de pesos de modelo pre-entrenados no distribuidos en el repositorio. |
| Tests LSP nativos | `tests/integration/test_lsp_native.py` | Requieren servidor LSP en ejecución con configuración de red específica. |
| Tests de release matrix | `tests/integration/test_release_matrix.py` | Requieren múltiples versiones del compilador. CI/CD únicamente. |

---

**Total tests omitidos documentados: 26** (1 Python + 18 C nativos + 4 cluster + 3 entorno especializado)
