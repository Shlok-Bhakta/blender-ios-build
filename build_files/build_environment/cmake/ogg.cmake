# SPDX-FileCopyrightText: 2002-2023 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

set(OGG_EXTRA_ARGS)

include(${CMAKE_CURRENT_LIST_DIR}/platform/ios/ogg_ios.cmake)
blender_platform_ios_patch_ogg_extra_args(OGG_EXTRA_ARGS)

ExternalProject_Add(external_ogg
  URL file://${PACKAGE_DIR}/${OGG_FILE}
  DOWNLOAD_DIR ${DOWNLOAD_DIR}
  URL_HASH ${OGG_HASH_TYPE}=${OGG_HASH}
  PREFIX ${BUILD_DIR}/ogg

  CMAKE_ARGS
    -DCMAKE_INSTALL_PREFIX=${LIBDIR}/ogg
    ${DEFAULT_CMAKE_FLAGS}
    ${OGG_EXTRA_ARGS}

  INSTALL_DIR ${LIBDIR}/ogg
)

if(NOT WIN32)
  harvest(external_ogg ogg/lib ffmpeg/lib "*.a")
endif()
