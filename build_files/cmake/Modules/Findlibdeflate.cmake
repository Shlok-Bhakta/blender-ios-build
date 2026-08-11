# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: BSD-3-Clause

# Find libdeflate and provide the target exported by its upstream CMake build.
# OpenEXR's static package requires this target when libdeflate support is on.

if(DEFINED libdeflate_ROOT)
  set(_libdeflate_SEARCH_DIRS ${libdeflate_ROOT})
elseif(DEFINED ENV{libdeflate_ROOT})
  set(_libdeflate_SEARCH_DIRS $ENV{libdeflate_ROOT})
else()
  set(_libdeflate_SEARCH_DIRS "")
endif()

find_path(libdeflate_INCLUDE_DIR
  NAMES libdeflate.h
  HINTS ${_libdeflate_SEARCH_DIRS}
  PATH_SUFFIXES include
)

find_library(libdeflate_LIBRARY
  NAMES deflate libdeflate
  HINTS ${_libdeflate_SEARCH_DIRS}
  PATH_SUFFIXES lib64 lib
)

include(FindPackageHandleStandardArgs)
find_package_handle_standard_args(libdeflate DEFAULT_MSG
  libdeflate_LIBRARY libdeflate_INCLUDE_DIR
)

if(libdeflate_FOUND AND NOT TARGET libdeflate::libdeflate_static)
  add_library(libdeflate::libdeflate_static STATIC IMPORTED)
  set_target_properties(libdeflate::libdeflate_static PROPERTIES
    IMPORTED_LOCATION "${libdeflate_LIBRARY}"
    INTERFACE_INCLUDE_DIRECTORIES "${libdeflate_INCLUDE_DIR}"
  )
endif()

mark_as_advanced(libdeflate_INCLUDE_DIR libdeflate_LIBRARY)
unset(_libdeflate_SEARCH_DIRS)
