# SPDX-FileCopyrightText: 2002-2022 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

set(BROTLI_PATCH_COMMAND)
if(APPLE AND WITH_APPLE_CROSSPLATFORM)
  set(BROTLI_PATCH_COMMAND
    COMMAND ${CMAKE_COMMAND} -E sed -i.bak
      "s/install(TARGETS brotli RUNTIME DESTINATION \"\\${CMAKE_INSTALL_BINDIR}\")/# DISABLED for iOS cross-compile: install(TARGETS brotli RUNTIME DESTINATION \"\\${CMAKE_INSTALL_BINDIR}\")/"
      ${BUILD_DIR}/brotli/src/external_brotli/CMakeLists.txt
  )
endif()

ExternalProject_Add(external_brotli
  URL file://${PACKAGE_DIR}/${BROTLI_FILE}
  DOWNLOAD_DIR ${DOWNLOAD_DIR}
  URL_HASH ${BROTLI_HASH_TYPE}=${BROTLI_HASH}
  PREFIX ${BUILD_DIR}/brotli
  CMAKE_GENERATOR ${PLATFORM_ALT_GENERATOR}
  PATCH_COMMAND ${BROTLI_PATCH_COMMAND}

  CMAKE_ARGS
    -DCMAKE_INSTALL_PREFIX=${LIBDIR}/brotli
    ${DEFAULT_CMAKE_FLAGS}
    -DCMAKE_POLICY_VERSION_MINIMUM=3.5

  INSTALL_DIR ${LIBDIR}/brotli
)

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
