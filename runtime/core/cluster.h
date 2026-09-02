// cumple Manual 6 7: cluster runtime
// synapse_rt_cluster.h — Public API of runtime/core/cluster.c
// Extraido de synapse_rt.c (deuda D-9(d), corte 4 tras modelo.c R39).
#ifndef SYNAPSE_RT_CLUSTER_H
#define SYNAPSE_RT_CLUSTER_H

#include "synapse_rt_types.h"

#ifdef __cplusplus
extern "C" {
#endif

// M8.1 transporte (UDP + Ed25519)
CadenaSegura cluster_generar_par_claves(void);
CadenaSegura cluster_firmar_mensaje(CadenaSegura mensaje, CadenaSegura clave_privada_hex);
int cluster_verificar_firma(CadenaSegura mensaje, CadenaSegura firma_hex, CadenaSegura clave_publica_hex);
int cluster_iniciar_nodo(int puerto);
int cluster_detener_nodo(void);
int cluster_enviar_hello(const char* ip, int puerto, CadenaSegura id_origen, CadenaSegura pubkey_hex);
CadenaSegura cluster_generar_nonce(void);
int cluster_enviar_hello_firmado(const char* ip, int puerto, CadenaSegura id_origen, CadenaSegura pubkey_hex, CadenaSegura nonce_hex, CadenaSegura firma_hex);
int cluster_canal_remoto_enviar(const char* ip, int puerto, const char* datos, int lon, int chan_id);
CadenaSegura cluster_recibir_paquete(int timeout_ms);
void cluster_establecer_clave_sesion(const char* pubkey_local_hex, const char* pubkey_remota_hex);
void cluster_limpiar_clave_sesion(void);
// R78 — derivación de clave de sesión crypto_kx-equivalente (Manual 5 §6.2 paso 3)
int cluster_kx_secreto_compartido(const unsigned char* sk_local, const unsigned char* pk_local,
                                   const char* kx_pk_remota_hex, int rol_cliente,
                                   unsigned char* clave_out32);
int cluster_kx_par(char* pk_hex_out65, unsigned char* sk_out32);
CadenaSegura cluster_kx_generar_par(void);
int cluster_kx_derivar(const char* kx_pk_remota_hex, int rol_cliente);
CadenaSegura cluster_clave_sesion_hex(void);
int cluster_enviar_kx_init(const char* ip, int puerto, CadenaSegura kx_pk_hex, CadenaSegura firma_hex);
// R83 — AEAD del transporte (Manual 6 §5.3 "DATOS_CIFRADOS"): XSalsa20-Poly1305
// con la clave de sesión; formato cifrado = [nonce 24B][MAC 16B][ciphertext].
// descifrar retorna -2 si la MAC no valida (tamper/clave incorrecta).
int cluster_sesion_cifrar_buffer(const unsigned char* clave32, const char* entrada,
                                  int lon, char* salida, int* lon_salida);
int cluster_sesion_descifrar_buffer(const unsigned char* clave32, const char* entrada,
                                     int lon, char* salida, int* lon_salida);
int ws_inicializar(int capacidad);
int ws_encolar(int id, CadenaSegura datos);
CadenaSegura ws_desencolar(void);
int ws_profundidad(void);
int ws_carga_estimada(void);
int ws_enviar_solicitud_robo(CadenaSegura ip, int puerto);
CadenaSegura ws_procesar_mensaje(CadenaSegura paquete);
CadenaSegura ws_ultima_robada(void);
int ws_reenviar_respuesta(CadenaSegura ip, int puerto, CadenaSegura respuesta);
int raft_inicializar(int node_id, int num_nodes, int seed);
int raft_iniciar(long long tiempo_actual_ns, int node_id);
int raft_estado(int node_id);
int raft_term_actual(int node_id);
int raft_lider_actual(int node_id);
int raft_log_entradas(int node_id);
int raft_commit_index(int node_id);
int raft_firmar_mensaje(int node_id, const char* msg, int msg_len, char* firma_out);
int raft_verificar_firma_rpc(const char* msg, int msg_len, const char* firma_hex, const char* pk_hex);
int raft_procesar_solicitud_voto(int voter_id, int candidate_term, int candidate_id, int candidate_last_log, int candidate_last_log_term);
int raft_procesar_respuesta_voto(int candidate_id, int responder_term, int responder_id, int granted);
int raft_procesar_heartbeat(int follower_id, int leader_term, int leader_id, int leader_commit);
int raft_tick(long long tiempo_actual_ns, int node_id);
int raft_forzar_abdicacion(int node_id);
int raft_agregar_entrada(int node_id);
int raft_reiniciar_nodo(int node_id);
CadenaSegura raft_info(int node_id);
int cm_inicializar(void);
CadenaSegura cm_serializar_checkpoint(int task_id, CadenaSegura datos);
CadenaSegura cm_deserializar_checkpoint(CadenaSegura checkpoint_str, int* out_task_id, int* out_seq);
int cm_verificar_integridad(CadenaSegura checkpoint_str);
int cm_restaurar_checkpoint(CadenaSegura checkpoint_str);
CadenaSegura cm_migrar_tarea(CadenaSegura datos_debug);
int cm_migrar_entre_nodos(CadenaSegura ip_destino, int puerto_destino);
CadenaSegura cm_ultima_migracion(void);
int cm_migraciones_completadas(void);
int cm_migraciones_fallidas(void);
int cluster_descubrimiento_inicializar(int max_nodos);
int cluster_descubrimiento_detener(void);
int cluster_registrar_nodo(CadenaSegura id, CadenaSegura ip, int puerto, CadenaSegura pubkey);
int cluster_eliminar_nodo(CadenaSegura id);
int cluster_nodos_activos(void);
int cluster_total_nodos(void);
CadenaSegura cluster_obtener_nodo(int idx);
int cluster_heartbeat_inicializar(int intervalo_s, int timeout_s);
int cluster_tick_heartbeat(int tiempo_actual_s);
int cluster_recibir_heartbeat(CadenaSegura id);
CadenaSegura cluster_generar_anuncio(CadenaSegura id, CadenaSegura ip, int puerto, CadenaSegura pubkey);
int cluster_procesar_anuncio(CadenaSegura paquete);
CadenaSegura cluster_info_membresia_como_texto(void);
int cluster_verificar_salud_nodo(CadenaSegura id);
int cluster_ultimo_tick_heartbeat(void);
CadenaSegura cluster_info_heartbeat(void);
int cluster_multicast_iniciar(const char* grupo, int puerto);
int cluster_multicast_detener(void);
int cluster_anunciar_por_multicast(CadenaSegura id, CadenaSegura ip_host, int puerto_host, CadenaSegura pubkey);
int cluster_escuchar_multicast(int timeout_ms);
int cluster_iniciar_hilo_descubrimiento(CadenaSegura id, CadenaSegura ip_host, int puerto_host, CadenaSegura pubkey, int intervalo_s);
int cluster_detener_hilo_descubrimiento(void);
int cluster_hilo_descubrimiento_activo(void);
CadenaSegura cluster_multicast_info(void);

#ifdef __cplusplus
}
#endif

#endif /* SYNAPSE_RT_CLUSTER_H */