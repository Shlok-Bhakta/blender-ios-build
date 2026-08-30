# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

# Preserve Blender's SBOM targets while resolving their static inputs from the
# upstream dependency tree rather than this standalone iOS project root.

set(SBOMCONTENTS "")
set(SBOM_FIRST_ENTRY TRUE)
get_cmake_property(_variableNames VARIABLES)
foreach(_variableName ${_variableNames})
  if(_variableName MATCHES "CPE$")
    string(REPLACE ":" ";" CPE_LIST ${${_variableName}})
    list(GET CPE_LIST 3 CPE_VENDOR)
    list(GET CPE_LIST 4 CPE_NAME)
    list(GET CPE_LIST 5 CPE_VERSION)
    if(SBOM_FIRST_ENTRY)
      set(SBOM_SEPARATOR "")
      set(SBOM_FIRST_ENTRY FALSE)
    else()
      set(SBOM_SEPARATOR ",\n")
    endif()
    set(SBOM_ENTRY "    {\n")
    string(APPEND SBOM_ENTRY "      \"type\": \"library\",\n")
    string(APPEND SBOM_ENTRY "      \"name\": \"${CPE_NAME}\",\n")
    string(APPEND SBOM_ENTRY "      \"version\": \"${CPE_VERSION}\",\n")
    string(APPEND SBOM_ENTRY "      \"cpe\": \"${${_variableName}}\"\n")
    string(APPEND SBOM_ENTRY "    }")
    string(APPEND SBOMCONTENTS "${SBOM_SEPARATOR}${SBOM_ENTRY}")
  endif()
endforeach()

configure_file(
  "${BLENDER_UPSTREAM_DEPS_ROOT}/cmake/sbom.json.in"
  "${CMAKE_CURRENT_BINARY_DIR}/sbom.json"
  @ONLY
)

add_custom_target(cve_check
  COMMAND grype
    sbom:${CMAKE_CURRENT_BINARY_DIR}/sbom.json
    -o table
    -v
    --sort-by package
    --config ${BLENDER_UPSTREAM_DEPS_ROOT}/cmake/grype.yaml
  SOURCES ${CMAKE_CURRENT_BINARY_DIR}/sbom.json
)

add_custom_target(cve_check_txt
  COMMAND grype
    sbom:${CMAKE_CURRENT_BINARY_DIR}/sbom.json
    -o table
    --sort-by package
    --file ${CMAKE_CURRENT_BINARY_DIR}/grype_results.txt
    --config ${BLENDER_UPSTREAM_DEPS_ROOT}/cmake/grype.yaml
  SOURCES ${CMAKE_CURRENT_BINARY_DIR}/sbom.json
)
