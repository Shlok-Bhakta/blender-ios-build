# SPDX-FileCopyrightText: 2017-2022 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

if(MSVC)
  if(BUILD_MODE STREQUAL Debug)
    set(CYTHON_DIR_POSTFIX -pydebug)
    set(CYTHON_ARCHIVE_POSTFIX d)
    set(CYTHON_BUILD_OPTION --debug)
  else()
    set(CYTHON_DIR_POSTFIX "")
    set(CYTHON_ARCHIVE_POSTFIX "")
    set(CYTHON_BUILD_OPTION "")
  endif()
endif()

set(CYTHON_POSTFIX "")

if(WITH_APPLE_CROSSPLATFORM)
  # Target Python is not executable on the build host (e.g. iOS simulator).
  set(CYTHON_PYTHON_EXECUTABLE ${CMAKE_DEPS_CROSSCOMPILE_INSTALLDIR}/python/bin/python${PYTHON_SHORT_VERSION})
  set(CYTHON_INSTALL_PREFIX_ARG --prefix=${LIBDIR}/python)
else()
  set(CYTHON_PYTHON_EXECUTABLE ${PYTHON_BINARY})
  set(CYTHON_INSTALL_PREFIX_ARG "")
endif()

ExternalProject_Add(external_cython
  URL file://${PACKAGE_DIR}/${CYTHON_FILE}
  DOWNLOAD_DIR ${DOWNLOAD_DIR}
  URL_HASH ${CYTHON_HASH_TYPE}=${CYTHON_HASH}
  PREFIX ${BUILD_DIR}/cython
  PATCH_COMMAND ${CYTHON_PATCH}
  CONFIGURE_COMMAND ""
  LOG_BUILD 1
  BUILD_IN_SOURCE 1

  BUILD_COMMAND
    ${CYTHON_PYTHON_EXECUTABLE} setup.py
      build ${CYTHON_BUILD_OPTION} -j${PYTHON_MAKE_THREADS}
      install
      ${CYTHON_INSTALL_PREFIX_ARG}
      --old-and-unmanageable

  INSTALL_COMMAND ""
)

add_dependencies(
  external_cython
  external_python
  external_python_site_packages
)
