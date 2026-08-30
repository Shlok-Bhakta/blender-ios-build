# SPDX-FileCopyrightText: 2002-2022 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

set(BROTLI_EXTRA_ARGS)
set(BROTLI_PATCH_COMMAND echo .)
set(BROTLI_INSTALL_COMMAND
  ${CMAKE_COMMAND} --build <BINARY_DIR> --target install
)
if(WITH_APPLE_CROSSPLATFORM)
  list(APPEND BROTLI_EXTRA_ARGS
    -DWITH_APPLE_CROSSPLATFORM=ON
    -DBROTLI_DISABLE_TESTS=ON
    -DCMAKE_POLICY_VERSION_MINIMUM=3.5
  )
  set(BROTLI_PATCH_COMMAND
    ${PATCH_CMD} -p 1 -d ${BUILD_DIR}/brotli/src/external_brotli <
    ${IOS_PATCH_DIR}/brotli_ios.diff
  )
  # Brotli 1.0.9's Emscripten probe succeeds for every cross-compiler because
  # the negative branch is empty. Its static libraries are still correct, but
  # the false-positive removes the upstream install target.
  set(BROTLI_INSTALL_COMMAND
    ${CMAKE_COMMAND} -E make_directory ${LIBDIR}/brotli/include &&
    ${CMAKE_COMMAND} -E copy_directory
      <SOURCE_DIR>/c/include ${LIBDIR}/brotli/include &&
    ${CMAKE_COMMAND} -E make_directory ${LIBDIR}/brotli/lib &&
    ${CMAKE_COMMAND} -E copy
      <BINARY_DIR>/libbrotlicommon-static.a
      <BINARY_DIR>/libbrotlidec-static.a
      <BINARY_DIR>/libbrotlienc-static.a
      ${LIBDIR}/brotli/lib &&
    ${CMAKE_COMMAND} -E copy
      <BINARY_DIR>/libbrotlicommon-static.a
      ${LIBDIR}/brotli/lib/libbrotlicommon.a &&
    ${CMAKE_COMMAND} -E copy
      <BINARY_DIR>/libbrotlidec-static.a
      ${LIBDIR}/brotli/lib/libbrotlidec.a &&
    ${CMAKE_COMMAND} -E copy
      <BINARY_DIR>/libbrotlienc-static.a
      ${LIBDIR}/brotli/lib/libbrotlienc.a &&
    ${CMAKE_COMMAND} -E make_directory ${LIBDIR}/brotli/lib/pkgconfig &&
    ${CMAKE_COMMAND} -E copy
      <BINARY_DIR>/libbrotlicommon.pc
      <BINARY_DIR>/libbrotlidec.pc
      <BINARY_DIR>/libbrotlienc.pc
      ${LIBDIR}/brotli/lib/pkgconfig
  )
endif()

ExternalProject_Add(external_brotli
  URL file://${PACKAGE_DIR}/${BROTLI_FILE}
  DOWNLOAD_DIR ${DOWNLOAD_DIR}
  URL_HASH ${BROTLI_HASH_TYPE}=${BROTLI_HASH}
  PREFIX ${BUILD_DIR}/brotli
  PATCH_COMMAND ${BROTLI_PATCH_COMMAND}
  CMAKE_GENERATOR ${PLATFORM_ALT_GENERATOR}

  CMAKE_ARGS
    -DCMAKE_INSTALL_PREFIX=${LIBDIR}/brotli
    ${DEFAULT_CMAKE_FLAGS}
    ${BROTLI_EXTRA_ARGS}

  INSTALL_COMMAND ${BROTLI_INSTALL_COMMAND}

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

if(WITH_APPLE_CROSSPLATFORM)
  ExternalProject_Add_Step(external_brotli harvest_ios
    COMMAND ${CMAKE_COMMAND} -E copy_directory
      ${LIBDIR}/brotli/include
      ${HARVEST_TARGET}/brotli/include
    COMMAND ${CMAKE_COMMAND} -E make_directory
      ${HARVEST_TARGET}/brotli/lib
    COMMAND ${CMAKE_COMMAND} -E copy
      ${LIBDIR}/brotli/lib/libbrotlicommon-static.a
      ${HARVEST_TARGET}/brotli/lib/libbrotlicommon-static.a
    COMMAND ${CMAKE_COMMAND} -E copy
      ${LIBDIR}/brotli/lib/libbrotlidec-static.a
      ${HARVEST_TARGET}/brotli/lib/libbrotlidec-static.a
    COMMAND ${CMAKE_COMMAND} -E copy
      ${LIBDIR}/brotli/lib/libbrotlienc-static.a
      ${HARVEST_TARGET}/brotli/lib/libbrotlienc-static.a
    DEPENDEES install
  )
endif()
