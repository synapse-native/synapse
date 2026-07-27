/*
 * validate_llvm_backend.c — M12.1.1 Validation Test
 *
 * Isolated test for synapse_llvm.c: verifies LLVM module initialization,
 * IR text generation for primitive expressions, and error reporting.
 *
 * File is OUTSIDE tests/ to comply with read-only lock.
 *
 * Compilar:
 *   gcc -O2 -std=c99 validate_llvm_backend.c synapse_llvm.c -o validate_llvm_backend.exe -lm
 *   ./validate_llvm_backend.exe
 */

#include <stdio.h>
#include <string.h>
#include <stdlib.h>

typedef struct LLVMContext LLVMContext;
typedef struct LLVMModule LLVMModule;
typedef struct LLVMBuilder LLVMBuilder;

extern LLVMContext* LLVMContextCreate(void);
extern void LLVMContextDispose(LLVMContext* ctx);
extern int LLVMContextGetErrorCount(LLVMContext* ctx);
extern const char* LLVMContextGetError(LLVMContext* ctx);

extern LLVMModule* LLVMModuleCreateWithName(const char* name, LLVMContext* ctx);
extern void LLVMModuleDispose(LLVMModule* mod);
extern const char* LLVMModuleGetIR(LLVMModule* mod);
extern size_t LLVMModuleGetIRLength(LLVMModule* mod);
extern void LLVMModuleEmitHeader(LLVMModule* mod);
extern void LLVMModuleEmitRuntimeDecls(LLVMModule* mod);

extern LLVMBuilder* LLVMBuilderCreate(LLVMContext* ctx);
extern void LLVMBuilderDispose(LLVMBuilder* b);
extern void LLVMBuilderSetModule(LLVMBuilder* b, LLVMModule* mod);
extern void LLVMBuilderBeginFunction(LLVMBuilder* b, const char* name, int return_type, int param_count, ...);
extern void LLVMBuilderCreateEntryBlock(LLVMBuilder* b);
extern void LLVMBuilderCreateRetConst(LLVMBuilder* b, int val);
extern void LLVMBuilderEndFunction(LLVMBuilder* b);
extern void LLVMBuilderConstInt(int val, char* out, size_t out_size);
extern void LLVMBuilderConstBool(int val, char* out, size_t out_size);
extern void LLVMBuilderCreateAdd(LLVMBuilder* b, const char* a, const char* b_op, char* out, size_t out_size);
extern void LLVMBuilderCreateSub(LLVMBuilder* b, const char* a, const char* b_op, char* out, size_t out_size);
extern void LLVMBuilderCreateMul(LLVMBuilder* b, const char* a, const char* b_op, char* out, size_t out_size);
extern void LLVMBuilderCreateSDiv(LLVMBuilder* b, const char* a, const char* b_op, char* out, size_t out_size);
extern void LLVMBuilderCreateRet(LLVMBuilder* b, const char* value);

// Fixed buffer-based alloca/load (replaced static buffer returns)
extern void LLVMBuilderCreateAlloca(LLVMBuilder* b, int type, const char* name,
                                     char* out, size_t out_size);
extern void LLVMBuilderCreateStore(LLVMBuilder* b, const char* val, const char* ptr);
extern void LLVMBuilderCreateLoad(LLVMBuilder* b, const char* ptr,
                                   char* out, size_t out_size);

extern const char* BuildMinimalProgram(LLVMContext* ctx, const char* name, int return_value);
extern const char* BuildArithmeticProgram(LLVMContext* ctx, const char* name, int op, int lhs, int rhs);

static int tests_passed = 0;
static int tests_total = 0;

#define TEST(name, cond) do { \
    tests_total++; \
    if (cond) { tests_passed++; printf("  [PASS] %s\n", name); } \
    else { printf("  [FAIL] %s\n", name); } \
} while(0)

int main(void) {
    printf("=== M12.1.1 LLVM Backend Validation ===\n\n");

    // ================================================================
    // Section 1: LLVMContext
    // ================================================================
    printf("--- Section 1: LLVMContext ---\n");

    LLVMContext* ctx = LLVMContextCreate();
    TEST("LLVMContextCreate returns non-NULL", ctx != NULL);
    TEST("Initial error count is 0", LLVMContextGetErrorCount(ctx) == 0);
    LLVMContextDispose(ctx);
    TEST("LLVMContextDispose (no crash)", 1);

    // ================================================================
    // Section 2: LLVMModule
    // ================================================================
    printf("\n--- Section 2: LLVMModule ---\n");

    ctx = LLVMContextCreate();
    LLVMModule* mod = LLVMModuleCreateWithName("test_module", ctx);
    TEST("LLVMModuleCreateWithName returns non-NULL", mod != NULL);
    TEST("Initial IR is empty", LLVMModuleGetIRLength(mod) == 0);

    LLVMModuleEmitHeader(mod);
    TEST("Header emission adds content", LLVMModuleGetIRLength(mod) > 0);

    const char* ir = LLVMModuleGetIR(mod);
    TEST("IR contains ModuleID", strstr(ir, "ModuleID") != NULL);
    TEST("IR contains target triple", strstr(ir, "target triple") != NULL);
    TEST("IR contains datalayout", strstr(ir, "target datalayout") != NULL);

    LLVMModuleEmitRuntimeDecls(mod);
    ir = LLVMModuleGetIR(mod);
    TEST("Runtime decls added", strstr(ir, "putchar") != NULL);
    TEST("printf declared", strstr(ir, "printf") != NULL);

    LLVMModuleDispose(mod);
    LLVMContextDispose(ctx);

    // ================================================================
    // Section 3: LLVMBuilder + Function Construction
    // ================================================================
    printf("\n--- Section 3: LLVMBuilder ---\n");

    ctx = LLVMContextCreate();
    mod = LLVMModuleCreateWithName("fn_test", ctx);
    LLVMBuilder* builder = LLVMBuilderCreate(ctx);
    TEST("LLVMBuilderCreate returns non-NULL", builder != NULL);

    LLVMBuilderSetModule(builder, mod);
    LLVMModuleEmitHeader(mod);
    LLVMModuleEmitRuntimeDecls(mod);

    // Build a function that returns 42
    LLVMBuilderBeginFunction(builder, "main", 0, 0);
    LLVMBuilderCreateEntryBlock(builder);
    LLVMBuilderCreateRetConst(builder, 42);
    LLVMBuilderEndFunction(builder);

    ir = LLVMModuleGetIR(mod);
    TEST("IR contains 'define' for function", strstr(ir, "define") != NULL);
    TEST("IR contains '@main' function", strstr(ir, "@main") != NULL);
    TEST("IR contains 'entry:' block", strstr(ir, "entry:") != NULL);
    TEST("IR contains 'ret i32 42'", strstr(ir, "ret i32 42") != NULL);

    LLVMBuilderDispose(builder);
    LLVMModuleDispose(mod);
    LLVMContextDispose(ctx);

    // ================================================================
    // Section 4: Arithmetic Operations using buffer-based API
    // ================================================================
    printf("\n--- Section 4: Arithmetic Operations ---\n");

    ctx = LLVMContextCreate();
    mod = LLVMModuleCreateWithName("arith_test", ctx);
    builder = LLVMBuilderCreate(ctx);
    LLVMBuilderSetModule(builder, mod);

    LLVMModuleEmitHeader(mod);
    LLVMModuleEmitRuntimeDecls(mod);

    // Build: main() { return 3 + 7; }
    LLVMBuilderBeginFunction(builder, "main", 0, 0);
    LLVMBuilderCreateEntryBlock(builder);
    char l_buf[32], r_buf[32], sum_buf[64];
    LLVMBuilderConstInt(3, l_buf, sizeof(l_buf));
    LLVMBuilderConstInt(7, r_buf, sizeof(r_buf));
    LLVMBuilderCreateAdd(builder, l_buf, r_buf, sum_buf, sizeof(sum_buf));
    LLVMBuilderCreateRet(builder, sum_buf);
    LLVMBuilderEndFunction(builder);

    ir = LLVMModuleGetIR(mod);
    TEST("Addition: contains 'add i32 3, 7'",
         strstr(ir, "add i32 3, 7") != NULL);

    LLVMModuleDispose(mod);
    LLVMBuilderDispose(builder);
    LLVMContextDispose(ctx);

    // ================================================================
    // Section 5: High-Level API
    // ================================================================
    printf("\n--- Section 5: High-Level API ---\n");

    ctx = LLVMContextCreate();
    const char* add_ir = BuildArithmeticProgram(ctx, "add_prog", 0, 10, 20);
    TEST("BuildArithmeticProgram(add) returns IR", add_ir != NULL);
    if (add_ir) {
        TEST("ADD program contains 'add i32 10, 20'",
             strstr(add_ir, "add i32 10, 20") != NULL);
        TEST("ADD program returns in main",
             strstr(add_ir, "ret i32") != NULL);
    }
    LLVMContextDispose(ctx);

    ctx = LLVMContextCreate();
    const char* sub_ir = BuildArithmeticProgram(ctx, "sub_prog", 1, 50, 30);
    TEST("BuildArithmeticProgram(sub) returns IR", sub_ir != NULL);
    if (sub_ir) {
        TEST("SUB program contains 'sub i32 50, 30'",
             strstr(sub_ir, "sub i32 50, 30") != NULL);
    }
    LLVMContextDispose(ctx);

    ctx = LLVMContextCreate();
    const char* mul_ir = BuildArithmeticProgram(ctx, "mul_prog", 2, 6, 7);
    TEST("BuildArithmeticProgram(mul) returns IR", mul_ir != NULL);
    if (mul_ir) {
        TEST("MUL program contains 'mul i32 6, 7'",
             strstr(mul_ir, "mul i32 6, 7") != NULL);
    }
    LLVMContextDispose(ctx);

    ctx = LLVMContextCreate();
    const char* div_ir = BuildArithmeticProgram(ctx, "div_prog", 3, 100, 4);
    TEST("BuildArithmeticProgram(div) returns IR", div_ir != NULL);
    if (div_ir) {
        TEST("DIV program contains 'sdiv i32 100, 4'",
             strstr(div_ir, "sdiv i32 100, 4") != NULL);
    }
    LLVMContextDispose(ctx);

    // ================================================================
    // Section 6: Alloca / Store / Load
    // ================================================================
    printf("\n--- Section 6: Alloca / Store / Load ---\n");

    ctx = LLVMContextCreate();
    mod = LLVMModuleCreateWithName("mem_test", ctx);
    builder = LLVMBuilderCreate(ctx);
    LLVMBuilderSetModule(builder, mod);
    LLVMModuleEmitHeader(mod);
    LLVMModuleEmitRuntimeDecls(mod);

    LLVMBuilderBeginFunction(builder, "main", 0, 0);
    LLVMBuilderCreateEntryBlock(builder);

    // alloca i32, store 42, load
    char alloc_buf[64], loaded_buf[64], const_buf[32];
    LLVMBuilderConstInt(42, const_buf, sizeof(const_buf));
    LLVMBuilderCreateAlloca(builder, 0, "x", alloc_buf, sizeof(alloc_buf));
    TEST("Alloca result starts with '%' ",
         alloc_buf[0] == '%');
    LLVMBuilderCreateStore(builder, const_buf, alloc_buf);
    LLVMBuilderCreateLoad(builder, alloc_buf, loaded_buf, sizeof(loaded_buf));
    TEST("Load result starts with '%' ",
         loaded_buf[0] == '%');
    LLVMBuilderCreateRet(builder, loaded_buf);
    LLVMBuilderEndFunction(builder);

    ir = LLVMModuleGetIR(mod);
    TEST("Memory ops: contains 'alloca i32'",
         strstr(ir, "alloca i32") != NULL);
    TEST("Memory ops: contains 'store i32'",
         strstr(ir, "store i32 42") != NULL);
    TEST("Memory ops: contains 'load i32'",
         strstr(ir, "load i32") != NULL);

    LLVMModuleDispose(mod);
    LLVMBuilderDispose(builder);
    LLVMContextDispose(ctx);

    // ================================================================
    // Section 7: Boolean Constants
    // ================================================================
    printf("\n--- Section 7: Boolean Constants ---\n");

    char bool_true[16], bool_false[16];
    LLVMBuilderConstBool(1, bool_true, sizeof(bool_true));
    TEST("ConstBool(true) returns 'true'",
         strcmp(bool_true, "true") == 0);
    LLVMBuilderConstBool(0, bool_false, sizeof(bool_false));
    TEST("ConstBool(false) returns 'false'",
         strcmp(bool_false, "false") == 0);

    // Build a function that uses booleans: return true ? 1 : 0
    ctx = LLVMContextCreate();
    mod = LLVMModuleCreateWithName("bool_test", ctx);
    builder = LLVMBuilderCreate(ctx);
    LLVMBuilderSetModule(builder, mod);
    LLVMModuleEmitHeader(mod);
    LLVMModuleEmitRuntimeDecls(mod);

    LLVMBuilderBeginFunction(builder, "main", 0, 0);
    LLVMBuilderCreateEntryBlock(builder);
    LLVMBuilderCreateRetConst(builder, 1);
    LLVMBuilderEndFunction(builder);

    ir = LLVMModuleGetIR(mod);
    TEST("Boolean IR: contains 'ret i32 1'",
         strstr(ir, "ret i32 1") != NULL);

    LLVMModuleDispose(mod);
    LLVMBuilderDispose(builder);
    LLVMContextDispose(ctx);

    // ================================================================
    // Section 8: BuildMinimalProgram
    // ================================================================
    printf("\n--- Section 8: BuildMinimalProgram ---\n");

    ctx = LLVMContextCreate();
    const char* min_ir = BuildMinimalProgram(ctx, "minimal", 0);
    TEST("BuildMinimalProgram returns IR", min_ir != NULL);
    if (min_ir) {
        TEST("Minimal: contains '@main'", strstr(min_ir, "@main") != NULL);
        TEST("Minimal: contains 'entry:'", strstr(min_ir, "entry:") != NULL);
        TEST("Minimal: contains 'ret i32 0'", strstr(min_ir, "ret i32 0") != NULL);
        TEST("Minimal: valid module header", strstr(min_ir, "ModuleID") != NULL);
    }
    LLVMContextDispose(ctx);

    ctx = LLVMContextCreate();
    const char* min42 = BuildMinimalProgram(ctx, "return42", 42);
    TEST("BuildMinimalProgram(42) contains 'ret i32 42'",
         min42 && strstr(min42, "ret i32 42") != NULL);
    LLVMContextDispose(ctx);

    // ================================================================
    // Summary
    // ================================================================
    printf("\n========================================\n");
    printf("M12.1.1 LLVM Backend: %d/%d tests PASS\n", tests_passed, tests_total);
    printf("========================================\n");

    return (tests_passed == tests_total) ? 0 : 1;
}
