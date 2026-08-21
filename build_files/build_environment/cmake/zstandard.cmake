# SPDX-FileCopyrightText: 2017-2022 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

if(MSVC)
  if(BUILD_MODE STREQUAL Debug)
    set(ZSTANDARD_DIR_POSTFIX -pydebug)
    set(ZSTANDARD_ARCHIVE_POSTFIX d)
    set(ZSTANDARD_BUILD_OPTION --debug)
  else()
    set(ZSTANDARD_DIR_POSTFIX "")
    set(ZSTANDARD_ARCHIVE_POSTFIX "")
    set(ZSTANDARD_BUILD_OPTION "")
  endif()
endif()

set(ZSTANDARD_POSTFIX "")

if(WITH_APPLE_CROSSPLATFORM)
  set(_zstandard_wheelhouse ${BUILD_DIR}/zstandard-wheelhouse)
  set(_zstandard_target_site_packages
    ${LIBDIR}/python/lib/python${PYTHON_SHORT_VERSION}/site-packages
  )

  ExternalProject_Add(external_zstandard
    URL file://${PACKAGE_DIR}/${ZSTANDARD_FILE}
    DOWNLOAD_DIR ${DOWNLOAD_DIR}
    URL_HASH ${ZSTANDARD_HASH_TYPE}=${ZSTANDARD_HASH}
    PREFIX ${BUILD_DIR}/zstandard
    PATCH_COMMAND ${ZSTANDARD_PATCH}
    BUILD_IN_SOURCE 1

    CONFIGURE_COMMAND ${CMAKE_COMMAND} -E rm -rf ${_zstandard_wheelhouse}
    BUILD_COMMAND
      ${CMAKE_COMMAND} -E make_directory ${_zstandard_wheelhouse}
      COMMAND ${CMAKE_COMMAND} -E env
        "PATH=${PYTHON_CROSS_VENV}/bin:$ENV{PATH}"
        "CFLAGS=-I${LIBDIR}/zstd/include"
        "LDFLAGS=-L${LIBDIR}/zstd/lib"
        ${PYTHON_CROSS_VENV}/bin/python -m pip wheel
          --disable-pip-version-check
          --no-build-isolation
          --no-deps
          --wheel-dir ${_zstandard_wheelhouse}
          -C--build-option=--system-zstd
          -C--build-option=--no-cffi-backend
          <SOURCE_DIR>

    INSTALL_COMMAND
      ${CMAKE_COMMAND} -E make_directory ${_zstandard_target_site_packages}
      COMMAND ${PYTHON_CROSS_VENV}/bin/python -m pip install
        --disable-pip-version-check
        --no-index
        --no-deps
        --upgrade
        --target ${_zstandard_target_site_packages}
        --find-links ${_zstandard_wheelhouse}
        zstandard==${ZSTANDARD_VERSION}
  )

  ExternalProject_Add_Step(external_zstandard harvest_ios
    COMMAND ${CMAKE_COMMAND} -E copy_directory
      ${_zstandard_target_site_packages}
      ${HARVEST_TARGET}/python/lib/python${PYTHON_SHORT_VERSION}/site-packages
    DEPENDEES install
  )

  add_dependencies(
    external_zstandard
    external_python_cross_environment
    external_python_site_packages
    external_zstd
  )
else()
  ExternalProject_Add(external_zstandard
    URL file://${PACKAGE_DIR}/${ZSTANDARD_FILE}
    DOWNLOAD_DIR ${DOWNLOAD_DIR}
    URL_HASH ${ZSTANDARD_HASH_TYPE}=${ZSTANDARD_HASH}
    PREFIX ${BUILD_DIR}/zstandard
    PATCH_COMMAND ${ZSTANDARD_PATCH}
    CONFIGURE_COMMAND ""
    LOG_BUILD 1
    BUILD_IN_SOURCE 1

    BUILD_COMMAND
      ${PYTHON_BINARY} setup.py
        --system-zstd
        build_ext ${ZSTANDARD_BUILD_OPTION} -j${PYTHON_MAKE_THREADS}
        --include-dirs=${LIBDIR}/zstd/include
        --library-dirs=${LIBDIR}/zstd/lib
        install
        --old-and-unmanageable

    INSTALL_COMMAND ""
  )

  add_dependencies(
    external_zstandard
    external_python
    external_zstd
  )
endif()

unset(_zstandard_target_site_packages)
unset(_zstandard_wheelhouse)
