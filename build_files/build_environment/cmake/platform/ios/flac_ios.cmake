# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

function(blender_platform_ios_patch_flac_configure_env out_var)
  if(NOT (APPLE AND WITH_APPLE_CROSSPLATFORM))
    return()
  endif()

  set(FLAC_CONFIGURE_ENV_WITH_CROSS
    ${CONFIGURE_ENV}
    flac_cv_prog_cc_cross=yes
    export CPPFLAGS="-I${LIBDIR}/ogg/include"
  )
  set(${out_var} "${FLAC_CONFIGURE_ENV_WITH_CROSS}" PARENT_SCOPE)
endfunction()
