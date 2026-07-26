"""
json_parser.py — Benchmark: parseo masivo de JSON (Python)
Comparativa contra json_simd.syn (Synapse)
Mide: tiempo de parseo de benchmarks/data.json con json.loads()

Uso: python benchmarks/json_parser.py
"""

import json
import time
import os

CANTIDAD = 50000
ITERACIONES = 5
RUTA = os.path.join(os.path.dirname(__file__), "data.json")

def main():
    print("--- Benchmark: Parseo JSON masivo (Python) ---")
    print(f"Objetos: {CANTIDAD}")
    print()

    if not os.path.exists(RUTA):
        print(f"ERROR: No se encuentra {RUTA}")
        return 1

    # Leer archivo una vez
    with open(RUTA, "r", encoding="utf-8") as f:
        json_str = f.read()

    print(f"Tamano JSON: {len(json_str)} bytes")
    print()

    suma_ms = 0.0
    for i in range(ITERACIONES):
        inicio = time.perf_counter()
        doc = json.loads(json_str)
        fin = time.perf_counter()

        tiempo = (fin - inicio) * 1000  # convertir a ms
        suma_ms += tiempo
        print(f"  Iteracion {i + 1}: {tiempo:.2f} ms")

        # Verificar parseo
        val0 = doc[0]
        _ = val0["id"]
        valN = doc[CANTIDAD - 1]
        _ = valN["id"]

    promedio = suma_ms / ITERACIONES
    tasa = (CANTIDAD * 1000) / promedio if promedio > 0 else 0
    tasa_mb = (CANTIDAD * 1000) / (promedio * 1024) if promedio > 0 else 0

    print()
    print("Resultados (Python):")
    print(f"  Promedio: {promedio:.2f} ms")
    print(f"  Tasa: {tasa:.0f} objetos/segundo")
    print(f"  Throughput: {tasa_mb:.2f} MB/s")

    return 0


if __name__ == "__main__":
    main()
