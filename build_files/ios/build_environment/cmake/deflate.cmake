# SPDX-FileCopyrightText: 2023 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later


set(DEFLATE_EXTRA_ARGS
  -DCMAKE_POSITION_INDEPENDENT_CODE=ON
  -DLIBDEFLATE_BUILD_STATIC_LIB=ON
  -DLIBDEFLATE_BUILD_SHARED_LIB=OFF
)
if(WITH_APPLE_CROSSPLATFORM)
  list(APPEND DEFLATE_EXTRA_ARGS -DLIBDEFLATE_BUILD_GZIP=OFF)
endif()

ExternalProject_Add(external_deflate
  URL file://${PACKAGE_DIR}/${DEFLATE_FILE}
  DOWNLOAD_DIR ${DOWNLOAD_DIR}
  URL_HASH ${DEFLATE_HASH_TYPE}=${DEFLATE_HASH}
  PREFIX ${BUILD_DIR}/deflate
  CMAKE_GENERATOR ${PLATFORM_ALT_GENERATOR}

  CMAKE_ARGS
    -DCMAKE_INSTALL_PREFIX=${LIBDIR}/deflate
    ${DEFAULT_CMAKE_FLAGS}
    ${DEFLATE_EXTRA_ARGS}

  INSTALL_DIR ${LIBDIR}/deflate
)

if(WITH_APPLE_CROSSPLATFORM)
  ExternalProject_Add_Step(external_deflate harvest_ios
    COMMAND ${CMAKE_COMMAND} -E copy_directory
      ${LIBDIR}/deflate/include
      ${HARVEST_TARGET}/deflate/include
    COMMAND ${CMAKE_COMMAND} -E make_directory
      ${HARVEST_TARGET}/deflate/lib
    COMMAND ${CMAKE_COMMAND} -E copy
      ${LIBDIR}/deflate/lib/libdeflate.a
      ${HARVEST_TARGET}/deflate/lib/libdeflate.a
    DEPENDEES install
  )
endif()
