# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

# First-pixel profile for an arm64 iOS Simulator build. Feature families are
# re-enabled only after the UIKit/GHOST/Metal launch path is proven.

include("${CMAKE_CURRENT_LIST_DIR}/blender_lite.cmake")

set(APPLE_TARGET_DEVICE      ios-simulator CACHE STRING "" FORCE)
set(WITH_APPLE_CROSSPLATFORM ON           CACHE BOOL   "" FORCE)

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
