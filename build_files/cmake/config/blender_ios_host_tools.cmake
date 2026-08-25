# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

# Native generator tools must use the feature flags that affect generated iOS
# source. This profile is native macOS, not an iOS cross-compilation profile.

include("${CMAKE_CURRENT_LIST_DIR}/blender_lite.cmake")

set(WITH_CYCLES               ON CACHE BOOL "" FORCE)
set(WITH_CYCLES_DEVICE_METAL  ON CACHE BOOL "" FORCE)
set(WITH_EXPERIMENTAL_FEATURES ON CACHE BOOL "" FORCE)
set(WITH_METAL_BACKEND        ON CACHE BOOL "" FORCE)
set(WITH_OPENGL_BACKEND      OFF CACHE BOOL "" FORCE)
set(WITH_VULKAN_BACKEND      OFF CACHE BOOL "" FORCE)
set(WITH_PYTHON               ON CACHE BOOL "" FORCE)
set(WITH_PYTHON_INSTALL      OFF CACHE BOOL "" FORCE)
set(WITH_TBB                  ON CACHE BOOL "" FORCE)
set(WITH_TBB_MALLOC_PROXY    OFF CACHE BOOL "" FORCE)
set(WITH_GHOST_SDL           OFF CACHE BOOL "" FORCE)
set(WITH_SDL                 OFF CACHE BOOL "" FORCE)
