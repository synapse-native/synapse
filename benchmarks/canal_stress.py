"""
canal_stress.py — Benchmark: paso de mensajes (Python threading.Queue)
Comparativa contra concurrencia.syn (Synapse Canal<T>)
50 productores, 1 consumidor (main thread), ~mensajes

Uso: python benchmarks/canal_stress.py
"""

import threading
import queue
import time

N_PROD = 50
MSG_X_PROD = 2000
TOTAL = N_PROD * MSG_X_PROD


def productor(q: queue.Queue, id: int):
    for j in range(MSG_X_PROD):
        q.put(id * MSG_X_PROD + j)


def main():
    print("--- Benchmark: Queue Concurrente (Python threading) ---")
    print(f"Productores: {N_PROD}")
    print(f"Mensajes/productor: {MSG_X_PROD}")
    print(f"Total: {TOTAL}")
    print()

    q: queue.Queue = queue.Queue(maxsize=64)

    threads = []
    for i in range(N_PROD):
        t = threading.Thread(target=productor, args=(q, i))
        t.start()
        threads.append(t)

    inicio = time.perf_counter()

    recibidos = 0
    while recibidos < TOTAL:
        _ = q.get()
        recibidos += 1

    fin = time.perf_counter()
    tiempo_total = (fin - inicio) * 1000  # ms
    tasa = (TOTAL * 1000) / tiempo_total if tiempo_total > 0 else 0

    for t in threads:
        t.join()

    print()
    print("Resultados (Python threading.Queue):")
    print(f"  Tiempo total: {tiempo_total:.2f} ms")
    print(f"  Throughput: {tasa:.0f} mensajes/segundo")

    return 0


if __name__ == "__main__":
    main()
