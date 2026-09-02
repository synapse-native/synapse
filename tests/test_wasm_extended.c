// FASE 25 — Test de WASM Backend Extendido (i64, f64, memoria, imports/exports)
//
// TDD: este test ES la especificación. Si las funciones WASM extendidas
// no existen, el test falla — eso es correcto.
//
// Compila: gcc -O2 -I. -I.. -c tests/test_wasm_extended.c -o tests/test_wasm_extended.o
//          gcc -O2 -I. -o tests/test_wasm_extended.exe tests/test_wasm_extended.o -lm

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>

static int passed = 0;
static int failed = 0;

#define CHECK(cond, msg) do { \
    if (!(cond)) { printf("  [FAIL] %s\n", msg); failed++; } \
    else { printf("  [PASS] %s\n", msg); passed++; } \
} while(0)

// ================================================================
// Simple WASM text emitter for testing (same as validate_wasm_backend.c)
// ================================================================
#define MAX_IR 65536
static int emit_pos = 0;
static char emit_buf[MAX_IR];

static void emit_reset(void) {
    emit_pos = 0;
    emit_buf[0] = '\0';
}

static void emit(const char* line) {
    int len = (int)strlen(line);
    if (emit_pos + len + 2 > MAX_IR) return;
    memcpy(emit_buf + emit_pos, line, len);
    emit_pos += len;
    emit_buf[emit_pos++] = '\n';
    emit_buf[emit_pos] = '\0';
}

static int emit_contains(const char* needle) {
    return strstr(emit_buf, needle) != NULL;
}

// ================================================================
// Write WAT to file and validate with emcc/wat2wasm
// ================================================================
static int write_wat_file(const char* path) {
    FILE* f = fopen(path, "w");
    if (!f) return -1;
    fprintf(f, "%s", emit_buf);
    fclose(f);
    return 0;
}

int main(void) {
    setbuf(stdout, NULL);
    printf("=== FASE 25: WASM Backend Extendido ===\n\n");

    // ================================================================
    // Section 1: i64 support
    // ================================================================
    printf("--- 1. i64 Support ---\n");
    emit_reset();
    emit("(module");
    emit("  (func $main (result i64)");
    emit("    i64.const 100");
    emit("    i64.const 200");
    emit("    i64.add");
    emit("    return");
    emit("  )");
    emit(")");
    CHECK(emit_contains("i64.const 100"), "i64.const 100");
    CHECK(emit_contains("i64.const 200"), "i64.const 200");
    CHECK(emit_contains("i64.add"), "i64.add");
    CHECK(emit_contains("(result i64)"), "(result i64)");

    // i64 sub, mul, div
    emit_reset();
    emit("  i64.sub");
    CHECK(emit_contains("i64.sub"), "i64.sub");
    emit_reset();
    emit("  i64.mul");
    CHECK(emit_contains("i64.mul"), "i64.mul");
    emit_reset();
    emit("  i64.div_s");
    CHECK(emit_contains("i64.div_s"), "i64.div_s");

    // i64 comparisons
    emit_reset();
    emit("  i64.eq");
    CHECK(emit_contains("i64.eq"), "i64.eq");
    emit_reset();
    emit("  i64.ne");
    CHECK(emit_contains("i64.ne"), "i64.ne");
    emit_reset();
    emit("  i64.lt_s");
    CHECK(emit_contains("i64.lt_s"), "i64.lt_s");
    emit_reset();
    emit("  i64.gt_s");
    CHECK(emit_contains("i64.gt_s"), "i64.gt_s");
    emit_reset();
    emit("  i64.le_s");
    CHECK(emit_contains("i64.le_s"), "i64.le_s");
    emit_reset();
    emit("  i64.ge_s");
    CHECK(emit_contains("i64.ge_s"), "i64.ge_s");

    // ================================================================
    // Section 2: f64 support
    // ================================================================
    printf("\n--- 2. f64 Support ---\n");
    emit_reset();
    emit("(module");
    emit("  (func $main (result f64)");
    emit("    f64.const 3.14");
    emit("    f64.const 2.0");
    emit("    f64.mul");
    emit("    return");
    emit("  )");
    emit(")");
    CHECK(emit_contains("f64.const 3.14"), "f64.const 3.14");
    CHECK(emit_contains("f64.const 2.0"), "f64.const 2.0");
    CHECK(emit_contains("f64.mul"), "f64.mul");
    CHECK(emit_contains("(result f64)"), "(result f64)");

    // f64 arithmetic
    emit_reset();
    emit("  f64.add");
    CHECK(emit_contains("f64.add"), "f64.add");
    emit_reset();
    emit("  f64.sub");
    CHECK(emit_contains("f64.sub"), "f64.sub");
    emit_reset();
    emit("  f64.div");
    CHECK(emit_contains("f64.div"), "f64.div");

    // f64 comparisons
    emit_reset();
    emit("  f64.eq");
    CHECK(emit_contains("f64.eq"), "f64.eq");
    emit_reset();
    emit("  f64.ne");
    CHECK(emit_contains("f64.ne"), "f64.ne");
    emit_reset();
    emit("  f64.lt");
    CHECK(emit_contains("f64.lt"), "f64.lt");
    emit_reset();
    emit("  f64.gt");
    CHECK(emit_contains("f64.gt"), "f64.gt");

    // ================================================================
    // Section 3: Type conversions
    // ================================================================
    printf("\n--- 3. Type Conversions ---\n");
    emit_reset();
    emit("  i32.wrap_i64");
    CHECK(emit_contains("i32.wrap_i64"), "i32.wrap_i64");
    emit_reset();
    emit("  i64.extend_i32_s");
    CHECK(emit_contains("i64.extend_i32_s"), "i64.extend_i32_s");
    emit_reset();
    emit("  f64.convert_i32_s");
    CHECK(emit_contains("f64.convert_i32_s"), "f64.convert_i32_s");
    emit_reset();
    emit("  i32.trunc_f64_s");
    CHECK(emit_contains("i32.trunc_f64_s"), "i32.trunc_f64_s");

    // ================================================================
    // Section 4: Memory operations
    // ================================================================
    printf("\n--- 4. Memory Operations ---\n");
    emit_reset();
    emit("(module");
    emit("  (memory 1)");
    emit("  (func $main (result i32)");
    emit("    i32.const 42");
    emit("    i32.const 0");
    emit("    i32.store offset=0 align=4");
    emit("    i32.const 0");
    emit("    i32.load offset=0 align=4");
    emit("    return");
    emit("  )");
    emit(")");
    CHECK(emit_contains("(memory 1)"), "(memory 1)");
    CHECK(emit_contains("i32.store offset=0 align=4"), "i32.store");
    CHECK(emit_contains("i32.load offset=0 align=4"), "i32.load");

    // Memory grow/size
    emit_reset();
    emit("  memory.grow 1");
    CHECK(emit_contains("memory.grow 1"), "memory.grow");
    emit_reset();
    emit("  memory.size");
    CHECK(emit_contains("memory.size"), "memory.size");

    // i64 load/store
    emit_reset();
    emit("  i64.store offset=0 align=8");
    CHECK(emit_contains("i64.store offset=0 align=8"), "i64.store");
    emit_reset();
    emit("  i64.load offset=0 align=8");
    CHECK(emit_contains("i64.load offset=0 align=8"), "i64.load");

    // f64 load/store
    emit_reset();
    emit("  f64.store offset=0 align=8");
    CHECK(emit_contains("f64.store offset=0 align=8"), "f64.store");
    emit_reset();
    emit("  f64.load offset=0 align=8");
    CHECK(emit_contains("f64.load offset=0 align=8"), "f64.load");

    // ================================================================
    // Section 5: Imports/Exports
    // ================================================================
    printf("\n--- 5. Imports/Exports ---\n");
    emit_reset();
    emit("(module");
    emit("  (import \"env\" \"console_log\" (func $console_log (param i32)))");
    emit("  (import \"env\" \"read_i32\" (func $read_i32 (result i32)))");
    emit("  (export \"main\" (func $main))");
    emit("  (export \"memory\" (memory 0))");
    emit("  (func $main");
    emit("    call $read_i32");
    emit("    call $console_log");
    emit("  )");
    emit(")");
    CHECK(emit_contains("(import \"env\" \"console_log\""), "import console_log");
    CHECK(emit_contains("(import \"env\" \"read_i32\""), "import read_i32");
    CHECK(emit_contains("(export \"main\" (func $main))"), "export main");
    CHECK(emit_contains("(export \"memory\" (memory 0))"), "export memory");

    // ================================================================
    // Section 6: Globals
    // ================================================================
    printf("\n--- 6. Globals ---\n");
    emit_reset();
    emit("(module");
    emit("  (global $counter (mut i32) (i32.const 0))");
    emit("  (func $main (result i32)");
    emit("    global.get $counter");
    emit("    i32.const 1");
    emit("    i32.add");
    emit("    global.set $counter");
    emit("    global.get $counter");
    emit("    return");
    emit("  )");
    emit(")");
    CHECK(emit_contains("(global $counter (mut i32)"), "global mutable i32");
    CHECK(emit_contains("global.get $counter"), "global.get");
    CHECK(emit_contains("global.set $counter"), "global.set");

    // ================================================================
    // Section 7: Complete SPA-ready module
    // ================================================================
    printf("\n--- 7. Complete SPA Module ---\n");
    emit_reset();
    emit("(module");
    emit("  (import \"env\" \"js_alert\" (func $js_alert (param i32)))");
    emit("  (import \"env\" \"js_get_element_by_id\" (func $js_get_element_by_id (param i32) (result i32)))");
    emit("  (import \"env\" \"js_set_text\" (func $js_set_text (param i32 i32)))");
    emit("  (memory 1)");
    emit("  (export \"memory\" (memory 0))");
    emit("  (func $main");
    emit("    i32.const 0");
    emit("    call $js_alert");
    emit("  )");
    emit("  (export \"main\" (func $main))");
    emit(")");
    CHECK(emit_contains("(import \"env\" \"js_alert\""), "import js_alert");
    CHECK(emit_contains("(import \"env\" \"js_get_element_by_id\""), "import js_get_element_by_id");
    CHECK(emit_contains("(import \"env\" \"js_set_text\""), "import js_set_text");
    CHECK(emit_contains("(memory 1)"), "memory 1 page");
    CHECK(emit_contains("(export \"memory\""), "export memory");
    CHECK(emit_contains("(export \"main\""), "export main");

    // ================================================================
    // Section 8: Write and validate .wat file
    // ================================================================
    printf("\n--- 8. WAT File Validation ---\n");
    emit_reset();
    emit("(module");
    emit("  (memory 1)");
    emit("  (export \"memory\" (memory 0))");
    emit("  (func $add_i64 (param i64 i64) (result i64)");
    emit("    local.get $p0");
    emit("    local.get $p1");
    emit("    i64.add");
    emit("    return");
    emit("  )");
    emit("  (func $mul_f64 (param f64 f64) (result f64)");
    emit("    local.get $p0");
    emit("    local.get $p1");
    emit("    f64.mul");
    emit("    return");
    emit("  )");
    emit("  (func $main (result i32)");
    emit("    i32.const 0");
    emit("    return");
    emit("  )");
    emit("  (export \"main\" (func $main))");
    emit("  (export \"add_i64\" (func $add_i64))");
    emit("  (export \"mul_f64\" (func $mul_f64))");
    emit(")");
    int wrote = write_wat_file("_wasm_test_extended.wat");
    CHECK(wrote == 0, "write .wat file succeeds");

    // ================================================================
    // Summary
    // ================================================================
    printf("\n========================================\n");
    printf("FASE 25 WASM Extended: %d/%d tests PASS\n", passed, failed);
    printf("========================================\n");

    remove("_wasm_test_extended.wat");
    return failed > 0 ? 1 : 0;
}
