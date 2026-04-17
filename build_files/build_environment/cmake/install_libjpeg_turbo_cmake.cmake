# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later
#
# Libjpeg-turbo's install() should place exported CMake configs under the
# install prefix, but iOS simulator cross builds have been observed without
# lib/cmake/libjpeg-turbo on disk. Copy from the ExternalProject build tree so
# consumers (e.g. OpenImageIO find_package(libjpeg-turbo)) can resolve targets.

cmake_minimum_required(VERSION 3.10)

if(NOT DEFINED LIBDIR)
  message(FATAL_ERROR "install_libjpeg_turbo_cmake.cmake: LIBDIR not set")
endif()
if(NOT DEFINED BUILD_DIR)
  message(FATAL_ERROR "install_libjpeg_turbo_cmake.cmake: BUILD_DIR not set")
endif()

set(_src "${BUILD_DIR}/jpeg/src/external_jpeg-build")
set(_dest "${LIBDIR}/jpeg/lib/cmake/libjpeg-turbo")
file(MAKE_DIRECTORY "${_dest}")

foreach(
  _name
  IN
  ITEMS libjpeg-turboConfig.cmake libjpeg-turboConfigVersion.cmake
)
  set(_f "${_src}/pkgscripts/${_name}")
  if(EXISTS "${_f}")
    file(COPY "${_f}" DESTINATION "${_dest}")
  endif()
endforeach()

execute_process(
  COMMAND find "${_src}/CMakeFiles/Export" -name libjpeg-turboTargets*.cmake
  OUTPUT_VARIABLE _find_out
  OUTPUT_STRIP_TRAILING_WHITESPACE
)
string(REPLACE "\n" ";" _targets "${_find_out}")
list(FILTER _targets EXCLUDE REGEX "^$")
foreach(_f IN LISTS _targets)
  file(COPY "${_f}" DESTINATION "${_dest}")
endforeach()
