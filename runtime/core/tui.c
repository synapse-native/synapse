// runtime/core/tui.c — Motor TUI para el chat de OpenSyn (Manual 7 §1.1/§8,
// Manual 9 §2.5: consola real con ANSI VT; pipes limpios).
//
// Proporciona al chat .syn una interfaz de pantalla completa estilo
// OpenCode/Freebuff SIN acoplar la lógica de negocio al C:
//   - pantalla alternativa + teclas en modo crudo (flechas/Enter/Esc/UTF-8),
//   - panel de mensajes (roles con color, ajuste por ancho visual, scroll),
//   - caja de entrada fija al pie con cursor,
//   - menú modal genérico (usado por "/" y "/model").
// El bucle de negocio, el streaming del modelo y los comandos viven en
// opensyn/principal.syn; aquí solo se dibuja y se leen eventos.
//
// Consumido por opensyn/principal.syn vía externos _syn_tui_*.
// Windows: consola real vía ReadConsoleInputW (robusto con UTF-8 y teclas
// especiales). POSIX: termios en modo crudo + secuencias ANSI.
// Cuando stdin/stdout NO son consola (pipes, tests) y la variable de entorno
// OPENSN_TUI_TEST=1 está presente, opera en "modo pipe": lee stdin por bytes
// y dibuja igual — permite oráculos E2E del gate MTS sin terminal.

#include "synapse_rt_types.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#ifdef _WIN32
  #include <windows.h>
  #include <process.h>
#else
  #include <termios.h>
  #include <unistd.h>
  #include <sys/ioctl.h>
  #include <errno.h>
  #include <pthread.h>
#endif

// ============================================================
// Estado global del widget (una única sesión de chat)
// ============================================================

#define MSG_MAX 600
#define ENT_MAX 4096
#define ROW_MAX 4096
#define MENU_MAX 200

typedef struct {
    int rol;        // 0 usuario, 1 asistente, 2 sistema (tenue), 3 error, 4 banner (cian)
    char* texto;    // UTF-8 (malloc)
} _Msg;

static _Msg _msgs[MSG_MAX];
static int _nmsgs = 0;

static char* _entrada = NULL;   // UTF-8, capacidad ENT_MAX
static int _elen = 0;           // bytes
static int _ecur = 0;           // índice de byte del cursor (en frontera de carácter)

static int _tui_activo = 0;     // 1 mientras la TUI está iniciada
static int _pipe_mode = 0;      // 1 = modo pipe (OPENSN_TUI_TEST) — sin consola
static int _alerts = 0;         // mensajes que requieren repintar (flag)

// ---- Estado "pensando" (spinner estilo OpenCode/Kilo, Manual 7 §8) ----
// Hilo propio anima el renglón de estado mientras el modelo genera; solo en
// consola real (en modo pipe contaminaría la salida de los oráculos).
static volatile int _pensando = 0;
static volatile long long _pens_ms = 0;   // inicio (ms monotónicos)
#ifdef _WIN32
static HANDLE _hilo_pens = NULL;
#else
static pthread_t _hilo_pens;
static int _hilo_pens_vivo = 0;
#endif
static char _pens_label[64] = "Consultando";  // etiqueta del spinner
static int _ctx_pct = 0;        // % del presupuesto de contexto usado
static int _tokens_ultimo = 0;  // tokens (~chars/4) de la última respuesta

// Exclusión mutua de salida: el spinner escribe desde su hilo mientras el
// hilo principal repinta — sin candado, dos escrituras pueden entremezclarse
// a mitad de secuencia ANSI y corromper el cuadro.
#ifdef _WIN32
static CRITICAL_SECTION _out_cs;
static int _out_cs_ok = 0;
static void _out_lock(void) { if (_out_cs_ok) EnterCriticalSection(&_out_cs); }
static void _out_unlock(void) { if (_out_cs_ok) LeaveCriticalSection(&_out_cs); }
#else
static pthread_mutex_t _out_cs = PTHREAD_MUTEX_INITIALIZER;
static void _out_lock(void) { pthread_mutex_lock(&_out_cs); }
static void _out_unlock(void) { pthread_mutex_unlock(&_out_cs); }
#endif

// Buffer para modo pipe: acumula entrada hasta recibir \n
static char _pipe_buf[ENT_MAX];
static int _pipe_buf_len = 0;

// ============================================================
// Historial persistente (Manual 7 §1.1: UX OpenCode)
// ============================================================

#define HIST_MAX 1000
#define HIST_FILE "history.jsonl"

typedef struct {
    char* texto;    // UTF-8 (malloc)
    long long ts;   // timestamp ms
} _HistEntry;

static _HistEntry _hist[HIST_MAX];
static int _hist_count = 0;
static int _hist_idx = -1;        // índice actual en navegación (-1 = sin navegar)
static int _hist_saved_count = 0; // cuántas entradas ya persistidas

// ============================================================
// Autocompletado Tab (Manual 7 §8: UX asistente)
// ============================================================

#define COMP_MAX 64

typedef struct {
    char* items[COMP_MAX];  // punteros a strings (malloc)
    int count;
    int common_len;         // longitud del prefijo común
} _Completions;

static _Completions _comp = {0};
static int _last_tab_time = 0;  // para detectar doble Tab

#ifdef _WIN32
static HANDLE _hin = NULL, _hout = NULL;
static DWORD _modo_in_orig = 0, _modo_out_orig = 0;
#else
static struct termios _term_orig;
#endif

// Forward declarations for history/autocomplete (usados en _syn_tui_iniciar/finalizar/evento)
void _syn_tui_historial_cargar(void);
void _syn_tui_historial_guardar(void);
void _syn_tui_historial_anadir(CadenaSegura texto);
int _syn_tui_historial_anterior(void);
int _syn_tui_historial_siguiente(void);
const char* _syn_tui_historial_actual(void);
void _syn_tui_completar(void);
void _comp_limpiar(void);

// Reloj monotónico local (para timestamps de historial) — evita depender de ollama.c
static long long _tui_ahora_ms(void) {
#ifdef _WIN32
    return (long long)GetTickCount64();
#else
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (long long)ts.tv_sec * 1000LL + ts.tv_nsec / 1000000LL;
#endif
}

// ============================================================
// Utilidades UTF-8 / ancho visual (aproximación wcwidth)
// ============================================================

// Decodifica un codepoint UTF-8 desde s; avanza *i. Devuelve cp (o -1).
static long _cp_leer(const char* s, int len, int* i) {
    unsigned char c = (unsigned char)s[*i];
    if (c < 0x80) { (*i)++; return c; }
    int n = 0; long cp = 0;
    if ((c & 0xE0) == 0xC0) { n = 1; cp = c & 0x1F; }
    else if ((c & 0xF0) == 0xE0) { n = 2; cp = c & 0x0F; }
    else if ((c & 0xF8) == 0xF0) { n = 3; cp = c & 0x07; }
    else { (*i)++; return -1; }
    if (*i + n > len) { (*i)++; return -1; }
    for (int k = 1; k <= n; k++) {
        unsigned char cc = (unsigned char)s[*i + k];
        if ((cc & 0xC0) != 0x80) { (*i)++; return -1; }
        cp = (cp << 6) | (cc & 0x3F);
    }
    *i += n;
    return cp;
}

// Ancho de columnas de un codepoint (1 = normal, 2 = ancho, 0 = combina/cero).
static int _cp_ancho(long cp) {
    if (cp < 0) return 1;
    if (cp == 0 || cp == 0x200B || cp == 0x200D) return 0;
    if (cp >= 0x0300 && cp <= 0x036F) return 0;   // combinantes
    if (cp >= 0x1AB0 && cp <= 0x1AFF) return 0;
    if (cp >= 0x20D0 && cp <= 0x20FF) return 0;
    if (cp >= 0xFE00 && cp <= 0xFE0F) return 0;
    if ((cp >= 0x1100 && cp <= 0x115F) ||   // hangul Jamo
        (cp >= 0x2E80 && cp <= 0xA4CF) ||   // CJK … Yi
        (cp >= 0xAC00 && cp <= 0xD7A3) ||   // hangul sílabas
        (cp >= 0xF900 && cp <= 0xFAFF) ||   // CJK compat
        (cp >= 0xFE30 && cp <= 0xFE4F) ||
        (cp >= 0xFF00 && cp <= 0xFF60) ||
        (cp >= 0xFFE0 && cp <= 0xFFE6) ||
        (cp >= 0x1F300 && cp <= 0x1FAFF) || // emoji
        (cp >= 0x20000 && cp <= 0x3FFFD)) return 2;
    return 1;
}

// Ancho visual en columnas de una cadena UTF-8.
static int _utf8_ancho(const char* s, int len) {
    int w = 0, i = 0;
    while (i < len) { w += _cp_ancho(_cp_leer(s, len, &i)); }
    return w;
}

// ============================================================
// Salida de bajo nivel (secuencias ANSI hacia stdout)
// ============================================================

static void _out(const char* s) {
    fputs(s, stdout);
}
static void _outn(const char* s, int n) {
    fwrite(s, 1, (size_t)n, stdout);
}
static void _flush(void) { fflush(stdout); }

static void _sgr(int code) {
    char b[24];
    snprintf(b, sizeof(b), "\x1b[%dm", code);
    _out(b);
}

// ============================================================
// Detección de consola + entrada en modo pipe
// ============================================================

static int _es_consola_real(void) {
#ifdef _WIN32
    HANDLE h = GetStdHandle(STD_INPUT_HANDLE);
    DWORD m = 0;
    return h != NULL && h != INVALID_HANDLE_VALUE && GetConsoleMode(h, &m) != 0;
#else
    return isatty(fileno(stdin)) != 0;
#endif
}

static int _pipe_forzado(void) {
    const char* e = getenv("OPENSN_TUI_TEST");
    return e != NULL && e[0] != '\0' && e[0] != '0';
}

// ============================================================
// API pública — iniciar / finalizar
// ============================================================

// cumple Manual 7 8: entra en modo TUI (pantalla alternativa + teclas crudas).
// Retorna 0 si la TUI quedó activa; -1 si no hay consola real ni modo pipe.
int64_t _syn_tui_iniciar(void) {
    if (_tui_activo) return 0;
    int consola = _es_consola_real();
    if (!consola && !_pipe_forzado()) return -1;
    _pipe_mode = !consola;
#ifdef _WIN32
    if (!_out_cs_ok) {
        InitializeCriticalSection(&_out_cs);
        _out_cs_ok = 1;
    }
    _hin = GetStdHandle(STD_INPUT_HANDLE);
    _hout = GetStdHandle(STD_OUTPUT_HANDLE);
    if (_pipe_mode) {
        // stdout ya escribe con VT (io.c lo activa si puede); no hay consola.
    } else {
        DWORD mi = 0, mo = 0;
        GetConsoleMode(_hin, &mi);
        GetConsoleMode(_hout, &mo);
        _modo_in_orig = mi;
        _modo_out_orig = mo;
        // Modo crudo: sin eco, sin línea, sin procesado; entrada VT; quitar
        // QuickEdit (bloquea la app al hacer clic) y Ctrl+C como señal.
        DWORD nuevo = mi;
        nuevo &= ~(ENABLE_LINE_INPUT | ENABLE_ECHO_INPUT | ENABLE_PROCESSED_INPUT | ENABLE_QUICK_EDIT_MODE);
        nuevo |= ENABLE_VIRTUAL_TERMINAL_INPUT;
        SetConsoleMode(_hin, nuevo);
        DWORD mout = mo | ENABLE_VIRTUAL_TERMINAL_PROCESSING;
        SetConsoleMode(_hout, mout);
        // Cumple Manual 9 §2.5: UTF-8 en consola real para banner/prompt sin mojibake
        SetConsoleOutputCP(65001);
        SetConsoleCP(65001);
    }
    _out("\x1b[?1049h");   // pantalla alternativa
    _out("\x1b[?25l");     // ocultar cursor (lo dibuja la caja de entrada)
    _out("\x1b[2J\x1b[H");
    _flush();
#else
    if (!_pipe_mode) {
        tcgetattr(fileno(stdin), &_term_orig);
        struct termios raw = _term_orig;
        raw.c_lflag &= (tcflag_t)~(ICANON | ECHO | ISIG);
        raw.c_iflag &= (tcflag_t)~(IXON | ICRNL);
        raw.c_cc[VMIN] = 0;
        raw.c_cc[VTIME] = 1;   // 100 ms
        tcsetattr(fileno(stdin), TCSANOW, &raw);
    }
    _out("\x1b[?1049h\x1b[?25l\x1b[2J\x1b[H");
    _flush();
#endif
    _tui_activo = 1;
    _syn_tui_historial_cargar();
    return 0;
}

int64_t _syn_tui_finalizar(void) {
    if (!_tui_activo) return 0;
    _out("\x1b[?25h");
    _out("\x1b[?1049l");
#ifdef _WIN32
    if (!_pipe_mode && _hin && _hout) {
        SetConsoleMode(_hin, _modo_in_orig);
        SetConsoleMode(_hout, _modo_out_orig);
    }
#else
    if (!_pipe_mode) tcsetattr(fileno(stdin), TCSANOW, &_term_orig);
#endif
    _flush();
    _syn_tui_historial_guardar();
    _tui_activo = 0;
    // Limpiar estado del widget para la próxima sesión
    for (int i = 0; i < _nmsgs; i++) { if (_msgs[i].texto) free(_msgs[i].texto); }
    _nmsgs = 0;
    if (_entrada) { _entrada[0] = '\0'; }
    _elen = 0;
    _ecur = 0;
    _pipe_buf_len = 0;
    _comp_limpiar();
    // Liberar historial
    for (int i = 0; i < _hist_count; i++) if (_hist[i].texto) free(_hist[i].texto);
    _hist_count = 0;
    _hist_saved_count = 0;
    _hist_idx = -1;
    return 0;
}

int64_t _syn_tui_alto(void) {
#ifdef _WIN32
    if (!_pipe_mode) {
        CONSOLE_SCREEN_BUFFER_INFO csbi;
        if (GetConsoleScreenBufferInfo(_hout, &csbi)) {
            return (int64_t)(csbi.srWindow.Bottom - csbi.srWindow.Top + 1);
        }
    }
    return 40;
#else
    if (!_pipe_mode) {
        struct winsize ws;
        if (ioctl(fileno(stdout), TIOCGWINSZ, &ws) == 0 && ws.ws_row > 0) return ws.ws_row;
    }
    return 40;
#endif
}

int64_t _syn_tui_ancho(void) {
#ifdef _WIN32
    if (!_pipe_mode) {
        CONSOLE_SCREEN_BUFFER_INFO csbi;
        if (GetConsoleScreenBufferInfo(_hout, &csbi)) {
            return (int64_t)(csbi.srWindow.Right - csbi.srWindow.Left + 1);
        }
    }
    return 120;
#else
    if (!_pipe_mode) {
        struct winsize ws;
        if (ioctl(fileno(stdout), TIOCGWINSZ, &ws) == 0 && ws.ws_col > 0) return ws.ws_col;
    }
    return 120;
#endif
}

void _syn_tui_pos(int64_t fila, int64_t col) {
    char b[32];
    snprintf(b, sizeof(b), "\x1b[%lld;%lldH", (long long)fila, (long long)col);
    _out(b);
}

// ============================================================
// Mensajes (modelo del panel superior)
// ============================================================

// cumple Manual 7 8: agrega un mensaje al panel (0 usuario, 1 asistente,
// 2 sistema, 3 error, 4 banner). Copia el texto (pool del llamador intacto).
int64_t _syn_tui_mensaje(int64_t rol, CadenaSegura texto) {
    if (_nmsgs >= MSG_MAX) return -1;
    int largo = texto.longitud;
    if (largo < 0) largo = 0;
    char* copia = (char*)malloc((size_t)largo + 1);
    if (!copia) return -1;
    if (largo > 0 && texto.datos) memcpy(copia, texto.datos, (size_t)largo);
    copia[largo] = '\0';
    _msgs[_nmsgs].rol = (int)rol;
    _msgs[_nmsgs].texto = copia;
    _nmsgs++;
    _alerts = 1;
    return 0;
}

// Elimina el último mensaje (p.ej. un turno de herramienta que no debe
// quedar como respuesta final).
void _syn_tui_mensaje_pop(void) {
    if (_nmsgs <= 0) return;
    _nmsgs--;
    if (_msgs[_nmsgs].texto) free(_msgs[_nmsgs].texto);
    _alerts = 1;
}

// Continúa el último mensaje de asistente (streaming) o crea uno nuevo.
void _syn_tui_asistente_continuar(CadenaSegura chunk) {
    if (chunk.longitud <= 0) return;
    if (_nmsgs > 0 && _msgs[_nmsgs - 1].rol == 1) {
        int largo = (int)strlen(_msgs[_nmsgs - 1].texto) + chunk.longitud;
        char* nn = (char*)realloc(_msgs[_nmsgs - 1].texto, (size_t)largo + 1);
        if (!nn) return;
        if (chunk.datos) memcpy(nn + strlen(nn), chunk.datos, (size_t)chunk.longitud);
        nn[largo] = '\0';
        _msgs[_nmsgs - 1].texto = nn;
    } else {
        _syn_tui_mensaje(1, chunk);
    }
    _alerts = 1;
}

// ============================================================
// Caja de entrada
// ============================================================

static void _entrada_asegurar(void) {
    if (!_entrada) {
        _entrada = (char*)malloc(ENT_MAX);
        if (_entrada) _entrada[0] = '\0';
    }
}

// En modo pipe, _pipe_buf es la fuente de verdad del renglón tecleado. Espeja
// su contenido en _entrada (que es lo que dibuja la caja de entrada) sin
// marcar alertas: en pipe no se repinta por cada tecla.
static void _pipe_sincronizar(void) {
    _entrada_asegurar();
    if (!_entrada) return;
    if (_pipe_buf_len > 0) {
        memcpy(_entrada, _pipe_buf, (size_t)_pipe_buf_len);
    }
    _entrada[_pipe_buf_len] = '\0';
    _elen = _pipe_buf_len;
    _ecur = _pipe_buf_len;
}

// Al Enter en modo pipe se REEMPLAZA _entrada con el buffer acumulado (no se
// inserta) para no duplicar lo que el Tab ya completó. Si el buffer está vacío
// (p.ej. tras navegar el historial con ↑/↓) se conserva _entrada.
static void _pipe_volcar_a_entrada(void) {
    _pipe_sincronizar();
    _pipe_buf_len = 0;
    _alerts = 1;
}

CadenaSegura _syn_tui_entrada_texto(void) {
    _entrada_asegurar();
    if (!_entrada) return (CadenaSegura){ .longitud = 0, .datos = "" };
    int l = (int)strlen(_entrada);
    char* pool = (char*)pool_alloc((size_t)l + 1);
    if (!pool) return (CadenaSegura){ .longitud = 0, .datos = "" };
    memcpy(pool, _entrada, (size_t)l + 1);
    return (CadenaSegura){ .longitud = l, .datos = pool };
}

void _syn_tui_entrada_poner(CadenaSegura texto) {
    _entrada_asegurar();
    if (!_entrada) return;
    int l = texto.longitud;
    if (l < 0) l = 0;
    if (l > ENT_MAX - 1) l = ENT_MAX - 1;
    if (l > 0 && texto.datos) memcpy(_entrada, texto.datos, (size_t)l);
    _entrada[l] = '\0';
    _elen = l;
    _ecur = l;
    _alerts = 1;
}

void _syn_tui_entrada_borrar(void) {
    _entrada_asegurar();
    if (_entrada) _entrada[0] = '\0';
    _elen = 0;
    _ecur = 0;
    _alerts = 1;
}

// Inserta una cadena UTF-8 en la posición del cursor (usado al pegar/teclear).
static void _entrada_insertar(const char* s, int largo) {
    _entrada_asegurar();
    if (!_entrada) return;
    if (largo <= 0) return;
    if (_elen + largo >= ENT_MAX) return;
    memmove(_entrada + _ecur + largo, _entrada + _ecur, (size_t)(_elen - _ecur) + 1);
    memcpy(_entrada + _ecur, s, (size_t)largo);
    _elen += largo;
    _ecur += largo;
    _alerts = 1;
}

// Borra un carácter hacia la izquierda del cursor (fronteras UTF-8).
static void _entrada_borrar_izq(void) {
    if (_ecur <= 0) return;
    int p = _ecur - 1;
    while (p > 0 && ((unsigned char)_entrada[p] & 0xC0) == 0x80) p--;
    memmove(_entrada + p, _entrada + _ecur, (size_t)(_elen - _ecur) + 1);
    _elen -= (_ecur - p);
    _ecur = p;
    _alerts = 1;
}

static void _entrada_borrar_der(void) {
    if (_ecur >= _elen) return;
    int p = _ecur + 1;
    while (p < _elen && ((unsigned char)_entrada[p] & 0xC0) == 0x80) p++;
    memmove(_entrada + _ecur, _entrada + p, (size_t)(_elen - p) + 1);
    _elen -= (p - _ecur);
    _alerts = 1;
}

// Mueve el cursor una posición (visual) a la izquierda/derecha.
static void _entrada_cursor_izq(void) {
    if (_ecur <= 0) return;
    int p = _ecur - 1;
    while (p > 0 && ((unsigned char)_entrada[p] & 0xC0) == 0x80) p--;
    _ecur = p;
    _alerts = 1;
}
static void _entrada_cursor_der(void) {
    if (_ecur >= _elen) return;
    int p = _ecur + 1;
    while (p < _elen && ((unsigned char)_entrada[p] & 0xC0) == 0x80) p++;
    _ecur = p;
    _alerts = 1;
}

// ============================================================
// Lectura de eventos de teclado
// ============================================================

// Devuelve códigos: 0 = carácter imprimible insertado (entrada cambió),
// 1 Enter, 2 Esc, 3 ↑, 4 ↓, 5 ←, 6 →, 7 Retroceso, 8 Supr, 9 Tab, 10 Ctrl+C.
// ============================================================
// Spinner "pensando" + status bar dinámico (Manual 7 §8: UX OpenCode/Kilo)
// ============================================================

// cumple Manual 7 §8: el hilo SOLO escribe su renglón reservado (alto-1); el
// repintado completo sigue siendo exclusivo del hilo principal. Sin estado
// compartido de mensajes — sin condiciones de carrera.
#ifdef _WIN32
static unsigned __stdcall _pens_hilo(void* arg) {
#else
static void* _pens_hilo(void* arg) {
#endif
    (void)arg;
    static const char* frames = "|/-\\";
    int i = 0;
    while (_pensando) {
        long long ms = _tui_ahora_ms() - _pens_ms;
        int alto = (int)_syn_tui_alto();
        _out_lock();
        // El spinner OCUPA la fila del status bar (patrón OpenCode: el pie
        // cambia a estado de actividad mientras el modelo genera).
        _syn_tui_pos(alto, 1);
        _out("\x1b[2K");
        _sgr(90);
        _out("  ");
        _sgr(93);   // amarillo: actividad en curso
        char f[2] = { frames[i % 4], 0 };
        _out(f);
        _sgr(90);
        _out(" ");
        _out(_pens_label);
        _out("… ");
        char t[32];
        snprintf(t, sizeof(t), "%llds", (long long)(ms / 1000));
        _out(t);
        _sgr(0);
        _out("\x1b[K");
        _flush();
        _out_unlock();
        i++;
#ifdef _WIN32
        Sleep(100);
#else
        struct timespec ts = { 0, 100 * 1000 * 1000 };
        nanosleep(&ts, NULL);
#endif
    }
#ifdef _WIN32
    return 0;
#else
    return NULL;
#endif
}

void _syn_tui_pensando(int64_t activar, CadenaSegura etiqueta) {
    if (activar) {
        int n = etiqueta.longitud;
        if (n > 0 && n < (int)sizeof(_pens_label) && etiqueta.datos) {
            memcpy(_pens_label, etiqueta.datos, (size_t)n);
            _pens_label[n] = '\0';
        }
        _pens_ms = _tui_ahora_ms();
        if (_pensando) return;   // ya activo: solo renovó etiqueta/tiempo
        if (!_pipe_mode && _tui_activo) {
            _pensando = 1;
#ifdef _WIN32
            _hilo_pens = (HANDLE)_beginthreadex(NULL, 0, _pens_hilo, NULL, 0, NULL);
#else
            _hilo_pens_vivo = (pthread_create(&_hilo_pens, NULL, _pens_hilo, NULL) == 0);
#endif
        } else {
            _pensando = 1;   // modo pipe: sin hilo ni animación (oráculos limpios)
        }
    } else {
        _pensando = 0;
#ifdef _WIN32
        if (_hilo_pens) {
            WaitForSingleObject(_hilo_pens, 500);
            CloseHandle(_hilo_pens);
            _hilo_pens = NULL;
        }
#else
        if (_hilo_pens_vivo) {
            pthread_join(_hilo_pens, NULL);
            _hilo_pens_vivo = 0;
        }
#endif
    }
}

void _syn_tui_contexto(int64_t pct, int64_t tokens) {
    _ctx_pct = (pct < 0) ? 0 : (pct > 100) ? 100 : (int)pct;
    _tokens_ultimo = (tokens < 0) ? 0 : (int)tokens;
}

int64_t _syn_tui_evento(void) {
    if (!_tui_activo) return 0;
    _alerts = 0;
#ifdef _WIN32
    if (_pipe_mode) {
        // stdin por bytes: en modo pipe, buffer hasta \n para evitar flickering.
// Solo retorna 1 (Enter) cuando hay línea completa; 0 mientras se acumula.
        unsigned char c = 0;
        DWORD leidos = 0;
        if (!ReadFile(GetStdHandle(STD_INPUT_HANDLE), &c, 1, &leidos, NULL) || leidos == 0) {
            // stdin cerrado (EOF) → si hay buffer, tratar como Enter; sino simular Ctrl+C para salir
            if (_pipe_buf_len > 0) {
                _pipe_volcar_a_entrada();
                return 1;
            }
            return 10;  // EOF sin buffer = Ctrl+C (salir limpio)
        }
        if (c == '\r') {
            // \r puede venir solo o antes de \n; leer siguiente si es \n
            unsigned char next = 0;
            DWORD n = 0;
            if (ReadFile(GetStdHandle(STD_INPUT_HANDLE), &next, 1, &n, NULL) && n == 1 && next == '\n') {
                // \r\n consumido
            }
            // Línea completa: volcar buffer a entrada y retornar Enter
            _pipe_volcar_a_entrada();
            return 1;
        }
        if (c == '\n') {
            // Línea completa: volcar buffer a entrada y retornar Enter
            _pipe_volcar_a_entrada();
            return 1;
        }
        if (c == 3) return 10;  // Ctrl+C
        if (c == 0x1b) {  // ESC o secuencia ANSI
            unsigned char s[3] = {0, 0, 0};
            DWORD n = 0;
            BOOL ok = ReadFile(GetStdHandle(STD_INPUT_HANDLE), &s[0], 1, &n, NULL);
            if (ok && n == 1 && s[0] == '[') {
                unsigned char t = 0;
                BOOL ok2 = ReadFile(GetStdHandle(STD_INPUT_HANDLE), &t, 1, &n, NULL);
                if (ok2 && n == 1) {
                    if (t == 'A') {
                        // Historial: navegar hacia atrás (caja vacía o cursor al final)
                        if (_elen == 0 || _ecur == _elen) {
                            if (_syn_tui_historial_anterior()) {
                                const char* h = _syn_tui_historial_actual();
                                _syn_tui_entrada_poner((CadenaSegura){ .longitud = (int)strlen(h), .datos = h });
                                _ecur = _elen;
                                _pipe_buf_len = _elen;
                                if (_pipe_buf_len > 0) memcpy(_pipe_buf, _entrada, (size_t)_pipe_buf_len);
                            }
                        }
                        return 3;
                    }
                    if (t == 'B') {
                        // Historial: navegar hacia adelante
                        if (_elen == 0 || _ecur == _elen) {
                            if (_syn_tui_historial_siguiente()) {
                                const char* h = _syn_tui_historial_actual();
                                _syn_tui_entrada_poner((CadenaSegura){ .longitud = (int)strlen(h), .datos = h });
                                _ecur = _elen;
                                _pipe_buf_len = _elen;
                                if (_pipe_buf_len > 0) memcpy(_pipe_buf, _entrada, (size_t)_pipe_buf_len);
                            } else {
                                _syn_tui_entrada_borrar();
                                _pipe_buf_len = 0;
                            }
                        }
                        return 4;
                    }
                    if (t == 'C') return 6;
                    if (t == 'D') return 5;
                    return 2;
                }
            }
            return 2;
        }
        if (c == 0x7f || c == 8) {  // Backspace/DEL
            if (_pipe_buf_len > 0) {
                _pipe_buf_len--;
                _pipe_sincronizar();
            }
            return 7;
        }
        if (c == '\t') {
            // En modo pipe, el input actual está en _pipe_buf, no en _entrada.
            // Copiar _pipe_buf a _entrada para que _syn_tui_completar lo use.
            _entrada_asegurar();
            if (_pipe_buf_len > 0) {
                memcpy(_entrada, _pipe_buf, (size_t)_pipe_buf_len);
            }
            _entrada[_pipe_buf_len] = '\0';
            _elen = _pipe_buf_len;
            _ecur = _pipe_buf_len;
            _syn_tui_completar();
            // Copiar resultado de vuelta a _pipe_buf
            _pipe_buf_len = _elen;
            if (_pipe_buf_len > 0) {
                memcpy(_pipe_buf, _entrada, (size_t)_pipe_buf_len);
            }
            return 9;
        }
        // Acumular carácter imprimible en buffer de pipe
        if (_pipe_buf_len < ENT_MAX - 1) {
            _pipe_buf[_pipe_buf_len++] = (char)c;
            // Decodificar el resto de una secuencia UTF-8 multibyte de stdin.
            int total = 1;
            if (c >= 0xC2 && c <= 0xDF) total = 2;
            else if (c >= 0xE0 && c <= 0xEF) total = 3;
            else if (c >= 0xF0 && c <= 0xF4) total = 4;
            while (_pipe_buf_len < total && _pipe_buf_len < ENT_MAX - 1) {
                DWORD r2 = 0;
                unsigned char x = 0;
                if (!ReadFile(GetStdHandle(STD_INPUT_HANDLE), &x, 1, &r2, NULL) || r2 == 0) break;
                _pipe_buf[_pipe_buf_len++] = (char)x;
            }
        }
        _pipe_sincronizar();
        return 0;  // No repintar hasta Enter
    }
    // Consola real: ReadConsoleInputW traduce teclas y UTF-16 → UTF-8.
    for (;;) {
        INPUT_RECORD ir;
        DWORD n = 0;
        if (!ReadConsoleInputW(_hin, &ir, 1, &n) || n == 0) return 0;
        if (ir.EventType != KEY_EVENT || !ir.Event.KeyEvent.bKeyDown) continue;
        KEY_EVENT_RECORD* k = &ir.Event.KeyEvent;
        // Caracteres (incl. acentos/emoji como pares sustitutos)
        if (k->uChar.UnicodeChar != 0) {
            wchar_t w = k->uChar.UnicodeChar;
            if (w == L'\r') return 1;
            if (w == L'\x1b') return 2;
            if (w == 3) return 10;
            if (w == L'\t') return 9;
            if (w == 8 || w == 0x7f) { _entrada_borrar_izq(); return 7; }
            // Convertir UTF-16 (con pares sustitutos) a UTF-8
            unsigned long cp = (unsigned long)w;
            wchar_t w2 = 0;
            if (cp >= 0xD800 && cp <= 0xDBFF) {
                if (ReadConsoleInputW(_hin, &ir, 1, &n) && n == 1 && ir.EventType == KEY_EVENT &&
                    ir.Event.KeyEvent.bKeyDown && ir.Event.KeyEvent.uChar.UnicodeChar >= 0xDC00 &&
                    ir.Event.KeyEvent.uChar.UnicodeChar <= 0xDFFF) {
                    w2 = ir.Event.KeyEvent.uChar.UnicodeChar;
                    cp = 0x10000 + ((cp - 0xD800) << 10) + (w2 - 0xDC00);
                } else {
                    continue;
                }
            }
            char buf[8];
            int largo = 0;
            if (cp < 0x80) buf[largo++] = (char)cp;
            else if (cp < 0x800) {
                buf[largo++] = (char)(0xC0 | (cp >> 6));
                buf[largo++] = (char)(0x80 | (cp & 0x3F));
            } else if (cp < 0x10000) {
                buf[largo++] = (char)(0xE0 | (cp >> 12));
                buf[largo++] = (char)(0x80 | ((cp >> 6) & 0x3F));
                buf[largo++] = (char)(0x80 | (cp & 0x3F));
            } else {
                buf[largo++] = (char)(0xF0 | (cp >> 18));
                buf[largo++] = (char)(0x80 | ((cp >> 12) & 0x3F));
                buf[largo++] = (char)(0x80 | ((cp >> 6) & 0x3F));
                buf[largo++] = (char)(0x80 | (cp & 0x3F));
            }
            _entrada_insertar(buf, largo);
            return 0;
        }
        // Teclas especiales
        switch (k->wVirtualKeyCode) {
            case VK_RETURN: return 1;
            case VK_ESCAPE: return 2;
            case VK_UP:
                // Historial: navegar hacia atrás si caja vacía o cursor al final
                if (_elen == 0 || _ecur == _elen) {
                    if (_syn_tui_historial_anterior()) {
                        const char* h = _syn_tui_historial_actual();
                        _syn_tui_entrada_poner((CadenaSegura){ .longitud = (int)strlen(h), .datos = h });
                        _ecur = _elen;
                    }
                    return 3;
                }
                return 3;
            case VK_DOWN:
                // Historial: navegar hacia adelante
                if (_elen == 0 || _ecur == _elen) {
                    if (_syn_tui_historial_siguiente()) {
                        const char* h = _syn_tui_historial_actual();
                        _syn_tui_entrada_poner((CadenaSegura){ .longitud = (int)strlen(h), .datos = h });
                        _ecur = _elen;
                    } else {
                        _syn_tui_entrada_borrar();
                    }
                    return 4;
                }
                return 4;
            case VK_LEFT: _entrada_cursor_izq(); return 5;
            case VK_RIGHT: _entrada_cursor_der(); return 6;
            case VK_BACK: _entrada_borrar_izq(); return 7;
            case VK_DELETE: _entrada_borrar_der(); return 8;
            case VK_TAB:
                _syn_tui_completar();
                return 9;
            case 'C': if (k->dwControlKeyState & (LEFT_CTRL_PRESSED | RIGHT_CTRL_PRESSED)) return 10; break;
            default: break;
        }
    }
#else
    if (_pipe_mode) {
        unsigned char c = 0;
        ssize_t r = read(fileno(stdin), &c, 1);
        if (r <= 0) {
            if (_pipe_buf_len > 0) {
                _pipe_volcar_a_entrada();
                return 1;
            }
            return 10;  // EOF sin buffer = Ctrl+C (salir limpio)
        }
        if (c == '\r') {
            // \r puede venir solo o antes de \n
            unsigned char next = 0;
            if (read(fileno(stdin), &next, 1) == 1 && next == '\n') {
                // \r\n consumido
            }
            _pipe_volcar_a_entrada();
            return 1;
        }
        if (c == '\n') {
            _pipe_volcar_a_entrada();
            return 1;
        }
        if (c == 3) return 10;
        if (c == 0x1b) {
            unsigned char s[3] = {0, 0, 0};
            if (read(fileno(stdin), &s[0], 1) == 1 && s[0] == '[') {
                unsigned char t = 0;
                if (read(fileno(stdin), &t, 1) == 1) {
                    if (t == 'A') {
                        // Historial: navegar hacia atrás
                        if (_elen == 0 || _ecur == _elen) {
                            if (_syn_tui_historial_anterior()) {
                                const char* h = _syn_tui_historial_actual();
                                _syn_tui_entrada_poner((CadenaSegura){ .longitud = (int)strlen(h), .datos = h });
                                _ecur = _elen;
                                _pipe_buf_len = _elen;
                                if (_pipe_buf_len > 0) memcpy(_pipe_buf, _entrada, (size_t)_pipe_buf_len);
                            }
                        }
                        return 3;
                    }
                    if (t == 'B') {
                        // Historial: navegar hacia adelante
                        if (_elen == 0 || _ecur == _elen) {
                            if (_syn_tui_historial_siguiente()) {
                                const char* h = _syn_tui_historial_actual();
                                _syn_tui_entrada_poner((CadenaSegura){ .longitud = (int)strlen(h), .datos = h });
                                _ecur = _elen;
                                _pipe_buf_len = _elen;
                                if (_pipe_buf_len > 0) memcpy(_pipe_buf, _entrada, (size_t)_pipe_buf_len);
                            } else {
                                _syn_tui_entrada_borrar();
                                _pipe_buf_len = 0;
                            }
                        }
                        return 4;
                    }
                    if (t == 'C') return 6;
                    if (t == 'D') return 5;
                    return 2;
                }
            }
            return 2;
        }
        if (c == 0x7f || c == 8) {
            if (_pipe_buf_len > 0) {
                _pipe_buf_len--;
                _pipe_sincronizar();
            }
            return 7;
        }
        if (c == '\t') {
            // En modo pipe, el input actual está en _pipe_buf, no en _entrada.
            // Copiar _pipe_buf a _entrada para que _syn_tui_completar lo use.
            _entrada_asegurar();
            if (_pipe_buf_len > 0) {
                memcpy(_entrada, _pipe_buf, _pipe_buf_len);
            }
            _entrada[_pipe_buf_len] = '\0';
            _elen = _pipe_buf_len;
            _ecur = _pipe_buf_len;
            _syn_tui_completar();
            // Copiar resultado de vuelta a _pipe_buf
            _pipe_buf_len = _elen;
            if (_pipe_buf_len > 0) {
                memcpy(_pipe_buf, _entrada, _pipe_buf_len);
            }
            return 9;
        }
        if (_pipe_buf_len < ENT_MAX - 1) {
            _pipe_buf[_pipe_buf_len++] = (char)c;
            int total = 1;
            if (c >= 0xC2 && c <= 0xDF) total = 2;
            else if (c >= 0xE0 && c <= 0xEF) total = 3;
            else if (c >= 0xF0 && c <= 0xF4) total = 4;
            while (_pipe_buf_len < total && _pipe_buf_len < ENT_MAX - 1) {
                unsigned char x = 0;
                if (read(fileno(stdin), &x, 1) != 1) break;
                _pipe_buf[_pipe_buf_len++] = (char)x;
            }
        }
        return 0;
    }
    unsigned char c = 0;
    ssize_t r = read(fileno(stdin), &c, 1);
    if (r <= 0) return 1;
    if (c == 3) return 10;
    if (c == 0x1b) {
        unsigned char s[2] = {0, 0};
        if (read(fileno(stdin), &s[0], 1) == 1 && s[0] == '[') {
            unsigned char t = 0;
            if (read(fileno(stdin), &t, 1) == 1) {
                if (t == 'A') {
                    if (_elen == 0 || _ecur == _elen) {
                        if (_syn_tui_historial_anterior()) {
                            const char* h = _syn_tui_historial_actual();
                            _syn_tui_entrada_poner((CadenaSegura){ .longitud = (int)strlen(h), .datos = h });
                            _ecur = _elen;
                        }
                    }
                    return 3;
                }
                if (t == 'B') {
                    if (_elen == 0 || _ecur == _elen) {
                        if (_syn_tui_historial_siguiente()) {
                            const char* h = _syn_tui_historial_actual();
                            _syn_tui_entrada_poner((CadenaSegura){ .longitud = (int)strlen(h), .datos = h });
                            _ecur = _elen;
                        } else {
                            _syn_tui_entrada_borrar();
                        }
                    }
                    return 4;
                }
                if (t == 'C') return 6;
                if (t == 'D') return 5;
                return 2;
            }
        }
        return 2;
    }
    if (c == '\r' || c == '\n') return 1;
    if (c == 0x7f || c == 8) { _entrada_borrar_izq(); return 7; }
    if (c == '\t') {
        // En modo pipe, el input actual está en _pipe_buf, no en _entrada.
        // Copiar _pipe_buf a _entrada para que _syn_tui_completar lo use.
        _entrada_asegurar();
        if (_pipe_buf_len > 0) {
            memcpy(_entrada, _pipe_buf, _pipe_buf_len);
        }
        _entrada[_pipe_buf_len] = '\0';
        _elen = _pipe_buf_len;
        _ecur = _pipe_buf_len;
        _syn_tui_completar();
        // Copiar resultado de vuelta a _pipe_buf
        _pipe_buf_len = _elen;
        if (_pipe_buf_len > 0) {
            memcpy(_pipe_buf, _entrada, _pipe_buf_len);
        }
        return 9;
    }
    char buf[8];
    int largo = 0;
    buf[largo++] = (char)c;
    int total = 1;
    if (c >= 0xC2 && c <= 0xDF) total = 2;
    else if (c >= 0xE0 && c <= 0xEF) total = 3;
    else if (c >= 0xF0 && c <= 0xF4) total = 4;
    while (largo < total) {
        unsigned char x = 0;
        if (read(fileno(stdin), &x, 1) != 1) break;
        buf[largo++] = (char)x;
    }
    _entrada_insertar(buf, largo);
    return 0;
#endif
}

// ============================================================
// Render (dibujado completo por evento)
// ============================================================

// Construye las filas visibles del panel de mensajes (ajustadas al ancho).
// Una fila = { desvío al texto dentro del mensaje, largo, rol }.
typedef struct {
    int msg;      // índice de mensaje
    int off;      // desvío de bytes del inicio de la línea lógica
    int largo;    // bytes de la línea lógica (sin \n)
    int rol;
} _Fila;

static _Fila _filas[ROW_MAX];
static int _nfilas = 0;

// Corta una línea lógica (offset off, largo logico) en sublíneas de <= ancho
// visual, respetando espacios: corta en el último espacio que quepa (estilo
// OpenCode); si una palabra es más ancha que la línea, parte por carácter.
static void _ajustar_linea(int msg, const char* txt, int off, int largo,
                           int ancho, int* cap) {
    int i = 0;
    while (i < largo && *cap < ROW_MAX) {
        int w = 0;
        int j = i;
        int ult_esp = -1;   // posición justo DESPUÉS del último espacio que cupo
        while (j < largo) {
            int prev = j;
            long cp = _cp_leer(txt + off + j, largo - j, &j);
            int cw = _cp_ancho(cp);
            if ((cp == ' ' || cp == '\t') && w > 0 && (j - i) > 1) ult_esp = j;
            if (w + cw > ancho) break;
            w += cw;
        }
        if (j >= largo) {
            // lo que queda cabe entero
            _filas[*cap].msg = msg;
            _filas[*cap].off = off + i;
            _filas[*cap].largo = largo - i;
            _filas[*cap].rol = _msgs[msg].rol;
            (*cap)++;
            return;
        }
        if (ult_esp > i + 1) {
            // partir tras el último espacio que cupo (sin incluirlo)
            _filas[*cap].msg = msg;
            _filas[*cap].off = off + i;
            _filas[*cap].largo = ult_esp - 1 - i;
            _filas[*cap].rol = _msgs[msg].rol;
            (*cap)++;
            i = ult_esp;
            continue;
        }
        if (j <= i) {
            // un carácter aislado más ancho que la línea
            int k = i;
            _cp_leer(txt + off + k, largo - k, &k);
            if (k <= i) k = i + 1;
            if (k > largo) k = largo;
            j = k;
        }
        _filas[*cap].msg = msg;
        _filas[*cap].off = off + i;
        _filas[*cap].largo = j - i;
        _filas[*cap].rol = _msgs[msg].rol;
        (*cap)++;
        i = j;
    }
}

static void _reconstruir_filas(int ancho) {
    _nfilas = 0;
    if (ancho < 8) ancho = 8;
    int wlinea = ancho - 2;  // -2 para borde color + espacio
    if (wlinea < 2) wlinea = 2;
    for (int m = 0; m < _nmsgs && _nfilas < ROW_MAX; m++) {
        const char* t = _msgs[m].texto ? _msgs[m].texto : "";
        int len = (int)strlen(t);
        int off = 0;
        for (;;) {
            if (_nfilas >= ROW_MAX) break;
            int eol = off;
            while (eol < len && t[eol] != '\n') eol++;
            int largo = eol - off;
            if (largo > 0) {
                _ajustar_linea(m, t, off, largo, wlinea, &_nfilas);
            } else if (off < len) {
                // línea vacía explícita: respetar como separador
                if (_nfilas < ROW_MAX) {
                    _filas[_nfilas].msg = m;
                    _filas[_nfilas].off = 0;
                    _filas[_nfilas].largo = 0;
                    _filas[_nfilas].rol = _msgs[m].rol;
                    _nfilas++;
                }
            }
            off = eol + 1;
            if (off > len) break;
        }
        // separador de un renglón entre mensajes
        if (_nfilas < ROW_MAX && m + 1 < _nmsgs) {
            _filas[_nfilas].msg = -1;
            _filas[_nfilas].off = 0;
            _filas[_nfilas].largo = 0;
            _filas[_nfilas].rol = -1;
            _nfilas++;
        }
    }
}

// Escribe una fila en la fila de pantalla dada, rellenando hasta el ancho y
// limpiando el resto de la línea.
static void _dibujar_fila(int pantalla, const _Fila* f, int ancho) {
    _syn_tui_pos(pantalla, 1);
    if (f->rol < 0) {
        // separador entre mensajes: línea tenue con color
        _sgr(90);
        _out("  ");
        for (int x = 2; x < ancho && x < 40; x++) _out("\xe2\x94\x80");
        _sgr(0);
        _out("\x1b[K");
        return;
    }
    int color = 37;
    int border_color = 90;
    const char* border_ch = "\xe2\x80\xa4";  // · (default)
    switch (f->rol) {
        case 0: color = 95; border_color = 95; border_ch = "\xe2\x96\x8f"; break;  // usuario: magenta brillante, ▏
        case 1: color = 94; border_color = 94; border_ch = "\xe2\x96\x8f"; break;  // asistente: azul brillante, ▏
        case 2: color = 90; border_color = 90; border_ch = "\xe2\x80\xa2"; break;  // sistema: gris, ·
        case 3: color = 91; border_color = 91; border_ch = "\xe2\x9c\x97"; break;  // error: rojo, ✗
        case 4: color = 96; border_color = 96; border_ch = "\xe2\x9c\x93"; break;  // banner: cian, ✓
        default: color = 37; break;
    }
    // Borde izquierdo coloreado (estilo OpenCode)
    _sgr(border_color);
    _out(border_ch);
    _out(" ");
    _sgr(color);
    const char* txt = _msgs[f->msg].texto ? _msgs[f->msg].texto : "";
    int dibujado = 0;
    // Markdown-lite (rol 1 = asistente): líneas dentro de un bloque de código
    // (que abre/cierra con ``` en el MISMO mensaje) se dibujan en caja tenue;
    // bullets "- " se dibujan con viñeta colgante estilo OpenCode (Manual 7 §8).
    if (f->rol == 1 && f->largo > 0) {
        int mlen = (int)strlen(txt);
        int i = 0, en_codigo = 0;
        while (i < f->off && i < mlen) {
            int eol = i;
            while (eol < mlen && txt[eol] != '\n') eol++;
            int ll = eol - i;
            if (ll >= 3 && strncmp(txt + i, "```", 3) == 0) en_codigo = !en_codigo;
            i = (eol < mlen) ? eol + 1 : mlen;
        }
        const char* linea = txt + f->off;
        int ll = f->largo;
        if (!en_codigo && ll >= 2 && linea[0] == '-' && (linea[1] == ' ' || linea[1] == 0)) {
            _sgr(96);
            _out("• ");
            _sgr(color);
            if (ll > 2) _outn(linea + 2, ll - 2);
            dibujado = 1;
        } else if (en_codigo) {
            _sgr(90);
            _out("│ ");
            _outn(linea, ll);
            dibujado = 1;
        }
    }
    if (!dibujado && f->largo > 0) _outn(txt + f->off, f->largo);
    _sgr(0);
    _out("\x1b[K");   // borra el resto de la línea (scroll correcto)
}

static void _repintar_todo(CadenaSegura modelo) {
    _out_lock();   // exclusión mutua con el hilo del spinner
    int alto = (int)_syn_tui_alto();
    int ancho = (int)_syn_tui_ancho();
    if (alto < 10) alto = 10;
    if (ancho < 20) ancho = 20;

    _out("\x1b[2J\x1b[H");

    // ---- Encabezado (fila 1): estilo OpenCode ----
    _syn_tui_pos(1, 1);
    _out("\x1b[1;94m  \xe2\x96\xb6 OpenSyn \x1b[0m");
    _out("\x1b[90m \xe2\x94\x82 \x1b[0m");
    if (modelo.longitud > 0 && modelo.datos) {
        _sgr(95);
        _outn(modelo.datos, modelo.longitud);
        _sgr(0);
    }
    _out("\x1b[K");

    // ---- Panel de mensajes: filas 2 .. alto-4 ----
    _reconstruir_filas(ancho);
    int p1 = 2;
    int p2 = alto - 4;
    int cap = p2 - p1 + 1;
    if (cap < 1) cap = 1;
    int inicio = _nfilas > cap ? _nfilas - cap : 0;
    int fila = p1;
    for (int r = inicio; r < _nfilas; r++) {
        _dibujar_fila(fila++, &_filas[r], ancho);
    }
    while (fila <= p2) {
        _syn_tui_pos(fila, 1);
        _out("\x1b[2K");
        fila++;
    }

    // ---- Caja de entrada con borde redondeado (estilo OpenCode/Kilo) ----
    int fila_top = alto - 3;
    int fila_ent = alto - 2;
    int fila_bot = alto - 1;
    _syn_tui_pos(fila_top, 1);
    _sgr(94);
    _out("  \xe2\x95\xad");                       // ╭
    for (int x = 4; x < ancho; x++) _out("\xe2\x94\x80");   // ─
    _out("\xe2\x95\xae");                       // ╮
    _sgr(0);
    _out("\x1b[K");

    _syn_tui_pos(fila_ent, 1);
    _out("\x1b[1;95m  \xe2\x94\x82 \xe2\x9d\xaf \x1b[0m");   // │ ❯
    _entrada_asegurar();
    const char* e = _entrada ? _entrada : "";
    int plen = 5;   // columnas del prefijo "  │ ❯ "
    _syn_tui_pos(fila_bot, 1);
    _sgr(94);
    _out("  \xe2\x95\xb0");                       // ╰
    for (int x = 4; x < ancho; x++) _out("\xe2\x94\x80");   // ─
    _out("\xe2\x95\xaf");                       // ╯
    _sgr(0);
    _out("\x1b[K");
    int disp = ancho - plen - 2;
    int p = 0;
    // parte visible antes del cursor
    int antes = _ecur;
    int w_antes = _utf8_ancho(e, antes);
    int avance = 0;   // bytes consumidos al recortar por la izquierda (scroll horizontal)
    while (w_antes > disp) {
        int q = avance;
        long cp = _cp_leer(e + q, antes - q, &q);
        if (q <= avance) q = avance + 1;
        avance = q;
        w_antes = _utf8_ancho(e + avance, antes - avance);
    }
    _outn(e + avance, antes - avance);
    // cursor
    _out("\x1b[7m");
    if (antes < _elen) {
        int q = antes;
        long cp = _cp_leer(e + q, _elen - q, &q);
        int cl = (q > antes) ? q - antes : 1;
        _outn(e + antes, cl);
    } else {
        _out(" ");
    }
    _out("\x1b[0m");
    // resto
    int despues_ini = antes;
    if (antes < _elen) {
        int q = antes;
        _cp_leer(e + q, _elen - q, &q);
        despues_ini = q;
    }
    if (despues_ini < _elen) _outn(e + despues_ini, _elen - despues_ini);
    _out("\x1b[K");

    // ---- Pie (status bar dinámico estilo OpenCode/Kilo) ----
    _syn_tui_pos(alto, 1);
    _sgr(90);
    _out("  \xe2\x96\xb6 /menu");
    _sgr(0);
    _out("\x1b[90m  \xe2\x94\x82  \x1b[0m");
    _sgr(90);
    _out("\xe2\x86\x91\xe2\x86\x93 navegar");
    _sgr(0);
    _out("\x1b[90m  \xe2\x94\x82  \x1b[0m");
    _sgr(90);
    _out("Tab autocompletar");
    _sgr(0);
    _out("\x1b[90m  \xe2\x94\x82  \x1b[0m");
    _sgr(90);
    _out("Ctrl+C salir");
    _sgr(0);
    if (_tokens_ultimo > 0) {
        _out("\x1b[90m  \xe2\x94\x82  \x1b[0m");
        _sgr(36);   // cian: tokens de la última respuesta
        char tb[48];
        snprintf(tb, sizeof(tb), "~%d tok", _tokens_ultimo);
        _out(tb);
        _sgr(0);
    }
    if (_ctx_pct > 0) {
        _out("\x1b[90m  \xe2\x94\x82  \x1b[0m");
        _sgr(_ctx_pct > 80 ? 91 : 92);   // verde; rojo si contexto casi lleno
        char cb[48];
        snprintf(cb, sizeof(cb), "ctx %d%%", _ctx_pct);
        _out(cb);
        _sgr(0);
    }
    _out("\x1b[K");

    // ---- Deja el cursor en la caja de entrada ----
    int col = plen + _utf8_ancho(e + avance, antes - avance) + 1;
    if (col < 1) col = 1;
    if (col > ancho) col = ancho;
    _syn_tui_pos(fila_ent, col);
    _flush();
    _out_unlock();
}

// ============================================================
// Repintado principal (llamado desde .syn tras cada cambio)
// ============================================================

// cumple Manual 7 1.1: dibuja la TUI completa — encabezado con modelo activo,
// panel de mensajes y caja de entrada con cursor. Repintado total por evento
// (la pantalla alternativa de Windows Terminal evita el parpadeo).
void _syn_tui_repintar(CadenaSegura modelo) {
    if (!_tui_activo) return;
    _repintar_todo(modelo);
}

// ============================================================
// Menú modal (comandos "/", selector de modelos)
// ============================================================

// items: lista de líneas UTF-8 separadas por '\n'.
static int _menu_contar(const char* items) {
    int n = 0;
    if (!items || !*items) return 0;
    n = 1;
    for (const char* p = items; *p; p++) if (*p == '\n') n++;
    return n;
}

static const char* _menu_linea(const char* items, int idx, int* largo) {
    const char* p = items;
    int cur = 0;
    while (cur < idx) {
        while (*p && *p != '\n') p++;
        if (*p == '\n') p++;
        cur++;
    }
    const char* ini = p;
    while (*p && *p != '\n') p++;
    *largo = (int)(p - ini);
    return ini;
}

// cumple Manual 7 8: menú modal — flechas ↑↓, Enter selecciona, Esc cancela.
// El filtro (teclear) filtra los elementos por subcadena (estilo OpenCode).
// Retorna la línea elegida (pool_alloc) o "" si Esc/Ctrl+C.
CadenaSegura _syn_tui_menu(CadenaSegura titulo, CadenaSegura items) {
    CadenaSegura vacio = { .longitud = 0, .datos = "" };
    if (!_tui_activo) return vacio;
    int largo_items = items.longitud;
    if (largo_items < 0) largo_items = 0;
    char* buf = (char*)malloc((size_t)largo_items + 1);
    if (!buf) return vacio;
    if (largo_items > 0 && items.datos) memcpy(buf, items.datos, (size_t)largo_items);
    buf[largo_items] = '\0';
    int total = _menu_contar(buf);
    if (total <= 0) { free(buf); return vacio; }
    if (total > MENU_MAX) total = MENU_MAX;

    const char** lineas = (const char**)malloc(sizeof(char*) * (size_t)total);
    int* largos = (int*)malloc(sizeof(int) * (size_t)total);
    int* visibles = (int*)malloc(sizeof(int) * (size_t)total);
    if (!lineas || !largos || !visibles) {
        free(buf); free(lineas); free(largos); free(visibles);
        return vacio;
    }
    for (int i = 0; i < total; i++) {
        lineas[i] = _menu_linea(buf, i, &largos[i]);
        visibles[i] = 1;
    }

    char filtro[128];
    int nfiltro = 0;
    filtro[0] = '\0';
    int sel = 0;

    int titulo_largo = titulo.longitud;
    if (titulo_largo > 120) titulo_largo = 120;
    char tbuf[128];
    if (titulo_largo > 0 && titulo.datos) memcpy(tbuf, titulo.datos, (size_t)titulo_largo);
    tbuf[titulo_largo] = '\0';

    for (;;) {
        // recalcular visibles por filtro
        int nvis = 0;
        int sel_real = -1;
        for (int i = 0; i < total; i++) {
            if (nfiltro == 0) { visibles[i] = 1; nvis++; }
            else {
                int match = 0;
                for (int k = 0; k + nfiltro <= largos[i]; k++) {
                    int igual = 1;
                    for (int j = 0; j < nfiltro; j++) {
                        char a = lineas[i][k + j];
                        char b = filtro[j];
                        if (a >= 'A' && a <= 'Z') a = (char)(a - 'A' + 'a');
                        if (b >= 'A' && b <= 'Z') b = (char)(b - 'A' + 'a');
                        if (a != b) { igual = 0; break; }
                    }
                    if (igual) { match = 1; break; }
                }
                visibles[i] = match;
                if (match) nvis++;
            }
        }
        if (nvis == 0 && nfiltro > 0) {
            // nada coincide: mostrar lista vacía, permite Esc
        }
        if (sel >= total || !visibles[sel]) {
            sel = 0;
            while (sel < total && !visibles[sel]) sel++;
            if (sel >= total) sel = 0;
        }

        // dibujar overlay (lista visible)
        int alto = (int)_syn_tui_alto();
        int ancho = (int)_syn_tui_ancho();
        int mw = ancho - 8;
        if (mw > 60) mw = 60;
        if (mw < 20) mw = 20;
        int maxvis = alto - 9;
        if (maxvis > 12) maxvis = 12;
        if (maxvis < 4) maxvis = 4;
        int mh = 4 + (nvis < maxvis ? nvis : maxvis);
        if (mh > alto - 2) mh = alto - 2;
        int top = (alto - mh) / 2;
        if (top < 1) top = 1;
        int left = (ancho - mw) / 2;
        if (left < 1) left = 1;

        // fondo del overlay
        _syn_tui_pos(top, left);
        for (int r = 0; r < mh; r++) {
            _syn_tui_pos(top + r, left);
            _out("\x1b[48;5;236m");
            for (int x = 0; x < mw; x++) _out(" ");
            _out("\x1b[0m");
        }
        // marco superior/inferior
        _syn_tui_pos(top, left);
        _out("\x1b[1;37;48;5;236m");
        _out("\xe2\x94\x8c");
        for (int x = 1; x < mw - 1; x++) _out("\xe2\x94\x80");
        _out("\xe2\x94\x90\x1b[0m");
        _syn_tui_pos(top + mh - 1, left);
        _out("\x1b[1;37;48;5;236m");
        _out("\xe2\x94\x94");
        for (int x = 1; x < mw - 1; x++) _out("\xe2\x94\x80");
        _out("\xe2\x94\x98\x1b[0m");

        // título
        _syn_tui_pos(top + 1, left + 1);
        _out("\x1b[1;36;48;5;236m ");
        _outn(tbuf, titulo_largo > mw - 4 ? mw - 4 : titulo_largo);
        _out(" \x1b[0m");

        // items visibles desde el seleccionado
        int fila_act = top + 2;
        int emitidos = 0;
        for (int i = 0; i < total && emitidos < maxvis; i++) {
            if (!visibles[i]) continue;
            int es_sel = (i == sel);
            if (!es_sel && emitidos >= maxvis - 1 && i < total - 1) continue; // (scroll simple)
            _syn_tui_pos(fila_act, left + 1);
            if (es_sel) _out("\x1b[1;30;46m");
            else _out("\x1b[37;48;5;236m");
            _out(es_sel ? "> " : "  ");
            int disp = mw - 3;
            int ln = largos[i];
            int emit = ln > disp ? disp : ln;
            if (emit > 0) _outn(lineas[i], emit);
            for (int s = emit; s < disp; s++) _out(" ");
            _out("\x1b[0m");
            fila_act++;
            emitidos++;
            if (es_sel && emitidos < maxvis && nvis > maxvis) {
                // se muestra el resto tras la selección hasta llenar
            }
        }
        // scroll si hay más
        if (nvis > maxvis) {
            _syn_tui_pos(top + mh - 2, left + 1);
            _out("\x1b[90;48;5;236m  ...  \x1b[0m");
        }
        // filtro
        _syn_tui_pos(top + mh - 2 >= top + 1 ? top + mh - 2 : top + 1, left + 1);
        _out("\x1b[90;48;5;236m  \xe2\x8c\x95 ");
        if (nfiltro > 0) _out("\x1b[97;48;5;236m");
        _outn(filtro, nfiltro);
        _out("\x1b[0m");
        _flush();

        // leer evento modal
        int64_t ev = _syn_tui_evento();
        if (ev == 1) {  // Enter
            if (nvis > 0) {
                int elegido = -1;
                for (int i = 0; i < total; i++) {
                    if (visibles[i]) { elegido = i; if (i >= sel) break; }
                }
                // elegido = primer visible >= sel; si sel no visible, primer visible
                if (elegido < 0 || !visibles[sel]) {
                    for (int i = 0; i < total; i++) if (visibles[i]) { elegido = i; break; }
                }
                if (elegido >= 0 && visibles[elegido]) {
                    int ln = largos[elegido];
                    char* pool = (char*)pool_alloc((size_t)ln + 1);
                    if (pool) {
                        memcpy(pool, lineas[elegido], (size_t)ln);
                        pool[ln] = '\0';
                        free(buf); free(lineas); free(largos); free(visibles);
                        _alerts = 1;
                        return (CadenaSegura){ .longitud = ln, .datos = pool };
                    }
                }
            }
        } else if (ev == 2 || ev == 10) {  // Esc / Ctrl+C
            free(buf); free(lineas); free(largos); free(visibles);
            _alerts = 1;
            return vacio;
        } else if (ev == 3) {  // ↑
            int ant = sel - 1;
            while (ant >= 0 && !visibles[ant]) ant--;
            if (ant >= 0) sel = ant;
        } else if (ev == 4) {  // ↓
            int sig = sel + 1;
            while (sig < total && !visibles[sig]) sig++;
            if (sig < total) sel = sig;
        } else if (ev == 7) {  // retroceso → quitar del filtro
            if (nfiltro > 0) {
                nfiltro--;
                filtro[nfiltro] = '\0';
            }
        } else if (ev == 0) {  // carácter imprimible → filtro
            CadenaSegura t = _syn_tui_entrada_texto();
            // el carácter quedó en la entrada global; tomamos el último
            int tl = t.longitud;
            if (tl > 0 && t.datos && nfiltro < 120) {
                // extraer último carácter
                int p = tl;
                while (p > 0 && ((unsigned char)t.datos[p - 1] & 0xC0) == 0x80) p--;
                int cl = tl - p;
                if (nfiltro + cl < 128) {
                    memcpy(filtro + nfiltro, t.datos + p, (size_t)cl);
                    nfiltro += cl;
                    filtro[nfiltro] = '\0';
                }
            }
            // limpiar la entrada global (el filtro vive en el menú)
            _syn_tui_entrada_borrar();
        }
    }
}

// ============================================================
// Utilidades varias para .syn
// ============================================================

// Retorna 1 si hay algo pendiente de repintar (bandera de eventos).
int64_t _syn_tui_dirty(void) {
    return _alerts;
}

// Limpia toda la pantalla (usado tras el banner inicial).
void _syn_tui_limpiar(void) {
    if (!_tui_activo) return;
    _out("\x1b[2J\x1b[H");
    _flush();
}

// ============================================================
// Historial persistente (Manual 7 §1.1: UX OpenCode)
// ============================================================

// Ruta del archivo de historial: ~/.opensyn/history.jsonl
static void _hist_ruta(char* buf, int cap) {
    const char* home = getenv("USERPROFILE");
    if (!home) home = ".";
    snprintf(buf, cap, "%s/.opensyn/%s", home, HIST_FILE);
}

// Carga historial desde JSONL (una línea por entrada).
// Formato: {"ts":1234567890,"role":"user","text":"..."}
void _syn_tui_historial_cargar(void) {
    _hist_count = 0;
    _hist_saved_count = 0;
    char ruta[512];
    _hist_ruta(ruta, sizeof(ruta));
    FILE* f = fopen(ruta, "rb");
    if (!f) return;
    char line[4096];
    int dst = 0;  // C89: declarar al inicio
    int i = 0;
    while (fgets(line, sizeof(line), f) && _hist_count < HIST_MAX) {
        // Parser JSON simple para "text":"..."
        char* text_start = strstr(line, "\"text\":\"");
        if (!text_start) continue;
        text_start += 8; // saltar "text":"
        char* text_end = text_start;
        // Buscar comilla de cierre sin pasarse del buffer
        while (*text_end && *text_end != '"' && (text_end - line) < 4095) {
            if (*text_end == '\\') {
                text_end++;
                if (*text_end) text_end++;
            } else {
                text_end++;
            }
        }
        if (*text_end != '"') continue; // JSON malformado
        int len = (int)(text_end - text_start);
        if (len <= 0 || len > 4000) continue;
        char* copy = (char*)malloc(len + 1);
        if (!copy) continue;
        // Desescapar básico: \n, \", \\
        // OJO: declarar el índice local SIN sombrear variables de la función
        // (gcc -O2 elimina el 'dst = 0' previo si la declaración sombrea; eso
        // corrompía el heap en la 2ª línea: dst acumulaba la longitud previa).
        dst = 0;
        int k = 0;
        while (k < len) {
            if (text_start[k] == '\\' && k + 1 < len) {
                char c = text_start[k + 1];
                if (c == 'n') copy[dst++] = '\n';
                else if (c == '"') copy[dst++] = '"';
                else if (c == '\\') copy[dst++] = '\\';
                else copy[dst++] = c;
                k += 2; // saltar el carácter escapado
            } else {
                copy[dst++] = text_start[k];
                k++;
            }
        }
        copy[dst] = '\0';
        _hist[_hist_count].texto = copy;
        _hist[_hist_count].ts = 0; // no parseamos ts por simplicidad
        _hist_count++;
    }
    fclose(f);
    _hist_saved_count = _hist_count;
    _hist_idx = -1;
}

// Guarda entradas nuevas al historial (append).
void _syn_tui_historial_guardar(void) {
    if (_hist_count <= _hist_saved_count) return;
    char ruta[512];
    _hist_ruta(ruta, sizeof(ruta));
    // Asegurar directorio
#ifdef _WIN32
    char dir[512];
    snprintf(dir, sizeof(dir), "%s/.opensyn", getenv("USERPROFILE") ? getenv("USERPROFILE") : ".");
    CreateDirectoryA(dir, NULL);
#else
    char dir[512];
    snprintf(dir, sizeof(dir), "%s/.opensyn", getenv("HOME") ? getenv("HOME") : ".");
    mkdir(dir, 0755);
#endif
    FILE* f = fopen(ruta, "ab");
    if (!f) return;
    for (int i = _hist_saved_count; i < _hist_count; i++) {
        // Escape JSON básico
        const char* src = _hist[i].texto;
        int len = (int)strlen(src);
        fprintf(f, "{\"ts\":%lld,\"role\":\"user\",\"text\":\"", _tui_ahora_ms());
        for (int j = 0; j < len; j++) {
            char c = src[j];
            if (c == '"') fputs("\\\"", f);
            else if (c == '\\') fputs("\\\\", f);
            else if (c == '\n') fputs("\\n", f);
            else if (c == '\r') fputs("\\r", f);
            else if (c == '\t') fputs("\\t", f);
            else if ((unsigned char)c < 0x20) fprintf(f, "\\u%04x", (unsigned char)c);
            else fputc(c, f);
        }
        fputs("\"}\n", f);
    }
    fclose(f);
    _hist_saved_count = _hist_count;
}

// Añade entrada al historial en memoria (llamar al enviar input).
void _syn_tui_historial_anadir(CadenaSegura texto) {
    if (texto.datos == NULL || texto.longitud <= 0) return;
    // No guardar comandos de salida (tolerante a espacios alrededor, p.ej.
    // " salir" tecleado en modo pipe con apertura de renglón)
    int ini = 0, fin = texto.longitud;
    while (ini < fin && (texto.datos[ini] == ' ' || texto.datos[ini] == '\t')) ini++;
    while (fin > ini && (texto.datos[fin - 1] == ' ' || texto.datos[fin - 1] == '\t')) fin--;
    int len_trim = fin - ini;
    if ((len_trim == 5 && strncmp(texto.datos + ini, "salir", 5) == 0) ||
        (len_trim == 4 && strncmp(texto.datos + ini, "exit", 4) == 0)) return;
    // Evitar duplicados consecutivos
    if (_hist_count > 0 && _hist[_hist_count - 1].texto &&
        strcmp(_hist[_hist_count - 1].texto, texto.datos) == 0) return;
    // FIFO si límite alcanzado
    if (_hist_count >= HIST_MAX) {
        free(_hist[0].texto);
        memmove(_hist, _hist + 1, sizeof(_HistEntry) * (HIST_MAX - 1));
        _hist_count = HIST_MAX - 1;
    }
    char* copy = (char*)malloc(texto.longitud + 1);
    if (!copy) return;
    memcpy(copy, texto.datos, texto.longitud);
    copy[texto.longitud] = '\0';
    _hist[_hist_count].texto = copy;
    _hist[_hist_count].ts = _tui_ahora_ms();
    _hist_count++;
    _hist_idx = -1;
}

// Navega al anterior (más viejo). Retorna 1 si hay cambio, 0 si no.
int _syn_tui_historial_anterior(void) {
    if (_hist_count == 0) return 0;
    if (_hist_idx == -1) {
        _hist_idx = _hist_count - 1;
    } else if (_hist_idx > 0) {
        _hist_idx--;
    } else {
        return 0;
    }
    return 1;
}

// Navega al siguiente (más nuevo). Retorna 1 si hay cambio, 0 si no.
int _syn_tui_historial_siguiente(void) {
    if (_hist_count == 0 || _hist_idx == -1) return 0;
    if (_hist_idx < _hist_count - 1) {
        _hist_idx++;
        return 1;
    } else {
        // Volver a entrada actual (vacía)
        _hist_idx = -1;
        return 1;
    }
}

// Obtiene la entrada actual del historial (para poner en la caja de entrada).
const char* _syn_tui_historial_actual(void) {
    if (_hist_idx >= 0 && _hist_idx < _hist_count) return _hist[_hist_idx].texto;
    return "";
}

// ============================================================
// Autocompletado Tab (Manual 7 §8: UX asistente)
// ============================================================

// Libera completaciones previas
void _comp_limpiar(void) {
    for (int i = 0; i < _comp.count; i++) free(_comp.items[i]);
    _comp.count = 0;
    _comp.common_len = 0;
}

// Añade una completación
static void _comp_anadir(const char* s) {
    if (_comp.count >= COMP_MAX) return;
    char* copy = (char*)malloc(strlen(s) + 1);
    if (!copy) return;
    strcpy(copy, s);
    _comp.items[_comp.count++] = copy;
}

// Calcula prefijo común de todas las completaciones
static void _comp_calcular_comun(void) {
    if (_comp.count == 0) { _comp.common_len = 0; return; }
    _comp.common_len = (int)strlen(_comp.items[0]);
    for (int i = 1; i < _comp.count; i++) {
        int j = 0;
        while (j < _comp.common_len && j < (int)strlen(_comp.items[i]) && _comp.items[0][j] == _comp.items[i][j]) j++;
        _comp.common_len = j;
    }
}

// Completa comandos que empiezan con '/'
static void _comp_comandos(const char* prefix) {
    const char* cmds[] = {"/model", "/modelos", "/tdd", "/revisar", "/plan", "/skills", "/ayuda", "/salir"};
    for (int i = 0; i < 8; i++) {
        if (strncmp(cmds[i], prefix, strlen(prefix)) == 0) _comp_anadir(cmds[i]);
    }
}

// Completa rutas relativas desde cwd
static void _comp_rutas(const char* prefix) {
    // Usar _syn_listar_directorio via asm desde .syn no es posible aquí en C puro.
    // Implementación simple: scan directorio actual con FindFirstFile / opendir.
    // Para rutas con '/', tomar directorio base y filtrar.
    const char* base = ".";
    const char* name_start = prefix;
    const char* last_slash = strrchr(prefix, '/');
#ifdef _WIN32
    const char* last_backslash = strrchr(prefix, '\\');
    if (last_backslash > last_slash) last_slash = last_backslash;
#endif
    if (last_slash) {
        int base_len = (int)(last_slash - prefix + 1);
        char* base_copy = (char*)malloc(base_len + 1);
        if (!base_copy) return;
        memcpy(base_copy, prefix, base_len);
        base_copy[base_len] = '\0';
        // Normalize to native separator
#ifdef _WIN32
        for (int i = 0; i < base_len; i++) if (base_copy[i] == '/') base_copy[i] = '\\';
#endif
        base = base_copy;
        name_start = last_slash + 1;
    }
#ifdef _WIN32
    WIN32_FIND_DATAA fd;
    char pattern[512];
    snprintf(pattern, sizeof(pattern), "%s\\*", base);
    HANDLE h = FindFirstFileA(pattern, &fd);
    if (h != INVALID_HANDLE_VALUE) {
        do {
            if (strcmp(fd.cFileName, ".") == 0 || strcmp(fd.cFileName, "..") == 0) continue;
            if (strncmp(fd.cFileName, name_start, strlen(name_start)) == 0) {
                char full[512];
                const char* rest = fd.cFileName + strlen(name_start);
                snprintf(full, sizeof(full), "%s%s", prefix, rest);
                // Si es directorio, añadir '/' al final para seguir completando
                char check[512];
                snprintf(check, sizeof(check), "%s\\%s", base, fd.cFileName);
                DWORD attr = GetFileAttributesA(check);
                if (attr != INVALID_FILE_ATTRIBUTES && (attr & FILE_ATTRIBUTE_DIRECTORY)) {
                    strcat(full, "/");
                }
                _comp_anadir(full);
            }
        } while (FindNextFileA(h, &fd));
        FindClose(h);
    }
    if (last_slash) free((void*)base);
#else
    DIR* d = opendir(base);
    if (d) {
        struct dirent* ent;
        while ((ent = readdir(d)) && _comp.count < COMP_MAX) {
            if (strcmp(ent->d_name, ".") == 0 || strcmp(ent->d_name, "..") == 0) continue;
            if (strncmp(ent->d_name, name_start, strlen(name_start)) == 0) {
                char full[512];
                const char* rest = ent->d_name + strlen(name_start);
                snprintf(full, sizeof(full), "%s%s", prefix, rest);
                char check[512];
                snprintf(check, sizeof(check), "%s/%s", base, ent->d_name);
                struct stat st;
                if (stat(check, &st) == 0 && S_ISDIR(st.st_mode)) strcat(full, "/");
                _comp_anadir(full);
            }
        }
        closedir(d);
    }
    if (last_slash) free((void*)base);
#endif
}

// API pública: invocar autocompletado (llamada desde _syn_tui_evento en Tab)
void _syn_tui_completar(void) {
    _comp_limpiar();
    _entrada_asegurar();
    const char* input = _entrada ? _entrada : "";
    if (!input || !*input) return;
    // Detectar doble Tab (mismo timestamp ~ 300ms)
    long long ahora = _tui_ahora_ms();
    int doble_tab = (ahora - _last_tab_time < 300);
    _last_tab_time = (int)ahora;
    if (input[0] == '/') {
        _comp_comandos(input);
    } else {
        _comp_rutas(input);
    }
    if (_comp.count == 0) return;
    _comp_calcular_comun();
    const char* current = input;
    int cur_len = (int)strlen(current);
    if (_comp.common_len > cur_len) {
        // Completar hasta prefijo común
        char* completion = _comp.items[0] + cur_len;
        int comp_len = _comp.common_len - cur_len;
        if (comp_len > 0) {
            // Insertar en entrada
            _entrada_insertar(completion, comp_len);
        }
    }
    if (doble_tab && _comp.count > 1) {
        // Segundo Tab: abrir menú modal con opciones
        // Construir string con items separados por \n
        int total_len = 0;
        for (int i = 0; i < _comp.count; i++) total_len += (int)strlen(_comp.items[i]) + 1;
        char* menu_items = (char*)malloc(total_len + 1);
        if (menu_items) {
            int pos = 0;
            for (int i = 0; i < _comp.count; i++) {
                int l = (int)strlen(_comp.items[i]);
                memcpy(menu_items + pos, _comp.items[i], l);
                pos += l;
                menu_items[pos++] = '\n';
            }
            menu_items[pos] = '\0';
            // Llamar menú modal (requiere _tui_activo)
            if (_tui_activo) {
                CadenaSegura titulo = { .longitud = (int)strlen("Completar"), .datos = "Completar" };
                CadenaSegura items = { .longitud = pos, .datos = menu_items };
                CadenaSegura elegido = _syn_tui_menu(titulo, items);
                if (elegido.longitud > 0 && elegido.datos) {
                    // Reemplazar entrada completa con lo elegido
                    _syn_tui_entrada_borrar();
                    _syn_tui_entrada_poner(elegido);
                }
            }
            free(menu_items);
        }
    }
}
