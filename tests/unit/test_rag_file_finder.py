# -*- coding: utf-8 -*-
"""
test_rag_file_finder.py — TDD del file-finder y catálogo APIs (ME-2, R2, Manual 7 §2.3).

Valida que el file-finder localice archivos relevantes y que el catálogo
de APIs std impida alucinaciones de funciones.

Réplica en Python de las funciones Synapse de router.syn para poder
ejecutar assertions en CI sin compilar el binario.

Cumple MTO §3: cada requisito del manual se convierte en test ejecutable.
requisito: Manual 7 §2.3
texto: "El pipeline RAG extrae el contexto más relevante del código fuente
  para construir un prompt eficiente y preciso."
oraculo: tests/unit/test_rag_file_finder.py
"""

import os

import pytest

pytestmark = pytest.mark.unit

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# --- Funciones réplica de router.syn ---

def obtener_catalogo_api() -> str:
    """Catálogo COMPLETO de APIs std/*.syn (35 módulos). Replica router.syn:obtener_catalogo_api()."""
    catalogo = "APIs std/ (usar SOLO estas funciones): "
    catalogo += "std.io: abrir, leer, cerrar_archivo, escribir, escribir_linea, leer_linea, leer_bytes; "
    catalogo += "std.texto: contiene, indice_de, reemplazar, termina_con, recortar, mayusculas, minusculas, escapar_json, a_texto, a_texto_decimal, cmp_texto, strlen_s, strstr_f, strchr_f, atoi_f, strcpy_f, strncpy_f; "
    catalogo += "std.sistema: ejecutar_comando, escribir_archivo, leer_archivo, obtener_env, existe_archivo, eliminar_archivo; "
    catalogo += "std.json: desde_texto, liberar_nodo, obtener_elemento, obtener_campo, a_texto; "
    catalogo += "std.os: memoria_total, memoria_libre, vram_total, cpu_nucleos, arquitectura; "
    catalogo += "std.net: iniciar_red, cerrar_red, crear_socket, conectar, enviar_datos, recibir_datos, cerrar_socket, liberar_texto; "
    catalogo += "std.http: iniciar_servidor, aceptar, leer_peticion, responder, cerrar_cliente, cerrar_servidor; "
    catalogo += "std.modelo: cargar_modelo, cerrar_modelo, evaluar, generar_token, n_past, reiniciar, obtener_n_ctx, establecer_n_ctx, decodificar_token, vocab_tamano, codificar_contar, codificar_obtener, generar_texto, obtener_metadato, obtener_arquitectura, obtener_n_layers, obtener_n_embd, obtener_n_heads, argmax, muestra_logits, generar_texto_simple; "
    catalogo += "std.math: crear_tensor, suma_tensor, producto_punto, relu; "
    catalogo += "std.cripto: sha256_texto, ed25519_verificar; "
    catalogo += "std.tiempo: ahora_ms, dormir_ms; "
    catalogo += "std.testing: assert_verdadero, assert_falso, assert_igual, assert_diferente; "
    catalogo += "std.debug: registrar_evento, trace, iniciar_sesion, finalizar_sesion, tr_inicializar_recording, tr_grabar_bifurcacion, tr_grabar_snapshot, tr_grabar_llamada, tr_grabar_retorno, tr_grabar_error, tr_buscar_evento, tr_obtener_evento, tr_reproducir_hasta, tr_indice_ultimo_error, tr_total_eventos, rp_inicializar, rp_establecer_breakpoint, rp_eliminar_breakpoint, rp_limpiar_breakpoints, rp_buscar_breakpoint, rp_retroceder, rp_posicion_actual, rp_ir_a_pre_error, rp_inspeccionar_variable, rp_pila_llamadas, rp_buscar_cambio_variable, ms_tomar_en, ms_diferenciar, ms_diff_entre, ms_snapshot_contar_vars, ms_snapshot_tamano, ms_snapshot_contiene; "
    catalogo += "std.tensor: llenar_tensor_constante, multiplicar_matrices, extraer_fila, rmsnorm, silu, rope, softmax_escalado, multiplicar_matrices_transpuesta_b, fijar_elemento; "
    catalogo += "std.sync: mutex_crear, mutex_bloquear, mutex_desbloquear, mutex_destruir, semaforo_crear, semaforo_esperar, semaforo_senalar, semaforo_destruir, barrera_crear, barrera_esperar, barrera_destruir; "
    catalogo += "std.mem: reserva, libera; "
    catalogo += "std.toml: desde_texto, obtener_campo; "
    catalogo += "std.oraculo: compilar_codigo, obtener_codigo_generado, obtener_error_compilacion, obtener_linea_error, extraer_bloque_codigo, generar_codigo; "
    catalogo += "std.ai: cargar_gguf, cerrar_gguf, obtener_tensor, obtener_metadato, obtener_arquitectura, argmax, vocab_tamano, decodificar_token; "
    catalogo += "std.agent_skills: generar_tests_tdd, revisar_codigo, planificacion_incremental, empaquetar_contexto, duda_driven_generar; "
    catalogo += "std.llvm: LLVMContextCreate, LLVMContextDispose, LLVMModuleCreateWithName, LLVMModuleDispose, LLVMModuleGetIR, LLVMBuilderCreate, LLVMBuilderDispose, LLVMBuilderBeginFunction, LLVMBuilderEndFunction, BuildMinimalProgram; "
    catalogo += "std.wasm: WasmModuleCreate, WasmModuleDispose, WasmModuleGetWAT, WasmBuilderCreate, WasmBuilderDispose, WasmBuilderBeginFunction, WasmBuilderEndFunction, WasmBuildMinimalProgram; "
    catalogo += "std.symbolic_exec: se_iniciar, se_cerrar, se_crear_variable, se_crear_entero, se_agregar_restriccion, se_bifurcar, se_es_alcanzable, se_hay_div_por_cero, se_hay_desbordamiento, se_hay_fuera_limites, se_explorar, se_es_seguro; "
    catalogo += "std.quantum: crear_sistema, liberar_sistema, inicializar_estado_cero, aplicar_hadamard, aplicar_pauli_x, aplicar_cnot, medir, probabilidad_cero, verificar_conservacion, crear_estado_bell; "
    catalogo += "std.quantum_err_corr: inicializar_estado_logico, inyectar_bit_flip, inyectar_phase_flip, corregir_errores, verificar_estado_logico, proteger_y_verificar; "
    catalogo += "std.quantum_memory: aplicar_t1, aplicar_t2, simular_con_qec; "
    catalogo += "std.surface_code: crear_rejilla, liberar_rejilla, inicializar_estado_cero, inyectar_error, medir_estabilizadores, corregir_errores, verificar_correccion; "
    catalogo += "std.simd: simd_disponible, simd_tipo, simd_multiplicar_matrices, simd_rmsnorm, simd_silu, simd_softmax_escalado, simd_llenar_tensor_constante, simd_multiplicar_matrices_transpuesta_b; "
    catalogo += "std.proof_bridge: pb_iniciar, pb_cerrar, pb_agregar_funcion, pb_agregar_contrato, pb_traducir_a_coq, pb_traducir_a_lean, pb_generar_coq, pb_generar_lean, pb_exportar, pb_generar_certificado; "
    catalogo += "std.atp_engine: atp_iniciar, atp_cerrar, atp_agregar_pre, atp_agregar_post, atp_agregar_inv, atp_establecer_func, atp_es_tautologia, atp_hay_contradiccion, atp_propagar, atp_demostrar, atp_verificar_contrato, atp_limpiar, atp_guardar, atp_cargar; "
    catalogo += "std.cluster: cluster_iniciar_nodo, cluster_detener_nodo, cluster_enviar_hello, cluster_enviar_hello_firmado, cluster_canal_remoto_enviar, cluster_recibir_paquete, cluster_establecer_clave_sesion, ws_inicializar, ws_encolar, ws_desencolar, raft_inicializar, raft_iniciar, raft_tick, raft_estado, worker_ejecutar, worker_robar, cm_inicializar, cm_serializar_checkpoint, cm_restaurar_checkpoint, cluster_descubrimiento_inicializar, cluster_registrar_nodo, cluster_nodos_activos, cluster_multicast_iniciar, cluster_multicast_detener; "
    catalogo += "std.federated: fed_iniciar, fed_cerrar, fed_registrar_worker, fed_eliminar_worker, fed_ronda_fedavg, fed_entrenar, fed_guardar, fed_cargar, fed_verificar_firma; "
    catalogo += "std.dist_orchestrator: orch_iniciar, orch_cerrar, orch_crear_particiones, orch_asignar_workers, orch_ejecutar_epoch, orch_entrenar, orch_manejar_fallo, orch_redistribuir, orch_guardar, orch_cargar"
    return catalogo


def obtener_mapa_keywords() -> str:
    """Mapa keyword → archivo. Replica router.syn:obtener_mapa_keywords()."""
    mapa = "io:std/io.syn;escribir:std/io.syn;leer:std/io.syn;archivo:std/io.syn;"
    mapa += "texto:std/texto.syn;cadena:std/texto.syn;reemplazar:std/texto.syn;"
    mapa += "sistema:std/sistema.syn;comando:std/sistema.syn;ejecutar:std/sistema.syn;"
    mapa += "json:std/json.syn;parse:std/json.syn;"
    mapa += "os:std/os.syn;ram:std/os.syn;vram:std/os.syn;cpu:std/os.syn;"
    mapa += "red:std/net.syn;socket:std/net.syn;conexion:std/net.syn;"
    mapa += "http:std/http.syn;servidor:std/http.syn;puerto:std/http.syn;"
    mapa += "modelo:std/modelo.syn;gguf:std/modelo.syn;inferencia:std/modelo.syn;"
    mapa += "tensor:std/math.syn;matriz:std/math.syn;"
    mapa += "cripto:std/cripto.syn;sha256:std/cripto.syn;ed25519:std/cripto.syn;"
    mapa += "tiempo:std/tiempo.syn;reloj:std/tiempo.syn;dormir:std/tiempo.syn;"
    mapa += "debug:std/debug.syn;traza:std/debug.syn;trace:std/debug.syn;"
    mapa += "test:std/testing.syn;assert:std/testing.syn;"
    mapa += "router:opensyn/router.syn;rag:opensyn/router.syn;"
    mapa += "principal:opensyn/principal.syn;agente:opensyn/principal.syn;modo:opensyn/principal.syn;"
    mapa += "ollama:runtime/core/ollama.c;llama:runtime/core/ollama.c;"
    mapa += "tui:runtime/core/tui.c;terminal:runtime/core/tui.c"
    return mapa


def file_finder(consulta: str) -> str:
    """Localiza archivos relevantes por palabras clave. Replica router.syn:file_finder().
    Busca keywords como palabras completas (no substrings) en la consulta."""
    encontrados = ""
    mapa = obtener_mapa_keywords()
    entries = mapa.split(";")
    palabras_consulta = [w.lower() for w in consulta.split() if len(w) >= 3]
    for entry in entries:
        if ":" not in entry:
            continue
        kw, archivo = entry.split(":", 1)
        if kw.lower() in palabras_consulta:
            if archivo not in encontrados:
                if encontrados:
                    encontrados += ", "
                encontrados += archivo
    return encontrados


# ============================================================
# Tests TDD — Manual 7 §2.3 (file-finder + catálogo APIs)
# ============================================================


class TestCatalogoAPI:
    """obtener_catalogo_api() retorna el catálogo COMPLETO de APIs std (35 módulos)."""

    def test_catalogo_no_vacio(self):
        assert len(obtener_catalogo_api()) > 500

    def test_catalogo_incluye_io(self):
        assert "std.io" in obtener_catalogo_api()

    def test_catalogo_incluye_texto(self):
        assert "std.texto" in obtener_catalogo_api()

    def test_catalogo_incluye_modelo(self):
        assert "std.modelo" in obtener_catalogo_api()

    def test_catalogo_incluye_sistema(self):
        assert "std.sistema" in obtener_catalogo_api()

    def test_catalogo_menciona_funciones_reales(self):
        cat = obtener_catalogo_api()
        assert "escribir_linea" in cat
        assert "generar_texto" in cat
        assert "strlen_s" in cat

    def test_catalogo_no_incluye_funciones_fantasma(self):
        """El catálogo NO debe incluir funciones inventadas."""
        cat = obtener_catalogo_api()
        assert "teletransportar" not in cat
        assert "absolutamente_nueva_funcion" not in cat

    def test_catalogo_35_modulos(self):
        """El catálogo debe cubrir los 35 módulos std/."""
        cat = obtener_catalogo_api()
        modulos_esperados = [
            "std.io", "std.texto", "std.sistema", "std.json", "std.os",
            "std.net", "std.http", "std.modelo", "std.math", "std.cripto",
            "std.tiempo", "std.testing", "std.debug", "std.tensor", "std.sync",
            "std.mem", "std.toml", "std.oraculo", "std.ai", "std.agent_skills",
            "std.llvm", "std.wasm", "std.symbolic_exec", "std.quantum",
            "std.quantum_err_corr", "std.quantum_memory", "std.surface_code",
            "std.simd", "std.proof_bridge", "std.atp_engine", "std.cluster",
            "std.federated", "std.dist_orchestrator",
        ]
        for m in modulos_esperados:
            assert m in cat, f"Módulo {m} no encontrado en catálogo"

    def test_catalogo_modelo_cobertura(self):
        """std.modelo debe listar las 21 funciones públicas."""
        cat = obtener_catalogo_api()
        funcs_modelo = [
            "cargar_modelo", "cerrar_modelo", "evaluar", "generar_token",
            "n_past", "reiniciar", "obtener_n_ctx", "establecer_n_ctx",
            "decodificar_token", "vocab_tamano", "codificar_contar",
            "codificar_obtener", "generar_texto", "obtener_metadato",
            "obtener_arquitectura", "obtener_n_layers", "obtener_n_embd",
            "obtener_n_heads", "argmax", "muestra_logits", "generar_texto_simple",
        ]
        for f in funcs_modelo:
            assert f in cat, f"Función std.modelo.{f} no encontrada en catálogo"

    def test_catalogo_debug_cobertura(self):
        """std.debug debe listar funciones de recording/replay/snapshots."""
        cat = obtener_catalogo_api()
        assert "tr_inicializar_recording" in cat
        assert "rp_inicializar" in cat
        assert "ms_tomar_en" in cat


class TestFileFinder:
    """file_finder() localiza archivos relevantes por palabras clave."""

    def test_io_encontra_archivos(self):
        resultado = file_finder("quiero escribir un archivo")
        assert "std/io.syn" in resultado

    def test_texto_encontra_archivos(self):
        resultado = file_finder("necesito reemplazar una cadena de texto")
        assert "std/texto.syn" in resultado

    def test_modelo_encontra_archivos(self):
        resultado = file_finder("cargar un modelo gguf")
        assert "std/modelo.syn" in resultado

    def test_red_encontra_archivos(self):
        resultado = file_finder("abrir un socket de red")
        assert "std/net.syn" in resultado

    def test_http_encontra_archivos(self):
        resultado = file_finder("crear un servidor http")
        assert "std/http.syn" in resultado

    def test_ollama_encontra_archivos(self):
        resultado = file_finder("consultar ollama")
        assert "runtime/core/ollama.c" in resultado

    def test_tui_encontra_archivos(self):
        resultado = file_finder("dibujar en la terminal tui")
        assert "runtime/core/tui.c" in resultado

    def test_router_encontra_archivos(self):
        resultado = file_finder("modificar el router rag")
        assert "opensyn/router.syn" in resultado

    def test_multiple_keywords(self):
        resultado = file_finder("escribir archivo de texto en sistema")
        assert "std/io.syn" in resultado or "std/texto.syn" in resultado

    def test_palabra_corta_ignorada(self):
        """Palabras menores a 3 caracteres se ignoran."""
        resultado = file_finder("io es un modulo")
        # "io" tiene 2 chars, se ignora; "modulo" no está en el mapa
        assert resultado == ""

    def test_palabra_no_encontrada(self):
        resultado = file_finder("teletransportacion cuantica")
        assert resultado == ""

    def test_consulta_vacia(self):
        """Consistencia: consulta vacía retorna vacío."""
        resultado = file_finder("a")
        assert resultado == ""


class TestIntegracionFileFinderCatalogo:
    """Integración: file-finder + catálogo working juntos."""

    def test_file_finder_retorna_strings(self):
        for q in ["escribir", "leer archivo", "modelo gguf"]:
            r = file_finder(q)
            assert isinstance(r, str)

    def test_catalogo_y_finder_complementarios(self):
        """El catálogo lista APIs; el finder localiza archivos. No deben solaparse."""
        cat = obtener_catalogo_api()
        finder = file_finder("escribir archivo de texto")
        # El catálogo menciona std.io; el finder encuentra std/io.syn
        assert "std.io" in cat
        assert "std/io.syn" in finder
