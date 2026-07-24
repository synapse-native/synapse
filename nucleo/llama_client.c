// llama_client.c — Cliente HTTP nativo para llama.cpp server (API /completion, /slot_save, /slot_restore, /embedding)
// WinHTTP en Windows, sockets POSIX en Linux/macOS
// API nativa llama.cpp con payload JSON estricto: {"prompt":"...", "n_predict":128, "temperature":0.7, "stop":["\n\n\n"]}

#include "llama_client.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#ifdef _WIN32
    #include <windows.h>
    #include <winhttp.h>
    #ifdef _MSC_VER
    #pragma comment(lib, "winhttp.lib")
    #endif
#else
    #include <unistd.h>
    #include <sys/socket.h>
    #include <netinet/in.h>
    #include <arpa/inet.h>
    #include <netdb.h>
    #include <fcntl.h>
    #include <errno.h>
#endif

// Configuración por defecto
#define LLAMA_DEFAULT_HOST "127.0.0.1"
#define LLAMA_DEFAULT_PORT 8088
#define LLAMA_TIMEOUT_MS 30000

// Estructuras internas
struct LlamaClient {
    char* host;
    int puerto;
#ifdef _WIN32
    HINTERNET hSession;
    HINTERNET hConnect;
#endif
};

// JSON helpers simples
static char* json_escape(const char* input) {
    if (!input) return strdup("");
    size_t len = strlen(input);
    char* output = (char*)malloc(len * 2 + 1);
    if (!output) return NULL;
    char* dst = output;
    for (size_t i = 0; i < len; i++) {
        char c = input[i];
        switch (c) {
            case '"': *dst++ = '\\'; *dst++ = '"'; break;
            case '\\': *dst++ = '\\'; *dst++ = '\\'; break;
            case '\n': *dst++ = '\\'; *dst++ = 'n'; break;
            case '\r': *dst++ = '\\'; *dst++ = 'r'; break;
            case '\t': *dst++ = '\\'; *dst++ = 't'; break;
            default: *dst++ = c; break;
        }
    }
    *dst = '\0';
    return output;
}

static char* extract_json_field(const char* json, const char* field) {
    if (!json || !field) return NULL;
    char search[128];
    snprintf(search, sizeof(search), "\"%s\":", field);
    char* start = strstr(json, search);
    if (!start) return NULL;
    start += strlen(search);
    while (*start == ' ' || *start == '\t') start++;
    if (*start != '"') return NULL;
    start++;
    char* end = start;
    while (*end && !(*end == '"' && *(end-1) != '\\')) end++;
    size_t len = end - start;
    char* result = (char*)malloc(len + 1);
    if (!result) return NULL;
    memcpy(result, start, len);
    result[len] = '\0';
    char* dst = result;
    for (char* src = result; *src; src++) {
        if (*src == '\\' && *(src+1)) {
            src++;
            switch (*src) {
                case 'n': *dst++ = '\n'; break;
                case 'r': *dst++ = '\r'; break;
                case 't': *dst++ = '\t'; break;
                case '"': *dst++ = '"'; break;
                case '\\': *dst++ = '\\'; break;
                default: *dst++ = *src; break;
            }
        } else {
            *dst++ = *src;
        }
    }
    *dst = '\0';
    return result;
}

static float* extract_json_embeddings(const char* json, int* out_count, int* out_dim) {
    if (!json) return NULL;
    char* embeddings_start = strstr(json, "\"embedding\":");
    if (!embeddings_start) return NULL;
    embeddings_start = strchr(embeddings_start, '[');
    if (!embeddings_start) return NULL;
    embeddings_start++;
    
    float* embeddings = NULL;
    int count = 0;
    int capacity = 16;
    embeddings = (float*)malloc(capacity * sizeof(float));
    if (!embeddings) return NULL;
    
    char* ptr = embeddings_start;
    while (*ptr && *ptr != ']') {
        while (*ptr == ' ' || *ptr == '\t' || *ptr == '\n' || *ptr == ',') ptr++;
        if (*ptr == ']') break;
        char* end;
        float val = strtof(ptr, &end);
        if (end == ptr) break;
        if (count >= capacity) {
            capacity *= 2;
            float* new_emb = (float*)realloc(embeddings, capacity * sizeof(float));
            if (!new_emb) { free(embeddings); return NULL; }
            embeddings = new_emb;
        }
        embeddings[count++] = val;
        ptr = end;
    }
    
    if (out_count) *out_count = count;
    if (out_dim) *out_dim = (count > 0) ? count : 0;
    return embeddings;
}

// HTTP request genérico (síncrono, no streaming)
#ifdef _WIN32
static int http_post_winhttp(LlamaClient* cli, const char* path, const char* body, char** out_response, int* out_status) {
    if (!cli->hSession) {
        cli->hSession = WinHttpOpen(L"Synapse-LSP/1.0", WINHTTP_ACCESS_TYPE_DEFAULT_PROXY, WINHTTP_NO_PROXY_NAME, WINHTTP_NO_PROXY_BYPASS, 0);
        if (!cli->hSession) return 0;
    }
    if (!cli->hConnect) {
        int wlen = MultiByteToWideChar(CP_UTF8, 0, cli->host, -1, NULL, 0);
        wchar_t* whost = (wchar_t*)malloc(wlen * sizeof(wchar_t));
        MultiByteToWideChar(CP_UTF8, 0, cli->host, -1, whost, wlen);
        cli->hConnect = WinHttpConnect(cli->hSession, whost, (INTERNET_PORT)cli->puerto, 0);
        free(whost);
        if (!cli->hConnect) return 0;
    }

    int wlen = MultiByteToWideChar(CP_UTF8, 0, path, -1, NULL, 0);
    wchar_t* wpath = (wchar_t*)malloc(wlen * sizeof(wchar_t));
    MultiByteToWideChar(CP_UTF8, 0, path, -1, wpath, wlen);

    HINTERNET hRequest = WinHttpOpenRequest(cli->hConnect, L"POST", wpath, NULL, WINHTTP_NO_REFERER, WINHTTP_DEFAULT_ACCEPT_TYPES, 0);
    free(wpath);
    if (!hRequest) return 0;

    const wchar_t* headers = L"Content-Type: application/json\r\n";
    int body_len = (int)strlen(body);

    WinHttpSetTimeouts(hRequest, 5000, 30000, 30000, 30000);

    BOOL sent = WinHttpSendRequest(hRequest, headers, -1, (LPVOID)body, body_len, body_len, 0);
    if (!sent) {
        WinHttpCloseHandle(hRequest);
        return 0;
    }

    BOOL recv = WinHttpReceiveResponse(hRequest, NULL);
    if (!recv) {
        WinHttpCloseHandle(hRequest);
        return 0;
    }

    DWORD statusCode = 0;
    DWORD statusSize = sizeof(statusCode);
    WinHttpQueryHeaders(hRequest, WINHTTP_QUERY_STATUS_CODE | WINHTTP_QUERY_FLAG_NUMBER, WINHTTP_HEADER_NAME_BY_INDEX, &statusCode, &statusSize, WINHTTP_NO_HEADER_INDEX);
    if (out_status) *out_status = (int)statusCode;

    DWORD totalRead = 0;
    DWORD bufferSize = 8192;
    char* buffer = (char*)malloc(bufferSize);
    if (!buffer) {
        WinHttpCloseHandle(hRequest);
        return 0;
    }

    while (1) {
        DWORD available = 0;
        if (!WinHttpQueryDataAvailable(hRequest, &available)) break;
        if (available == 0) break;

        if (totalRead + available + 1 > bufferSize) {
            bufferSize = totalRead + available + 4096;
            char* newBuf = (char*)realloc(buffer, bufferSize);
            if (!newBuf) break;
            buffer = newBuf;
        }

        DWORD read = 0;
        if (!WinHttpReadData(hRequest, buffer + totalRead, available, &read)) break;
        totalRead += read;
        if (read < available) break;
    }

    WinHttpCloseHandle(hRequest);
    buffer[totalRead] = '\0';
    *out_response = buffer;
    return 1;
}
#else
static int http_post_posix(LlamaClient* cli, const char* path, const char* body, char** out_response, int* out_status) {
    int sock = socket(AF_INET, SOCK_STREAM, 0);
    if (sock < 0) return 0;

    struct sockaddr_in addr = {0};
    addr.sin_family = AF_INET;
    addr.sin_port = htons((unsigned short)cli->puerto);
    addr.sin_addr.s_addr = inet_addr(cli->host);

    struct timeval tv = {30, 0};
    setsockopt(sock, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));
    setsockopt(sock, SOL_SOCKET, SO_SNDTIMEO, &tv, sizeof(tv));

    if (connect(sock, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
        close(sock);
        return 0;
    }

    char request[8192];
    int req_len = snprintf(request, sizeof(request),
        "POST %s HTTP/1.1\r\n"
        "Host: %s:%d\r\n"
        "Content-Type: application/json\r\n"
        "Content-Length: %zu\r\n"
        "Connection: close\r\n"
        "\r\n"
        "%s",
        path, cli->host, cli->puerto, strlen(body), body);

    if (send(sock, request, req_len, 0) != req_len) {
        close(sock);
        return 0;
    }

    char* buffer = (char*)malloc(8192);
    size_t bufSize = 8192;
    size_t total = 0;
    while (1) {
        if (total + 1024 >= bufSize) {
            bufSize *= 2;
            char* newBuf = (char*)realloc(buffer, bufSize);
            if (!newBuf) break;
            buffer = newBuf;
        }
        int n = recv(sock, buffer + total, 1024, 0);
        if (n <= 0) break;
        total += n;
    }
    close(sock);
    buffer[total] = '\0';

    if (out_status) {
        char* statusPtr = strstr(buffer, "HTTP/1.1 ");
        if (statusPtr) *out_status = atoi(statusPtr + 9);
    }

    char* bodyPtr = strstr(buffer, "\r\n\r\n");
    if (bodyPtr) {
        *out_response = strdup(bodyPtr + 4);
    } else {
        *out_response = strdup("");
    }
    free(buffer);
    return 1;
}
#endif

// Implementación pública

int llama_inicializar_red(void) {
#ifdef _WIN32
    WSADATA wsa;
    return WSAStartup(MAKEWORD(2,2), &wsa) == 0;
#else
    return 1;
#endif
}

void llama_cerrar_red(void) {
#ifdef _WIN32
    WSACleanup();
#endif
}

LlamaClient* llama_cliente_crear(const char* host, int puerto) {
    LlamaClient* cli = (LlamaClient*)calloc(1, sizeof(LlamaClient));
    if (!cli) return NULL;

    cli->host = host ? strdup(host) : strdup(LLAMA_DEFAULT_HOST);
    cli->puerto = puerto > 0 ? puerto : LLAMA_DEFAULT_PORT;
#ifdef _WIN32
    cli->hSession = NULL;
    cli->hConnect = NULL;
#endif
    return cli;
}

void llama_cliente_destruir(LlamaClient* cli) {
    if (!cli) return;
#ifdef _WIN32
    if (cli->hConnect) WinHttpCloseHandle(cli->hConnect);
    if (cli->hSession) WinHttpCloseHandle(cli->hSession);
#endif
    free(cli->host);
    free(cli);
}

// === /completion ===
LlamaRespuesta llama_generar(LlamaClient* cliente, const char* prompt_ensamblado,
                              int n_predict, double temperature,
                              const char** stop, int stop_count) {
    LlamaRespuesta resp = {0};

    if (!cliente || !prompt_ensamblado) {
        resp.es_ok = 0;
        resp.error = strdup("Cliente o prompt inválido");
        return resp;
    }

    if (n_predict <= 0) n_predict = 128;
    if (temperature < 0.0) temperature = 0.7;

    char* escaped = json_escape(prompt_ensamblado);
    if (!escaped) {
        resp.es_ok = 0;
        resp.error = strdup("Error de memoria escapando prompt");
        return resp;
    }

    char* stop_json = NULL;
    if (stop && stop_count > 0) {
        size_t stop_len = 2;
        for (int i = 0; i < stop_count; i++) {
            if (stop[i]) stop_len += strlen(stop[i]) + 4;
        }
        stop_json = (char*)malloc(stop_len);
        if (stop_json) {
            char* dst = stop_json;
            *dst++ = '[';
            for (int i = 0; i < stop_count; i++) {
                if (i > 0) *dst++ = ',';
                *dst++ = '"';
                if (stop[i]) {
                    char* esc = json_escape(stop[i]);
                    if (esc) {
                        strcpy(dst, esc);
                        dst += strlen(esc);
                        free(esc);
                    }
                }
                *dst++ = '"';
            }
            *dst++ = ']';
            *dst = '\0';
        }
    } else {
        stop_json = strdup("[]");
    }

    size_t payload_size = strlen(escaped) + (stop_json ? strlen(stop_json) : 2) + 256;
    char* payload = (char*)malloc(payload_size);
    if (!payload) {
        free(escaped);
        free(stop_json);
        resp.es_ok = 0;
        resp.error = strdup("Error de memoria construyendo payload");
        return resp;
    }

    snprintf(payload, payload_size,
        "{\"prompt\":\"%s\",\"n_predict\":%d,\"temperature\":%.2f,\"stop\":%s}",
        escaped, n_predict, temperature, stop_json ? stop_json : "[]");

    free(escaped);
    free(stop_json);

    char* response = NULL;
    int status = 0;
    int ok = 0;

#ifdef _WIN32
    ok = http_post_winhttp(cliente, "/completion", payload, &response, &status);
#else
    ok = http_post_posix(cliente, "/completion", payload, &response, &status);
#endif

    free(payload);

    if (!ok) {
        resp.es_ok = 0;
        resp.error = strdup("Error en petición HTTP");
        resp.codigo_http = 0;
        return resp;
    }

    resp.codigo_http = status;

    if (status != 200) {
        resp.es_ok = 0;
        resp.error = response ? response : strdup("Error HTTP sin cuerpo");
        return resp;
    }

    char* content = extract_json_field(response, "content");
    free(response);

    if (!content) {
        resp.es_ok = 0;
        resp.error = strdup("Respuesta JSON inválida: sin campo 'content'");
        return resp;
    }

    resp.es_ok = 1;
    resp.respuesta = content;
    resp.error = NULL;
    return resp;
}

void llama_libre_respuesta(LlamaRespuesta* resp) {
    if (!resp) return;
    free(resp->respuesta);
    free(resp->error);
    resp->respuesta = NULL;
    resp->error = NULL;
}

// === /slot_save ===
LlamaSlotSaveRespuesta llama_slot_guardar(LlamaClient* cliente, int slot) {
    LlamaSlotSaveRespuesta resp = {0};

    if (!cliente) {
        resp.es_ok = 0;
        resp.error = strdup("Cliente inválido");
        return resp;
    }

    char payload[64];
    snprintf(payload, sizeof(payload), "{\"slot\":%d}", slot);

    char* response = NULL;
    int status = 0;
    int ok = 0;

#ifdef _WIN32
    ok = http_post_winhttp(cliente, "/slot_save", payload, &response, &status);
#else
    ok = http_post_posix(cliente, "/slot_save", payload, &response, &status);
#endif

    if (!ok) {
        resp.es_ok = 0;
        resp.error = strdup("Error en petición HTTP");
        resp.codigo_http = 0;
        return resp;
    }

    resp.codigo_http = status;

    if (status != 200) {
        resp.es_ok = 0;
        resp.error = response ? response : strdup("Error HTTP sin cuerpo");
        return resp;
    }

    char* slot_id = extract_json_field(response, "slot_id");
    free(response);

    if (!slot_id) {
        resp.es_ok = 0;
        resp.error = strdup("Respuesta JSON inválida: sin campo 'slot_id'");
        return resp;
    }

    resp.es_ok = 1;
    resp.slot_id = slot_id;
    resp.error = NULL;
    return resp;
}

void llama_libre_slot_save(LlamaSlotSaveRespuesta* resp) {
    if (!resp) return;
    free(resp->slot_id);
    free(resp->error);
    resp->slot_id = NULL;
    resp->error = NULL;
}

// === /slot_restore ===
LlamaSlotRestoreRespuesta llama_slot_restaurar(LlamaClient* cliente, int slot, const char* slot_id,
                                                const char* prompt_ensamblado,
                                                int n_predict, double temperature,
                                                const char** stop, int stop_count) {
    LlamaSlotRestoreRespuesta resp = {0};

    if (!cliente || !slot_id || !prompt_ensamblado) {
        resp.es_ok = 0;
        resp.error = strdup("Parámetros inválidos");
        return resp;
    }

    if (n_predict <= 0) n_predict = 128;
    if (temperature < 0.0) temperature = 0.7;

    char* escaped = json_escape(prompt_ensamblado);
    if (!escaped) {
        resp.es_ok = 0;
        resp.error = strdup("Error de memoria escapando prompt");
        return resp;
    }

    char* stop_json = NULL;
    if (stop && stop_count > 0) {
        size_t stop_len = 2;
        for (int i = 0; i < stop_count; i++) {
            if (stop[i]) stop_len += strlen(stop[i]) + 4;
        }
        stop_json = (char*)malloc(stop_len);
        if (stop_json) {
            char* dst = stop_json;
            *dst++ = '[';
            for (int i = 0; i < stop_count; i++) {
                if (i > 0) *dst++ = ',';
                *dst++ = '"';
                if (stop[i]) {
                    char* esc = json_escape(stop[i]);
                    if (esc) {
                        strcpy(dst, esc);
                        dst += strlen(esc);
                        free(esc);
                    }
                }
                *dst++ = '"';
            }
            *dst++ = ']';
            *dst = '\0';
        }
    } else {
        stop_json = strdup("[]");
    }

    char* slot_id_escaped = json_escape(slot_id);

    size_t payload_size = strlen(escaped) + strlen(slot_id_escaped) + (stop_json ? strlen(stop_json) : 2) + 256;
    char* payload = (char*)malloc(payload_size);
    if (!payload) {
        free(escaped);
        free(stop_json);
        free(slot_id_escaped);
        resp.es_ok = 0;
        resp.error = strdup("Error de memoria construyendo payload");
        return resp;
    }

    snprintf(payload, payload_size,
        "{\"slot\":%d,\"slot_id\":\"%s\",\"prompt\":\"%s\",\"n_predict\":%d,\"temperature\":%.2f,\"stop\":%s}",
        slot, slot_id_escaped, escaped, n_predict, temperature, stop_json ? stop_json : "[]");

    free(escaped);
    free(stop_json);
    free(slot_id_escaped);

    char* response = NULL;
    int status = 0;
    int ok = 0;

#ifdef _WIN32
    ok = http_post_winhttp(cliente, "/slot_restore", payload, &response, &status);
#else
    ok = http_post_posix(cliente, "/slot_restore", payload, &response, &status);
#endif

    free(payload);

    if (!ok) {
        resp.es_ok = 0;
        resp.error = strdup("Error en petición HTTP");
        resp.codigo_http = 0;
        return resp;
    }

    resp.codigo_http = status;

    if (status != 200) {
        resp.es_ok = 0;
        resp.error = response ? response : strdup("Error HTTP sin cuerpo");
        return resp;
    }

    char* content = extract_json_field(response, "content");
    free(response);

    if (!content) {
        resp.es_ok = 0;
        resp.error = strdup("Respuesta JSON inválida: sin campo 'content'");
        return resp;
    }

    resp.es_ok = 1;
    resp.respuesta = content;
    resp.error = NULL;
    return resp;
}

void llama_libre_slot_restore(LlamaSlotRestoreRespuesta* resp) {
    if (!resp) return;
    free(resp->respuesta);
    free(resp->error);
    resp->respuesta = NULL;
    resp->error = NULL;
}

// === /embedding ===
LlamaEmbeddingRespuesta llama_embedding(LlamaClient* cliente, const char* input) {
    LlamaEmbeddingRespuesta resp = {0};

    if (!cliente || !input) {
        resp.es_ok = 0;
        resp.error = strdup("Parámetros inválidos");
        return resp;
    }

    char* escaped = json_escape(input);
    if (!escaped) {
        resp.es_ok = 0;
        resp.error = strdup("Error de memoria escapando input");
        return resp;
    }

    size_t payload_size = strlen(escaped) + 64;
    char* payload = (char*)malloc(payload_size);
    if (!payload) {
        free(escaped);
        resp.es_ok = 0;
        resp.error = strdup("Error de memoria construyendo payload");
        return resp;
    }

    snprintf(payload, payload_size, "{\"input\":\"%s\"}", escaped);
    free(escaped);

    char* response = NULL;
    int status = 0;
    int ok = 0;

#ifdef _WIN32
    ok = http_post_winhttp(cliente, "/embedding", payload, &response, &status);
#else
    ok = http_post_posix(cliente, "/embedding", payload, &response, &status);
#endif

    free(payload);

    if (!ok) {
        resp.es_ok = 0;
        resp.error = strdup("Error en petición HTTP");
        resp.codigo_http = 0;
        return resp;
    }

    resp.codigo_http = status;

    if (status != 200) {
        resp.es_ok = 0;
        resp.error = response ? response : strdup("Error HTTP sin cuerpo");
        return resp;
    }

    int count = 0, dim = 0;
    float* embeddings = extract_json_embeddings(response, &count, &dim);
    free(response);

    if (!embeddings) {
        resp.es_ok = 0;
        resp.error = strdup("Respuesta JSON inválida: sin embeddings");
        return resp;
    }

    resp.es_ok = 1;
    resp.embeddings = embeddings;
    resp.embedding_count = count;
    resp.embedding_dim = dim;
    resp.error = NULL;
    return resp;
}

void llama_libre_embedding(LlamaEmbeddingRespuesta* resp) {
    if (!resp) return;
    free(resp->embeddings);
    free(resp->error);
    resp->embeddings = NULL;
    resp->error = NULL;
    resp->embedding_count = 0;
    resp->embedding_dim = 0;
}

int llama_verificar_disponible(LlamaClient* cliente) {
    if (!cliente) return 0;

    char* response = NULL;
    int status = 0;
    int ok = 0;

#ifdef _WIN32
    ok = http_post_winhttp(cliente, "/health", "{}", &response, &status);
#else
    ok = http_post_posix(cliente, "/health", "{}", &response, &status);
#endif

    if (response) free(response);
    return (ok && status == 200);
}

char* llama_obtener_props(LlamaClient* cliente) {
    if (!cliente) return NULL;

    char* response = NULL;
    int status = 0;
    int ok = 0;

#ifdef _WIN32
    ok = http_post_winhttp(cliente, "/props", "{}", &response, &status);
#else
    ok = http_post_posix(cliente, "/props", "{}", &response, &status);
#endif

    if (!ok || status != 200) {
        if (response) free(response);
        return NULL;
    }
    return response;
}