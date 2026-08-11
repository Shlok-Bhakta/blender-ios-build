# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

cmake_minimum_required(VERSION 3.25)
project(BlenderIOSSigningProbe LANGUAGES OBJC)

if(NOT CMAKE_SYSTEM_NAME STREQUAL "iOS")
  message(FATAL_ERROR "The signing probe must be cross-compiled for iOS")
endif()

add_executable(SigningProbe MACOSX_BUNDLE main.m)
target_link_libraries(SigningProbe PRIVATE "-framework UIKit")

set_target_properties(SigningProbe PROPERTIES
  MACOSX_BUNDLE_INFO_PLIST "${CMAKE_CURRENT_SOURCE_DIR}/Info.plist.in"
  XCODE_ATTRIBUTE_GENERATE_INFOPLIST_FILE NO
  XCODE_ATTRIBUTE_PRODUCT_BUNDLE_IDENTIFIER "org.blender.ios-signing-probe"
  XCODE_ATTRIBUTE_TARGETED_DEVICE_FAMILY "1,2"
)
