# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

include(${CMAKE_CURRENT_LIST_DIR}/cmake_policy_compat.cmake)

function(blender_platform_ios_patch_robinmap_extra_args out_var)
  blender_platform_ios_append_legacy_cmake_policy_flag(${out_var})
endfunction()
