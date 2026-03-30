# SPDX-FileCopyrightText: 2002-2022 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

if(APPLE AND WITH_APPLE_CROSSPLATFORM)
  set(BROTLI_EXTRA_ARGS
    -DBROTLI_CLI_C=
    -DCMAKE_POLICY_VERSION_MINIMUM=3.5
  )
else()
  set(BROTLI_EXTRA_ARGS
    -DCMAKE_POLICY_VERSION_MINIMUM=3.5
  )
endif()

ExternalProject_Add(external_brotli
  URL file://${PACKAGE_DIR}/${BROTLI_FILE}
  DOWNLOAD_DIR ${DOWNLOAD_DIR}
  URL_HASH ${BROTLI_HASH_TYPE}=${BROTLI_HASH}
  PREFIX ${BUILD_DIR}/brotli
  CMAKE_GENERATOR ${PLATFORM_ALT_GENERATOR}

  CMAKE_ARGS
    -DCMAKE_INSTALL_PREFIX=${LIBDIR}/brotli
    ${DEFAULT_CMAKE_FLAGS}
    ${BROTLI_EXTRA_ARGS}

  INSTALL_DIR ${LIBDIR}/brotli
)

if(APPLE AND WITH_APPLE_CROSSPLATFORM)
  ExternalProject_Add_Step(external_brotli patch_brotli
    COMMAND ${CMAKE_CURRENT_LIST_DIR}/platform/ios/patch_brotli.sh
      ${BUILD_DIR}/brotli/src/external_brotli/CMakeLists.txt
    DEPENDEES download
    DEPENDERS configure
  )
endif()

if(WIN32)
  if(BUILD_MODE STREQUAL Release)
    ExternalProject_Add_Step(external_brotli after_install
      COMMAND ${CMAKE_COMMAND} -E copy_directory
        ${LIBDIR}/brotli/include
        ${HARVEST_TARGET}/brotli/include
      COMMAND ${CMAKE_COMMAND} -E copy
        ${LIBDIR}/brotli/lib/brotlidec-static${LIBEXT}
        ${HARVEST_TARGET}/brotli/lib/brotlidec-static${LIBEXT}
      COMMAND ${CMAKE_COMMAND} -E copy
        ${LIBDIR}/brotli/lib/brotlicommon-static${LIBEXT}
        ${HARVEST_TARGET}/brotli/lib/brotlicommon-static${LIBEXT}

      DEPENDEES install
    )
  endif()
else()
  harvest(external_brotli brotli/include brotli/include "*.h")
  harvest(external_brotli brotli/lib brotli/lib "*.a")
endif()
