# SPDX-FileCopyrightText: 2002-2022 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

set(YAMLCPP_EXTRA_ARGS
  -DYAML_CPP_BUILD_TESTS=OFF
  -DYAML_CPP_BUILD_TOOLS=OFF
  -DYAML_CPP_BUILD_CONTRIB=OFF
)

if(WITH_APPLE_CROSSPLATFORM)
  list(APPEND YAMLCPP_EXTRA_ARGS
    -DBUILD_SHARED_LIBS=OFF
    -DCMAKE_POLICY_VERSION_MINIMUM=3.5
  )
endif()

if(WIN32)
  set(YAMLCPP_EXTRA_ARGS
    ${YAMLCPP_EXTRA_ARGS}
    -DBUILD_GMOCK=OFF
    -DYAML_MSVC_SHARED_RT=ON
  )
endif()

ExternalProject_Add(external_yamlcpp
  URL file://${PACKAGE_DIR}/${YAMLCPP_FILE}
  DOWNLOAD_DIR ${DOWNLOAD_DIR}
  URL_HASH ${YAMLCPP_HASH_TYPE}=${YAMLCPP_HASH}
  PREFIX ${BUILD_DIR}/yamlcpp
  CMAKE_GENERATOR ${PLATFORM_ALT_GENERATOR}

  CMAKE_ARGS
    -DCMAKE_INSTALL_PREFIX=${LIBDIR}/yamlcpp
    ${DEFAULT_CMAKE_FLAGS}
    ${YAMLCPP_EXTRA_ARGS}

  INSTALL_DIR ${LIBDIR}/yamlcpp
)

if(WITH_APPLE_CROSSPLATFORM)
  ExternalProject_Add_Step(external_yamlcpp harvest_ios
    COMMAND ${CMAKE_COMMAND} -E copy_directory
      ${LIBDIR}/yamlcpp/include
      ${HARVEST_TARGET}/yamlcpp/include
    COMMAND ${CMAKE_COMMAND} -E copy_directory
      ${LIBDIR}/yamlcpp/lib
      ${HARVEST_TARGET}/yamlcpp/lib
    DEPENDEES install
  )
endif()
