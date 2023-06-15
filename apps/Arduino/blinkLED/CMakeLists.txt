# include our arduino tools
include_directories(${ARDUINO_BASE_DIR}/Arduinocore)
LINK_DIRECTORIES(${ARDUINO_BASE_DIR}/Arduinocore)
link_libraries(Arduinocore)
add_executable(blinkLED blinkLED.cc)
