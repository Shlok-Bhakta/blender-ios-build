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
set(WITH_PYTHON_INSTALL_NUMPY     OFF CACHE BOOL "" FORCE)
set(WITH_PYTHON_INSTALL_ZSTANDARD OFF CACHE BOOL "" FORCE)
