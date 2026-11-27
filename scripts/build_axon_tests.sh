#!/bin/bash
# scripts/build_axon_tests.sh
# Compiles the Axon E2E test binary dependencies
# (Manual 6.4, 6.5 - F18)
# Run from project root.

set -e

echo "[1/3] Compiling gen_axon_test_fixtures.exe..."
gcc -I. -O2 tests/gen_axon_test_fixtures.c axon/tweetnacl.c -o tests/gen_axon_test_fixtures.exe -lm

echo "[2/3] Compiling test_ed25519_axon_new.exe..."
# Build .o files if not present
for obj in synapse_rt.o synapse_rt_memory.o tweetnacl.o; do
    if [ ! -f "$obj" ]; then
        src="${obj%.o}"
        [ "$src" = "tweetnacl" ] && src="$src.c" || src="${src}.c"
        echo "  [WARN] $obj not found, building from $src..."
        gcc -I. -O2 -c "$src" -o "$obj"
    fi
done
gcc -I. -O2 tests/test_ed25519_axon.c synapse_rt.o synapse_rt_memory.o tweetnacl.o \
    -o tests/test_ed25519_axon_new.exe -lpthread -lm -lws2_32

echo "[3/3] Compiling test_path_traversal_new.exe..."
gcc -I. -O2 tests/test_path_traversal.c synapse_rt.o synapse_rt_memory.o tweetnacl.o \
    -o tests/test_path_traversal_new.exe -lpthread -lm -lws2_32

# Prepare .axon_cache directory for tests
mkdir -p tests/.axon_cache

echo ""
echo "=== BUILD COMPLETE ==="
echo "Run: python tests/test_axon_e2e.py"
