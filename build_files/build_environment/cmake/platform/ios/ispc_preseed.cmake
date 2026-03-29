# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

function(blender_platform_ios_try_use_preseeded_ispc out_var)
  if(APPLE AND EXISTS "${LIBDIR}/ispc/bin/ispc")
    message(STATUS "Using preseeded ISPC at ${LIBDIR}/ispc/bin/ispc")
    add_custom_target(external_ispc)
    set(${out_var} TRUE PARENT_SCOPE)
    return()
  endif()

  set(${out_var} FALSE PARENT_SCOPE)
endfunction()
