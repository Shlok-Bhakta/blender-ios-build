# SPDX-FileCopyrightText: 2002-2022 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

set(LZMA_PATCH_CMD echo .)

ExternalProject_Add(external_lzma
  URL file://${PACKAGE_DIR}/${LZMA_FILE}
  DOWNLOAD_DIR ${DOWNLOAD_DIR}
  URL_HASH ${LZMA_HASH_TYPE}=${LZMA_HASH}
  PREFIX ${BUILD_DIR}/lzma
  PATCH_COMMAND ${LZMA_PATCH_CMD}

  CONFIGURE_COMMAND ${CONFIGURE_ENV} &&
    cd ${BUILD_DIR}/lzma/src/external_lzma/ &&
    ${CONFIGURE_COMMAND} --prefix=${LIBDIR}/lzma --disable-shared

  BUILD_COMMAND ${CONFIGURE_ENV} &&
    cd ${BUILD_DIR}/lzma/src/external_lzma/ &&
    make -j${MAKE_THREADS}

  INSTALL_COMMAND ${CONFIGURE_ENV} &&
    cd ${BUILD_DIR}/lzma/src/external_lzma/ &&
    make install

  INSTALL_DIR ${LIBDIR}/lzma
)

if(WITH_APPLE_CROSSPLATFORM)
  ExternalProject_Add_Step(external_lzma harvest_ios
    COMMAND ${CMAKE_COMMAND} -E copy_directory
      ${LIBDIR}/lzma/include
      ${HARVEST_TARGET}/lzma/include
    COMMAND ${CMAKE_COMMAND} -E make_directory
      ${HARVEST_TARGET}/lzma/lib
    COMMAND ${CMAKE_COMMAND} -E copy
      ${LIBDIR}/lzma/lib/liblzma.a
      ${HARVEST_TARGET}/lzma/lib/liblzma.a
    DEPENDEES install
  )
endif()
