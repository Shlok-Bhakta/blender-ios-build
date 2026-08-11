# SPDX-FileCopyrightText: 2022 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

set(PYSTRING_EXTRA_ARGS)

if(WITH_APPLE_CROSSPLATFORM)
  list(APPEND PYSTRING_EXTRA_ARGS -DBUILD_SHARED_LIBS=OFF)
endif()

ExternalProject_Add(external_pystring
  URL file://${PACKAGE_DIR}/${PYSTRING_FILE}
  DOWNLOAD_DIR ${DOWNLOAD_DIR}
  URL_HASH ${PYSTRING_HASH_TYPE}=${PYSTRING_HASH}
  PREFIX ${BUILD_DIR}/pystring

  PATCH_COMMAND ${CMAKE_COMMAND} -E copy
    ${PATCH_DIR}/cmakelists_pystring.txt
    ${BUILD_DIR}/pystring/src/external_pystring/CMakeLists.txt

  CMAKE_ARGS
    -DCMAKE_INSTALL_PREFIX=${LIBDIR}/pystring
    ${DEFAULT_CMAKE_FLAGS}
    ${PYSTRING_EXTRA_ARGS}

  INSTALL_DIR ${LIBDIR}/pystring
)

if(WIN32)
  ExternalProject_Add_Step(external_pystring after_install
    COMMAND ${CMAKE_COMMAND} -E copy_directory
      ${LIBDIR}/pystring/lib
      ${HARVEST_TARGET}/pystring/lib
    COMMAND ${CMAKE_COMMAND} -E copy_directory
      ${LIBDIR}/pystring/include
      ${HARVEST_TARGET}/pystring/include

    DEPENDEES install
  )
endif()

if(WITH_APPLE_CROSSPLATFORM)
  ExternalProject_Add_Step(external_pystring harvest_ios
    COMMAND ${CMAKE_COMMAND} -E copy_directory
      ${LIBDIR}/pystring/include
      ${HARVEST_TARGET}/pystring/include
    COMMAND ${CMAKE_COMMAND} -E copy_directory
      ${LIBDIR}/pystring/lib
      ${HARVEST_TARGET}/pystring/lib
    DEPENDEES install
  )
endif()
