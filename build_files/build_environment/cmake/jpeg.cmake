# SPDX-FileCopyrightText: 2017-2022 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

if(WIN32)
  # CMAKE for MS-Windows.
  set(JPEG_EXTRA_ARGS
    -DNASM=${NASM_PATH}
    -DWITH_JPEG8=ON
    -DCMAKE_DEBUG_POSTFIX=d
    -DWITH_CRT_DLL=On
    -DENABLE_SHARED=OFF
    -DENABLE_STATIC=ON
  )

  ExternalProject_Add(external_jpeg
    URL file://${PACKAGE_DIR}/${JPEG_FILE}
    DOWNLOAD_DIR ${DOWNLOAD_DIR}
    URL_HASH ${JPEG_HASH_TYPE}=${JPEG_HASH}
    PREFIX ${BUILD_DIR}/jpeg
    CMAKE_ARGS -DCMAKE_INSTALL_PREFIX=${LIBDIR}/jpeg -DCMAKE_POLICY_VERSION_MINIMUM=3.5 ${DEFAULT_CMAKE_FLAGS} ${JPEG_EXTRA_ARGS}
    INSTALL_DIR ${LIBDIR}/jpeg
  )

  if(BUILD_MODE STREQUAL Release)
    set(JPEG_LIBRARY jpeg-static${LIBEXT})
  else()
    set(JPEG_LIBRARY jpeg-staticd${LIBEXT})
  endif()

  if(BUILD_MODE STREQUAL Release)
    ExternalProject_Add_Step(external_jpeg after_install
      COMMAND ${CMAKE_COMMAND} -E copy
        ${LIBDIR}/jpeg/lib/${JPEG_LIBRARY}
        ${LIBDIR}/jpeg/lib/jpeg${LIBEXT}

      DEPENDEES install
    )
  endif()

else()
  # CMAKE for UNIX.
  set(JPEG_EXTRA_ARGS
    -DWITH_JPEG8=ON
    -DENABLE_STATIC=ON
    -DENABLE_SHARED=OFF
    -DCMAKE_INSTALL_LIBDIR=lib)

  ExternalProject_Add(external_jpeg
    URL file://${PACKAGE_DIR}/${JPEG_FILE}
    DOWNLOAD_DIR ${DOWNLOAD_DIR}
    URL_HASH ${JPEG_HASH_TYPE}=${JPEG_HASH}
    PREFIX ${BUILD_DIR}/jpeg

    CMAKE_ARGS
      -DCMAKE_INSTALL_PREFIX=${LIBDIR}/jpeg
      -DCMAKE_POLICY_VERSION_MINIMUM=3.5
      ${DEFAULT_CMAKE_FLAGS}
      ${JPEG_EXTRA_ARGS}

    INSTALL_DIR ${LIBDIR}/jpeg
  )

  set(JPEG_LIBRARY libjpeg${LIBEXT})

  if(APPLE AND WITH_APPLE_CROSSPLATFORM)
    ExternalProject_Add_Step(external_jpeg copy_libjpeg_turbo_cmake_package
      COMMAND ${CMAKE_COMMAND}
        -DLIBDIR=${LIBDIR}
        -DBUILD_DIR=${BUILD_DIR}
        -P "${CMAKE_CURRENT_LIST_DIR}/install_libjpeg_turbo_cmake.cmake"
      DEPENDEES install
    )
  endif()

  harvest(external_jpeg jpeg/include jpeg/include "*.h")
  harvest(external_jpeg jpeg/lib jpeg/lib "libjpeg.a")
endif()
