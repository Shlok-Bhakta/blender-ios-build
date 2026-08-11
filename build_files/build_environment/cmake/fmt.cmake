# SPDX-FileCopyrightText: 2022 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

set(FMT_EXTRA_ARGS
  -DFMT_TEST=OFF
  -DFMT_DOC=OFF
)

if(WITH_APPLE_CROSSPLATFORM)
  list(APPEND FMT_EXTRA_ARGS -DBUILD_SHARED_LIBS=OFF)
endif()

ExternalProject_Add(external_fmt
  URL file://${PACKAGE_DIR}/${FMT_FILE}
  DOWNLOAD_DIR ${DOWNLOAD_DIR}
  URL_HASH ${FMT_HASH_TYPE}=${FMT_HASH}
  PREFIX ${BUILD_DIR}/fmt

  CMAKE_ARGS
    -DCMAKE_INSTALL_PREFIX=${LIBDIR}/fmt
    ${DEFAULT_CMAKE_FLAGS}
    ${FMT_EXTRA_ARGS}

  INSTALL_DIR ${LIBDIR}/fmt
)

if(WIN32)
  ExternalProject_Add_Step(external_fmt after_install
    COMMAND ${CMAKE_COMMAND} -E copy_directory
      ${LIBDIR}/fmt/
      ${HARVEST_TARGET}/fmt

    DEPENDEES install
  )

else()
  harvest(external_fmt fmt/include fmt/include "*.h")
  harvest(external_fmt fmt/lib/cmake/fmt fmt/lib/cmake/fmt "*.cmake")
  harvest(external_fmt fmt/lib fmt/lib "*.a")
endif()

if(WITH_APPLE_CROSSPLATFORM)
  ExternalProject_Add_Step(external_fmt harvest_ios
    COMMAND ${CMAKE_COMMAND} -E copy_directory
      ${LIBDIR}/fmt/include
      ${HARVEST_TARGET}/fmt/include
    COMMAND ${CMAKE_COMMAND} -E copy_directory
      ${LIBDIR}/fmt/lib
      ${HARVEST_TARGET}/fmt/lib
    DEPENDEES install
  )
endif()
