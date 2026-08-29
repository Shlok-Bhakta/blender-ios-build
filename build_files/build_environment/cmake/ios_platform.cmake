# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

# Generic Apple cross-compilation contract shared by dependency packets.

if(NOT CMAKE_SYSTEM_NAME STREQUAL "iOS")
  message(FATAL_ERROR "iOS dependencies require CMAKE_SYSTEM_NAME=iOS")
endif()
if(NOT CMAKE_OSX_ARCHITECTURES STREQUAL "arm64")
  message(FATAL_ERROR "iOS dependencies currently require arm64")
endif()
if(NOT APPLE_TARGET_DEVICE STREQUAL "ios" AND
   NOT APPLE_TARGET_DEVICE STREQUAL "ios-simulator")
  message(FATAL_ERROR "Invalid iOS APPLE_TARGET_DEVICE: ${APPLE_TARGET_DEVICE}")
endif()
if(NOT CMAKE_OSX_DEPLOYMENT_TARGET)
  message(FATAL_ERROR "CMAKE_OSX_DEPLOYMENT_TARGET must be explicit")
endif()
if(NOT IS_ABSOLUTE "${CMAKE_OSX_SYSROOT}" OR NOT EXISTS "${CMAKE_OSX_SYSROOT}")
  message(FATAL_ERROR "CMAKE_OSX_SYSROOT must be an existing absolute SDK path")
endif()

set(BLENDER_PLATFORM_ARM ON)
set(CMAKE_TRY_COMPILE_TARGET_TYPE STATIC_LIBRARY)

if(APPLE_TARGET_DEVICE STREQUAL "ios-simulator")
  set(BLENDER_IOS_PLATFORM "IOSSIMULATOR")
  set(BLENDER_IOS_TARGET_TRIPLE "arm64-apple-ios${CMAKE_OSX_DEPLOYMENT_TARGET}-simulator")
  set(BLENDER_IOS_XCRUN_SDK "iphonesimulator")
else()
  set(BLENDER_IOS_PLATFORM "IOS")
  set(BLENDER_IOS_TARGET_TRIPLE "arm64-apple-ios${CMAKE_OSX_DEPLOYMENT_TARGET}")
  set(BLENDER_IOS_XCRUN_SDK "iphoneos")
endif()

set(_target_flags "-target ${BLENDER_IOS_TARGET_TRIPLE} -isysroot ${CMAKE_OSX_SYSROOT}")
set(PLATFORM_CFLAGS "${_target_flags} -fvisibility=hidden")
set(PLATFORM_CXXFLAGS "${_target_flags} -std=c++20 -stdlib=libc++ -fvisibility=hidden")
set(PLATFORM_LDFLAGS "${_target_flags} -Wl,-dead_strip")
set(PLATFORM_BUILD_TARGET --host=arm-apple-darwin)

# Cross-built projects sometimes compile small generators which must execute
# during the build. Give those tools an explicit macOS target: the exported
# iOS deployment target would otherwise make Clang produce an iOS executable.
execute_process(
  COMMAND xcrun --sdk macosx --show-sdk-path
  OUTPUT_VARIABLE BLENDER_APPLE_HOST_SYSROOT
  OUTPUT_STRIP_TRAILING_WHITESPACE
  COMMAND_ERROR_IS_FATAL ANY
)
set(BLENDER_APPLE_HOST_TARGET_TRIPLE
  "${CMAKE_HOST_SYSTEM_PROCESSOR}-apple-macos11.0"
)
set(BLENDER_APPLE_HOST_FLAGS
  "-target ${BLENDER_APPLE_HOST_TARGET_TRIPLE} -isysroot ${BLENDER_APPLE_HOST_SYSROOT}"
)

find_program(BLENDER_IOS_MESON meson REQUIRED NO_CMAKE_FIND_ROOT_PATH)
find_program(BLENDER_IOS_PKG_CONFIG pkg-config REQUIRED NO_CMAKE_FIND_ROOT_PATH)
set(MESON ${BLENDER_IOS_MESON})

# Meson otherwise treats exported CFLAGS as a native build. Keep host tools
# native while making the compiler, linker, and executable-run policy explicit.
set(BLENDER_IOS_MESON_CROSS_FILE "${CMAKE_CURRENT_BINARY_DIR}/ios-meson-cross.ini")
set(BLENDER_IOS_MESON_NATIVE_FILE "${CMAKE_CURRENT_BINARY_DIR}/ios-meson-native.ini")
file(WRITE "${BLENDER_IOS_MESON_NATIVE_FILE}" "[binaries]\n")
file(APPEND "${BLENDER_IOS_MESON_NATIVE_FILE}" "c = '${CMAKE_C_COMPILER}'\n")
file(APPEND "${BLENDER_IOS_MESON_NATIVE_FILE}" "cpp = '${CMAKE_CXX_COMPILER}'\n")
file(APPEND "${BLENDER_IOS_MESON_NATIVE_FILE}" "ar = '${CMAKE_AR}'\n")
file(APPEND "${BLENDER_IOS_MESON_NATIVE_FILE}" "strip = '/usr/bin/strip'\n")
file(APPEND "${BLENDER_IOS_MESON_NATIVE_FILE}" "pkg-config = '${BLENDER_IOS_PKG_CONFIG}'\n")
file(APPEND "${BLENDER_IOS_MESON_NATIVE_FILE}" "\n[built-in options]\n")
file(APPEND "${BLENDER_IOS_MESON_NATIVE_FILE}" "c_link_args = ['-Wl,-adhoc_codesign']\n")
file(APPEND "${BLENDER_IOS_MESON_NATIVE_FILE}" "cpp_link_args = ['-Wl,-adhoc_codesign']\n")
file(WRITE "${BLENDER_IOS_MESON_CROSS_FILE}" "[binaries]\n")
file(APPEND "${BLENDER_IOS_MESON_CROSS_FILE}" "c = '${CMAKE_C_COMPILER}'\n")
file(APPEND "${BLENDER_IOS_MESON_CROSS_FILE}" "cpp = '${CMAKE_CXX_COMPILER}'\n")
file(APPEND "${BLENDER_IOS_MESON_CROSS_FILE}" "ar = '${CMAKE_AR}'\n")
file(APPEND "${BLENDER_IOS_MESON_CROSS_FILE}" "strip = '/usr/bin/strip'\n")
file(APPEND "${BLENDER_IOS_MESON_CROSS_FILE}" "pkg-config = '${BLENDER_IOS_PKG_CONFIG}'\n\n")
file(APPEND "${BLENDER_IOS_MESON_CROSS_FILE}" "[host_machine]\n")
file(APPEND "${BLENDER_IOS_MESON_CROSS_FILE}" "system = 'darwin'\n")
file(APPEND "${BLENDER_IOS_MESON_CROSS_FILE}" "cpu_family = 'aarch64'\n")
file(APPEND "${BLENDER_IOS_MESON_CROSS_FILE}" "cpu = 'arm64'\n")
file(APPEND "${BLENDER_IOS_MESON_CROSS_FILE}" "endian = 'little'\n\n")
file(APPEND "${BLENDER_IOS_MESON_CROSS_FILE}" "[properties]\n")
file(APPEND "${BLENDER_IOS_MESON_CROSS_FILE}" "needs_exe_wrapper = true\n\n")
file(APPEND "${BLENDER_IOS_MESON_CROSS_FILE}" "[built-in options]\n")
file(APPEND "${BLENDER_IOS_MESON_CROSS_FILE}" "c_args = ['-target', '${BLENDER_IOS_TARGET_TRIPLE}', '-isysroot', '${CMAKE_OSX_SYSROOT}', '-fvisibility=hidden']\n")
file(APPEND "${BLENDER_IOS_MESON_CROSS_FILE}" "cpp_args = ['-target', '${BLENDER_IOS_TARGET_TRIPLE}', '-isysroot', '${CMAKE_OSX_SYSROOT}', '-stdlib=libc++', '-fvisibility=hidden']\n")
file(APPEND "${BLENDER_IOS_MESON_CROSS_FILE}" "c_link_args = ['-target', '${BLENDER_IOS_TARGET_TRIPLE}', '-isysroot', '${CMAKE_OSX_SYSROOT}', '-Wl,-dead_strip']\n")
file(APPEND "${BLENDER_IOS_MESON_CROSS_FILE}" "cpp_link_args = ['-target', '${BLENDER_IOS_TARGET_TRIPLE}', '-isysroot', '${CMAKE_OSX_SYSROOT}', '-stdlib=libc++', '-Wl,-dead_strip']\n")

set(PLATFORM_CMAKE_FLAGS
  # Some still-supported upstream dependencies declare a pre-3.5 CMake
  # minimum. Current CMake can configure them when the compatibility floor is
  # explicit, so apply that policy only to iOS dependency sub-builds.
  -DCMAKE_POLICY_VERSION_MINIMUM:STRING=3.5
  -DCMAKE_SYSTEM_NAME:STRING=iOS
  -DCMAKE_SYSTEM_PROCESSOR:STRING=arm64
  -DCMAKE_OSX_ARCHITECTURES:STRING=arm64
  -DCMAKE_OSX_DEPLOYMENT_TARGET:STRING=${CMAKE_OSX_DEPLOYMENT_TARGET}
  -DCMAKE_OSX_SYSROOT:PATH=${CMAKE_OSX_SYSROOT}
  -DCMAKE_TRY_COMPILE_TARGET_TYPE:STRING=STATIC_LIBRARY
  -DCMAKE_FIND_ROOT_PATH_MODE_PROGRAM:STRING=NEVER
  -DCMAKE_FIND_ROOT_PATH_MODE_LIBRARY:STRING=ONLY
  -DCMAKE_FIND_ROOT_PATH_MODE_INCLUDE:STRING=ONLY
  -DCMAKE_FIND_ROOT_PATH_MODE_PACKAGE:STRING=ONLY
)

message(STATUS "Apple dependency target = ${APPLE_TARGET_DEVICE}")
message(STATUS "Apple dependency triple = ${BLENDER_IOS_TARGET_TRIPLE}")
message(STATUS "Apple dependency SDK = ${CMAKE_OSX_SYSROOT}")
message(STATUS "Apple Meson cross file = ${BLENDER_IOS_MESON_CROSS_FILE}")
message(STATUS "Apple Meson native file = ${BLENDER_IOS_MESON_NATIVE_FILE}")

unset(_target_flags)
