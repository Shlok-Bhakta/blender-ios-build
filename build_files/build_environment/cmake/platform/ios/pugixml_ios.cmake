# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

function(blender_platform_ios_patch_pugixml_extra_args out_var)
  set(_pugixml_extra_args "${${out_var}}")

  if(APPLE AND WITH_APPLE_CROSSPLATFORM)
    list(APPEND _pugixml_extra_args -DCMAKE_POLICY_VERSION_MINIMUM=3.5)
  endif()

  set(${out_var} "${_pugixml_extra_args}" PARENT_SCOPE)
endfunction()
