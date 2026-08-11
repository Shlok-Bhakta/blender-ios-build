# SPDX-FileCopyrightText: 2002-2022 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

set(PUGIXML_EXTRA_ARGS)

if(WITH_APPLE_CROSSPLATFORM)
  list(APPEND PUGIXML_EXTRA_ARGS
    -DBUILD_SHARED_LIBS=OFF
    -DCMAKE_POLICY_VERSION_MINIMUM=3.5
  )
endif()

ExternalProject_Add(external_pugixml
  URL file://${PACKAGE_DIR}/${PUGIXML_FILE}
  DOWNLOAD_DIR ${DOWNLOAD_DIR}
  URL_HASH ${PUGIXML_HASH_TYPE}=${PUGIXML_HASH}
  PREFIX ${BUILD_DIR}/pugixml

  CMAKE_ARGS
    -DCMAKE_INSTALL_PREFIX=${LIBDIR}/pugixml
    ${DEFAULT_CMAKE_FLAGS}
    ${PUGIXML_EXTRA_ARGS}

  INSTALL_DIR ${LIBDIR}/pugixml
)
if(WIN32)
  if(BUILD_MODE STREQUAL Release)
    ExternalProject_Add_Step(external_pugixml after_install
      COMMAND ${CMAKE_COMMAND} -E copy_directory
        ${LIBDIR}/pugixml
        ${HARVEST_TARGET}/pugixml

      DEPENDEES install
    )
  endif()
  if(BUILD_MODE STREQUAL Debug)
    ExternalProject_Add_Step(external_pugixml after_install
      COMMAND ${CMAKE_COMMAND} -E copy
        ${LIBDIR}/pugixml/lib/pugixml.lib
        ${HARVEST_TARGET}/pugixml/lib/pugixml_d.lib

      DEPENDEES install
    )
  endif()
else()
  harvest(external_pugixml pugixml/include pugixml/include "*.hpp")
  harvest(external_pugixml pugixml/lib pugixml/lib "*.a")
endif()

if(WITH_APPLE_CROSSPLATFORM)
  ExternalProject_Add_Step(external_pugixml harvest_ios
    COMMAND ${CMAKE_COMMAND} -E copy_directory
      ${LIBDIR}/pugixml/include
      ${HARVEST_TARGET}/pugixml/include
    COMMAND ${CMAKE_COMMAND} -E copy_directory
      ${LIBDIR}/pugixml/lib
      ${HARVEST_TARGET}/pugixml/lib
    DEPENDEES install
  )
endif()
