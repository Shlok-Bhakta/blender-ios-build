# SPDX-FileCopyrightText: 2002-2023 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

if(MSVC)
  set(OPUS_CMAKE_ARGS
    -DPACKAGE_VERSION=${OPUS_VERSION}
    -DOPUS_BUILD_PROGRAMS=OFF
    -DOPUS_BUILD_TESTING=OFF
  )
endif()

if(NOT WIN32)
  include(${CMAKE_CURRENT_LIST_DIR}/platform/ios/opus_ios.cmake)
  blender_platform_ios_patch_opus_configure_env(OPUS_CONFIGURE_ENV)
  blender_platform_ios_patch_opus_configure_command(OPUS_CONFIGURE_COMMAND)

  ExternalProject_Add(external_opus
    URL file://${PACKAGE_DIR}/${OPUS_FILE}
    DOWNLOAD_DIR ${DOWNLOAD_DIR}
    URL_HASH ${OPUS_HASH_TYPE}=${OPUS_HASH}
    PREFIX ${BUILD_DIR}/opus

    CONFIGURE_COMMAND ${OPUS_CONFIGURE_ENV} &&
      cd ${BUILD_DIR}/opus/src/external_opus/ &&
      ${OPUS_CONFIGURE_COMMAND}
        --prefix=${LIBDIR}/opus

    BUILD_COMMAND ${CONFIGURE_ENV} &&
      cd ${BUILD_DIR}/opus/src/external_opus/ &&
      make -j${MAKE_THREADS}

    INSTALL_COMMAND ${CONFIGURE_ENV} &&
      cd ${BUILD_DIR}/opus/src/external_opus/ &&
      make install

    INSTALL_DIR ${LIBDIR}/opus
  )

  harvest(external_opus opus/lib ffmpeg/lib "*.a")
else()
  ExternalProject_Add(external_opus
    URL file://${PACKAGE_DIR}/${OPUS_FILE}
    DOWNLOAD_DIR ${DOWNLOAD_DIR}
    URL_HASH ${OPUS_HASH_TYPE}=${OPUS_HASH}
    PREFIX ${BUILD_DIR}/opus

    PATCH_COMMAND COMMAND
      ${PATCH_CMD} -p 1 -d
        ${BUILD_DIR}/opus/src/external_opus <
        ${PATCH_DIR}/opus_windows.diff

    CMAKE_ARGS
      -DCMAKE_INSTALL_PREFIX=${LIBDIR}/opus
      ${OPUS_CMAKE_ARGS}

    INSTALL_DIR ${LIBDIR}/opus
  )
endif()
