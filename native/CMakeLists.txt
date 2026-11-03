cmake_minimum_required(VERSION 3.22)
project(essay_native LANGUAGES C CXX)

include(FetchContent)
set(BUILD_SHARED_LIBS OFF CACHE BOOL "Build llama.cpp dependencies as static libraries" FORCE)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)
set(LLAMA_BUILD_TESTS OFF CACHE BOOL "" FORCE)
set(LLAMA_BUILD_EXAMPLES OFF CACHE BOOL "" FORCE)
set(LLAMA_BUILD_SERVER OFF CACHE BOOL "" FORCE)
set(LLAMA_CURL OFF CACHE BOOL "" FORCE)
set(GGML_NATIVE OFF CACHE BOOL "" FORCE)
set(GGML_OPENMP OFF CACHE BOOL "" FORCE)
set(GGML_LLAMAFILE OFF CACHE BOOL "" FORCE)
set(GGML_VULKAN OFF CACHE BOOL "" FORCE)

FetchContent_Declare(
    llama_cpp
    GIT_REPOSITORY https://github.com/ggml-org/llama.cpp.git
    GIT_TAG master
    GIT_SHALLOW TRUE
)
FetchContent_MakeAvailable(llama_cpp)

add_library(essay_llama SHARED bridge.cpp)
target_compile_features(essay_llama PRIVATE cxx_std_17)
# llama-sampler.h is an internal header kept in llama.cpp/src.
target_include_directories(essay_llama PRIVATE "${llama_cpp_SOURCE_DIR}/src")
target_link_libraries(essay_llama PRIVATE llama)
target_compile_options(essay_llama PRIVATE -O3 -fvisibility=hidden)
set_target_properties(essay_llama PROPERTIES OUTPUT_NAME "essay_llama")
