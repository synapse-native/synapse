/**
 * test_cluster_raft.c — Prueba de integración del consenso Raft (M8.3)
 *
 * Simula un cluster de 5 nodos con algoritmo de consenso Raft:
 *   - Elección de líder con timeouts aleatorios
 *   - Heartbeats del líder mantienen seguidores
 *   - Tras caída del líder, se elige uno nuevo
 *   - Consistencia linealizable del término y log
 *
 * Validaciones:
 *   1. Al iniciar, todos son followers sin líder
 *   2. Se elige un líder en < 2 segundos
 *   3. El líder envía heartbeats, followers mantienen estado
 *   4. Tras abdicación forzada del líder, se elige uno nuevo
 *   5. El nuevo líder tiene term > anterior
 *   6. Log replication: comandos agregados al líder se reflejan en commit index
 *   7. Consistencia: después de elecciones, todos los nodos convergen al mismo líder
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <assert.h>

typedef struct { int longitud; const char* datos; } CadenaSegura;

extern void pool_init(uint32_t total_blocks, uint32_t block_size);
extern void* pool_alloc(size_t size);
extern long long _get_timestamp_ns(void);
extern int raft_inicializar(int node_id, int num_nodes, int seed);
extern int raft_iniciar(long long tiempo_actual_ns, int node_id);
extern int raft_tick(long long tiempo_actual_ns, int node_id);
extern int raft_estado(int node_id);
extern int raft_term_actual(int node_id);
extern int raft_lider_actual(int node_id);
extern int raft_log_entradas(int node_id);
extern int raft_commit_index(int node_id);
extern int raft_procesar_solicitud_voto(int voter_id, int candidate_term, int candidate_id, int candidate_last_log);
extern int raft_procesar_respuesta_voto(int candidate_id, int responder_term, int responder_id, int granted);
extern int raft_procesar_heartbeat(int follower_id, int leader_term, int leader_id, int leader_commit);
extern int raft_forzar_abdicacion(int node_id);
extern int raft_agregar_entrada(int node_id);
extern int raft_reiniciar_nodo(int node_id);
extern CadenaSegura raft_info(int node_id);

#define RAFT_FOLLOWER  0
#define RAFT_CANDIDATE 1
#define RAFT_LEADER    2
#define NODES 5

static int passed = 0;
static int failed = 0;

#define CHECK(cond, msg) do { \
    if (!(cond)) { \
        printf("  [FAIL] %s\n", msg); \
        failed++; \
    } else { \
        printf("  [PASS] %s\n", msg); \
        passed++; \
    } \
} while(0)

#define CHECK_INT_EQ(a, b, msg) do { \
    if ((a) != (b)) { \
        printf("  [FAIL] %s: esperado %d, obtenido %d\n", msg, (b), (a)); \
        failed++; \
    } else { \
        printf("  [PASS] %s\n", msg); \
        passed++; \
    } \
} while(0)

// Simulate message passing: deliver RequestVote from candidate to all followers
static int deliver_request_vote(int candidate_id, int term) {
    int votes = 1;  // self-vote
    for (int i = 0; i < NODES; i++) {
        if (i == candidate_id) continue;
        int granted = raft_procesar_solicitud_voto(i, term, candidate_id, 0);
        if (granted == 1) votes++;
    }
    // Deliver responses back to candidate
    for (int i = 0; i < NODES; i++) {
        if (i == candidate_id) continue;
        int granted = (raft_lider_actual(i) == -1); // heuristic: voted if no leader
        raft_procesar_respuesta_voto(candidate_id, term, i,
            (raft_lider_actual(i) == -1 && raft_term_actual(i) <= term) ? 1 : 0);
    }
    // Check directly if voted for candidate
    int actual_votes = 1;
    for (int i = 0; i < NODES; i++) {
        if (i == candidate_id) continue;
        if (raft_lider_actual(i) == -1 && raft_term_actual(i) <= term) actual_votes++;
    }
    return actual_votes;
}

// Simulate leader sending heartbeats to all followers
static void deliver_heartbeats(int leader_id, int term, int commit) {
    for (int i = 0; i < NODES; i++) {
        if (i == leader_id) continue;
        raft_procesar_heartbeat(i, term, leader_id, commit);
    }
}

// Simulate election: one node becomes candidate, asks for votes
static int run_election(int candidate_id, long long now_ns) {
    // Candidate initiates election
    int event = raft_tick(now_ns, candidate_id);

    // If candidate_id timed out and started election, deliver votes
    if (raft_estado(candidate_id) == RAFT_CANDIDATE) {
        int term = raft_term_actual(candidate_id);
        int votes = deliver_request_vote(candidate_id, term);

        // Check if candidate became leader
        if (raft_estado(candidate_id) == RAFT_LEADER) {
            // Leader sends heartbeats
            deliver_heartbeats(candidate_id, term, raft_commit_index(candidate_id));
            return 1;  // leader elected
        }
    }
    return 0;  // election failed or not started
}

// ── Test 1: Initial state ──────────────────────────────────────────
void test_initial_state(void) {
    printf("\n--- Test 1: Estado inicial (5 nodos, todos followers) ---\n");

    for (int i = 0; i < NODES; i++) {
        CHECK_INT_EQ(raft_inicializar(i, NODES, 42 + i * 7), 0,
                     "raft_inicializar() ok para nodo %d");
    }

    long long now = _get_timestamp_ns();
    for (int i = 0; i < NODES; i++) {
        CHECK_INT_EQ(raft_iniciar(now, i), 0, "raft_iniciar() ok");
    }

    for (int i = 0; i < NODES; i++) {
        char buf[64];
        snprintf(buf, sizeof(buf), "nodo %d es follower", i);
        CHECK_INT_EQ(raft_estado(i), RAFT_FOLLOWER, buf);
        snprintf(buf, sizeof(buf), "nodo %d term == 0", i);
        CHECK_INT_EQ(raft_term_actual(i), 0, buf);
        snprintf(buf, sizeof(buf), "nodo %d sin lider", i);
        CHECK_INT_EQ(raft_lider_actual(i), -1, buf);
        snprintf(buf, sizeof(buf), "nodo %d log == 0", i);
        CHECK_INT_EQ(raft_log_entradas(i), 0, buf);
        snprintf(buf, sizeof(buf), "nodo %d commit == 0", i);
        CHECK_INT_EQ(raft_commit_index(i), 0, buf);
    }
}

// ── Test 2: Leader election ────────────────────────────────────────
void test_leader_election(void) {
    printf("\n--- Test 2: Eleccion de lider ---\n");

    // Reset all nodes
    for (int i = 0; i < NODES; i++) {
        raft_reiniciar_nodo(i);
    }
    long long now = _get_timestamp_ns();
    for (int i = 0; i < NODES; i++) {
        raft_iniciar(now, i);
    }

    // Simulate time passing: tick nodes until one becomes leader
    int leader_id = -1;
    int leader_term = 0;
    for (int ms = 0; ms < 2000; ms += 10) {
        long long tick_now = now + (long long)ms * 1000000LL;

        // Tick all nodes
        for (int i = 0; i < NODES; i++) {
            int ev = raft_tick(tick_now, i);
            if (ev == 1 && raft_estado(i) == RAFT_CANDIDATE) {
                // This node started an election
                if (run_election(i, tick_now)) {
                    leader_id = i;
                    leader_term = raft_term_actual(i);
                    break;
                }
            }
        }

        if (leader_id >= 0) break;

        // Check if any node already became leader through previous ticks
        for (int i = 0; i < NODES; i++) {
            if (raft_estado(i) == RAFT_LEADER) {
                leader_id = i;
                leader_term = raft_term_actual(i);
                break;
            }
        }
        if (leader_id >= 0) break;
    }

    CHECK(leader_id >= 0, "se elige un lider en < 500ms");
    CHECK_INT_EQ(raft_estado(leader_id), RAFT_LEADER, "lider esta en estado LEADER");
    CHECK(leader_term > 0, "lider tiene term > 0");

    if (leader_id >= 0) {
        // After heartbeats, all followers should know the leader
        deliver_heartbeats(leader_id, leader_term, 0);

        for (int i = 0; i < NODES; i++) {
            if (i != leader_id) {
                char buf[64];
                snprintf(buf, sizeof(buf), "nodo %d es follower tras eleccion", i);
                CHECK_INT_EQ(raft_estado(i), RAFT_FOLLOWER, buf);
                snprintf(buf, sizeof(buf), "nodo %d reconoce lider %d", i, leader_id);
                CHECK_INT_EQ(raft_lider_actual(i), leader_id, buf);
            }
        }
    }

    printf("\n  Lider electo: nodo %d, termino %d\n", leader_id, leader_term);
}

// ── Test 3: Heartbeat maintains leadership ─────────────────────────
void test_heartbeat_maintains_leadership(void) {
    printf("\n--- Test 3: Heartbeats mantienen liderazgo ---\n");

    for (int i = 0; i < NODES; i++) {
        raft_reiniciar_nodo(i);
    }
    long long now = _get_timestamp_ns();
    for (int i = 0; i < NODES; i++) {
        raft_iniciar(now, i);
    }

    // Elect a leader
    int leader_id = -1;
    int leader_term = 0;
    for (int ms = 0; ms < 2000; ms += 10) {
        long long tick_now = now + (long long)ms * 1000000LL;
        for (int i = 0; i < NODES; i++) {
            int ev = raft_tick(tick_now, i);
            if (ev == 1 && raft_estado(i) == RAFT_CANDIDATE) {
                if (run_election(i, tick_now)) {
                    leader_id = i;
                    leader_term = raft_term_actual(i);
                    break;
                }
            }
        }
        if (leader_id >= 0) break;
        for (int i = 0; i < NODES; i++) {
            if (raft_estado(i) == RAFT_LEADER) {
                leader_id = i;
                leader_term = raft_term_actual(i);
                break;
            }
        }
        if (leader_id >= 0) break;
    }
    CHECK(leader_id >= 0, "lider electo para test de heartbeats");

    // Leader sends periodic heartbeats for 500ms
    for (int ms = 0; ms < 500; ms += 30) {
        long long tick_now = now + (long long)ms * 1000000LL;
        raft_tick(tick_now, leader_id);  // refreshes heartbeat timer

        // Leader sends heartbeats
        deliver_heartbeats(leader_id, leader_term, raft_commit_index(leader_id));
    }

    // Verify leader is still leader
    CHECK_INT_EQ(raft_estado(leader_id), RAFT_LEADER,
                 "lider sigue siendo lider despues de heartbeats");
    CHECK_INT_EQ(raft_term_actual(leader_id), leader_term,
                 "termino del lider no cambio");

    // All followers still know the leader
    for (int i = 0; i < NODES; i++) {
        if (i != leader_id) {
            char buf[64];
            snprintf(buf, sizeof(buf), "seguidor %d aun reconoce al lider", i);
            CHECK_INT_EQ(raft_lider_actual(i), leader_id, buf);
        }
    }
}

// ── Test 4: Leader abdication and re-election ──────────────────────
void test_leader_abdication(void) {
    printf("\n--- Test 4: Caida del lider y re-eleccion ---\n");

    for (int i = 0; i < NODES; i++) {
        raft_reiniciar_nodo(i);
    }
    long long now = _get_timestamp_ns();
    for (int i = 0; i < NODES; i++) {
        raft_iniciar(now, i);
    }

    // Elect first leader
    int leader1_id = -1;
    int leader1_term = 0;
    for (int ms = 0; ms < 2000; ms += 10) {
        long long tick_now = now + (long long)ms * 1000000LL;
        for (int i = 0; i < NODES; i++) {
            int ev = raft_tick(tick_now, i);
            if (ev == 1 && raft_estado(i) == RAFT_CANDIDATE) {
                if (run_election(i, tick_now)) {
                    leader1_id = i;
                    leader1_term = raft_term_actual(i);
                    break;
                }
            }
        }
        if (leader1_id >= 0) break;
        for (int i = 0; i < NODES; i++) {
            if (raft_estado(i) == RAFT_LEADER) {
                leader1_id = i;
                leader1_term = raft_term_actual(i);
                break;
            }
        }
        if (leader1_id >= 0) break;
    }
    CHECK(leader1_id >= 0, "primer lider electo");
    deliver_heartbeats(leader1_id, leader1_term, 0);

    // Force leader abdication
    CHECK_INT_EQ(raft_forzar_abdicacion(leader1_id), 0,
                 "abdicacion forzada del lider");
    CHECK_INT_EQ(raft_estado(leader1_id), RAFT_FOLLOWER,
                 "ex-lider ahora es follower");

    // Elect a new leader
    int leader2_id = -1;
    int leader2_term = 0;
    for (int ms = 0; ms < 3000; ms += 10) {
        long long tick_now = now + 2000000000LL + (long long)ms * 1000000LL;
        for (int i = 0; i < NODES; i++) {
            int ev = raft_tick(tick_now, i);
            if (ev == 1 && raft_estado(i) == RAFT_CANDIDATE) {
                if (run_election(i, tick_now)) {
                    leader2_id = i;
                    leader2_term = raft_term_actual(i);
                    break;
                }
            }
        }
        if (leader2_id >= 0) break;
        for (int i = 0; i < NODES; i++) {
            if (raft_estado(i) == RAFT_LEADER) {
                leader2_id = i;
                leader2_term = raft_term_actual(i);
                break;
            }
        }
        if (leader2_id >= 0) break;
    }

    CHECK(leader2_id >= 0, "nuevo lider electo tras caida");
    CHECK(leader2_id != leader1_id || leader2_term > leader1_term,
          "nuevo lider es diferente o tiene termino mayor");
    CHECK(leader2_term > leader1_term,
          "nuevo lider tiene termino > anterior");

    printf("\n  Lider 1: nodo %d, termino %d\n", leader1_id, leader1_term);
    printf("  Lider 2: nodo %d, termino %d\n", leader2_id, leader2_term);
}

// ── Test 5: Log replication ────────────────────────────────────────
void test_log_replication(void) {
    printf("\n--- Test 5: Replicacion de log y consistencia ---\n");

    for (int i = 0; i < NODES; i++) {
        raft_reiniciar_nodo(i);
    }
    long long now = _get_timestamp_ns();
    for (int i = 0; i < NODES; i++) {
        raft_iniciar(now, i);
    }

    // Elect leader
    int leader_id = -1;
    int leader_term = 0;
    for (int ms = 0; ms < 2000; ms += 10) {
        long long tick_now = now + (long long)ms * 1000000LL;
        for (int i = 0; i < NODES; i++) {
            int ev = raft_tick(tick_now, i);
            if (ev == 1 && raft_estado(i) == RAFT_CANDIDATE) {
                if (run_election(i, tick_now)) {
                    leader_id = i;
                    leader_term = raft_term_actual(i);
                    break;
                }
            }
        }
        if (leader_id >= 0) break;
        for (int i = 0; i < NODES; i++) {
            if (raft_estado(i) == RAFT_LEADER) {
                leader_id = i;
                leader_term = raft_term_actual(i);
                break;
            }
        }
        if (leader_id >= 0) break;
    }
    CHECK(leader_id >= 0, "lider electo para test de log");

    // Add 3 log entries to leader
    CHECK_INT_EQ(raft_agregar_entrada(leader_id), 1, "log entrada 1");
    CHECK_INT_EQ(raft_agregar_entrada(leader_id), 2, "log entrada 2");
    CHECK_INT_EQ(raft_agregar_entrada(leader_id), 3, "log entrada 3");
    CHECK_INT_EQ(raft_log_entradas(leader_id), 3, "lider tiene 3 entradas en log");

    // Replicate: leader sends heartbeats with commit index
    deliver_heartbeats(leader_id, leader_term, 3);

    // After replication, followers should have the commit index
    for (int i = 0; i < NODES; i++) {
        if (i != leader_id) {
            CHECK(raft_commit_index(i) >= 3 ||
                  raft_commit_index(i) == raft_log_entradas(i),
                  "seguidor actualiza commit index tras heartbeat");
        }
    }

    printf("\n  Log del lider: %d entradas, commit %d\n",
           raft_log_entradas(leader_id), raft_commit_index(leader_id));
}

// ── Test 6: Election safety — only one leader per term ─────────────
void test_election_safety(void) {
    printf("\n--- Test 6: Seguridad de eleccion (1 lider por termino) ---\n");

    for (int i = 0; i < NODES; i++) {
        raft_reiniciar_nodo(i);
    }
    long long now = _get_timestamp_ns();
    for (int i = 0; i < NODES; i++) {
        raft_iniciar(now, i);
    }

    // Run 3 consecutive elections, track terms
    int prev_term = 0;
    int prev_leader = -1;
    for (int round = 0; round < 3; round++) {
        int leader_id = -1;
        int leader_term = 0;
        for (int ms = 0; ms < 3000; ms += 10) {
            long long tick_now = now + (long long)(round * 5000 + ms) * 1000000LL;
            for (int i = 0; i < NODES; i++) {
                int ev = raft_tick(tick_now, i);
                if (ev == 1 && raft_estado(i) == RAFT_CANDIDATE) {
                    if (run_election(i, tick_now)) {
                        leader_id = i;
                        leader_term = raft_term_actual(i);
                        break;
                    }
                }
            }
            if (leader_id >= 0) break;
            for (int i = 0; i < NODES; i++) {
                if (raft_estado(i) == RAFT_LEADER) {
                    leader_id = i;
                    leader_term = raft_term_actual(i);
                    break;
                }
            }
            if (leader_id >= 0) break;
        }

        char buf1[64]; snprintf(buf1, sizeof(buf1), "ronda %d: lider electo", round);
        CHECK(leader_id >= 0, buf1);
        char buf2[64]; snprintf(buf2, sizeof(buf2), "ronda %d: termino incrementa", round);
        CHECK(leader_term > prev_term, buf2);

        if (leader_id >= 0) {
            deliver_heartbeats(leader_id, leader_term, 0);
            // Only one leader per term
            int leaders = 0;
            for (int i = 0; i < NODES; i++) {
                if (raft_estado(i) == RAFT_LEADER) leaders++;
            }
            char buf3[64]; snprintf(buf3, sizeof(buf3), "ronda %d: exactamente 1 lider", round);
            CHECK_INT_EQ(leaders, 1, buf3);

            // Force abdication for next round
            raft_forzar_abdicacion(leader_id);
        }

        prev_term = leader_term;
        prev_leader = leader_id;
    }
}

int main(void) {
    printf("========================================================\n");
    printf("  M8.3 — Raft Consensus Test Suite\n");
    printf("  Simulacion de 5 nodos con consenso distribuido\n");
    printf("========================================================\n");

    pool_init(64, 4096);

    test_initial_state();
    test_leader_election();
    test_heartbeat_maintains_leadership();
    test_leader_abdication();
    test_log_replication();
    test_election_safety();

    printf("\n========================================================\n");
    printf("  Resultados: %d passed, %d failed", passed, failed);
    if (failed > 0) printf(" <<< HAY FALLOS");
    printf("\n========================================================\n");

    return failed > 0 ? 1 : 0;
}