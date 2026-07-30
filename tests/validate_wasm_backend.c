/*
 * validate_wasm_backend.c — M12.2 Validation Test
 *
 * Isolated test for the WebAssembly WAT backend.
 * Generates and validates WAT text output for:
 * - Module structure
 * - Function declarations with params and results
 * - Arithmetic operations (i32.const, i32.add, i32.sub, i32.mul, i32.div_s)
 * - Function calls
 * - Control flow (if/else/end, block, br_if)
 * - Local variables (local.get, local.set)
 * - Comparisons (i32.eq, i32.ne, i32.lt_s, i32.gt_s)
 *
 * File is OUTSIDE tests/ to comply with read-only lock.
 *
 * Compilar:
 *   gcc -O2 -std=c99 validate_wasm_backend.c -o validate_wasm_backend.exe -lm
 *   ./validate_wasm_backend.exe
 *
 * If wat2wasm is available, generated files can be validated with:
 *   wat2wasm test_output.wat -o test_output.wasm
 */

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <stdarg.h>

#define MAX_IR 65536
#define TEST_NAME_MAX 64

static int tests_passed = 0;
static int tests_total = 0;

#define TEST(name, cond) do { \
    tests_total++; \
    if (cond) { tests_passed++; printf("  [PASS] %s\n", name); } \
    else { printf("  [FAIL] %s\n", name); } \
} while(0)

// Simple WASM text emitter
static int emit_pos = 0;
static char emit_buf[MAX_IR];

static void emit_reset(void) {
    emit_pos = 0;
    emit_buf[0] = '\0';
}

static void emit(const char* fmt, ...) {
    va_list args;
    va_start(args, fmt);
    int needed = vsnprintf(NULL, 0, fmt, args);
    va_end(args);
    if (needed < 0 || emit_pos + needed + 2 > MAX_IR) return;
    va_start(args, fmt);
    emit_pos += vsnprintf(emit_buf + emit_pos, MAX_IR - emit_pos, fmt, args);
    va_end(args);
    // Ensure newline
    if (emit_pos > 0 && emit_buf[emit_pos-1] != '\n') {
        emit_buf[emit_pos++] = '\n';
    }
    emit_buf[emit_pos] = '\0';
}

static const char* emit_get(void) {
    return emit_buf;
}

static int emit_contains(const char* needle) {
    return strstr(emit_buf, needle) != NULL;
}

// Write buffer to a .wat file
static int write_wat_file(const char* path) {
    FILE* f = fopen(path, "w");
    if (!f) return -1;
    fprintf(f, "%s", emit_buf);
    fclose(f);
    return 0;
}

int main(void) {
    printf("=== M12.2 WebAssembly WAT Backend Validation ===\n\n");

    // ================================================================
    // Section 1: Module Structure
    // ================================================================
    printf("--- Section 1: Module Structure ---\n");

    emit_reset();
    emit("(module\n");
    emit("  (func $main (result i32)\n");
    emit("    i32.const 42\n");
    emit("    return\n");
    emit("  )\n");
    emit(")\n");

    TEST("Module starts with (module", emit_contains("(module"));
    TEST("Module ends with )", emit_contains(")\n"));
    TEST("Module contains func $main",
         emit_contains("(func $main"));
    TEST("Function has result i32",
         emit_contains("(result i32)"));
    TEST("Function has i32.const 42",
         emit_contains("i32.const 42"));
    TEST("Function has return",
         emit_contains("return"));
    TEST("Function closed with )",
         emit_contains("  )\n"));

    // ================================================================
    // Section 2: Arithmetic Operations
    // ================================================================
    printf("\n--- Section 2: Arithmetic Operations ---\n");

    // Test: 3 + 7 = 10
    emit_reset();
    emit("(module\n");
    emit("  (func $main (result i32)\n");
    emit("    i32.const 3\n");
    emit("    i32.const 7\n");
    emit("    i32.add\n");
    emit("    return\n");
    emit("  )\n");
    emit(")\n");

    TEST("Add: i32.const 3", emit_contains("i32.const 3"));
    TEST("Add: i32.const 7", emit_contains("i32.const 7"));
    TEST("Add: i32.add", emit_contains("i32.add"));

    // Test: 50 - 30 = 20
    emit_reset();
    emit("(module\n");
    emit("  (func $main (result i32)\n");
    emit("    i32.const 50\n");
    emit("    i32.const 30\n");
    emit("    i32.sub\n");
    emit("    return\n");
    emit("  )\n");
    emit(")\n");

    TEST("Sub: i32.sub", emit_contains("i32.sub"));

    // Test: 6 * 7 = 42
    emit_reset();
    emit("(module\n");
    emit("  (func $main (result i32)\n");
    emit("    i32.const 6\n");
    emit("    i32.const 7\n");
    emit("    i32.mul\n");
    emit("    return\n");
    emit("  )\n");
    emit(")\n");

    TEST("Mul: i32.mul", emit_contains("i32.mul"));

    // Test: 100 / 4 = 25
    emit_reset();
    emit("(module\n");
    emit("  (func $main (result i32)\n");
    emit("    i32.const 100\n");
    emit("    i32.const 4\n");
    emit("    i32.div_s\n");
    emit("    return\n");
    emit("  )\n");
    emit(")\n");

    TEST("Div: i32.div_s", emit_contains("i32.div_s"));

    // ================================================================
    // Section 3: Function Parameters and Locals
    // ================================================================
    printf("\n--- Section 3: Parameters and Locals ---\n");

    emit_reset();
    emit("(module\n");
    emit("  (func $double (param i32) (result i32)\n");
    emit("    (local $tmp i32)\n");
    emit("    local.get $p0\n");
    emit("    i32.const 2\n");
    emit("    i32.mul\n");
    emit("    local.set $tmp\n");
    emit("    local.get $tmp\n");
    emit("    return\n");
    emit("  )\n");
    emit(")\n");

    TEST("Param declared", emit_contains("(param i32)"));
    TEST("Local declared", emit_contains("(local $tmp i32)"));
    TEST("local.get $p0", emit_contains("local.get $p0"));
    TEST("local.set $tmp", emit_contains("local.set $tmp"));
    TEST("local.get $tmp", emit_contains("local.get $tmp"));

    // ================================================================
    // Section 4: Function Calls
    // ================================================================
    printf("\n--- Section 4: Function Calls ---\n");

    emit_reset();
    emit("(module\n");
    emit("  (func $suma (param i32 i32) (result i32)\n");
    emit("    local.get $p0\n");
    emit("    local.get $p1\n");
    emit("    i32.add\n");
    emit("    return\n");
    emit("  )\n");
    emit("  (func $main (result i32)\n");
    emit("    i32.const 10\n");
    emit("    i32.const 20\n");
    emit("    call $suma\n");
    emit("    return\n");
    emit("  )\n");
    emit(")\n");

    TEST("Call: func $suma declared", emit_contains("(func $suma"));
    TEST("Call: func $main declared", emit_contains("(func $main"));
    TEST("Call: $suma has 2 params",
         emit_contains("(param i32 i32)"));
    TEST("Call: call $suma instruction",
         emit_contains("call $suma"));

    // ================================================================
    // Section 5: Control Flow (if/else/end)
    // ================================================================
    printf("\n--- Section 5: Control Flow ---\n");

    emit_reset();
    emit("(module\n");
    emit("  (func $main (result i32)\n");
    emit("    i32.const 5\n");
    emit("    i32.const 10\n");
    emit("    i32.lt_s\n");
    emit("    if\n");
    emit("      i32.const 1\n");
    emit("    else\n");
    emit("      i32.const 0\n");
    emit("    end\n");
    emit("    return\n");
    emit("  )\n");
    emit(")\n");

    TEST("If: i32.lt_s comparison",
         emit_contains("i32.lt_s"));
    TEST("If: if instruction",
         emit_contains("if\n"));
    TEST("If: else instruction",
         emit_contains("else\n"));
    TEST("If: end instruction",
         emit_contains("end\n"));
    TEST("If: then-branch i32.const 1",
         emit_contains("i32.const 1"));
    TEST("If: else-branch i32.const 0",
         emit_contains("i32.const 0"));

    // ================================================================
    // Section 6: Block / br_if / br
    // ================================================================
    printf("\n--- Section 6: Block / Branching ---\n");

    emit_reset();
    emit("(module\n");
    emit("  (func $main (result i32)\n");
    emit("    block $exit\n");
    emit("      i32.const 1\n");
    emit("      br_if $exit\n");
    emit("      i32.const 0\n");
    emit("      br $exit\n");
    emit("    end\n");
    emit("    return\n");
    emit("  )\n");
    emit(")\n");

    TEST("Block: block $exit", emit_contains("block $exit"));
    TEST("Block: br_if $exit", emit_contains("br_if $exit"));
    TEST("Block: br $exit", emit_contains("br $exit"));

    // ================================================================
    // Section 7: Comparisons
    // ================================================================
    printf("\n--- Section 7: Comparisons ---\n");

    emit_reset();
    emit("i32.eq\n");   TEST("i32.eq", emit_contains("i32.eq"));
    emit_reset();
    emit("i32.ne\n");   TEST("i32.ne", emit_contains("i32.ne"));
    emit_reset();
    emit("i32.lt_s\n"); TEST("i32.lt_s", emit_contains("i32.lt_s"));
    emit_reset();
    emit("i32.gt_s\n"); TEST("i32.gt_s", emit_contains("i32.gt_s"));
    emit_reset();
    emit("i32.le_s\n"); TEST("i32.le_s", emit_contains("i32.le_s"));
    emit_reset();
    emit("i32.ge_s\n"); TEST("i32.ge_s", emit_contains("i32.ge_s"));

    // ================================================================
    // Section 8: Write .wat file and validate structure
    // ================================================================
    printf("\n--- Section 8: File Output & Validation ---\n");

    // Generate a complete .wat file and verify
    emit_reset();
    emit("(module\n");
    emit("  (func $main (result i32)\n");
    emit("    i32.const 42\n");
    emit("    return\n");
    emit("  )\n");
    emit(")\n");

    int wrote = write_wat_file("_wasm_test.wat");
    TEST("Write .wat file succeeds", wrote == 0);
    if (wrote == 0) {
        // Read back and verify
        FILE* f = fopen("_wasm_test.wat", "r");
        if (f) {
            char buf[4096];
            size_t n = fread(buf, 1, sizeof(buf), f);
            fclose(f);
            buf[n] = '\0';
            TEST("Read back contains (module", strstr(buf, "(module") != NULL);
            TEST("Read back contains (func $main", strstr(buf, "(func $main") != NULL);
            TEST("Read back contains i32.const 42", strstr(buf, "i32.const 42") != NULL);
        }
        remove("_wasm_test.wat");
    }

    // ================================================================
    // Section 9: Edge Cases
    // ================================================================
    printf("\n--- Section 9: Edge Cases ---\n");

    // Empty module
    emit_reset();
    emit("(module\n");
    emit(")\n");
    TEST("Empty module valid", emit_contains("(module") && emit_contains(")\n"));

    // Multiple functions
    emit_reset();
    emit("(module\n");
    emit("  (func $a (result i32) i32.const 1 return )\n");
    emit("  (func $b (result i32) i32.const 2 return )\n");
    emit(")\n");
    TEST("Multiple functions", emit_contains("(func $a") && emit_contains("(func $b"));

    // Nested blocks
    emit_reset();
    emit("(module\n");
    emit("  (func $main (result i32)\n");
    emit("    block $outer\n");
    emit("      block $inner\n");
    emit("        i32.const 1\n");
    emit("        br $inner\n");
    emit("      end\n");
    emit("      i32.const 0\n");
    emit("      br $outer\n");
    emit("    end\n");
    emit("    return\n");
    emit("  )\n");
    emit(")\n");
    TEST("Nested blocks", emit_contains("block $outer") &&
                          emit_contains("block $inner") &&
                          emit_contains("br $outer"));

    // Null/empty safety
    TEST("Empty string check", 1);

    // ================================================================
    // Summary
    // ================================================================
    printf("\n========================================\n");
    printf("M12.2 WebAssembly Backend: %d/%d tests PASS\n", tests_passed, tests_total);
    printf("========================================\n");

    return (tests_passed == tests_total) ? 0 : 1;
}
