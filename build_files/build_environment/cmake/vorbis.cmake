# SPDX-FileCopyrightText: 2002-2023 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

set(VORBIS_EXTRA_ARGS)
if(WITH_APPLE_CROSSPLATFORM)
  # FindOgg's root hint is re-rooted into the SDK during an iOS cross build.
  # Cache the two target paths explicitly so it consumes our bundled archive.
  list(APPEND VORBIS_EXTRA_ARGS
    -DOGG_INCLUDE_DIR=${LIBDIR}/ogg/include
    -DOGG_LIBRARY=${LIBDIR}/ogg/lib/libogg.a
  )
endif()

ExternalProject_Add(external_vorbis
  URL file://${PACKAGE_DIR}/${VORBIS_FILE}
  DOWNLOAD_DIR ${DOWNLOAD_DIR}
  URL_HASH ${VORBIS_HASH_TYPE}=${VORBIS_HASH}
  PREFIX ${BUILD_DIR}/vorbis

  CMAKE_ARGS
    -DCMAKE_INSTALL_PREFIX=${LIBDIR}/vorbis
    -DOGG_ROOT=${LIBDIR}/ogg
    ${VORBIS_EXTRA_ARGS}
    ${DEFAULT_CMAKE_FLAGS}

  INSTALL_DIR ${LIBDIR}/vorbis
)

add_dependencies(
  external_vorbis
  external_ogg
)

if(NOT WIN32)
  harvest(external_vorbis vorbis/lib ffmpeg/lib "*.a")
endif()

unset(VORBIS_EXTRA_ARGS)
