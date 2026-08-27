# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

# Canonical arm64 iOS Simulator profile. Feature families are enabled here as
# their target dependencies and runtime acceptance gates become available.
include("${CMAKE_CURRENT_LIST_DIR}/blender_ios_sim_minimal.cmake")

set(WITH_PYTHON         ON CACHE BOOL "" FORCE)
set(WITH_PYTHON_INSTALL ON CACHE BOOL "" FORCE)

# Native Python packages are enabled in their own feature slices after their
# iOS wheels pass the same simulator and device runtime gates as CPython.
set(WITH_PYTHON_INSTALL_NUMPY     ON CACHE BOOL "" FORCE)
set(WITH_PYTHON_INSTALL_ZSTANDARD ON CACHE BOOL "" FORCE)

# Required by the Subdivision Surface and Multiresolution modifiers. The iOS
# dependency sysroot provides the portable CPU evaluator and Metal support.
set(WITH_OPENSUBDIV ON CACHE BOOL "" FORCE)

# Keep the portable CPU renderer as the fallback while compiling the native
# Metal device. TBB is static in the iOS dependency sysroot.
set(WITH_TBB                 ON  CACHE BOOL "" FORCE)
set(WITH_TBB_MALLOC_PROXY    OFF CACHE BOOL "" FORCE)
set(WITH_CYCLES              ON  CACHE BOOL "" FORCE)
set(WITH_CYCLES_DEVICE_METAL ON  CACHE BOOL "" FORCE)
set(WITH_CYCLES_EMBREE       OFF CACHE BOOL "" FORCE)
set(WITH_CYCLES_OSL          OFF CACHE BOOL "" FORCE)
set(WITH_CYCLES_PATH_GUIDING OFF CACHE BOOL "" FORCE)
