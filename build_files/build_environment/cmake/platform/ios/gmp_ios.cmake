# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

function(blender_platform_ios_patch_gmp_options)
  if(NOT (APPLE AND WITH_APPLE_CROSSPLATFORM))
    return()
  endif()

  set(GMP_OPTIONS_WITH_HOST
    --host=aarch64-apple-ios
    --enable-static
    --disable-shared
    --disable-assembly
    -enable-cxx
  )

  set(GMP_OPTIONS ${GMP_OPTIONS_WITH_HOST} PARENT_SCOPE)

  set(GMP_CONFIGURE_ENV_WITH_CROSS
    ${CONFIGURE_ENV_NO_PERL}
    gmp_cv_prog_cc_cross=yes
  )
  set(GMP_CONFIGURE_ENV ${GMP_CONFIGURE_ENV_WITH_CROSS} PARENT_SCOPE)
endfunction()
