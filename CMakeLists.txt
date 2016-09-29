cmake_minimum_required(VERSION 3.5.0 FATAL_ERROR)


set(CPM_MODULE_NAME openocd_tools)

#-----------------------------------------------------------------------
# Required CPM Setup - no need to modify - See: https://github.com/iauns/cpm
#-----------------------------------------------------------------------
set(CPM_LIB_TARGET_NAME ${CPM_MODULE_NAME})

if ((DEFINED CPM_DIR) AND (DEFINED CPM_UNIQUE_ID) AND (DEFINED CPM_TARGET_NAME))
    set(CPM_LIB_TARGET_NAME ${CPM_TARGET_NAME})
    set(CMAKE_MODULE_PATH ${CMAKE_MODULE_PATH} ${CPM_DIR})
    include(CPM)
else()
    set (CPM_DIR "${CMAKE_CURRENT_BINARY_DIR}/cpm-packages" CACHE TYPE STRING)
    find_package(Git)
    if(NOT GIT_FOUND)
        message(FATAL_ERROR "CPM requires Git.")
    endif()
    if (NOT EXISTS ${CPM_DIR}/CPM.cmake)
        message(STATUS "Cloning repo (https://github.com/iauns/cpm)")
        execute_process(
            COMMAND "${GIT_EXECUTABLE}" clone https://github.com/iauns/cpm ${CPM_DIR}
            RESULT_VARIABLE error_code
            OUTPUT_QUIET ERROR_QUIET)
        if(error_code)
            message(FATAL_ERROR "CPM failed to get the hash for HEAD")
        endif()
    endif()
    include(${CPM_DIR}/CPM.cmake)
endif()

CPM_InitModule(${CPM_MODULE_NAME})

#-----------------------------------------------------------------------
# Required variables: these should be supplied by the parent CMakeLists
#-----------------------------------------------------------------------
#
# EXE_NAME                  name of compiled executable (e.g. prog.bin)
# EXE_PATH                  path to compiled executable (e.g. /path/prog.bin) 
# ELF_PATH                  path to compiled elf file   (e.g. /path/prog)

# FLASH_FILE                path to flash config file   (e.g. /path/flash.cfg)
# FLASH_CFG                 name of OpenOCD config file (e.g. lpc4337_swd)
# FLASH_ADDR                memory address to write the binary to
#                           (e.g. 0x1A00000000, see microcontroller datasheet)

# DEBUG_BREAKPOINT_LIMIT    maximum breakpoints supported (e.g. 6)
# DEBUG_WATCHPOINT_LIMIT    maximum watchpoints supported (e.g. 4)

#-----------------------------------------------------------------------
# Project sources / settings
#-----------------------------------------------------------------------

set(MODULE_DIR "${CMAKE_CURRENT_LIST_DIR}/${CPM_MODULE_NAME}")
set(FLASH_SCRIPT "${MODULE_DIR}/flash.py")

if(NOT TARGET flash)
    add_custom_target(flash
        COMMAND ${FLASH_SCRIPT} --config ${FLASH_FILE}
    )
endif(NOT TARGET flash)

add_custom_target(flash_${EXE_NAME}
    COMMAND ${FLASH_SCRIPT} ${EXE_PATH} ${FLASH_ADDR} ${FLASH_CFG}
    )

set(DEBUG_CMD "${CMAKE_GDB}" -tui -ex "target remote localhost:3333"
    -ex "set remote hardware-breakpoint-limit ${DEBUG_BREAKPOINT_LIMIT}"
    -ex "set remote hardware-watchpoint-limit ${DEBUG_WATCHPOINT_LIMIT}"
    "${ELF_PATH}")

add_custom_target(debug_${EXE_NAME}
    COMMAND ${DEBUG_CMD})

if(NOT TARGET debug)
    add_custom_target(debug
        DEPENDS debug_${EXE_NAME}
    )
endif(NOT TARGET debug)

