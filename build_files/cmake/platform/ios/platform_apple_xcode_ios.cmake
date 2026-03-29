set(CMAKE_OSX_ARCHITECTURES "arm64" CACHE STRING "" FORCE)

if(APPLE_TARGET_DEVICE STREQUAL "ios")
  set(CMAKE_SYSTEM_NAME "iOS" CACHE INTERNAL "" FORCE)
  set(APPLE_TARGET_IOS TRUE)
  set(APPLE_SDK_NAME "iPhoneOS")
  set(APPLE_SDK_NAME_LOWER "iphoneos")
  set(OSX_MIN_DEPLOYMENT_TARGET 16.0)
  set(APPLE_OS_MINVERSION_CFLAG "-miphoneos-version-min=${OSX_MIN_DEPLOYMENT_TARGET}")
elseif(APPLE_TARGET_DEVICE STREQUAL "ios-simulator")
  set(CMAKE_SYSTEM_NAME "iOS" CACHE INTERNAL "" FORCE)
  set(APPLE_TARGET_IOS TRUE)
  set(APPLE_SDK_NAME "iPhoneSimulator")
  set(APPLE_SDK_NAME_LOWER "iphonesimulator")
  set(OSX_MIN_DEPLOYMENT_TARGET 16.0)
  set(APPLE_OS_MINVERSION_CFLAG "-miphonesimulator-version-min=${OSX_MIN_DEPLOYMENT_TARGET}")
else()
  message(FATAL_ERROR "Unsupported APPLE_TARGET_DEVICE=${APPLE_TARGET_DEVICE}")
endif()

set(CMAKE_OSX_DEPLOYMENT_TARGET "${OSX_MIN_DEPLOYMENT_TARGET}" CACHE STRING "" FORCE)

execute_process(
  COMMAND xcode-select --print-path
  OUTPUT_VARIABLE XCODE_DEVELOPER_DIR OUTPUT_STRIP_TRAILING_WHITESPACE
)

if(NOT ${CMAKE_GENERATOR} MATCHES "Xcode")
  execute_process(
    COMMAND xcodebuild -version
    OUTPUT_VARIABLE _xcode_vers_build_nr
    RESULT_VARIABLE _xcode_vers_result
    ERROR_QUIET)

  if(_xcode_vers_result EQUAL 0)
    string(REPLACE "\n" " " _xcode_vers_build_nr_single_line "${_xcode_vers_build_nr}")
    string(REGEX REPLACE "(.*)Xcode ([0-9\\.]+).*" "\\2" XCODE_VERSION "${_xcode_vers_build_nr_single_line}")
    unset(_xcode_vers_build_nr_single_line)
  endif()

  unset(_xcode_vers_build_nr)
  unset(_xcode_vers_result)
endif()

if(NOT XCODE_VERSION)
  message(FATAL_ERROR "No Xcode detected")
endif()

if(${XCODE_VERSION} VERSION_LESS 16.0)
  message(FATAL_ERROR "Only Xcode version 16.0 and newer is supported")
endif()

set(XCODE_PLATFORM_DIR ${XCODE_DEVELOPER_DIR}/Platforms/${APPLE_SDK_NAME}.platform)
set(XCODE_SDK_DIR ${XCODE_PLATFORM_DIR}/Developer/SDKs)

if(NOT DEFINED OSX_SYSTEM)
  execute_process(
    COMMAND xcodebuild -version -sdk ${APPLE_SDK_NAME_LOWER} SDKVersion
    OUTPUT_VARIABLE OSX_SYSTEM
    OUTPUT_STRIP_TRAILING_WHITESPACE
  )
endif()

message(STATUS "Detected ${APPLE_SDK_NAME} ${OSX_SYSTEM} and Xcode ${XCODE_VERSION} at ${XCODE_DEVELOPER_DIR}")
message(STATUS "SDKs Directory: ${XCODE_SDK_DIR}")

set(OSX_SDK_TEST_VERSIONS ${OSX_SYSTEM})
if(OSX_SYSTEM MATCHES "([0-9]+)\\.([0-9]+)\\.([0-9]+)")
  string(REGEX REPLACE "([0-9]+)\\.([0-9]+)\\.([0-9]+)" "\\1.\\2" OSX_SYSTEM_NO_PATCH "${OSX_SYSTEM}")
  list(APPEND OSX_SDK_TEST_VERSIONS ${OSX_SYSTEM_NO_PATCH})
  unset(OSX_SYSTEM_NO_PATCH)
endif()

set(OSX_SDK_PATH "")
set(OSX_SDK_FOUND FALSE)
set(OSX_SDKROOT "")
foreach(OSX_SDK_VERSION ${OSX_SDK_TEST_VERSIONS})
  set(CURRENT_OSX_SDK_PATH "${XCODE_SDK_DIR}/${APPLE_SDK_NAME}${OSX_SDK_VERSION}.sdk")
  if(EXISTS ${CURRENT_OSX_SDK_PATH})
    set(OSX_SDK_PATH "${CURRENT_OSX_SDK_PATH}")
    set(OSX_SDKROOT ${APPLE_SDK_NAME_LOWER}${OSX_SDK_VERSION})
    set(OSX_SDK_FOUND TRUE)
    break()
  endif()
endforeach()
unset(OSX_SDK_TEST_VERSIONS)

if(NOT OSX_SDK_FOUND)
  message(FATAL_ERROR "Unable to find SDK for ${APPLE_SDK_NAME} version ${OSX_SYSTEM}")
endif()

message(STATUS "Detected ${APPLE_SDK_NAME} SYSROOT: ${OSX_SDK_PATH}")

set(CMAKE_OSX_SYSROOT ${OSX_SDK_PATH} CACHE PATH "" FORCE)
unset(OSX_SDK_PATH)
unset(OSX_SDK_FOUND)

if(${CMAKE_GENERATOR} MATCHES "Xcode")
  set(CMAKE_XCODE_ATTRIBUTE_SDKROOT ${OSX_SDKROOT})
endif()
unset(OSX_SDKROOT)

set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
set(CMAKE_FIND_FRAMEWORK FIRST)
set(CMAKE_SYSTEM_FRAMEWORK_PATH
  ${XCODE_PLATFORM_DIR}/System/Library/Frameworks
  ${XCODE_PLATFORM_DIR}/System/Library/PrivateFrameworks
  ${XCODE_PLATFORM_DIR}/Developer/Library/Frameworks
)

if(NOT ${CMAKE_GENERATOR} MATCHES "Xcode")
  string(APPEND CMAKE_C_FLAGS " ${APPLE_OS_MINVERSION_CFLAG}")
  string(APPEND CMAKE_CXX_FLAGS " ${APPLE_OS_MINVERSION_CFLAG}")
  add_definitions("-DMACOSX_DEPLOYMENT_TARGET=${CMAKE_OSX_DEPLOYMENT_TARGET}")
endif()
