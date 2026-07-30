/*
 * validate_llvm_control_flow.c — M12.1.2 Validation Test
 *
 * Isolated test for synapse_llvm.c control flow extensions:
 * - icmp (eq, ne, sgt, sge, slt, sle)
 * - br (unconditional and conditional)
 * - Basic block labels
 * - phi nodes
 * - Function declarations and calls
 * - Loop construction
 * - High-level if-else, loop, and call programs
 *
 * File is OUTSIDE tests/ to comply with read-only lock.
 *
 * Compilar:
 *   gcc -O2 -std=c99 validate_llvm_control_flow.c synapse_llvm.c -o validate_llvm_control_flow.exe -lm
 *   ./validate_llvm_control_flow.exe
 */

#include <stdio.h>
#include <string.h>
#include <stdlib.h>

// Opaque handle types from synapse_llvm.c
typedef struct LLVMContext LLVMContext;
typedef struct LLVMModule LLVMModule;
typedef struct LLVMBuilder LLVMBuilder;

// IR type and ICmp enums
typedef enum { IR_I32 = 0, IR_I1, IR_VOID, IR_PTR } IRType;
typedef enum { ICMP_EQ, ICMP_NE, ICMP_SGT, ICMP_SGE, ICMP_SLT, ICMP_SLE } ICmpPredicate;

// -- Existing M12.1.1 externs (reused) --
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
extern void LLVMBuilderCreateRet(LLVMBuilder* b, const char* value);
extern void LLVMBuilderEndFunction(LLVMBuilder* b);
extern void LLVMBuilderConstInt(int val, char* out, size_t out_size);
extern void LLVMBuilderConstBool(int val, char* out, size_t out_size);

// -- M12.1.2 new externs --
extern void LLVMModuleDeclareFunction(LLVMModule* mod, const char* name, int return_type, int param_count, ...);
extern void LLVMBuilderEmitLabel(LLVMBuilder* b, const char* name);
extern void LLVMBuilderCreateICmp(LLVMBuilder* b, int pred, const char* a, const char* b_op, char* out, size_t out_size);
extern void LLVMBuilderCreateBr(LLVMBuilder* b, const char* dest_label);
extern void LLVMBuilderCreateCondBr(LLVMBuilder* b, const char* cond, const char* true_label, const char* false_label);
extern void LLVMBuilderCreatePhi(LLVMBuilder* b, int num_incoming, const char** values, const char** labels, char* out, size_t out_size);
extern void LLVMBuilderCreateCall(LLVMBuilder* b, const char* callee, int return_type, int arg_count, const char** arg_values, const int* arg_types, char* out, size_t out_size);

// -- High-level externs --
extern const char* BuildIfElseProgram(LLVMContext* ctx, const char* name, int a, int b);
extern const char* BuildLoopProgram(LLVMContext* ctx, const char* name, int n);
extern const char* BuildCallProgram(LLVMContext* ctx, const char* name, int value);
extern void LLVMDisposeBuiltModule(LLVMModule* mod);

static int tests_passed = 0;
static int tests_total = 0;

#define TEST(name, cond) do { \
    tests_total++; \
    if (cond) { tests_passed++; printf("  [PASS] %s\n", name); } \
    else { printf("  [FAIL] %s\n", name); } \
} while(0)

int main(void) {
    printf("=== M12.1.2 LLVM Control Flow & Functions Validation ===\n\n");

    // ================================================================
    // Section 1: ICmp (all 6 predicates)
    // ================================================================
    printf("--- Section 1: ICmp ---\n");

    LLVMContext* ctx = LLVMContextCreate();
    LLVMModule* mod = LLVMModuleCreateWithName("icmp_test", ctx);
    LLVMBuilder* builder = LLVMBuilderCreate(ctx);
    LLVMBuilderSetModule(builder, mod);
    LLVMModuleEmitHeader(mod);
    LLVMModuleEmitRuntimeDecls(mod);

    LLVMBuilderBeginFunction(builder, "main", 0, 0);
    LLVMBuilderCreateEntryBlock(builder);

    char a_buf[16], b_buf[16], eq_buf[64], ne_buf[64], gt_buf[64];
    char ge_buf[64], lt_buf[64], le_buf[64];
    LLVMBuilderConstInt(3, a_buf, sizeof(a_buf));
    LLVMBuilderConstInt(7, b_buf, sizeof(b_buf));

    LLVMBuilderCreateICmp(builder, ICMP_EQ, a_buf, b_buf, eq_buf, sizeof(eq_buf));
    LLVMBuilderCreateICmp(builder, ICMP_NE, a_buf, b_buf, ne_buf, sizeof(ne_buf));
    LLVMBuilderCreateICmp(builder, ICMP_SGT, a_buf, b_buf, gt_buf, sizeof(gt_buf));
    LLVMBuilderCreateICmp(builder, ICMP_SGE, a_buf, b_buf, ge_buf, sizeof(ge_buf));
    LLVMBuilderCreateICmp(builder, ICMP_SLT, a_buf, b_buf, lt_buf, sizeof(lt_buf));
    LLVMBuilderCreateICmp(builder, ICMP_SLE, a_buf, b_buf, le_buf, sizeof(le_buf));
    LLVMBuilderCreateRetConst(builder, 0);
    LLVMBuilderEndFunction(builder);

    const char* ir = LLVMModuleGetIR(mod);
    TEST("ICmp EQ contains 'icmp eq'", strstr(ir, "icmp eq") != NULL);
    TEST("ICmp NE contains 'icmp ne'", strstr(ir, "icmp ne") != NULL);
    TEST("ICmp SGT contains 'icmp sgt'", strstr(ir, "icmp sgt") != NULL);
    TEST("ICmp SGE contains 'icmp sge'", strstr(ir, "icmp sge") != NULL);
    TEST("ICmp SLT contains 'icmp slt'", strstr(ir, "icmp slt") != NULL);
    TEST("ICmp SLE contains 'icmp sle'", strstr(ir, "icmp sle") != NULL);
    TEST("ICmp uses i32 operands", strstr(ir, "i32 3, 7") != NULL);

    LLVMModuleDispose(mod);
    LLVMBuilderDispose(builder);
    LLVMContextDispose(ctx);

    // ================================================================
    // Section 2: Unconditional Br (br label)
    // ================================================================
    printf("\n--- Section 2: Br (unconditional) ---\n");

    ctx = LLVMContextCreate();
    mod = LLVMModuleCreateWithName("br_test", ctx);
    builder = LLVMBuilderCreate(ctx);
    LLVMBuilderSetModule(builder, mod);
    LLVMModuleEmitHeader(mod);
    LLVMModuleEmitRuntimeDecls(mod);

    LLVMBuilderBeginFunction(builder, "main", 0, 0);
    LLVMBuilderCreateEntryBlock(builder);
    LLVMBuilderCreateBr(builder, "end");
    LLVMBuilderEmitLabel(builder, "end");
    LLVMBuilderCreateRetConst(builder, 42);
    LLVMBuilderEndFunction(builder);

    ir = LLVMModuleGetIR(mod);
    TEST("Uncond br: contains 'br label %end'",
         strstr(ir, "br label %end") != NULL);
    TEST("Uncond br: contains 'end:' label",
         strstr(ir, "end:") != NULL);
    TEST("Uncond br: ret i32 42 in end block",
         strstr(ir, "ret i32 42") != NULL);

    LLVMModuleDispose(mod);
    LLVMBuilderDispose(builder);
    LLVMContextDispose(ctx);

    // ================================================================
    // Section 3: Conditional Br (br i1, label, label)
    // ================================================================
    printf("\n--- Section 3: Br (conditional) ---\n");

    ctx = LLVMContextCreate();
    mod = LLVMModuleCreateWithName("condbr_test", ctx);
    builder = LLVMBuilderCreate(ctx);
    LLVMBuilderSetModule(builder, mod);
    LLVMModuleEmitHeader(mod);
    LLVMModuleEmitRuntimeDecls(mod);

    LLVMBuilderBeginFunction(builder, "main", 0, 0);
    LLVMBuilderCreateEntryBlock(builder);

    char cond_buf[64];
    LLVMBuilderConstInt(1, a_buf, sizeof(a_buf));
    LLVMBuilderCreateICmp(builder, ICMP_EQ, a_buf, a_buf, cond_buf, sizeof(cond_buf));
    LLVMBuilderCreateCondBr(builder, cond_buf, "then", "else");

    LLVMBuilderEmitLabel(builder, "then");
    LLVMBuilderCreateRetConst(builder, 1);

    LLVMBuilderEmitLabel(builder, "else");
    LLVMBuilderCreateRetConst(builder, 0);
    LLVMBuilderEndFunction(builder);

    ir = LLVMModuleGetIR(mod);
    TEST("Cond br: contains 'br i1'",
         strstr(ir, "br i1") != NULL);
    TEST("Cond br: contains 'label %then'",
         strstr(ir, "label %then") != NULL);
    TEST("Cond br: contains 'label %else'",
         strstr(ir, "label %else") != NULL);
    TEST("Cond br: has then: block",
         strstr(ir, "then:") != NULL);
    TEST("Cond br: has else: block",
         strstr(ir, "else:") != NULL);

    LLVMModuleDispose(mod);
    LLVMBuilderDispose(builder);
    LLVMContextDispose(ctx);

    // ================================================================
    // Section 4: Function Declarations (LLVMModuleDeclareFunction)
    // ================================================================
    printf("\n--- Section 4: Function Declarations ---\n");

    ctx = LLVMContextCreate();
    mod = LLVMModuleCreateWithName("declare_test", ctx);
    LLVMModuleEmitHeader(mod);

    LLVMModuleDeclareFunction(mod, "foo", 0, 2, 0, 1);
    LLVMModuleDeclareFunction(mod, "bar", 1, 1, 3); // 3 = IR_PTR
    LLVMModuleDeclareFunction(mod, "baz_void", 2, 0);

    ir = LLVMModuleGetIR(mod);
    TEST("Declare: foo with i32 ret and i32,i1 params",
         strstr(ir, "declare i32 @foo(i32, i1)") != NULL);
    TEST("Declare: bar with i1 ret and ptr param",
         strstr(ir, "declare i1 @bar(i8*)") != NULL);
    TEST("Declare: baz_void with void ret",
         strstr(ir, "declare void @baz_void()") != NULL);

    LLVMModuleDispose(mod);
    LLVMContextDispose(ctx);

    // ================================================================
    // Section 5: Call Instruction
    // ================================================================
    printf("\n--- Section 5: Call ---\n");

    ctx = LLVMContextCreate();
    mod = LLVMModuleCreateWithName("call_test", ctx);
    builder = LLVMBuilderCreate(ctx);
    LLVMBuilderSetModule(builder, mod);
    LLVMModuleEmitHeader(mod);

    LLVMBuilderBeginFunction(builder, "main", 0, 0);
    LLVMBuilderCreateEntryBlock(builder);

    // call i32 @putchar(i32 65)
    char arg_buf[16], call_out[64];
    LLVMBuilderConstInt(65, arg_buf, sizeof(arg_buf));
    const char* call_args[] = { arg_buf };
    int call_types[] = { 0 };  // IR_I32
    LLVMBuilderCreateCall(builder, "putchar", 0, 1,
                           call_args, call_types, call_out, sizeof(call_out));
    LLVMBuilderCreateRetConst(builder, 0);
    LLVMBuilderEndFunction(builder);

    ir = LLVMModuleGetIR(mod);
    TEST("Call: contains 'call i32 @putchar'",
         strstr(ir, "call i32 @putchar") != NULL);
    TEST("Call: argument 'i32 65'",
         strstr(ir, "i32 65") != NULL);
    TEST("Call: SSA result assigned",
         call_out[0] == '%');

    LLVMModuleDispose(mod);
    LLVMBuilderDispose(builder);
    LLVMContextDispose(ctx);

    // ================================================================
    // Section 6: Phi Node
    // ================================================================
    printf("\n--- Section 6: Phi ---\n");

    ctx = LLVMContextCreate();
    mod = LLVMModuleCreateWithName("phi_test", ctx);
    builder = LLVMBuilderCreate(ctx);
    LLVMBuilderSetModule(builder, mod);
    LLVMModuleEmitHeader(mod);
    LLVMModuleEmitRuntimeDecls(mod);

    LLVMBuilderBeginFunction(builder, "main", 0, 0);
    LLVMBuilderCreateEntryBlock(builder);

    // Branch to two blocks, then merge with phi
    LLVMBuilderCreateCondBr(builder, "true", "left", "right");

    LLVMBuilderEmitLabel(builder, "left");
    char left_val[16];
    LLVMBuilderConstInt(10, left_val, sizeof(left_val));
    LLVMBuilderCreateBr(builder, "merge");

    LLVMBuilderEmitLabel(builder, "right");
    char right_val[16];
    LLVMBuilderConstInt(20, right_val, sizeof(right_val));
    LLVMBuilderCreateBr(builder, "merge");

    LLVMBuilderEmitLabel(builder, "merge");
    const char* phi_vals[] = { left_val, right_val };
    const char* phi_labels[] = { "left", "right" };
    char phi_out[64];
    LLVMBuilderCreatePhi(builder, 2, phi_vals, phi_labels, phi_out, sizeof(phi_out));
    LLVMBuilderCreateRet(builder, phi_out);
    LLVMBuilderEndFunction(builder);

    ir = LLVMModuleGetIR(mod);
    TEST("Phi: contains 'phi i32'",
         strstr(ir, "phi i32") != NULL);
    TEST("Phi: incoming from left",
         strstr(ir, "[10, %left]") != NULL);
    TEST("Phi: incoming from right",
         strstr(ir, "[20, %right]") != NULL);

    LLVMModuleDispose(mod);
    LLVMBuilderDispose(builder);
    LLVMContextDispose(ctx);

    // ================================================================
    // Section 7: High-Level If-Else Program
    // ================================================================
    printf("\n--- Section 7: BuildIfElseProgram ---\n");

    ctx = LLVMContextCreate();
    const char* if_ir = BuildIfElseProgram(ctx, "ifelse", 5, 10);
    TEST("IfElse: returns IR", if_ir != NULL);
    if (if_ir) {
        TEST("IfElse: contains 'icmp slt'",
             strstr(if_ir, "icmp slt") != NULL);
        TEST("IfElse: contains conditional br",
             strstr(if_ir, "br i1") != NULL);
        TEST("IfElse: contains 'ret i32 1'",
             strstr(if_ir, "ret i32 1") != NULL);
        TEST("IfElse: contains 'ret i32 0'",
             strstr(if_ir, "ret i32 0") != NULL);
    }
    LLVMContextDispose(ctx);

    // ================================================================
    // Section 8: High-Level Loop Program
    // ================================================================
    printf("\n--- Section 8: BuildLoopProgram ---\n");

    ctx = LLVMContextCreate();
    const char* loop_ir = BuildLoopProgram(ctx, "loop", 5);
    TEST("Loop: returns IR", loop_ir != NULL);
    if (loop_ir) {
        TEST("Loop: contains alloca i32",
             strstr(loop_ir, "alloca i32") != NULL);
        TEST("Loop: contains store i32 0",
             strstr(loop_ir, "store i32 0") != NULL);
        TEST("Loop: contains load i32",
             strstr(loop_ir, "load i32") != NULL);
        TEST("Loop: contains icmp slt (i < 5)",
             strstr(loop_ir, "icmp slt") != NULL);
        TEST("Loop: contains br label (back-edge)",
             strstr(loop_ir, "br label") != NULL);
        TEST("Loop: contains add i32 (sum += i)",
             strstr(loop_ir, "add i32") != NULL);
        TEST("Loop: contains loop_header label",
             strstr(loop_ir, "loop_header") != NULL);
    }
    LLVMContextDispose(ctx);

    // ================================================================
    // Section 9: High-Level Call Program
    // ================================================================
    printf("\n--- Section 9: BuildCallProgram ---\n");

    ctx = LLVMContextCreate();
    const char* call_ir = BuildCallProgram(ctx, "callprog", 65);
    TEST("CallProg: returns IR", call_ir != NULL);
    if (call_ir) {
        TEST("CallProg: contains declare i32 @putchar",
             strstr(call_ir, "declare i32 @putchar") != NULL);
        TEST("CallProg: contains call i32 @putchar",
             strstr(call_ir, "call i32 @putchar") != NULL);
        TEST("CallProg: argument i32 65",
             strstr(call_ir, "i32 65") != NULL);
        TEST("CallProg: ret i32 0",
             strstr(call_ir, "ret i32 0") != NULL);
    }
    LLVMContextDispose(ctx);

    // ================================================================
    // Section 10: Edge Cases
    // ================================================================
    printf("\n--- Section 10: Edge Cases ---\n");

    // Null builder: should not crash
    ctx = LLVMContextCreate();
    LLVMBuilderCreateICmp(NULL, ICMP_EQ, "1", "2", a_buf, sizeof(a_buf));
    TEST("ICmp with NULL builder (no crash)", 1);

    LLVMBuilderCreateBr(NULL, "dest");
    TEST("Br with NULL builder (no crash)", 1);

    LLVMBuilderCreateCondBr(NULL, "c", "t", "f");
    TEST("CondBr with NULL builder (no crash)", 1);

    LLVMModuleDeclareFunction(NULL, "test", 0, 0);
    TEST("Declare with NULL module (no crash)", 1);

    LLVMBuilderCreateCall(NULL, "foo", 0, 0, NULL, NULL, a_buf, sizeof(a_buf));
    TEST("Call with NULL builder (no crash)", 1);

    // Empty module header
    mod = LLVMModuleCreateWithName("empty", ctx);
    TEST("Empty module has 0 length", LLVMModuleGetIRLength(mod) == 0);
    LLVMModuleDispose(mod);

    LLVMContextDispose(ctx);

    // ================================================================
    // Summary
    // ================================================================
    printf("\n========================================\n");
    printf("M12.1.2 Control Flow & Functions: %d/%d tests PASS\n", tests_passed, tests_total);
    printf("========================================\n");

    return (tests_passed == tests_total) ? 0 : 1;
}
