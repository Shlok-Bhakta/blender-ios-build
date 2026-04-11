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
  set(OPUS_CONFIGURE_COMMAND ${CONFIGURE_COMMAND})
  set(OPUS_CONFIGURE_ARGS
    --prefix=${LIBDIR}/opus
    --disable-shared
    --enable-static
    --with-pic
    --disable-maintainer-mode)

  if(WITH_APPLE_CROSSPLATFORM)
    if("${CMAKE_OSX_ARCHITECTURES}" STREQUAL "x86_64")
      list(APPEND OPUS_CONFIGURE_ARGS --host=x86_64-apple-darwin19.0.0)
    else()
      list(APPEND OPUS_CONFIGURE_ARGS --host=aarch64-apple-darwin20.0.0)
    endif()
    set(OPUS_CONFIGURE_COMMAND ${CONFIGURE_COMMAND_NO_TARGET})
  endif()

  ExternalProject_Add(external_opus
    URL file://${PACKAGE_DIR}/${OPUS_FILE}
    DOWNLOAD_DIR ${DOWNLOAD_DIR}
    URL_HASH ${OPUS_HASH_TYPE}=${OPUS_HASH}
    PREFIX ${BUILD_DIR}/opus

    CONFIGURE_COMMAND ${CONFIGURE_ENV} &&
      cd ${BUILD_DIR}/opus/src/external_opus/ &&
      ${OPUS_CONFIGURE_COMMAND}
        ${OPUS_CONFIGURE_ARGS}

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
