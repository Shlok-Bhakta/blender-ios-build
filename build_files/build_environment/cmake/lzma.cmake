# SPDX-FileCopyrightText: 2002-2022 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

set(LZMA_PATCH_CMD echo .)

if(WITH_APPLE_CROSSPLATFORM)
  if("${CMAKE_OSX_ARCHITECTURES}" STREQUAL "x86_64")
    set(LZMA_EXTRA_ARGS --host=x86_64-apple-darwin19.0.0)
  else()
    set(LZMA_EXTRA_ARGS --host=aarch64-apple-darwin20.0.0)
  endif()
else()
  set(LZMA_EXTRA_ARGS)
endif()

ExternalProject_Add(external_lzma
  URL file://${PACKAGE_DIR}/${LZMA_FILE}
  DOWNLOAD_DIR ${DOWNLOAD_DIR}
  URL_HASH ${LZMA_HASH_TYPE}=${LZMA_HASH}
  PREFIX ${BUILD_DIR}/lzma
  PATCH_COMMAND ${LZMA_PATCH_CMD}

  CONFIGURE_COMMAND ${CONFIGURE_ENV} &&
    cd ${BUILD_DIR}/lzma/src/external_lzma/ &&
    ${CONFIGURE_COMMAND} --prefix=${LIBDIR}/lzma --disable-shared ${LZMA_EXTRA_ARGS}

  BUILD_COMMAND ${CONFIGURE_ENV} &&
    cd ${BUILD_DIR}/lzma/src/external_lzma/ &&
    make -j${MAKE_THREADS}

  INSTALL_COMMAND ${CONFIGURE_ENV} &&
    cd ${BUILD_DIR}/lzma/src/external_lzma/ &&
    make install

  INSTALL_DIR ${LIBDIR}/lzma
)
