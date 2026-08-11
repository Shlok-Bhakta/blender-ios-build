# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

cmake_minimum_required(VERSION 3.25)
project(BlenderFirstPixel LANGUAGES C CXX OBJC OBJCXX)

if(NOT CMAKE_SYSTEM_NAME STREQUAL "iOS")
  message(FATAL_ERROR "BlenderFirstPixel must be configured for iOS")
endif()

add_executable(BlenderFirstPixel MACOSX_BUNDLE main.mm)
target_compile_options(BlenderFirstPixel PRIVATE -fobjc-arc)
target_link_libraries(BlenderFirstPixel PRIVATE
  "-framework Foundation"
  "-framework UIKit"
  "-framework CoreGraphics"
  "-framework Metal"
  "-framework QuartzCore"
)

set_target_properties(BlenderFirstPixel PROPERTIES
  MACOSX_BUNDLE_INFO_PLIST "${CMAKE_CURRENT_SOURCE_DIR}/Info.plist.in"
  MACOSX_BUNDLE_BUNDLE_NAME "Blender First Pixel"
  MACOSX_BUNDLE_GUI_IDENTIFIER "org.blenderfoundation.blender.firstpixel"
  MACOSX_BUNDLE_SHORT_VERSION_STRING "1.0"
  MACOSX_BUNDLE_BUNDLE_VERSION "1"
  XCODE_ATTRIBUTE_CODE_SIGNING_ALLOWED "NO"
)
