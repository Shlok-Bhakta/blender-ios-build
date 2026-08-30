# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

# iOS is already selected by the toolchain before project() runs. Keep that
# selection intact instead of replacing it with the host macOS SDK below.
add_definitions(-DWITH_APPLE_CROSSPLATFORM)
set(BLENDER_PLATFORM_CMAKE
  "${CMAKE_SOURCE_DIR}/build_files/ios/cmake/platform_ios.cmake"
)
if(WITH_APPLE_CROSSPLATFORM)
  if(NOT CMAKE_SYSTEM_NAME STREQUAL "iOS")
    message(FATAL_ERROR "WITH_APPLE_CROSSPLATFORM requires CMAKE_SYSTEM_NAME=iOS")
  endif()
  if(NOT APPLE_TARGET_DEVICE STREQUAL "ios" AND
     NOT APPLE_TARGET_DEVICE STREQUAL "ios-simulator")
    message(FATAL_ERROR "Unsupported APPLE_TARGET_DEVICE: ${APPLE_TARGET_DEVICE}")
  endif()

  set(CMAKE_OSX_ARCHITECTURES "arm64" CACHE STRING "iOS architecture" FORCE)
  set(APPLE_TARGET_IOS TRUE)
  set(CMAKE_XCODE_ATTRIBUTE_ONLY_ACTIVE_ARCH "YES")

  execute_process(
    COMMAND xcode-select --print-path
    OUTPUT_VARIABLE XCODE_DEVELOPER_DIR
    OUTPUT_STRIP_TRAILING_WHITESPACE
  )
  execute_process(
    COMMAND xcodebuild -version
    OUTPUT_VARIABLE _xcode_version_output
    RESULT_VARIABLE _xcode_version_result
    ERROR_QUIET
  )
  if(NOT _xcode_version_result EQUAL 0)
    message(FATAL_ERROR "Unable to determine the Xcode version")
  endif()
  string(REPLACE "\n" " " _xcode_version_line "${_xcode_version_output}")
  string(REGEX REPLACE ".*Xcode ([0-9\\.]+).*" "\\1" XCODE_VERSION "${_xcode_version_line}")
  if(XCODE_VERSION VERSION_LESS 16.0)
    message(FATAL_ERROR "Only Xcode version 16.0 and newer is supported")
  endif()

  if(APPLE_TARGET_DEVICE STREQUAL "ios-simulator")
    set(_apple_sdk iphonesimulator)
    set(_apple_platform iPhoneSimulator)
  else()
    set(_apple_sdk iphoneos)
    set(_apple_platform iPhoneOS)
  endif()
  execute_process(
    COMMAND xcrun --sdk ${_apple_sdk} --show-sdk-path
    OUTPUT_VARIABLE _apple_sdk_path
    OUTPUT_STRIP_TRAILING_WHITESPACE
    COMMAND_ERROR_IS_FATAL ANY
  )
  set(CMAKE_OSX_SYSROOT "${_apple_sdk_path}" CACHE PATH "iOS SDK" FORCE)
  if(NOT CMAKE_OSX_DEPLOYMENT_TARGET)
    set(CMAKE_OSX_DEPLOYMENT_TARGET "18.0" CACHE STRING "iOS deployment target" FORCE)
  endif()

  set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
  set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY BOTH)
  set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE BOTH)
  set(CMAKE_FIND_ROOT_PATH_MODE_PACKAGE BOTH)
  set(CMAKE_FIND_FRAMEWORK FIRST)
  set(CMAKE_SYSTEM_FRAMEWORK_PATH
    "${_apple_sdk_path}/System/Library/Frameworks"
    "${XCODE_DEVELOPER_DIR}/Platforms/${_apple_platform}.platform/Developer/Library/Frameworks"
  )

  if(CMAKE_GENERATOR MATCHES "Xcode")
    set(CMAKE_XCODE_ATTRIBUTE_SDKROOT ${_apple_sdk})
  endif()

  string(APPEND CMAKE_C_FLAGS " -m${_apple_sdk}-version-min=${CMAKE_OSX_DEPLOYMENT_TARGET}")
  string(APPEND CMAKE_CXX_FLAGS " -m${_apple_sdk}-version-min=${CMAKE_OSX_DEPLOYMENT_TARGET}")
  add_definitions("-DIOS_DEPLOYMENT_TARGET=${CMAKE_OSX_DEPLOYMENT_TARGET}")

  message(STATUS "Building for ${APPLE_TARGET_DEVICE} with Xcode ${XCODE_VERSION}")
  message(STATUS "Detected iOS sysroot: ${CMAKE_OSX_SYSROOT}")
  return()
endif()
