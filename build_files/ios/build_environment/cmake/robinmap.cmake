# SPDX-FileCopyrightText: 2022 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

set(ROBINMAP_EXTRA_ARGS)

if(WITH_APPLE_CROSSPLATFORM)
  list(APPEND ROBINMAP_EXTRA_ARGS -DCMAKE_POLICY_VERSION_MINIMUM=3.5)
endif()

ExternalProject_Add(external_robinmap
  URL file://${PACKAGE_DIR}/${ROBINMAP_FILE}
  DOWNLOAD_DIR ${DOWNLOAD_DIR}
  URL_HASH ${ROBINMAP_HASH_TYPE}=${ROBINMAP_HASH}
  PREFIX ${BUILD_DIR}/robinmap

  CMAKE_ARGS
    -DCMAKE_INSTALL_PREFIX=${LIBDIR}/robinmap
    ${DEFAULT_CMAKE_FLAGS}
    ${ROBINMAP_EXTRA_ARGS}

  INSTALL_DIR ${LIBDIR}/robinmap
)

if(WITH_APPLE_CROSSPLATFORM)
  ExternalProject_Add_Step(external_robinmap harvest_ios
    COMMAND ${CMAKE_COMMAND} -E copy_directory
      ${LIBDIR}/robinmap/include
      ${HARVEST_TARGET}/robinmap/include
    COMMAND ${CMAKE_COMMAND} -E copy_directory
      ${LIBDIR}/robinmap/share
      ${HARVEST_TARGET}/robinmap/share
    DEPENDEES install
  )
endif()
