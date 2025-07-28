cmake_minimum_required(VERSION 3.10)
project(CoCoChain)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find OMNeT++
find_path(OMNETPP_ROOT NAMES bin/omnetpp PATHS /usr/local/omnetpp* /opt/omnetpp* $ENV{OMNETPP_ROOT})
if(NOT OMNETPP_ROOT)
    message(FATAL_ERROR "OMNeT++ not found. Please set OMNETPP_ROOT environment variable.")
endif()

set(OMNETPP_BIN_DIR ${OMNETPP_ROOT}/bin)
set(OMNETPP_INCL_DIR ${OMNETPP_ROOT}/include)
set(OMNETPP_LIB_DIR ${OMNETPP_ROOT}/lib)

# Include directories
include_directories(${OMNETPP_INCL_DIR})
include_directories(src)

# Find Veins
find_path(VEINS_ROOT NAMES src/veins PATHS /usr/local/veins* /opt/veins* $ENV{VEINS_ROOT})
if(VEINS_ROOT)
    include_directories(${VEINS_ROOT}/src)
    link_directories(${VEINS_ROOT}/src)
endif()

# Compiler flags
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -Wextra")

# Source files
file(GLOB_RECURSE SOURCES "src/*.cc" "src/*.cpp")
file(GLOB_RECURSE HEADERS "src/*.h" "src/*.hpp")

# Create executable
add_executable(CoCoChain ${SOURCES})

# Link libraries
target_link_libraries(CoCoChain ${OMNETPP_LIB_DIR}/liboppsim.so)
target_link_libraries(CoCoChain ${OMNETPP_LIB_DIR}/liboppenvir.so)
if(VEINS_ROOT)
    target_link_libraries(CoCoChain veins)
endif()

# Install target
install(TARGETS CoCoChain DESTINATION bin)