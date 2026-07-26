"""
generar_datos.py — Genera benchmarks/data.json para los tests de parseo JSON
Crea un array de 50,000 objetos con campos id, nombre, activo, valor, datos

Uso: python benchmarks/generar_datos.py
"""

import json
import os

CANTIDAD = 50000
RUTA = os.path.join(os.path.dirname(__file__), "data.json")


def generar():
    print(f"Generando {CANTIDAD} objetos JSON...")
    data = []
    for i in range(CANTIDAD):
        obj = {
            "id": i,
            "nombre": f"item_{i}",
            "activo": bool(i % 2),
            "valor": (i * 3.14) / 100.0,
            "datos": {"x": i, "y": i * 2, "z": i * 3},
        }
        data.append(obj)

    with open(RUTA, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

    tamano = os.path.getsize(RUTA)
    print(f"Archivo generado: {RUTA}")
    print(f"Tamano: {tamano:,} bytes ({tamano / 1024:.1f} KB)")


if __name__ == "__main__":
    generar()
