# SPDX-FileCopyrightText: 2022-2023 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

if(WIN32)
  set(FRIBIDI_CONFIGURE_ENV ${CONFIGURE_ENV_MSVC})
else()
  if(WITH_APPLE_CROSSPLATFORM)
    set(FRIBIDI_CONFIGURE_ENV
      unset CFLAGS CXXFLAGS LDFLAGS IPHONEOS_DEPLOYMENT_TARGET
    )
  else()
    set(FRIBIDI_CONFIGURE_ENV ${CONFIGURE_ENV})
  endif()
endif()

set(FRIBIDI_EXTRA_OPTIONS
  -Ddocs=false
)
set(FRIBIDI_CROSS_OPTIONS)
if(WITH_APPLE_CROSSPLATFORM)
  list(APPEND FRIBIDI_EXTRA_OPTIONS
    -Dbin=false
    -Dtests=false
  )
  set(FRIBIDI_CROSS_OPTIONS
    --cross-file ${BLENDER_IOS_MESON_CROSS_FILE}
    --native-file ${BLENDER_IOS_MESON_NATIVE_FILE}
  )
endif()

ExternalProject_Add(external_fribidi
  URL file://${PACKAGE_DIR}/${FRIBIDI_FILE}
  URL_HASH ${FRIBIDI_HASH_TYPE}=${FRIBIDI_HASH}
  DOWNLOAD_DIR ${DOWNLOAD_DIR}
  PREFIX ${BUILD_DIR}/fribidi

  CONFIGURE_COMMAND ${FRIBIDI_CONFIGURE_ENV} &&
    ${MESON} setup
      --prefix ${LIBDIR}/fribidi
      --libdir lib
      --default-library static
      ${FRIBIDI_CROSS_OPTIONS}
      ${MESON_BUILD_TYPE}
      ${FRIBIDI_EXTRA_OPTIONS}
      ${BUILD_DIR}/fribidi/src/external_fribidi-build
      ${BUILD_DIR}/fribidi/src/external_fribidi

  BUILD_COMMAND ninja
  INSTALL_COMMAND ninja install
  INSTALL_DIR ${LIBDIR}/fribidi
)

if(NOT WITH_APPLE_CROSSPLATFORM)
  add_dependencies(
    external_fribidi
    external_python
    # Needed for `MESON`.
    external_python_site_packages
  )
endif()

if(WIN32)
  if(BUILD_MODE STREQUAL Release)
    ExternalProject_Add_Step(external_fribidi after_install
      COMMAND ${CMAKE_COMMAND} -E copy_directory
        ${LIBDIR}/fribidi/include
        ${HARVEST_TARGET}/fribidi/include
      COMMAND ${CMAKE_COMMAND} -E copy
        ${LIBDIR}/fribidi/lib/libfribidi.a
        ${HARVEST_TARGET}/fribidi/lib/libfribidi.lib

      DEPENDEES install
    )
  endif()
else()
  harvest(external_fribidi fribidi/include fribidi/include "*.h")
  harvest(external_fribidi fribidi/lib fribidi/lib "*.a")
endif()

if(WITH_APPLE_CROSSPLATFORM)
  ExternalProject_Add_Step(external_fribidi harvest_ios
    COMMAND ${CMAKE_COMMAND} -E copy_directory
      ${LIBDIR}/fribidi/include
      ${HARVEST_TARGET}/fribidi/include
    COMMAND ${CMAKE_COMMAND} -E make_directory
      ${HARVEST_TARGET}/fribidi/lib
    COMMAND ${CMAKE_COMMAND} -E copy
      ${LIBDIR}/fribidi/lib/libfribidi.a
      ${HARVEST_TARGET}/fribidi/lib/libfribidi.a
    DEPENDEES install
  )
endif()
