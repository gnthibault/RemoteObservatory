# include our arduino tools
include_directories(${ARDUINO_BASE_DIR}/Arduinocore
                    ${CMAKE_CURRENT_SOURCE_DIR})
LINK_DIRECTORIES(${ARDUINO_BASE_DIR}/Arduinocore)
link_libraries(Arduinocore)

set(sources
    AccelStepper.cpp
    INDIDUINOStepper.cc)

add_executable(INDIDUINOStepper ${sources})
