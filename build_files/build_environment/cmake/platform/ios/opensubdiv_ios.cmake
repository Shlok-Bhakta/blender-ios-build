# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

function(blender_platform_ios_patch_opensubdiv_extra_args out_var)
  set(_opensubdiv_extra_args "${${out_var}}")

  if(APPLE AND WITH_APPLE_CROSSPLATFORM)
    list(APPEND _opensubdiv_extra_args -DNO_OPENGL=ON)
  endif()

  set(${out_var} "${_opensubdiv_extra_args}" PARENT_SCOPE)
endfunction()
