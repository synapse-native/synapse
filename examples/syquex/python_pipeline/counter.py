# examples/syquex/python_pipeline/counter.py
# Ejemplo simple: calcula factorial sin usar std.io

def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

result = factorial(5)
