# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

if(WITH_APPLE_CROSSPLATFORM)
  set(PYTHON_CROSS_VENV ${BUILD_DIR}/python-cross-venv)
  if(APPLE_TARGET_DEVICE STREQUAL "ios-simulator")
    set(PYTHON_CROSS_SDK iphonesimulator)
  else()
    set(PYTHON_CROSS_SDK iphoneos)
  endif()

  # Native package build frontends must execute on the build machine while
  # observing the target CPython ABI. Keep one disposable environment shared
  # by NumPy, zstandard, and later Python extension recipes.
  ExternalProject_Add(external_python_cross_environment
    PREFIX ${BUILD_DIR}/python-cross-environment
    DOWNLOAD_COMMAND ""
    UPDATE_COMMAND ""
    PATCH_COMMAND ""
    CONFIGURE_COMMAND
      ${CMAKE_COMMAND} -E rm -rf ${PYTHON_CROSS_VENV}
      COMMAND ${PYTHON_BINARY} -m venv ${PYTHON_CROSS_VENV}
      COMMAND ${PYTHON_CROSS_VENV}/bin/python -m pip install
        --disable-pip-version-check
        --cache-dir ${DOWNLOAD_DIR}/python-wheels
        Cython==${CYTHON_VERSION}
        meson-python==${MESON_PYTHON_VERSION}
        meson==${MESON_VERSION}
        packaging==${PACKAGING_VERSION}
        pyproject-metadata==${PYPROJECT_METADATA_VERSION}
        setuptools==${SETUPTOOLS_VERSION}
      COMMAND ${PYTHON_BINARY}
        ${BLENDER_IOS_DEPS_ROOT}/../configure_python_cross_venv.py
        --venv ${PYTHON_CROSS_VENV}
        --python-root ${LIBDIR}/python
        --sdk ${PYTHON_CROSS_SDK}
        --arch arm64
        --deployment-target ${CMAKE_OSX_DEPLOYMENT_TARGET}
        --python-version ${PYTHON_SHORT_VERSION}
    BUILD_COMMAND ""
    INSTALL_COMMAND ""
  )

  add_dependencies(external_python_cross_environment external_python)
endif()
