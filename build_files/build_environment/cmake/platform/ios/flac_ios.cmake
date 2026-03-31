# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

function(blender_platform_ios_patch_flac_configure_command out_var)
  if(NOT (APPLE AND WITH_APPLE_CROSSPLATFORM))
    return()
  endif()

  set(FLAC_CONFIGURE_COMMAND_WITH_OPTS
    flac_cv_prog_cc_cross=yes
    CC="clang -target aarch64-apple-ios -isysroot ${CMAKE_OSX_SYSROOT} -miphoneos-version-min=16.0"
    CXX="clang++ -target aarch64-apple-ios -isysroot ${CMAKE_OSX_SYSROOT} -miphoneos-version-min=16.0 -stdlib=libc++"
    CPPFLAGS="-I${LIBDIR}/ogg/include"
    ./configure
    --host=aarch64-apple-ios
    --prefix=${LIBDIR}/flac
    --disable-shared
    --enable-static
  )
  set(${out_var} "${FLAC_CONFIGURE_COMMAND_WITH_OPTS}" PARENT_SCOPE)
endfunction()
