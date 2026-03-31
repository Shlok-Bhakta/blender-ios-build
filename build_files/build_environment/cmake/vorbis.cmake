# SPDX-FileCopyrightText: 2002-2023 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

set(VORBIS_EXTRA_ARGS)

include(${CMAKE_CURRENT_LIST_DIR}/platform/ios/vorbis_ios.cmake)
blender_platform_ios_patch_vorbis_extra_args(VORBIS_EXTRA_ARGS)

ExternalProject_Add(external_vorbis
  URL file://${PACKAGE_DIR}/${VORBIS_FILE}
  DOWNLOAD_DIR ${DOWNLOAD_DIR}
  URL_HASH ${VORBIS_HASH_TYPE}=${VORBIS_HASH}
  PREFIX ${BUILD_DIR}/vorbis

  CMAKE_ARGS
    -DCMAKE_INSTALL_PREFIX=${LIBDIR}/vorbis
    -DOGG_ROOT=${LIBDIR}/ogg
    -DOGG_LIBRARY=${LIBDIR}/ogg/lib/libogg.a
    -DOGG_INCLUDE_DIR=${LIBDIR}/ogg/include
    ${DEFAULT_CMAKE_FLAGS}
    ${VORBIS_EXTRA_ARGS}

  INSTALL_DIR ${LIBDIR}/vorbis
)

add_dependencies(
  external_vorbis
  external_ogg
)

if(NOT WIN32)
  harvest(external_vorbis vorbis/lib ffmpeg/lib "*.a")
endif()
