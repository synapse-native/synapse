# examples/syquex/python_pipeline/fibonacci.py
# Script de ejemplo para el pipeline Python -> Syquex
# Calcula los primeros 10 números de Fibonacci

def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

def main():
    print("Fibonacci sequence:")
    for i in range(10):
        result = fibonacci(i)
        print(result)

main()
