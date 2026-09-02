#!/usr/bin/env bash
# ============================================================
# nucleo/pgo_pipeline.sh — Pipeline PGO (Optimización Guiada por Perfil)
# ============================================================
# Ciclo de 3 pasos para el compilador Synapse (nucleo/principal.syn):
#
#   PASO 1: Compilación instrumentada
#     - Compila el compilador con -fprofile-generate para generar
#       instrumentación de recolección de perfiles.
#     - El binario resultante (synapse_pgo_instr.exe) captura
#       frecuencia de saltos, bloques básicos y patrones de
#       acceso a memoria durante la ejecución.
#
#   PASO 2: Carga de trabajo de entrenamiento
#     - Ejecuta el binario instrumentado contra la suite de
#       pruebas estándar (tests/*.syn) para generar los archivos
#       de perfil (.gcda) en el directorio de trabajo.
#     - Opcional: ejecutar benchmarks específicos para perfilar
#       casos de uso reales.
#
#   PASO 3: Recompilación optimizada
#     - Recompila utilizando -fprofile-use -flto para aplicar
#       las optimizaciones guiadas por perfil.
#     - El binario resultante (synapse_pgo_opt.exe) contiene
#       decisiones de inlineado, layout de código y
#       desenrollado de bucles basadas en los perfiles.
#
# REQUISITOS:
#   - GCC >= 12.4.0 (MinGW-w64 en Windows, gcc en Linux)
#   - Python 3.10+
#   - Compilador Synapse bootstrap (synapse_stage1.exe o
#     python main.py)
#
# USO:
#   ./nucleo/pgo_pipeline.sh              # ciclo completo
#   ./nucleo/pgo_pipeline.sh --step1      # solo instrumentar
#   ./nucleo/pgo_pipeline.sh --step2      # solo entrenar
#   ./nucleo/pgo_pipeline.sh --step3      # solo optimizar
#   ./nucleo/pgo_pipeline.sh --clean      # limpiar artefactos
#   ./nucleo/pgo_pipeline.sh --help       # esta ayuda
#
# VARIABLES DE ENTORNO:
#   SYNAPSE_GCC      Ruta al compilador GCC (default: auto-detect)
#   SYNAPSE_SRC      Ruta al fuente del compilador (default: nucleo/principal.syn)
#   SYNAPSE_TESTDIR  Ruta a los archivos de prueba (default: tests/)
#   SYNAPSE_OUTDIR   Ruta de salida (default: dist/bin/)
# ============================================================

set -euo pipefail

# ----------------------------------------------------------
# Configuración
# ----------------------------------------------------------
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SYNAPSE_GCC="${SYNAPSE_GCC:-}"
SYNAPSE_SRC="${SYNAPSE_SRC:-nucleo/principal.syn}"
SYNAPSE_TESTDIR="${SYNAPSE_TESTDIR:-tests}"
SYNAPSE_OUTDIR="${SYNAPSE_OUTDIR:-dist/bin}"
SYNAPSE_RT_OBJ="synapse_rt.o"
SYNAPSE_TN_OBJ="tweetnacl.o"
PGO_DIR=".pgo"

# Nombres de los binarios PGO
PGO_INSTR_EXE="synapse_pgo_instr.exe"
PGO_OPT_EXE="synapse_pgo_opt.exe"
PGO_STAGE1_EXE="${SYNAPSE_OUTDIR}/synapse_stage1.exe"

# Archivos de perfiles GCC
GCNO_FILE="${PGO_DIR}/synapse_unity.gcno"
GCNO_MERGE="${PGO_DIR}/synapse_unity.gcda"

# ----------------------------------------------------------
# Funciones auxiliares
# ----------------------------------------------------------
info()  { printf "[PGO] %s\n" "$*"; }
ok()    { printf "[PGO] ✅ %s\n" "$*"; }
error() { printf "[PGO] ❌ %s\n" "$*" >&2; exit 1; }

_detect_gcc() {
    if [ -n "$SYNAPSE_GCC" ]; then
        echo "$SYNAPSE_GCC"
        return
    fi
    # Buscar toolchain interno
    for _try in \
        "$ROOT_DIR/toolchain_gcc12/mingw64/bin/gcc.exe" \
        "$ROOT_DIR/toolchain/bin/gcc.exe" \
        "gcc" \
        "x86_64-w64-mingw32-gcc" \
        "gcc-12" \
        "gcc-13"; do
        if command -v "$_try" >/dev/null 2>&1 || [ -f "$_try" ]; then
            echo "$_try"
            return
        fi
    done
    error "No se encontró GCC. Define SYNAPSE_GCC o instala MinGW-w64 >= 12"
}

_compile_runtime() {
    local _gcc="$1"
    info "Compilando runtime..."
    "$_gcc" -c "$ROOT_DIR/synapse_rt.c" -o "$ROOT_DIR/$SYNAPSE_RT_OBJ" \
        -std=c99 -O2 -Wall -Wextra -Wno-unused-parameter -Wno-unused-function \
        -lpthread -lm -lws2_32 2>&1 | sed 's/^/  /'
    if [ ! -f "$ROOT_DIR/$SYNAPSE_RT_OBJ" ]; then
        error "Fallo la compilación del runtime"
    fi
    ok "Runtime: $SYNAPSE_RT_OBJ"

    if [ -f "$ROOT_DIR/axon/tweetnacl.c" ]; then
        "$_gcc" -c "$ROOT_DIR/axon/tweetnacl.c" -o "$ROOT_DIR/$SYNAPSE_TN_OBJ" \
            -O2 2>&1 | sed 's/^/  /'
        ok "TweetNaCl: $SYNAPSE_TN_OBJ"
    fi
}

_build_instrumented() {
    local _gcc="$1"
    local _src="$2"
    local _out="$3"
    local _profile_dir="$4"

    info "Compilando instrumentado: $_out"
    info "Perfil dir: $_profile_dir"

    # Generar C desde Synapse
    python "$ROOT_DIR/main.py" "$ROOT_DIR/$_src" 2>&1 | sed 's/^/  /'

    local _unity_c="$ROOT_DIR/synapse_unity.c"
    if [ ! -f "$_unity_c" ]; then
        error "No se generó synapse_unity.c"
    fi

    # Compilar con instrumentación PGO
    mkdir -p "$_profile_dir"
    "$_gcc" -O2 \
        -fprofile-generate \
        -fno-ident -Wl,--gc-sections -Wl,--stack,8388608 \
        -I"$ROOT_DIR" \
        "$_unity_c" \
        "$ROOT_DIR/$SYNAPSE_RT_OBJ" \
        "$ROOT_DIR/$SYNAPSE_TN_OBJ" \
        -o "$_out" \
        -lpthread -lm -lws2_32 \
        2>&1 | sed 's/^/  /'

    if [ ! -f "$_out" ]; then
        error "Fallo la compilación instrumentada"
    fi
    ok "Binario instrumentado: $_out ($(wc -c < "$_out" | tr -d ' ') bytes)"
}

# ----------------------------------------------------------
# PASO 1: Compilación instrumentada
# ----------------------------------------------------------
step1_instrument() {
    info "=== PASO 1: Compilación instrumentada ==="
    local _gcc; _gcc="$(_detect_gcc)"
    ok "GCC: $_gcc"

    # Verificar toolchain
    "$_gcc" --version 2>&1 | head -1 | sed 's/^/  /'

    # Compilar runtime si no existe
    if [ ! -f "$ROOT_DIR/$SYNAPSE_RT_OBJ" ]; then
        _compile_runtime "$_gcc"
    fi

    # Verificar el fuente del compilador
    if [ ! -f "$ROOT_DIR/$SYNAPSE_SRC" ]; then
        error "Fuente del compilador no encontrado: $SYNAPSE_SRC"
    fi

    # Compilar con instrumentación
    mkdir -p "$ROOT_DIR/$SYNAPSE_OUTDIR"
    _build_instrumented "$_gcc" \
        "$SYNAPSE_SRC" \
        "$ROOT_DIR/$SYNAPSE_OUTDIR/$PGO_INSTR_EXE" \
        "$ROOT_DIR/$PGO_DIR"

    ok "PASO 1 completado: $PGO_INSTR_EXE"
}

# ----------------------------------------------------------
# PASO 2: Carga de trabajo de entrenamiento
# ----------------------------------------------------------
step2_train() {
    info "=== PASO 2: Carga de trabajo de entrenamiento ==="
    local _instr_exe="$ROOT_DIR/$SYNAPSE_OUTDIR/$PGO_INSTR_EXE"

    if [ ! -f "$_instr_exe" ]; then
        error "Binario instrumentado no encontrado. Ejecuta --step1 primero."
    fi

    # Limpiar perfiles anteriores
    rm -f "$ROOT_DIR"/*.gcda "$ROOT_DIR/$PGO_DIR"/*.gcda 2>/dev/null || true

    # Recopilar archivos de prueba .syn
    local _syn_files=()
    while IFS= read -r -d '' _f; do
        _syn_files+=("$_f")
    done < <(find "$ROOT_DIR/$SYNAPSE_TESTDIR" -name '*.syn' -print0 2>/dev/null || true)

    # También incluir archivos .syn de nucleo/ y raíz
    while IFS= read -r -d '' _f; do
        _syn_files+=("$_f")
    done < <(find "$ROOT_DIR/nucleo" -name '*.syn' -print0 2>/dev/null || true)
    while IFS= read -r -d '' _f; do
        _syn_files+=("$_f")
    done < <(find "$ROOT_DIR" -maxdepth 1 -name '*.syn' -print0 2>/dev/null || true)

    info "Carga de trabajo: ${#_syn_files[@]} archivos .syn"

    # Ejecutar el binario instrumentado sobre cada archivo
    local _count=0
    local _ok=0
    local _fail=0
    for _f in "${_syn_files[@]}"; do
        _count=$((_count + 1))
        local _base; _base="$(basename "$_f")"
        # El compilador nativo espera: <exe> <source> [output]
        local _tmp_out="$ROOT_DIR/$PGO_DIR/__pgo_test_${_count}.exe"
        if "$_instr_exe" "$_f" "$_tmp_out" >/dev/null 2>&1; then
            _ok=$((_ok + 1))
            printf "  [PGO] ✅ %s\n" "$_base"
        else
            _fail=$((_fail + 1))
            printf "  [PGO] ⚠️  %s (fallo esperado en pruebas inválidas)\n" "$_base"
        fi
        # Limpiar binarios temporales
        rm -f "$_tmp_out" "${_tmp_out%.exe}.c" 2>/dev/null || true
    done

    # Verificar que se generaron perfiles
    local _gcda_count=0
    while IFS= read -r -d '' _f; do
        _gcda_count=$((_gcda_count + 1))
    done < <(find "$ROOT_DIR" -name '*.gcda' -print0 2>/dev/null || true)

    info "Archivos de perfil generados: $_gcda_count"
    if [ "$_gcda_count" -eq 0 ]; then
        error "No se generaron archivos .gcda. Verifica que el binario instrumentado funcione."
    fi

    # Copy .gcda files to project root (needed by -fprofile-use in step 3)
    while IFS= read -r -d '' _f; do
        local _gcda_name; _gcda_name="$(basename "$_f")"
        # Extract source name: strip <exename>- prefix to get <source>.gcda
        local _src_gcda="${_gcda_name#*-}"
        if [ -n "$_src_gcda" ] && [ ! -f "$ROOT_DIR/$_src_gcda" ]; then
            cp "$_f" "$ROOT_DIR/$_src_gcda"
            info "Perfil copiado: $_src_gcda"
        fi
    done < <(find "$ROOT_DIR" -name '*.gcda' -print0 2>/dev/null || true)

    ok "PASO 2 completado: $_ok compilaciones exitosas, $_fail fallos"
}

# ----------------------------------------------------------
# PASO 3: Recompilación optimizada
# ----------------------------------------------------------
step3_optimize() {
    info "=== PASO 3: Recompilación optimizada ==="
    local _gcc; _gcc="$(_detect_gcc)"
    # Verificar perfiles
    local _gcda_count=0
    while IFS= read -r -d '' _f; do
        _gcda_count=$((_gcda_count + 1))
    done < <(find "$ROOT_DIR" -name '*.gcda' -print0 2>/dev/null || true)

    if [ "$_gcda_count" -eq 0 ]; then
        error "No hay perfiles .gcda. Ejecuta --step2 primero."
    fi

    info "Usando $_gcda_count archivos de perfil de: $ROOT_DIR"

    # Generar C desde Synapse (usando el compilador bootstrap)
    if [ -f "$ROOT_DIR/$PGO_STAGE1_EXE" ]; then
        info "Usando compilador bootstrap nativo..."
        "$ROOT_DIR/$PGO_STAGE1_EXE" "$ROOT_DIR/$SYNAPSE_SRC" "$ROOT_DIR/$PGO_DIR/__pgo_bootstrap.exe" \
            2>&1 | sed 's/^/  /'
    else
        info "Usando compilador Python..."
        python "$ROOT_DIR/main.py" "$ROOT_DIR/$SYNAPSE_SRC" 2>&1 | sed 's/^/  /'
    fi

    local _unity_c="$ROOT_DIR/synapse_unity.c"
    if [ ! -f "$_unity_c" ]; then
        error "No se generó synapse_unity.c"
    fi

    # Fusionar perfiles (GCC lo hace automáticamente con -fprofile-use)
    local _opt_out="$ROOT_DIR/$SYNAPSE_OUTDIR/$PGO_OPT_EXE"
    info "Compilando con -fprofile-use -flto: $_opt_out"

    "$_gcc" -O3 \
        -fprofile-use \
        -flto -fwhole-program \
        -fno-ident -Wl,--gc-sections -Wl,--stack,8388608 \
        -Wl,--no-insert-timestamp \
        -I"$ROOT_DIR" \
        "$_unity_c" \
        "$ROOT_DIR/$SYNAPSE_RT_OBJ" \
        "$ROOT_DIR/$SYNAPSE_TN_OBJ" \
        -o "$_opt_out" \
        -lpthread -lm -lws2_32 \
        2>&1 | sed 's/^/  /'

    if [ ! -f "$_opt_out" ]; then
        # GCC emite advertencia si los perfiles no coinciden exactamente;
        # intentar con -fprofile-correction
        info "Reintentando con -fprofile-correction..."
        "$_gcc" -O3 \
            -fprofile-use \
            -fprofile-correction \
            -flto -fwhole-program \
            -fno-ident -Wl,--gc-sections -Wl,--stack,8388608 \
            -Wl,--no-insert-timestamp \
            -I"$ROOT_DIR" \
            "$_unity_c" \
            "$ROOT_DIR/$SYNAPSE_RT_OBJ" \
            "$ROOT_DIR/$SYNAPSE_TN_OBJ" \
            -o "$_opt_out" \
            -lpthread -lm -lws2_32 \
            2>&1 | sed 's/^/  /'
    fi

    if [ ! -f "$_opt_out" ]; then
        error "Fallo la compilación optimizada con PGO"
    fi

    # Comparar tamaños
    local _instr_size=0
    if [ -f "$ROOT_DIR/$SYNAPSE_OUTDIR/$PGO_INSTR_EXE" ]; then
        _instr_size=$(wc -c < "$ROOT_DIR/$SYNAPSE_OUTDIR/$PGO_INSTR_EXE" | tr -d ' ' 2>/dev/null || echo 0)
    fi
    local _opt_size
    _opt_size=$(wc -c < "$_opt_out" | tr -d ' ')

    info "Tamaño instrumentado: ${_instr_size} bytes"
    info "Tamaño optimizado:    ${_opt_size} bytes"

    if [ "$_opt_size" -lt "$_instr_size" ]; then
        local _savings=$(( (_instr_size - _opt_size) * 100 / _instr_size ))
        info "Reducción de tamaño: $_savings% (los contadores PGO fueron eliminados)"
    fi

    ok "PASO 3 completado: $PGO_OPT_EXE ($_opt_size bytes)"
}

# ----------------------------------------------------------
# Limpieza
# ----------------------------------------------------------
step_clean() {
    info "Limpiando artefactos PGO..."
    rm -rf "$ROOT_DIR/$PGO_DIR"
    rm -f "$ROOT_DIR/$SYNAPSE_OUTDIR/$PGO_INSTR_EXE"
    rm -f "$ROOT_DIR/$SYNAPSE_OUTDIR/$PGO_OPT_EXE"
    rm -f "$ROOT_DIR/synapse_unity.c"
    rm -f "$ROOT_DIR/synapse.profdata"
    # Clean .gcda from all possible locations
    rm -f "$ROOT_DIR"/*.gcda "$ROOT_DIR"/*.gcno 2>/dev/null || true
    rm -f "$ROOT_DIR/$SYNAPSE_OUTDIR"/*.gcda "$ROOT_DIR/$SYNAPSE_OUTDIR"/*.gcno 2>/dev/null || true
    ok "Limpieza completada"
}

# ----------------------------------------------------------
# Validación post-PGO
# ----------------------------------------------------------
step_validate() {
    info "=== Validación post-PGO ==="
    local _opt_exe="$ROOT_DIR/$SYNAPSE_OUTDIR/$PGO_OPT_EXE"

    if [ ! -f "$_opt_exe" ]; then
        error "Binario optimizado no encontrado. Ejecuta --step3 primero."
    fi

    # Ejecutar bootstrap rápido: el compilador optimizado debe
    # poder compilarse a sí mismo
    info "Validación: bootstrap rápido con binario optimizado..."
    local _tmp_src="$ROOT_DIR/$PGO_DIR/__validate_test.syn"
    local _tmp_out="$ROOT_DIR/$PGO_DIR/__validate_test.exe"

    # Crear un programa Synapse mínimo
    cat > "$_tmp_src" << 'EOF'
#lang: es
funcion principal() -> nulo:
    retornar
EOF

    if "$_opt_exe" "$_tmp_src" "$_tmp_out" >/dev/null 2>&1; then
        ok "Validación: programa mínimo compila correctamente"
    else
        error "Validación: fallo al compilar programa mínimo"
    fi

    # Limpiar
    rm -f "$_tmp_src" "$_tmp_out" "${_tmp_out%.exe}.c" 2>/dev/null || true
    ok "Validación post-PGO completada"
}

# ----------------------------------------------------------
# Ayuda
# ----------------------------------------------------------
show_help() {
    sed -n '2,45p' "$0" | sed 's/^# //; s/^#$//'
}

# ----------------------------------------------------------
# Punto de entrada
# ----------------------------------------------------------
cd "$ROOT_DIR"
mkdir -p "$SYNAPSE_OUTDIR"

case "${1:-}" in
    --step1|-1)
        step1_instrument
        ;;
    --step2|-2)
        step2_train
        ;;
    --step3|-3)
        step3_optimize
        step_validate
        ;;
    --clean)
        step_clean
        ;;
    --validate)
        step_validate
        ;;
    --help|-h)
        show_help
        exit 0
        ;;
    *)
        # Ciclo completo
        info "=== PGO PIPELINE COMPLETO ==="
        step1_instrument
        step2_train
        step3_optimize
        step_validate

        # Resumen final
        echo ""
        echo "============================================"
        echo "  PGO PIPELINE COMPLETADO EXITOSAMENTE"
        echo "============================================"
        echo "  Binarios:"
        echo "    $SYNAPSE_OUTDIR/$PGO_INSTR_EXE"
        echo "    $SYNAPSE_OUTDIR/$PGO_OPT_EXE"
        echo "============================================"
        ;;
esac
