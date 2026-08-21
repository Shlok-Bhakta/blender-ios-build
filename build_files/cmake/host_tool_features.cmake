# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

# makesrna evaluates these options while generating target source. A native
# makesrna built with different values can produce a successful cross-build
# whose RNA metadata is internally inconsistent with the target binary.
set(BLENDER_HOST_TOOL_FEATURES
  WITH_ALEMBIC
  WITH_BULLET
  WITH_CODEC_FFMPEG
  WITH_COREAUDIO
  WITH_CYCLES
  WITH_EXPERIMENTAL_FEATURES
  WITH_FFTW3
  WITH_FREESTYLE
  WITH_GMP
  WITH_IMAGE_CINEON
  WITH_IMAGE_OPENJPEG
  WITH_IMAGE_WEBP
  WITH_INPUT_NDOF
  WITH_INTERNATIONAL
  WITH_JACK
  WITH_METAL_BACKEND
  WITH_MOD_FLUID
  WITH_MOD_OCEANSIM
  WITH_OPENAL
  WITH_OPENGL_BACKEND
  WITH_OPENSUBDIV
  WITH_PULSEAUDIO
  WITH_PYTHON
  WITH_SDL
  WITH_USD
  WITH_VULKAN_BACKEND
  WITH_WASAPI
  WITH_XR_OPENXR
)

function(blender_host_tool_feature_manifest_content result)
  set(_content "schema=1\n")
  foreach(_feature IN LISTS BLENDER_HOST_TOOL_FEATURES)
    if(DEFINED ${_feature} AND ${_feature})
      set(_value ON)
    else()
      set(_value OFF)
    endif()
    string(APPEND _content "${_feature}=${_value}\n")
  endforeach()
  set(${result} "${_content}" PARENT_SCOPE)
endfunction()

function(blender_generate_host_tool_feature_manifest output_path)
  blender_host_tool_feature_manifest_content(_content)
  file(GENERATE OUTPUT "${output_path}" CONTENT "${_content}")
endfunction()

function(blender_validate_host_tool_features manifest_path)
  if(NOT EXISTS "${manifest_path}")
    message(FATAL_ERROR
      "Native host tools are missing feature manifest: ${manifest_path}. "
      "Rebuild the native host tools from this Blender revision."
    )
  endif()

  file(STRINGS "${manifest_path}" _manifest_lines)
  list(FIND _manifest_lines "schema=1" _schema_index)
  if(_schema_index EQUAL -1)
    message(FATAL_ERROR
      "Unsupported native host tools feature manifest: ${manifest_path}. "
      "Rebuild the native host tools from this Blender revision."
    )
  endif()

  set(_mismatches)
  foreach(_feature IN LISTS BLENDER_HOST_TOOL_FEATURES)
    if(DEFINED ${_feature} AND ${_feature})
      set(_expected ON)
    else()
      set(_expected OFF)
    endif()
    list(FIND _manifest_lines "${_feature}=${_expected}" _feature_index)
    if(_feature_index EQUAL -1)
      list(APPEND _mismatches "${_feature}=${_expected} (missing feature or different value)")
    endif()
  endforeach()

  if(_mismatches)
    list(JOIN _mismatches ", " _mismatch_text)
    message(FATAL_ERROR
      "Native host tools do not match the target feature set: ${_mismatch_text}. "
      "Rebuild the native host tools with the same feature profile as the target."
    )
  endif()
endfunction()
