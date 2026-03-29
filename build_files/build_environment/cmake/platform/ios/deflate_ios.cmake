# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

function(blender_platform_ios_patch_deflate_extra_args out_var)
  set(_deflate_extra_args "${${out_var}}")

  if(WITH_APPLE_CROSSPLATFORM)
    list(APPEND _deflate_extra_args -DLIBDEFLATE_BUILD_GZIP=OFF)
  endif()

  set(${out_var} "${_deflate_extra_args}" PARENT_SCOPE)
endfunction()
