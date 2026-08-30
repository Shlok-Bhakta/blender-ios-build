# SPDX-FileCopyrightText: 2017-2022 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

set(ALEMBIC_USE_BINARIES ON)
if(WITH_APPLE_CROSSPLATFORM)
  set(ALEMBIC_USE_BINARIES OFF)
endif()

set(ALEMBIC_EXTRA_ARGS
  -DImath_ROOT=${LIBDIR}/imath
  -DImath_DIR=${LIBDIR}/imath/lib/cmake/Imath
  -DUSE_PYALEMBIC=OFF
  -DUSE_ARNOLD=OFF
  -DUSE_MAYA=OFF
  -DUSE_PRMAN=OFF
  -DUSE_HDF5=OFF
  -DUSE_TESTS=OFF
  -DUSE_BINARIES=${ALEMBIC_USE_BINARIES}
  -DALEMBIC_ILMBASE_LINK_STATIC=OFF
  -DALEMBIC_SHARED_LIBS=OFF
)

ExternalProject_Add(external_alembic
  URL file://${PACKAGE_DIR}/${ALEMBIC_FILE}
  DOWNLOAD_DIR ${DOWNLOAD_DIR}
  URL_HASH ${ALEMBIC_HASH_TYPE}=${ALEMBIC_HASH}
  CMAKE_GENERATOR ${PLATFORM_ALT_GENERATOR}
  PREFIX ${BUILD_DIR}/alembic

  CMAKE_ARGS
    -DCMAKE_INSTALL_PREFIX=${LIBDIR}/alembic
    -Wno-dev
    ${DEFAULT_CMAKE_FLAGS}
    ${ALEMBIC_EXTRA_ARGS}

  INSTALL_DIR ${LIBDIR}/alembic
)

if(WIN32)
  if(BUILD_MODE STREQUAL Release)
    ExternalProject_Add_Step(external_alembic after_install
      COMMAND ${CMAKE_COMMAND} -E copy_directory
        ${LIBDIR}/alembic
        ${HARVEST_TARGET}/alembic

      DEPENDEES install
    )
  endif()
  if(BUILD_MODE STREQUAL Debug)
    ExternalProject_Add_Step(external_alembic after_install
      COMMAND ${CMAKE_COMMAND} -E copy
        ${LIBDIR}/alembic/lib/alembic.lib
        ${HARVEST_TARGET}/alembic/lib/alembic_d.lib

      DEPENDEES install
    )
  endif()
else()
  harvest(external_alembic alembic/include alembic/include "*.h")
  harvest(external_alembic alembic/lib/libAlembic.a alembic/lib/libAlembic.a)
  if(NOT WITH_APPLE_CROSSPLATFORM)
    harvest_rpath_bin(external_alembic alembic/bin alembic/bin "*")
  endif()
endif()



add_dependencies(
  external_alembic
  external_imath
)

unset(ALEMBIC_USE_BINARIES)
