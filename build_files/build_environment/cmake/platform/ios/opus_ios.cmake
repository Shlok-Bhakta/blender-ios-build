# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

function(blender_platform_ios_patch_opus_configure_env out_var)
  if(NOT (APPLE AND WITH_APPLE_CROSSPLATFORM))
    return()
  endif()

  set(OPUS_CONFIGURE_ENV_WITH_CROSS
    ${CONFIGURE_ENV}
    opus_cv_prog_cc_cross=yes
  )
  set(${out_var} "${OPUS_CONFIGURE_ENV_WITH_CROSS}" PARENT_SCOPE)
endfunction()

function(blender_platform_ios_patch_opus_configure_command out_var)
  if(NOT (APPLE AND WITH_APPLE_CROSSPLATFORM))
    return()
  endif()

  set(OPUS_CONFIGURE_COMMAND_WITH_HOST
    ./configure
    --host=aarch64-apple-ios
    --disable-shared
    --enable-static
    --with-pic
    --disable-maintainer-mode
  )
  set(${out_var} "${OPUS_CONFIGURE_COMMAND_WITH_HOST}" PARENT_SCOPE)
endfunction()
