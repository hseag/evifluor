# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: © 2024 HSE AG, <opensource@hseag.com>

cmake_minimum_required(VERSION 3.20)

project(evifluor-commandline LANGUAGES C)

set(TOP ${PROJECT_SOURCE_DIR})

if(EXISTS "${PROJECT_SOURCE_DIR}/.isrepo.txt")
  set(COMMOM        ${TOP}/../../common/module/commandline)
  set(COMMOM_LIB    ${COMMOM}/lib)
  set(COMMOM_CMD    ${COMMOM}/cmd)
  set(FW_COMMON     ${TOP}/../../common/module/firmware/application)
  set(FW            ${TOP}/../firmware/application/src)
else()
  set(COMMOM        ${TOP}/src)
  set(COMMOM_LIB    ${TOP}/src)
  set(COMMOM_CMD    ${TOP}/src)
  set(FW_COMMON     ${TOP}/src)
  set(FW            ${TOP}/src)
endif()

message("TOP DIR    : ${TOP}")
message("COMMOM DIR : ${COMMOM}")

set(CMAKE_VERBOSE_MAKEFILE ON CACHE BOOL "ON")

include(FetchContent)
set(FETCHCONTENT_QUIET FALSE)

add_library(libevifluor SHARED)

target_include_directories(libevifluor PRIVATE "${COMMOM_LIB}" "${PROJECT_SOURCE_DIR}/src" "${FW_COMMON}" "${FW}")

target_sources(libevifluor PRIVATE
  ${COMMOM_LIB}/evibase.h
  ${COMMOM_LIB}/evibase.c
  ${COMMOM_LIB}/crc-16-ccitt.c
  src/evifluor.c
  src/channel.c
  src/channel.h
  src/singlemeasurement.c
  src/singlemeasurement.h
  src/measurement.c
  src/measurement.h
)

# Stuff only for WIN32
if (WIN32)
    add_definitions(-D_CRT_SECURE_NO_WARNINGS)
    target_sources(libevifluor PRIVATE ${COMMOM_LIB}/evi_win.c)
    target_link_libraries(libevifluor setupapi)
endif()

if (UNIX)
    set (CMAKE_C_FLAGS "-Wall")
    target_sources(libevifluor PRIVATE ${COMMOM_LIB}/evi_unix.c)
    target_link_libraries(libevifluor m)
    find_path(LIBUSB_INCLUDE_DIR NAMES libusb.h PATH_SUFFIXES "include" "libusb" "libusb-1.0")
    find_library(LIBUSB_LIBRARY NAMES usb PATH_SUFFIXES "lib" "lib32" "lib64")    
    target_link_libraries(libevifluor usb-1.0)
endif()

set_target_properties(libevifluor PROPERTIES PUBLIC_HEADER "src/evifluor.h;${FW}/evifluorerror.h;${FW}/evifluorindex.h;${FW_COMMON}/commonerror.h;${FW_COMMON}/commonindex.h;${COMMOM_LIB}/evibase.h")

add_executable(evifluor)
target_sources(evifluor PRIVATE
  src/main.c
  src/cmdmeasure.c
  src/cmddata.c
  src/cmdsave.c
  src/cmdbaseline.c
  src/cmdselftest.c
  src/cmdexport.c
  src/cmdempty.c
  src/json.c
  ${COMMOM_CMD}/printerror.c
  ${COMMOM_CMD}/cmdcommand.c
  ${COMMOM_CMD}/cmdfwupdate.c
  ${COMMOM_CMD}/cmdget.c
  ${COMMOM_CMD}/cmdset.c)

FetchContent_Declare(
    cJSON
    GIT_REPOSITORY "https://github.com/DaveGamble/cJSON.git"
    GIT_TAG "v1.7.18"
    GIT_PROGRESS TRUE
    GIT_SHALLOW TRUE
)
set(ENABLE_CJSON_TEST OFF CACHE BOOL "cJSON: Build with unit testing" FORCE)
FetchContent_MakeAvailable(cJSON)

message("cJSON_SOURCE_DIR    : ${cJSON_SOURCE_DIR}")

target_include_directories(evifluor PRIVATE ${cJSON_SOURCE_DIR})
target_include_directories(evifluor PRIVATE ${COMMOM_CMD})
target_include_directories(evifluor PRIVATE ${COMMOM_LIB})
target_include_directories(evifluor PRIVATE "${PROJECT_SOURCE_DIR}/src" "${FW}" "${FW_COMMON}")
target_link_libraries(evifluor PRIVATE libevifluor cjson)

install(TARGETS libevifluor PUBLIC_HEADER)
install(TARGETS evifluor)
