# SPDX-FileCopyrightText: 2020 Blender Authors
#
# SPDX-License-Identifier: BSD-3-Clause

# - Find sse2neon library
# Find the native sse2neon includes and library
# This module defines
#  SSE2NEON_INCLUDE_DIRS, where to find sse2neon.h, Set when
#                         SSE2NEON_INCLUDE_DIR is found.
#  SSE2NEON_ROOT_DIR, The base directory to search for sse2neon.
#                     This can also be an environment variable.
#  SSE2NEON_FOUND, If false, do not try to use sse2neon.

# If `SSE2NEON_ROOT_DIR` was defined in the environment, use it.
if(DEFINED SSE2NEON_ROOT_DIR)
  # Pass.
elseif(DEFINED ENV{SSE2NEON_ROOT_DIR})
  set(SSE2NEON_ROOT_DIR $ENV{SSE2NEON_ROOT_DIR})
elseif(DEFINED LIBDIR)
  set(SSE2NEON_ROOT_DIR ${LIBDIR}/sse2neon)
else()
  set(SSE2NEON_ROOT_DIR "")
endif()

set(_sse2neon_SEARCH_DIRS
  ${SSE2NEON_ROOT_DIR}
)

set(_sse2neon_INCLUDE_SEARCH_DIRS ${_sse2neon_SEARCH_DIRS})
foreach(_sse2neon_dir ${_sse2neon_SEARCH_DIRS})
  list(APPEND _sse2neon_INCLUDE_SEARCH_DIRS "${_sse2neon_dir}/include")
endforeach()
unset(_sse2neon_dir)

find_path(SSE2NEON_INCLUDE_DIR
  NAMES
    sse2neon.h
  HINTS
    ${_sse2neon_INCLUDE_SEARCH_DIRS}
)

# handle the QUIETLY and REQUIRED arguments and set SSE2NEON_FOUND to TRUE if
# all listed variables are TRUE
include(FindPackageHandleStandardArgs)
find_package_handle_standard_args(sse2neon DEFAULT_MSG
  SSE2NEON_INCLUDE_DIR)

if(SSE2NEON_FOUND)
  set(SSE2NEON_INCLUDE_DIRS ${SSE2NEON_INCLUDE_DIR})
endif()

mark_as_advanced(
  SSE2NEON_INCLUDE_DIR
)

unset(_sse2neon_SEARCH_DIRS)
unset(_sse2neon_INCLUDE_SEARCH_DIRS)
