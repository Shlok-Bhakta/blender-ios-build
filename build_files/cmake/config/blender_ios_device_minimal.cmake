# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

# Reduced arm64 profile for an unsigned physical iPhone/iPad handoff. This must
# use a build tree and dependency prefix separate from the simulator lane.

include("${CMAKE_CURRENT_LIST_DIR}/blender_lite.cmake")

set(APPLE_TARGET_DEVICE      ios CACHE STRING "" FORCE)
set(WITH_APPLE_CROSSPLATFORM ON  CACHE BOOL   "" FORCE)
set(BLENDER_PLATFORM_XCODE_CMAKE
  "${CMAKE_SOURCE_DIR}/build_files/ios/cmake/platform_ios_xcode.cmake"
  CACHE FILEPATH "iOS Xcode platform setup" FORCE)

set(WITH_PYTHON              OFF CACHE BOOL "" FORCE)
set(WITH_PYTHON_INSTALL      OFF CACHE BOOL "" FORCE)
set(WITH_COMPILER_SIMD       OFF CACHE BOOL "" FORCE)
set(WITH_COMPILER_CCACHE     OFF CACHE BOOL "" FORCE)
set(WITH_GTESTS              OFF CACHE BOOL "" FORCE)
set(WITH_HEADLESS            OFF CACHE BOOL "" FORCE)
set(WITH_GHOST_SDL           OFF CACHE BOOL "" FORCE)

set(WITH_OPENGL_BACKEND      OFF CACHE BOOL "" FORCE)
set(WITH_VULKAN_BACKEND      OFF CACHE BOOL "" FORCE)
set(WITH_METAL_BACKEND       ON  CACHE BOOL "" FORCE)

set(WITH_TBB                 OFF CACHE BOOL "" FORCE)
set(WITH_HARFBUZZ            OFF CACHE BOOL "" FORCE)
set(WITH_FRIBIDI             OFF CACHE BOOL "" FORCE)
set(WITH_PUGIXML             OFF CACHE BOOL "" FORCE)
set(WITH_INSTALL_PORTABLE    ON  CACHE BOOL "" FORCE)

# The artifact is intentionally handed to the owner without an identity,
# provisioning profile, signer entitlements, or bundle signature.
set(CMAKE_XCODE_ATTRIBUTE_CODE_SIGNING_ALLOWED "NO" CACHE STRING "" FORCE)
set(CMAKE_XCODE_ATTRIBUTE_CODE_SIGNING_REQUIRED "NO" CACHE STRING "" FORCE)
set(CMAKE_XCODE_ATTRIBUTE_CODE_SIGN_STYLE "Manual" CACHE STRING "" FORCE)
