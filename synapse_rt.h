// synapse_rt.h — Public API del runtime Synapse (modular)
#ifndef SYNAPSE_RT_H
#define SYNAPSE_RT_H

#include "synapse_rt_types.h"

void escribir(CadenaSegura contenido);
void escribir_linea(CadenaSegura contenido);
CadenaSegura leer_linea(void);
Canal abrir(CadenaSegura ruta, CadenaSegura modo);
CadenaSegura leer(Canal canal);
void cerrar(Canal canal);

Tensor crear_tensor(int filas, int columnas);
Tensor suma_tensor(Tensor a, Tensor b);
Tensor producto_punto(Tensor a, Tensor b);
Tensor relu(Tensor a);
Tensor suma(Tensor a, Tensor b);
Tensor producto(Tensor a, Tensor b);

Tensor reserva(int tamano);
void libera(Tensor bloque);

int64_t texto_a_entero(CadenaSegura str);
double texto_a_decimal(CadenaSegura str);
CadenaSegura decimal_a_texto(double n);
CadenaSegura entero_a_texto(int64_t n);

// --- CanalConcurrencia API (Zero-Copy, Thread-Safe) ---
CanalConcurrencia* canal_crear(uint32_t capacidad);
void canal_enviar(CanalConcurrencia* canal, void* paquete);
void* canal_recibir(CanalConcurrencia* canal);
void canal_destruir(CanalConcurrencia* canal);
void cerrar_canal(CanalConcurrencia* canal);

void synapse_lanzar_hilo(void* (*fn)(void*), void* arg);
void synapse_esperar_hilos(void);
void synapse_esperar_fibras(void);

// --- Primitivas de sincronización (Manual 5 §5, F4.5) ---
// Implementación fiber-aware: una fibra bloqueada se parquea en el scheduler
// (F4.2) en vez de bloquear a su worker; los hilos OS usan cond_wait.
Mutex* mutex_crear(void);
void mutex_bloquear(Mutex* m);
void mutex_desbloquear(Mutex* m);
void mutex_destruir(Mutex* m);
Semaforo* semaforo_crear(int valor);
void semaforo_esperar(Semaforo* s);
void semaforo_señalar(Semaforo* s);
void semaforo_destruir(Semaforo* s);
Barrera* barrera_crear(int total);
void barrera_esperar(Barrera* b);
void barrera_destruir(Barrera* b);

#endif
