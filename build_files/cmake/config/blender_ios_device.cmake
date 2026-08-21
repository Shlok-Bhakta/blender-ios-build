# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

# Canonical physical iPhone/iPad profile. Keep ABI and signing policy inherited
# from the proven device profile while features converge with desktop Blender.
include("${CMAKE_CURRENT_LIST_DIR}/blender_ios_device_minimal.cmake")

set(WITH_PYTHON         ON CACHE BOOL "" FORCE)
set(WITH_PYTHON_INSTALL ON CACHE BOOL "" FORCE)

set(WITH_PYTHON_INSTALL_NUMPY     ON CACHE BOOL "" FORCE)
set(WITH_PYTHON_INSTALL_ZSTANDARD ON CACHE BOOL "" FORCE)
