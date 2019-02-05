cmake_minimum_required(VERSION 3.5)

Project(ArduinoCode)

# This is sometimes interesting:
set(CMAKE_VERBOSE_MAKEFILE ON)

#Define SDK base dir
set(ARDUINO_SDK_PATH $ENV{ARDUINO_SDK_PATH})

# Define the base dir
set(ARDUINO_BASE_DIR ${CMAKE_CURRENT_SOURCE_DIR})

# We need those info for proper building of the projects
include(${ARDUINO_BASE_DIR}/arduino_crosscompile.cmake)

add_subdirectory(Arduinocore)
add_subdirectory(blinkLED)
add_subdirectory(Controller)
add_subdirectory(Focuser)
