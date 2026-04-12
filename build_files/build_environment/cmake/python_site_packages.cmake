# SPDX-FileCopyrightText: 2017-2023 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

if(WIN32 AND BUILD_MODE STREQUAL Debug)
  set(SITE_PACKAGES_EXTRA --global-option build --global-option --debug)
  # zstandard is determined to build and link release mode libs in a debug
  # configuration, the only way to make it happy is to bend to its will
  # and give it a library to link with.
  set(
    PIP_CONFIGURE_COMMAND ${CMAKE_COMMAND} -E copy
    ${LIBDIR}/python/libs/python${PYTHON_SHORT_VERSION_NO_DOTS}_d.lib
    ${LIBDIR}/python/libs/python${PYTHON_SHORT_VERSION_NO_DOTS}.lib
  )
else()
  set(PIP_CONFIGURE_COMMAND echo ".")
endif()

set(PIP_CONSTRAINT_FILE ${BUILD_DIR}/constraints.txt)
  # setuptools-scm is causing issues with their latest version
  # issue: https://github.com/pypa/setuptools-scm/issues/1316
  # but pinning it doesn't work since downstream package dependencies
  # also seem to resolve the later versions
  # we can alter this behaviour by using pip constraints
file(WRITE ${PIP_CONSTRAINT_FILE}
"setuptools-scm==${SETUPTOOLS_SCM_VERSION}\n"
)

# Target Python is not executable on the build host (e.g. iOS simulator); use the
# host build-python from the cross prefix and install pure packages into LIBDIR/python.
if(WITH_APPLE_CROSSPLATFORM)
  set(PYTHON_PIP_EXECUTABLE ${CMAKE_DEPS_CROSSCOMPILE_INSTALLDIR}/python/bin/python${PYTHON_SHORT_VERSION})
  set(PIP_DEST_PREFIX_ARG --prefix=${LIBDIR}/python)
else()
  set(PYTHON_PIP_EXECUTABLE ${PYTHON_BINARY})
  set(PIP_DEST_PREFIX_ARG "")
endif()

ExternalProject_Add(external_python_site_packages
  DOWNLOAD_COMMAND ""
  CONFIGURE_COMMAND ${PIP_CONFIGURE_COMMAND}
  BUILD_COMMAND ""
  PREFIX ${BUILD_DIR}/site_packages

  # We do not build numpy, cython, or zstandard here as the pip builds are not reproducible.
  INSTALL_COMMAND
    ${CMAKE_COMMAND} -E env
      PIP_CONSTRAINT=${PIP_CONSTRAINT_FILE}
      ${PYTHON_PIP_EXECUTABLE} -m pip install --no-cache-dir ${PIP_DEST_PREFIX_ARG} ${SITE_PACKAGES_EXTRA}
      setuptools==${SETUPTOOLS_VERSION}
      meson-python==${MESON_PYTHON_VERSION}
      packaging==${PACKAGING_VERSION}
      pyproject-metadata==${PYPROJECT_METADATA_VERSION}
      idna==${IDNA_VERSION}
      charset-normalizer==${CHARSET_NORMALIZER_VERSION}
      urllib3==${URLLIB3_VERSION}
      certifi==${CERTIFI_VERSION}
      requests==${REQUESTS_VERSION}
      autopep8==${AUTOPEP8_VERSION}
      pycodestyle==${PYCODESTYLE_VERSION}
      meson==${MESON_VERSION}
      attrs==${ATTRS_VERSION}
      cattrs==${CATTRS_VERSION}
      fastjsonschema==${FASTJSONSCHEMA_VERSION}
      typing-extensions==${TYPING_EXTENSIONS_VERSION}
      --no-binary :all:
)

add_dependencies(
  external_python_site_packages
  external_python
)
