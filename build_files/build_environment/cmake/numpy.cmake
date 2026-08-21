# SPDX-FileCopyrightText: 2017-2022 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

if(MSVC)
  if(BUILD_MODE STREQUAL Debug)
    set(NUMPY_DIR_POSTFIX -pydebug)
    set(NUMPY_ARCHIVE_POSTFIX d)
    set(NUMPY_BUILD_OPTION --debug)
  else()
    set(NUMPY_DIR_POSTFIX "")
    set(NUMPY_ARCHIVE_POSTFIX "")
    set(NUMPY_BUILD_OPTION "")
  endif()
endif()

set(NUMPY_POSTFIX "")

if(WITH_APPLE_CROSSPLATFORM)
  set(_numpy_wheelhouse ${BUILD_DIR}/numpy-wheelhouse)
  set(_numpy_target_site_packages
    ${LIBDIR}/python/lib/python${PYTHON_SHORT_VERSION}/site-packages
  )
  ExternalProject_Add(external_numpy
    URL file://${PACKAGE_DIR}/${NUMPY_FILE}
    DOWNLOAD_DIR ${DOWNLOAD_DIR}
    URL_HASH ${NUMPY_HASH_TYPE}=${NUMPY_HASH}
    PREFIX ${BUILD_DIR}/numpy
    PATCH_COMMAND ${NUMPY_PATCH}
    BUILD_IN_SOURCE 1

    CONFIGURE_COMMAND
      ${CMAKE_COMMAND} -E rm -rf ${_numpy_wheelhouse}

    BUILD_COMMAND
      ${CMAKE_COMMAND} -E make_directory ${_numpy_wheelhouse}
      COMMAND ${CMAKE_COMMAND} -E env
        "PATH=${PYTHON_CROSS_VENV}/bin:$ENV{PATH}"
        ${PYTHON_CROSS_VENV}/bin/python -m pip wheel
          --disable-pip-version-check
          --no-build-isolation
          --no-deps
          --wheel-dir ${_numpy_wheelhouse}
          <SOURCE_DIR>
          -Csetup-args=--cross-file=${PYTHON_CROSS_VENV}/ios-cross.ini
          -Csetup-args=-Dallow-noblas=true
          -Csetup-args=-Dcpu-baseline=min
          -Csetup-args=-Dcpu-dispatch=none
          -Ccompile-args=-j${PYTHON_MAKE_THREADS}

    INSTALL_COMMAND
      ${CMAKE_COMMAND} -E make_directory ${_numpy_target_site_packages}
      COMMAND ${PYTHON_CROSS_VENV}/bin/python -m pip install
        --disable-pip-version-check
        --no-index
        --no-deps
        --upgrade
        --target ${_numpy_target_site_packages}
        --find-links ${_numpy_wheelhouse}
        numpy==${NUMPY_VERSION}
  )

  ExternalProject_Add_Step(external_numpy harvest_ios
    COMMAND ${CMAKE_COMMAND} -E copy_directory
      ${_numpy_target_site_packages}
      ${HARVEST_TARGET}/python/lib/python${PYTHON_SHORT_VERSION}/site-packages
    DEPENDEES install
  )

  add_dependencies(
    external_numpy
    external_python
    external_python_cross_environment
    external_python_site_packages
  )
elseif(WIN32)
  file(WRITE ${CMAKE_BINARY_DIR}/fix_path.bat
    "set PATH=${LIBDIR}/python;${LIBDIR}/python/scripts;%PATH%\n"
  )
  set(NUMPY_CONF ${CMAKE_BINARY_DIR}/fix_path.bat)
else()
  set(NUMPY_CONF export CYTHON=${LIBDIR}/python/bin/cython)
endif()

if(NOT WITH_APPLE_CROSSPLATFORM)
  ExternalProject_Add(external_numpy
    URL file://${PACKAGE_DIR}/${NUMPY_FILE}
    DOWNLOAD_DIR ${DOWNLOAD_DIR}
    URL_HASH ${NUMPY_HASH_TYPE}=${NUMPY_HASH}
    PREFIX ${BUILD_DIR}/numpy
    PATCH_COMMAND ${NUMPY_PATCH}
    CONFIGURE_COMMAND ""
    BUILD_IN_SOURCE 1

    BUILD_COMMAND ${NUMPY_CONF} && ${PYTHON_BINARY} -m pip install --no-build-isolation .

    INSTALL_COMMAND ""
  )

  add_dependencies(
    external_numpy
    external_python
    external_python_site_packages
    external_cython
  )
endif()

unset(_numpy_target_site_packages)
unset(_numpy_wheelhouse)
