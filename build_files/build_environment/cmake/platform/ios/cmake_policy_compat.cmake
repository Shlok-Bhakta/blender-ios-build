# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

function(blender_platform_ios_append_legacy_cmake_policy_flag out_var)
  set(_extra_args "${${out_var}}")

  list(APPEND _extra_args -DCMAKE_POLICY_VERSION_MINIMUM=3.5)

  set(${out_var} "${_extra_args}" PARENT_SCOPE)
endfunction()
