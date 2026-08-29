// TDD — D-1 (Manual 4 §5.2; Manual 2 §4.3): primitivas rc/arc del runtime.
// Verifica que el decremento de refcount a 0 dispara el destructor exactamente 1 vez.
#include <stdio.h>
#include <stdlib.h>

extern void* _syn_rc_crear(void* data, void (*dtor)(void*));
extern void  _syn_rc_increment(void* p);
extern void  _syn_rc_decrement(void* p);
extern void* _syn_arc_crear(void* data, void (*dtor)(void*));
extern void  _syn_arc_increment(void* p);
extern void  _syn_arc_decrement(void* p);

static int g_rc_dtor = 0;
static int g_arc_dtor = 0;

static void rc_dtor(void* d) { g_rc_dtor++; free(d); }
static void arc_dtor(void* d) { g_arc_dtor++; free(d); }

int main(void) {
    int* p = (int*)malloc(sizeof(int));
    void* rc = _syn_rc_crear(p, rc_dtor);
    _syn_rc_increment(rc);
    _syn_rc_decrement(rc);            // sigue vivo (1)
    if (g_rc_dtor != 0) { printf("RC_FAIL prematuro\n"); return 1; }
    _syn_rc_decrement(rc);            // -> 0: destructor 1 vez
    if (g_rc_dtor != 1) { printf("RC_FAIL dtor=%d\n", g_rc_dtor); return 1; }
    printf("RC_OK\n");

    int* q = (int*)malloc(sizeof(int));
    void* arc = _syn_arc_crear(q, arc_dtor);
    _syn_arc_increment(arc);
    _syn_arc_decrement(arc);          // strong=1
    if (g_arc_dtor != 0) { printf("ARC_FAIL prematuro\n"); return 1; }
    _syn_arc_decrement(arc);          // strong=0 -> dtor; luego weak -> free header
    if (g_arc_dtor != 1) { printf("ARC_FAIL dtor=%d\n", g_arc_dtor); return 1; }
    printf("ARC_OK\n");
    return 0;
}
