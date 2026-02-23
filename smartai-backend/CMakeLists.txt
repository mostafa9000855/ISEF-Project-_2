cmake_minimum_required(VERSION 3.16)
project(SmartAI_Core)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Windows-specific settings
if(WIN32)
    add_definitions(-D_WIN32_WINNT=0x0A00)  # Windows 10+
endif()

# Include directories
include_directories(
    ${CMAKE_CURRENT_SOURCE_DIR}/include
    ${CMAKE_CURRENT_SOURCE_DIR}/third_party/openssl/include
    ${CMAKE_CURRENT_SOURCE_DIR}/third_party/nlohmann_json/include
)

# OpenSSL Library
find_package(OpenSSL REQUIRED)
if(NOT OPENSSL_FOUND)
    message(FATAL_ERROR "OpenSSL not found!")
endif()

# Source files
set(SOURCES
    src/cpp/core_engine.cpp
)

# Add executable
add_executable(core_engine ${SOURCES})

# Link libraries
target_link_libraries(core_engine
    PRIVATE
        OpenSSL::Crypto
        OpenSSL::SSL
        ws2_32.lib
        wtsapi32.lib
        psapi.lib
        iphlpapi.lib
        wininet.lib
        netapi32.lib
        crypt32.lib
        advapi32.lib
        kernel32.lib
)

# Compiler flags
if(MSVC)
    target_compile_options(core_engine PRIVATE
        /W4           # Warning level 4
        /WX           # Treat warnings as errors
        /Ox           # Optimization
        /fp:precise   # Floating point precision
        /EHsc         # Exception handling
    )
else()
    target_compile_options(core_engine PRIVATE
        -Wall
        -Wextra
        -O3
    )
endif()

# Set output directory
set_target_properties(core_engine PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/Release"
)

# Installation
install(TARGETS core_engine DESTINATION bin)
