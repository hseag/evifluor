#----------------------------------------------------------------
# Generated CMake target import file for configuration "RELEASE".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "cjson" for configuration "RELEASE"
set_property(TARGET cjson APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(cjson PROPERTIES
  IMPORTED_IMPLIB_RELEASE "/builds/pro/colibri/evifluor/evifluor-project/api/c/dist/win32/lib/libcjson.dll.a"
  IMPORTED_LOCATION_RELEASE "/builds/pro/colibri/evifluor/evifluor-project/api/c/dist/win32/bin/libcjson.dll"
  )

list(APPEND _cmake_import_check_targets cjson )
list(APPEND _cmake_import_check_files_for_cjson "/builds/pro/colibri/evifluor/evifluor-project/api/c/dist/win32/lib/libcjson.dll.a" "/builds/pro/colibri/evifluor/evifluor-project/api/c/dist/win32/bin/libcjson.dll" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
