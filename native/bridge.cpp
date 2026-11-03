#include "llama.h"
#include "llama-sampler.h"
#include <algorithm>
#include <cstdlib>
#include <cstring>
#include <mutex>
#include <new>
#include <string>
#include <vector>

#if defined(_WIN32)
#define API __declspec(dllexport)
#else
#define API __attribute__((visibility("default")))
#endif

static llama_model * g_model = nullptr;
static llama_context * g_ctx = nullptr;
static std::mutex g_mutex;
static std::string g_error;
static bool g_backend_initialized = false;

static void set_error(const std::string & message) { g_error = message; }

static void release_context() {
    if (g_ctx) {
        llama_free(g_ctx);
        g_ctx = nullptr;
    }
}

static void release_model() {
    release_context();
    if (g_model) {
        llama_model_free(g_model);
        g_model = nullptr;
    }
}

extern "C" {

API int essay_llama_load(const char * model_path, int n_ctx, int n_threads) {
    std::lock_guard<std::mutex> guard(g_mutex);
    if (!model_path || std::strlen(model_path) == 0) {
        set_error("Не указан путь к файлу модели.");
        return 1;
    }
    release_model();
    if (!g_backend_initialized) {
        llama_backend_init();
        g_backend_initialized = true;
    }

    llama_model_params model_params = llama_model_default_params();
    model_params.n_gpu_layers = 0; // безопасный CPU-режим, работает без отдельной GPU-сборки.
    g_model = llama_model_load_from_file(model_path, model_params);
    if (!g_model) {
        set_error("llama.cpp не смог открыть GGUF. Проверь целостность файла модели и свободную память.");
        return 2;
    }

    llama_context_params context_params = llama_context_default_params();
    context_params.n_ctx = static_cast<uint32_t>(std::max(2048, n_ctx));
    context_params.n_batch = 512;
    context_params.n_ubatch = 256;
    context_params.n_threads = std::max(2, n_threads);
    context_params.n_threads_batch = std::max(2, n_threads);
    context_params.no_perf = true;
    g_ctx = llama_init_from_model(g_model, context_params);
    if (!g_ctx) {
        release_model();
        set_error("Не удалось создать контекст ИИ. Попробуй уменьшить контекст или закрыть другие приложения.");
        return 3;
    }
    set_error("");
    return 0;
}

API const char * essay_llama_last_error() {
    return g_error.c_str();
}

API void essay_llama_free_string(void * value) {
    std::free(value);
}

API void essay_llama_unload() {
    std::lock_guard<std::mutex> guard(g_mutex);
    release_model();
}

API void * essay_llama_generate(const char * prompt, int max_tokens, float temperature, float top_p) {
    std::lock_guard<std::mutex> guard(g_mutex);
    if (!g_model || !g_ctx || !prompt) {
        set_error("Модель не загружена. Перезапусти локальный ИИ.");
        return nullptr;
    }

    llama_memory_clear(llama_get_memory(g_ctx), true);
    const llama_vocab * vocab = llama_model_get_vocab(g_model);
    const std::string input(prompt);
    const int n_prompt = -llama_tokenize(vocab, input.c_str(), input.size(), nullptr, 0, true, true);
    if (n_prompt <= 0) {
        set_error("Не удалось разобрать входной текст.");
        return nullptr;
    }
    if (static_cast<uint32_t>(n_prompt + max_tokens) > llama_n_ctx(g_ctx)) {
        set_error("Запрос слишком длинный для текущего контекста. Сократи текст или раздели его на части.");
        return nullptr;
    }

    std::vector<llama_token> prompt_tokens(static_cast<size_t>(n_prompt));
    const int actual = llama_tokenize(vocab, input.c_str(), input.size(), prompt_tokens.data(), prompt_tokens.size(), true, true);
    if (actual < 0) {
        set_error("Не удалось токенизировать запрос.");
        return nullptr;
    }

    llama_batch batch = llama_batch_get_one(prompt_tokens.data(), actual);
    if (llama_decode(g_ctx, batch) != 0) {
        set_error("Ошибка обработки текста моделью. Попробуй сократить запрос.");
        return nullptr;
    }

    llama_sampler_chain_params sampler_params = llama_sampler_chain_default_params();
    llama_sampler * sampler = llama_sampler_chain_init(sampler_params);
    if (!sampler) {
        set_error("Не удалось создать механизм генерации.");
        return nullptr;
    }
    llama_sampler_chain_add(sampler, llama_sampler_init_top_k(40));
    llama_sampler_chain_add(sampler, llama_sampler_init_top_p(std::min(1.0f, std::max(0.1f, top_p)), 1));
    llama_sampler_chain_add(sampler, llama_sampler_init_temp(std::max(0.05f, temperature)));
    llama_sampler_chain_add(sampler, llama_sampler_init_dist(LLAMA_DEFAULT_SEED));

    std::string output;
    bool decode_error = false;
    output.reserve(static_cast<size_t>(std::max(256, max_tokens * 5)));
    llama_token next_token = 0;
    char piece[512];
    for (int i = 0; i < max_tokens; ++i) {
        next_token = llama_sampler_sample(sampler, g_ctx, -1);
        if (llama_vocab_is_eog(vocab, next_token)) {
            break;
        }
        int n = llama_token_to_piece(vocab, next_token, piece, sizeof(piece), 0, false);
        if (n < 0) {
            std::vector<char> larger(static_cast<size_t>(-n));
            n = llama_token_to_piece(vocab, next_token, larger.data(), static_cast<int32_t>(larger.size()), 0, false);
            if (n > 0) output.append(larger.data(), static_cast<size_t>(n));
        } else if (n > 0) {
            output.append(piece, static_cast<size_t>(n));
        }
        batch = llama_batch_get_one(&next_token, 1);
        if (llama_decode(g_ctx, batch) != 0) {
            set_error("Генерация остановилась из-за ошибки вычисления.");
            decode_error = true;
            break;
        }
    }
    llama_sampler_free(sampler);
    if (!decode_error) set_error("");

    char * result = static_cast<char *>(std::malloc(output.size() + 1));
    if (!result) {
        set_error("Недостаточно памяти для ответа.");
        return nullptr;
    }
    if (!output.empty()) {
        std::memcpy(result, output.data(), output.size());
    }
    result[output.size()] = '\0';
    return result;
}

} // extern "C"
