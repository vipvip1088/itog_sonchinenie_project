# -*- coding: utf-8 -*-
from __future__ import annotations

import ctypes
import os
import platform
import re
import threading
from pathlib import Path

MODEL_NAME = "Qwen3-4B-Q4_K_M.gguf"
CONTEXT_SIZE = 8192
THREADS = 6


def clean_model_output(text: str) -> str:
    """Remove Qwen internal-channel markers from user-visible model output."""
    text = (text or "").strip()
    text = re.sub(r"<think>.*?(?:</think>|$)", "", text, flags=re.DOTALL)
    text = re.sub(r"<\|(?:im_end|endoftext|fim_suffix)\|>", "", text)
    return text.strip()


class LocalLlama:
    """CTypes-обёртка над llama.cpp, скомпилированным в libessay_llama.so."""

    def __init__(self):
        self._lib = None
        self._loaded = False
        self._lock = threading.RLock()
        self._model_path = self._find_model()
        self._error = ""

    def _find_model(self):
        # Модель хранится в assets APK; на первом запуске p4a распаковывает assets в каталог приложения.
        return Path(__file__).resolve().parents[1] / "assets" / "models" / MODEL_NAME

    def _native_library_path(self):
        if platform.system().lower() == "linux" and "ANDROID_ARGUMENT" not in os.environ:
            candidate = Path(__file__).resolve().parents[1] / "native" / "libs" / "linux-x86_64" / "libessay_llama.so"
            return candidate
        try:
            from jnius import autoclass
            activity = autoclass("org.kivy.android.PythonActivity").mActivity
            native_dir = str(activity.getApplicationInfo().nativeLibraryDir)
            return Path(native_dir) / "libessay_llama.so"
        except Exception:
            return Path("/nonexistent/libessay_llama.so")

    def _load_library(self):
        if self._lib is not None:
            return self._lib
        lib_path = self._native_library_path()
        if not lib_path.exists():
            raise RuntimeError(f"Не найдена встроенная библиотека {lib_path}. Сначала собери libessay_llama.so скриптом scripts/build_native_android.sh.")
        lib = ctypes.CDLL(str(lib_path))
        lib.essay_llama_load.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.c_int]
        lib.essay_llama_load.restype = ctypes.c_int
        lib.essay_llama_generate.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.c_float, ctypes.c_float]
        lib.essay_llama_generate.restype = ctypes.c_void_p
        lib.essay_llama_free_string.argtypes = [ctypes.c_void_p]
        lib.essay_llama_free_string.restype = None
        lib.essay_llama_last_error.restype = ctypes.c_char_p
        lib.essay_llama_unload.argtypes = []
        lib.essay_llama_unload.restype = None
        self._lib = lib
        return lib

    def ensure_loaded(self):
        with self._lock:
            if self._loaded:
                return
            if not self._model_path.exists():
                raise RuntimeError(
                    f"В APK не включена модель {MODEL_NAME}. Положи файл в assets/models/ и пересобери APK. "
                    "Размер модели около 2,5 ГБ."
                )
            lib = self._load_library()
            result = lib.essay_llama_load(str(self._model_path).encode("utf-8"), CONTEXT_SIZE, THREADS)
            if result != 0:
                message = lib.essay_llama_last_error()
                raise RuntimeError(message.decode("utf-8", "replace") if message else "llama.cpp не смог загрузить модель.")
            self._loaded = True

    def generate(self, prompt, max_tokens=900, temperature=0.55, top_p=0.9):
        with self._lock:
            self.ensure_loaded()
            ptr = self._lib.essay_llama_generate(prompt.encode("utf-8"), int(max_tokens), float(temperature), float(top_p))
            if not ptr:
                message = self._lib.essay_llama_last_error()
                raise RuntimeError(message.decode("utf-8", "replace") if message else "Ошибка генерации.")
            try:
                text = ctypes.string_at(ptr).decode("utf-8", "replace")
                return clean_model_output(text)
            finally:
                self._lib.essay_llama_free_string(ptr)

    def status(self):
        if self._loaded:
            return "ЛОКАЛЬНЫЙ ИИ · готов"
        if not self._model_path.exists():
            return "ИИ · модель не включена в APK"
        lib = self._native_library_path()
        if not lib.exists():
            return "ИИ · движок не включён в APK"
        return "ЛОКАЛЬНЫЙ ИИ · готов к запуску"

    def close(self):
        with self._lock:
            if self._lib is not None and self._loaded:
                self._lib.essay_llama_unload()
            self._loaded = False
