# SPDX-FileCopyrightText: 2022-2023 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

if(WIN32)
  set(HARFBUZZ_CONFIGURE_ENV ${CONFIGURE_ENV_MSVC})
  set(HARFBUZZ_PKG_ENV FREETYPE_DIR=${LIBDIR}/freetype)
else()
  if(WITH_APPLE_CROSSPLATFORM)
    # Target arguments live in the Meson cross file. Exporting them as generic
    # CFLAGS also poisons native generators used during the cross build.
    set(HARFBUZZ_CONFIGURE_ENV
      unset CFLAGS CXXFLAGS LDFLAGS IPHONEOS_DEPLOYMENT_TARGET
    )
  else()
    set(HARFBUZZ_CONFIGURE_ENV ${CONFIGURE_ENV})
  endif()
  set(HARFBUZZ_PKG_ENV "PKG_CONFIG_PATH=\
${LIBDIR}/freetype/lib/pkgconfig:\
${LIBDIR}/brotli/lib/pkgconfig:\
${LIBDIR}/zlib/share/pkgconfig:\
${LIBDIR}/lib/python3.10/pkgconfig:\
$PKG_CONFIG_PATH"
  )
endif()

set(HARFBUZZ_EXTRA_OPTIONS
  -Dtests=disabled
  -Dfreetype=enabled
  -Dglib=disabled
  -Dgobject=disabled
  # Only used for command line utilities,
  # disable as this would add an additional & unnecessary build-dependency.
  -Dcairo=disabled
)
set(HARFBUZZ_CROSS_OPTIONS)
if(WITH_APPLE_CROSSPLATFORM)
  list(APPEND HARFBUZZ_EXTRA_OPTIONS
    -Ddocs=disabled
    -Dintrospection=disabled
    -Dutilities=disabled
  )
  set(HARFBUZZ_CROSS_OPTIONS
    --cross-file ${BLENDER_IOS_MESON_CROSS_FILE}
    --native-file ${BLENDER_IOS_MESON_NATIVE_FILE}
  )
endif()

ExternalProject_Add(external_harfbuzz
  URL file://${PACKAGE_DIR}/${HARFBUZZ_FILE}
  URL_HASH ${HARFBUZZ_HASH_TYPE}=${HARFBUZZ_HASH}
  DOWNLOAD_DIR ${DOWNLOAD_DIR}
  PREFIX ${BUILD_DIR}/harfbuzz

  CONFIGURE_COMMAND ${HARFBUZZ_CONFIGURE_ENV} &&
    ${CMAKE_COMMAND} -E env ${HARFBUZZ_PKG_ENV} ${MESON} setup
      --prefix ${LIBDIR}/harfbuzz
      --libdir lib
      --default-library static
      ${HARFBUZZ_CROSS_OPTIONS}
      ${MESON_BUILD_TYPE}
      ${HARFBUZZ_EXTRA_OPTIONS}
      ${BUILD_DIR}/harfbuzz/src/external_harfbuzz-build
      ${BUILD_DIR}/harfbuzz/src/external_harfbuzz

  BUILD_COMMAND ninja
  INSTALL_COMMAND ninja install
  INSTALL_DIR ${LIBDIR}/harfbuzz
)

if(WITH_APPLE_CROSSPLATFORM)
  add_dependencies(external_harfbuzz external_freetype)
else()
  add_dependencies(
    external_harfbuzz
    external_python
    external_freetype
    # Needed for `MESON`.
    external_python_site_packages
  )
endif()

if(WIN32)
  if(BUILD_MODE STREQUAL Release)
    ExternalProject_Add_Step(external_harfbuzz after_install
      COMMAND ${CMAKE_COMMAND} -E copy_directory
        ${LIBDIR}/harfbuzz/include
        ${HARVEST_TARGET}/harfbuzz/include
      # We do not use the subset API currently, so copying only the main library will suffice for now
      COMMAND ${CMAKE_COMMAND} -E copy
        ${LIBDIR}/harfbuzz/lib/libharfbuzz.a
        ${HARVEST_TARGET}/harfbuzz/lib/libharfbuzz.lib
      DEPENDEES install
    )
  endif()

  if(BUILD_MODE STREQUAL Debug)
    ExternalProject_Add_Step(external_harfbuzz after_install
      COMMAND ${CMAKE_COMMAND} -E copy
        ${LIBDIR}/harfbuzz/lib/libharfbuzz.a
        ${HARVEST_TARGET}/harfbuzz/lib/libharfbuzz_d.lib
      DEPENDEES install
    )
  endif()
else()
  harvest(external_harfbuzz harfbuzz/include harfbuzz/include "*.h")
  harvest(external_harfbuzz harfbuzz/lib harfbuzz/lib "*.a")
endif()

if(WITH_APPLE_CROSSPLATFORM)
  ExternalProject_Add_Step(external_harfbuzz harvest_ios
    COMMAND ${CMAKE_COMMAND} -E copy_directory
      ${LIBDIR}/harfbuzz/include
      ${HARVEST_TARGET}/harfbuzz/include
    COMMAND ${CMAKE_COMMAND} -E make_directory
      ${HARVEST_TARGET}/harfbuzz/lib
    COMMAND ${CMAKE_COMMAND} -E copy
      ${LIBDIR}/harfbuzz/lib/libharfbuzz.a
      ${HARVEST_TARGET}/harfbuzz/lib/libharfbuzz.a
    DEPENDEES install
  )
endif()
